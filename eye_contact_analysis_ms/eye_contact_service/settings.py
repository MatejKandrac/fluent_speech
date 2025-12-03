"""Django settings for eye_contact_service."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-eye-contact-dev-key-2024')

DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'gaze_api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'eye_contact_service.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'eye_contact_service.wsgi.application'

# Database - Using default SQLite for Django admin
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# PostgreSQL Configuration (accessed directly via psycopg2)
POSTGRES_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'fluent'),
    'user': os.getenv('DB_USERNAME', ''),
    'password': os.getenv('DB_PASSWORD', ''),
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
}

# Eye Contact Analysis Configuration
EYE_CONTACT_ANALYSIS_CONFIG = {
    # Heatmap configuration
    'yaw_min': float(os.getenv('YAW_MIN', '-60')),  # degrees
    'yaw_max': float(os.getenv('YAW_MAX', '60')),
    'yaw_bin_size': float(os.getenv('YAW_BIN_SIZE', '5')),

    'pitch_min': float(os.getenv('PITCH_MIN', '-30')),
    'pitch_max': float(os.getenv('PITCH_MAX', '30')),
    'pitch_bin_size': float(os.getenv('PITCH_BIN_SIZE', '5')),

    # Audience zone thresholds (what counts as "looking at audience")
    'audience_yaw_min': float(os.getenv('AUDIENCE_YAW_MIN', '-30')),
    'audience_yaw_max': float(os.getenv('AUDIENCE_YAW_MAX', '30')),
    'audience_pitch_min': float(os.getenv('AUDIENCE_PITCH_MIN', '-15')),
    'audience_pitch_max': float(os.getenv('AUDIENCE_PITCH_MAX', '15')),

    # Event detection
    'min_consecutive_frames': int(os.getenv('MIN_CONSECUTIVE_FRAMES', '5')),

    # Staring detection (staying in same position too long)
    'staring_angle_threshold': float(os.getenv('STARING_ANGLE_THRESHOLD', '3')),  # degrees
    'min_staring_frames': int(os.getenv('MIN_STARING_FRAMES', '30')),  # ~2 seconds at 15fps
}
