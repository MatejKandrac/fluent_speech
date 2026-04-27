import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY_PERFORMANCE', 'django-insecure-performance-dev-key')

DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS_PERFORMANCE', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'rest_framework',
    'performance_api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'performance_service.urls'

WSGI_APPLICATION = 'performance_service.wsgi.application'

TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Performance dimension weights — loaded from .env
WEIGHT_VOICE       = float(os.getenv('WEIGHT_VOICE',       '0.37'))
WEIGHT_FLUENCY     = float(os.getenv('WEIGHT_FLUENCY',     '0.27'))
WEIGHT_EYE_CONTACT = float(os.getenv('WEIGHT_EYE_CONTACT', '0.27'))
WEIGHT_BODY        = float(os.getenv('WEIGHT_BODY',        '0.09'))

# Filler distribution penalty (model v3)
# Penalises uniform filler distribution more than concentrated (per H2.1 finding)
FILLER_DISTRIBUTION_BINS        = int(os.getenv('FILLER_DISTRIBUTION_BINS',        '6'))
FILLER_DISTRIBUTION_MAX_PENALTY = float(os.getenv('FILLER_DISTRIBUTION_MAX_PENALTY', '20.0'))
FILLER_DISTRIBUTION_CV_THRESHOLD = float(os.getenv('FILLER_DISTRIBUTION_CV_THRESHOLD', '1.0'))

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
}
