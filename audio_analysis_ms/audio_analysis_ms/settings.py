import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY_AUDIO', 'django-insecure-change-this-in-production')

DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS_AUDIO', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'rest_framework',
    'analysis_api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'audio_analysis_ms.urls'

WSGI_APPLICATION = 'audio_analysis_ms.wsgi.application'

POSTGRES_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'fluent'),
    'user': os.getenv('DB_USERNAME', ''),
    'password': os.getenv('DB_PASSWORD', ''),
}

VIDEO_STORAGE_PATH = os.getenv('VIDEO_STORAGE_PATH', 'D:/VideoData')

# Audio Extraction Configuration
AUDIO_EXTRACTION_CONFIG = {
    'sample_rate': int(os.getenv('AUDIO_SAMPLE_RATE', '22050')),  # Audio sample rate in Hz
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

