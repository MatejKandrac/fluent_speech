from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('analyze/<str:recording_id>/', views.run_analysis, name='run_analysis'),
]
