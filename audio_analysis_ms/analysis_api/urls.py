from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('audio/<str:recording_id>/analyze/', views.analyze_audio, name='analyze_audio'),
]
