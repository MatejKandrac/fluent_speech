from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('filler-words/<int:recording_id>/analyze/', views.analyze_filler_words, name='analyze_filler_words'),
]
