from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('analyze/arm-movements/<int:recording_id>/', views.analyze_arm_movements, name='analyze_arm_movements'),
]
