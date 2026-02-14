from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout as auth_logout
from django.contrib.auth.forms import UserCreationForm
from .models import Note, UserProfile
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
import easyocr
import pytesseract
from transformers import pipeline
import re

# Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# EasyOCR reader (initialize once)
reader = easyocr.Reader(['en'], gpu=False)

# Summarization pipeline (initialize once)
try:
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
except:
    summarizer = None

def advanced_preprocess(image):
    """Advanced image preprocessing for better OCR"""
    # Convert to numpy array
    img = np.array(image)
    
    # Convert to grayscale
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        gray = img
    
    # Resize if too small
    height, width = gray.shape
    if height < 600 or width < 600:
        scale = max(600/height, 600/width)
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    
    # Increase contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    contrast = clahe.apply(denoised)
    
    # Sharpen
    kernel = np.array([[-1,-1,-1],
                       [-1, 9,-1],
                       [-1,-1,-1]])
    sharpened = cv2.filter2D(contrast, -1, kernel)
    
    # Adaptive threshold
    thresh = cv2.adaptiveThreshold(
        sharpened, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    # Morphological operations
    kernel = np.ones((1,1), np.uint8)
    morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    return Image.fromarray(morph)

def extract_text_from_image(image):
    """Enhanced OCR for both printed and handwritten text"""
    try:
        # Convert to numpy array
        img_array = np.array(image)
        
        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Resize if too small
        height, width = gray.shape
        if height < 1000 or width < 1000:
            scale = max(1000/height, 1000/width)
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        # Multiple approaches
        results = []
        
        # Method 1: Simple binary threshold (best for printed text)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        text1 = pytesseract.image_to_string(binary, config='--psm 3 --oem 3')
        results.append(text1)
        
        # Method 2: Denoise + enhance (for digital screenshots)
        denoised = cv2.fastNlMeansDenoising(gray, None, h=10)
        text2 = pytesseract.image_to_string(denoised, config='--psm 6 --oem 3')
        results.append(text2)
        
        # Method 3: EasyOCR (slower but good for tricky text)
        try:
            easyocr_result = reader.readtext(gray, detail=0, paragraph=True)
            text3 = '\n'.join(easyocr_result)
            results.append(text3)
        except:
            pass
        
        # Get best result (longest valid text)
        valid_results = [r for r in results if len(r.strip()) > 10]
        
        if valid_results:
            best_text = max(valid_results, key=lambda x: len(x.strip()))
            return best_text
        else:
            return "No text detected. Please try:\n- Better image quality\n- Higher resolution\n- Clearer lighting"
        
    except Exception as e:
        return f"Error processing image: {str(e)}"
 
def generate_summary(text):
    """Generate AI summary of text"""
    try:
        if not text or len(text.strip()) < 50:
            return "Text too short to summarize"
        
        # Clean text
        text = text.strip()
        
        # Limit text length (model has token limit)
        if len(text) > 1000:
            text = text[:1000]
        
        # Generate summary
        if summarizer:
            summary = summarizer(text, max_length=150, min_length=30, do_sample=False)
            return summary[0]['summary_text']
        else:
            # Fallback: simple extraction
            sentences = text.split('.')
            return '. '.join(sentences[:3]) + '.'
            
    except Exception as e:
        return "Could not generate summary"

def extract_keywords(text):
    """Extract important keywords from text"""
    try:
        # Simple keyword extraction
        words = re.findall(r'\b[A-Z][a-z]+\b|\b[a-z]{4,}\b', text)
        word_freq = {}
        for word in words:
            word = word.lower()
            if len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top 10 keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, freq in sorted_words[:10]]
        
        return ', '.join(keywords)
    except:
        return ""
            
def home(request):
    return render(request, 'home.html')

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def upload_note(request):
    if request.method == 'POST':
        title = request.POST['title']
        image_file = request.FILES['image']
        
        try:
            img = Image.open(image_file)
            
            # Extract text
            extracted_text = extract_text_from_image(img)
            
            # Save to database
            note = Note.objects.create(
                user=request.user,
                title=title,
                original_image=image_file,
                extracted_text=extracted_text
            )
            
            # Redirect to edit page so user can fix mistakes
            return redirect('note_edit', pk=note.pk)
            
        except Exception as e:
            return render(request, 'notes/upload.html', {
                'error': f'Error processing image: {str(e)}'
            })
    
    return render(request, 'notes/upload.html')

@login_required
def notes_list(request):
    notes = Note.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'notes/list.html', {'notes': notes})

@login_required
def note_detail(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    
    # Split keywords for template
    keywords_list = []
    if note.keywords:
        keywords_list = [k.strip() for k in note.keywords.split(',')]
    
    return render(request, 'notes/detail.html', {
        'note': note,
        'keywords_list': keywords_list
    })

@login_required
def note_edit(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    
    if request.method == 'POST':
        note.extracted_text = request.POST['text']
        
        # Generate summary if requested
        if 'generate_summary' in request.POST:
            note.summary = generate_summary(note.extracted_text)
            note.keywords = extract_keywords(note.extracted_text)
        
        note.save()
        return redirect('note_detail', pk=pk)
    
    return render(request, 'notes/edit.html', {'note': note})

@login_required
def user_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    notes = Note.objects.filter(user=request.user).order_by('-created_at')
    total_notes = notes.count()
    
    context = {
        'profile': profile,
        'notes': notes,
        'total_notes': total_notes,
    }
    return render(request, 'notes/profile.html', context)

@login_required
def user_settings(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        
        profile.bio = request.POST.get('bio', '')
        profile.phone = request.POST.get('phone', '')
        profile.location = request.POST.get('location', '')
        
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']
        
        profile.save()
        return redirect('user_settings')
    
    return render(request, 'notes/settings.html', {'profile': profile})

def logout_view(request):
    auth_logout(request)
    return redirect('login')