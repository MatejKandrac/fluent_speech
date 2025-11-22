"""
URL patterns for the movement analysis API.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health_check'),

    # Hand movement analysis endpoint
    path('analyze/hand-movements/<str:video_id>/', views.analyze_hand_movements, name='analyze_hand_movements'),
]
