import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY_SEGMENTATION', 'django-insecure-segmentation-dev-key')

DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS_SEGMENTATION', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'rest_framework',
    'segmentation_api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'segmentation_service.urls'
WSGI_APPLICATION = 'segmentation_service.wsgi.application'

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

SEGMENTATION_CONFIG = {
    # Penalty bounds for PELT. sensitivity=0 → max_penalty (fewest segments),
    # sensitivity=1 → min_penalty (most segments). Log scale is used.
    'min_penalty': float(os.getenv('SEGMENTATION_MIN_PENALTY', '1.0')),
    'max_penalty': float(os.getenv('SEGMENTATION_MAX_PENALTY', '500.0')),
    # Default sensitivity when caller does not specify one
    'default_sensitivity': float(os.getenv('SEGMENTATION_DEFAULT_SENSITIVITY', '0.5')),
    # Minimum number of samples a segment must contain (ruptures min_size)
    'min_segment_samples': int(os.getenv('SEGMENTATION_MIN_SEGMENT_SAMPLES', '2')),
}
