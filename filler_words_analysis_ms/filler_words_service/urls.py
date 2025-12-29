from django.urls import path, include

urlpatterns = [
    path('api/', include('speech_api.urls')),
]
