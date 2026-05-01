import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY_VOLUME', 'django-insecure-change-this-in-production')

DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS_VOLUME', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'rest_framework',
    'volume_api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'volume_analysis_ms.urls'

WSGI_APPLICATION = 'volume_analysis_ms.wsgi.application'

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

VIDEO_STORAGE_PATH = os.getenv('VIDEO_STORAGE_PATH', 'D:/VideoData')

SEGMENTATION_SERVICE_URL = os.getenv('SEGMENTATION_SERVICE_URL', 'http://localhost:8010')

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

VOLUME_ANALYSIS_CONFIG = {
    'silence_floor_dbfs': float(os.getenv('VOLUME_SILENCE_FLOOR_DBFS', -60.0)),
    'soft_margin_db': float(os.getenv('VOLUME_SOFT_MARGIN_DB', 8.0)),
    'loud_margin_db': float(os.getenv('VOLUME_LOUD_MARGIN_DB', 6.0)),
    'min_segment_duration_ms': float(os.getenv('VOLUME_MIN_SEGMENT_MS', 500.0)),
    'merge_gap_s': float(os.getenv('VOLUME_MERGE_GAP_S', 0.5)),
    'min_bad_frame_coverage': float(os.getenv('VOLUME_MIN_BAD_FRAME_COVERAGE', 0.5)),
    'segmentation_sensitivity': float(os.getenv('VOLUME_SEGMENTATION_SENSITIVITY', 0.2)),
}
