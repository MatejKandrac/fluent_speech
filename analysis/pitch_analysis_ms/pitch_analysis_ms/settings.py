import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY_PITCH', 'django-insecure-change-this-in-production')

DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS_PITCH', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'rest_framework',
    'pitch_api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'pitch_analysis_ms.urls'

WSGI_APPLICATION = 'pitch_analysis_ms.wsgi.application'

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

PITCH_ANALYSIS_CONFIG = {
    'pitch_grace_period': float(os.getenv('PITCH_GRACE_PERIOD_MS', 100)),
    'monotonous_window_size': int(os.getenv('MONOTONOUS_WINDOW_SIZE', 30)),
    'monotonous_std_threshold': float(os.getenv('MONOTONOUS_STD_THRESHOLD', 10.0)),
    'monotonous_range_threshold': float(os.getenv('MONOTONOUS_RANGE_THRESHOLD', 20.0)),
    'monotonous_merge_gap_ms': float(os.getenv('MONOTONOUS_MERGE_GAP_MS', 2500)),
    'monotonous_min_duration_ms': float(os.getenv('MONOTONOUS_MIN_DURATION_MS', 3000)),
}