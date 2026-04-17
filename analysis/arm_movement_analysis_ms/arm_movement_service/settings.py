import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY_ARM', 'django-insecure-change-this-in-production')

DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS_ARM', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'rest_framework',
    'movement_api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'arm_movement_service.urls'

WSGI_APPLICATION = 'arm_movement_service.wsgi.application'

POSTGRES_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'fluent'),
    'user': os.getenv('DB_USERNAME', ''),
    'password': os.getenv('DB_PASSWORD', ''),
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

MOVEMENT_ANALYSIS_CONFIG = {
    'no_movement_velocity_threshold': float(os.getenv('NO_MOVEMENT_VELOCITY_THRESHOLD', '0.01')),
    'excessive_movement_velocity_threshold': float(os.getenv('EXCESSIVE_MOVEMENT_VELOCITY_THRESHOLD', '0.15')),
    'min_consecutive_duration_ms': int(os.getenv('MIN_CONSECUTIVE_DURATION_MS', '333')),
    'excessive_min_consecutive_duration_ms': int(os.getenv('EXCESSIVE_MIN_CONSECUTIVE_DURATION_MS', '0')),
    'excessive_merge_gap_ms': int(os.getenv('EXCESSIVE_MERGE_GAP_MS', '600')),
    'arm_segmentation_sensitivity': float(os.getenv('ARM_SEGMENTATION_SENSITIVITY', '0.5')),
}
