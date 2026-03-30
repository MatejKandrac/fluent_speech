import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY_HIP', 'django-insecure-change-this-in-production')

DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS_HIP', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'rest_framework',
    'hip_api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'hip_analysis_ms.urls'

WSGI_APPLICATION = 'hip_analysis_ms.wsgi.application'

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

SEGMENTATION_SERVICE_URL = os.getenv('SEGMENTATION_SERVICE_URL', 'http://localhost:8010')

HIP_ANALYSIS_CONFIG = {
    'min_hip_direction_changes': float(os.getenv('MIN_HIP_DIRECTION_CHANGES', 4)),
    'min_hip_amplitude_change': float(os.getenv('MIN_HIP_AMPLITUDE_CHANGE', 0.02)),
    'hip_window_duration': float(os.getenv('HIP_WINDOW_DURATION_MS', 3000)),
    'hip_segmentation_bin_size': float(os.getenv('HIP_SEGMENTATION_BIN_SIZE', '10.0')),
    'hip_segmentation_sensitivity': float(os.getenv('HIP_SEGMENTATION_SENSITIVITY', '0.5')),
}
