# NoteScan AI
Convert handwritten notes and printed text to digital format using AI-powered OCR.

## Tech Stack
Backend: Django 5.0  
OCR: Tesseract (printed text), EasyOCR (handwriting)  
Image Processing: OpenCV, Pillow  
AI: Hugging Face Transformers (BART for summarization)  
Frontend: Bootstrap 5, JavaScript  
Database: SQLite  

## Key Features
- Dual OCR mode (printed/handwritten)
- Image preprocessing pipeline (denoise, contrast enhance, threshold)
- Manual text editing interface
- AI text summarization
- Keyword extraction
- User profiles and authentication

## Installation
Clone and setup
```
git clone <repo-url>
cd NoteScanAI
python -m venv venv
source venv/bin/activate
```
Windows: venv\Scripts\activate
Install dependencies
```
pip install -r requirements.txt
```
Install Tesseract OCR
- Windows: https://github.com/UB-Mannheim/tesseract/wiki
- Mac: brew install tesseract
- Linux: sudo apt install tesseract-ocr
Run migrations and start server
```
python manage.py migrate
python manage.py runserver
```

## How It Works
1. Upload image and select text type (printed/handwritten)
2. OCR extracts text with preprocessing
3. Edit extracted text manually
4. Generate AI summary (optional)
5. Save and manage notes

## Accuracy
- Printed text: 95-99%
- Clear handwriting: 60-80%
- Cursive: 30-50%

## Why These Technologies
Tesseract: Fast and accurate for printed text  
EasyOCR: Better handwriting recognition using deep learning  
OpenCV: Image quality enhancement improves OCR accuracy  
BART: Pre-trained summarization model, no fine-tuning needed  
Manual Edit: OCR is never 100% accurate, user correction essential  
