"""
URL patterns for the audio analysis API.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('analyze/audio/<str:recording_id>/', views.analyze_audio, name='analyze_audio'),
]
