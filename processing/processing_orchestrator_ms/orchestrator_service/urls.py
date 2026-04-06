from django.urls import path, include

urlpatterns = [
    path('api/v1/processing/', include('orchestrator_api.urls')),
]
