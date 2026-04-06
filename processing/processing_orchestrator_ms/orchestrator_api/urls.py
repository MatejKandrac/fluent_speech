from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('status/', views.get_processing_status, name='get_processing_status'),
    path('upload/', views.upload_video, name='upload_video')
]
