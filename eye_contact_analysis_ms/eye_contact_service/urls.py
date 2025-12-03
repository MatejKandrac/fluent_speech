"""URL configuration for eye_contact_service."""
from django.urls import path, include

urlpatterns = [
    path('api/v1/', include('gaze_api.urls')),
]
