from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('pitch/<str:recording_id>/analyze/', views.analyze_pitch, name='analyze_pitch'),
]
