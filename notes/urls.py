from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('upload/', views.upload_note, name='upload'),
    path('notes/', views.notes_list, name='notes_list'),
    path('notes/<int:pk>/', views.note_detail, name='note_detail'),
    path('notes/<int:pk>/edit/', views.note_edit, name='note_edit'),
    path('profile/', views.user_profile, name='user_profile'),
    path('settings/', views.user_settings, name='user_settings'),
    path('logout/', views.logout_view, name='logout'),
]