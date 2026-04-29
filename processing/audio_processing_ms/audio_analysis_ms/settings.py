import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY_AUDIO', 'django-insecure-change-this-in-production')

DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS_AUDIO', 'localhost,127.0.0.1').split(',')

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

ROOT_URLCONF = 'audio_analysis_ms.urls'

WSGI_APPLICATION = 'audio_analysis_ms.wsgi.application'

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

# Audio Extraction Configuration
AUDIO_EXTRACTION_CONFIG = {
    'sample_rate': int(os.getenv('AUDIO_SAMPLE_RATE', '16000')),
}

# Noise Reduction Configuration
# prop_decrease controls aggressiveness: 1.0 = full removal, 0.5 = 50% attenuation.
# Stationary mode estimates a fixed noise profile from the whole signal — can misidentify
# monotone speech as noise. Reduce prop_decrease or disable if pitch detection suffers.
NOISE_REDUCTION_CONFIG = {
    'enabled': os.getenv('NOISE_REDUCTION_ENABLED', 'True') == 'True',
    'prop_decrease': float(os.getenv('NOISE_REDUCTION_PROP_DECREASE', '0.5')),
}

# Transcript Processing Service Configuration
TRANSCRIPT_SERVICE_URL = os.getenv('TRANSCRIPT_SERVICE_URL', 'http://localhost:8009/api/v1')
AUTO_TRIGGER_TRANSCRIPTION = os.getenv('AUTO_TRIGGER_TRANSCRIPTION', 'True') == 'True'

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

