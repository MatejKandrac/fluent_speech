"""
URL configuration for audio_analysis_service project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('analysis_api.urls')),
]
