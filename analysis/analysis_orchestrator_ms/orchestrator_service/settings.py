import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY_ORCHESTRATOR', 'django-insecure-orchestrator-dev-key')

DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS_ORCHESTRATOR', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'rest_framework',
    'orchestrator_api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'orchestrator_service.urls'

WSGI_APPLICATION = 'orchestrator_service.wsgi.application'

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

ANALYSIS_SERVICES = {
    'arm_movement': os.getenv('ARM_MOVEMENT_SERVICE_URL', 'http://localhost:8002'),
    'eye_contact':  os.getenv('EYE_CONTACT_SERVICE_URL',  'http://localhost:8003'),
    'pitch':        os.getenv('PITCH_ANALYSIS_SERVICE_URL', 'http://localhost:8005'),
    'volume':       os.getenv('VOLUME_ANALYSIS_SERVICE_URL', 'http://localhost:8006'),
    'hip':          os.getenv('HIP_ANALYSIS_SERVICE_URL',   'http://localhost:8007'),
    'filler_words': os.getenv('FILLER_WORDS_SERVICE_URL',  'http://localhost:8008'),
}

PERFORMANCE_SERVICE_URL = os.getenv('PERFORMANCE_SERVICE_URL', 'http://localhost:8012')

# Timeout per analysis service call in seconds
ANALYSIS_TIMEOUT = int(os.getenv('ANALYSIS_TIMEOUT', 120))