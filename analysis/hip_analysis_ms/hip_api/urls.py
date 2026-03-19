from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('hip/<str:recording_id>/analyze/', views.analyze_hip_movement, name='analyze_hip_movement'),
]
