"""
URL patterns for the arm movement analysis API.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health_check'),

    # Arm movement analysis endpoint with anomaly detection
    path('analyze/arm-movements/<int:recording_id>/', views.analyze_arm_movements, name='analyze_arm_movements'),
]
