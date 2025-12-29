from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('analyze-filler-words/<int:recording_id>/', views.analyze_filler_words, name='analyze_filler_words'),
]
