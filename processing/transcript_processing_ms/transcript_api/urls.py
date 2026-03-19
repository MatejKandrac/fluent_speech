from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('<int:recording_id>/transcribe/', views.process_transcript, name='process_transcript'),
]
