from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('volume/<str:recording_id>/analyze/', views.analyze_volume, name='analyze_volume'),
]
