from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),

    path('video/<str:video_id>/analyze/', views.analyze_video, name='analyze_video'),
]
