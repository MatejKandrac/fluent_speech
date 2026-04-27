import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY_EYE', 'django-insecure-eye-contact-dev-key-2024')

DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS_EYE', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'rest_framework',
    'gaze_api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'eye_contact_service.urls'

WSGI_APPLICATION = 'eye_contact_service.wsgi.application'

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

EYE_CONTACT_ANALYSIS_CONFIG = {
    'yaw_min': float(os.getenv('YAW_MIN', '-90')),  # degrees
    'yaw_max': float(os.getenv('YAW_MAX', '90')),
    'yaw_bin_size': float(os.getenv('YAW_BIN_SIZE', '5')),

    'pitch_min': float(os.getenv('PITCH_MIN', '-30')),
    'pitch_max': float(os.getenv('PITCH_MAX', '30')),
    'pitch_bin_size': float(os.getenv('PITCH_BIN_SIZE', '5')),

    'audience_yaw_min': float(os.getenv('AUDIENCE_YAW_MIN', '-30')),
    'audience_yaw_max': float(os.getenv('AUDIENCE_YAW_MAX', '30')),
    'audience_pitch_min': float(os.getenv('AUDIENCE_PITCH_MIN', '-15')),
    'audience_pitch_max': float(os.getenv('AUDIENCE_PITCH_MAX', '15')),

    'min_looking_away_duration': int(os.getenv('EYE_CONTACT_MIN_LOOKING_AWAY_DURATION', '330')),

    'staring_angle_threshold': float(os.getenv('STARING_ANGLE_THRESHOLD', '3')),  # degrees
    'min_staring_time': int(os.getenv('MIN_STARING_MS', '2000')),  # ~2 seconds at 15fps

    # Median-filter window (in frames) applied to ear Δz before recomputing yaw.
    # Larger smooths more MP z-noise but blurs fast head turns. 1 disables smoothing.
    'yaw_smoothing_window': int(os.getenv('YAW_SMOOTHING_WINDOW', '5')),

    # Back facing
    'back_facing_threshold': float(os.getenv('BACK_FACING_THRESHOLD', '-0.1')),
    'min_back_facing_duration': int(os.getenv('MIN_BACK_FACING_DURATION', '300')),

    'pitch_scale': float(os.getenv('PITCH_SCALE', '1.0')),  # unused by current formula, kept for config compat
    'pitch_bias': float(os.getenv('PITCH_BIAS', '20')),

    'eye_segmentation_sensitivity': float(os.getenv('EYE_SEGMENTATION_SENSITIVITY', '0.5')),
}
