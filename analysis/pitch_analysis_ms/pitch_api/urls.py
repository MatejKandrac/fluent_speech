from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('pitch/<str:recording_id>/analyze/', views.analyze_pitch, name='analyze_pitch'),
    path('pitch/<str:recording_id>/timeseries/', views.get_pitch_timeseries, name='get_pitch_timeseries'),
]
