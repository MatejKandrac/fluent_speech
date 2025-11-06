"""
URL patterns for the analysis API.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health_check'),

    # Video analysis endpoints
    path('analyze/video/<str:video_id>/', views.analyze_video, name='analyze_video'),
    path('analysis/<str:analysis_id>/', views.get_analysis, name='get_analysis'),
    path('analysis/video/<str:video_id>/', views.get_video_analyses, name='get_video_analyses'),
    path('analysis/<str:analysis_id>/delete/', views.delete_analysis, name='delete_analysis'),
]
