import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY_VIDEO', 'django-insecure-change-this-in-production')

DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS_VIDEO', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'rest_framework',
    'analysis_api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'video_analysis_service.urls'

WSGI_APPLICATION = 'video_analysis_service.wsgi.application'

POSTGRES_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'fluent'),
    'user': os.getenv('DB_USERNAME', ''),
    'password': os.getenv('DB_PASSWORD', ''),
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': POSTGRES_CONFIG['database'],
        'USER': POSTGRES_CONFIG['user'],
        'PASSWORD': POSTGRES_CONFIG['password'],
        'HOST': POSTGRES_CONFIG['host'],
        'PORT': POSTGRES_CONFIG['port'],
    }
}

TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
}

VIDEO_STORAGE_PATH = os.getenv('VIDEO_STORAGE_PATH', 'D:/VideoData')

MEDIAPIPE_CONFIG = {
    'min_detection_confidence': 0.5,
    'min_tracking_confidence': 0.5,
    'model_complexity': 1,  # 0, 1, or 2 (higher = more accurate but slower)
}

VIDEO_PROCESSING_CONFIG = {
    'frame_interval': float(os.getenv('FRAME_INTERVAL', '0.2')),  # Process frame every N seconds
    'max_video_duration': 600,  # Maximum video duration in seconds (10 minutes)
}

AUDIO_EXTRACTION_CONFIG = {
    'sample_rate': int(os.getenv('AUDIO_SAMPLE_RATE', '22050')),  # Audio sample rate in Hz
}

AUDIO_ANALYSIS_SERVICE_URL = os.getenv('AUDIO_ANALYSIS_SERVICE_URL', 'http://localhost:8004')
