from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health'),
    path('analyze/eye-contact/<int:recording_id>/', views.analyze_eye_contact, name='analyze_eye_contact'),
]
