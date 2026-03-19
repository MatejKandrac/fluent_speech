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

EYE_CONTACT_ANALYSIS_CONFIG = {
    'yaw_min': float(os.getenv('YAW_MIN', '-60')),  # degrees
    'yaw_max': float(os.getenv('YAW_MAX', '60')),
    'yaw_bin_size': float(os.getenv('YAW_BIN_SIZE', '5')),

    'pitch_min': float(os.getenv('PITCH_MIN', '-30')),
    'pitch_max': float(os.getenv('PITCH_MAX', '30')),
    'pitch_bin_size': float(os.getenv('PITCH_BIN_SIZE', '5')),

    'audience_yaw_min': float(os.getenv('AUDIENCE_YAW_MIN', '-30')),
    'audience_yaw_max': float(os.getenv('AUDIENCE_YAW_MAX', '30')),
    'audience_pitch_min': float(os.getenv('AUDIENCE_PITCH_MIN', '-15')),
    'audience_pitch_max': float(os.getenv('AUDIENCE_PITCH_MAX', '15')),

    'min_consecutive_frames': int(os.getenv('EYE_CONTACT_MIN_CONSECUTIVE_FRAMES', '5')),

    'staring_angle_threshold': float(os.getenv('STARING_ANGLE_THRESHOLD', '3')),  # degrees
    'min_staring_frames': int(os.getenv('MIN_STARING_FRAMES', '30')),  # ~2 seconds at 15fps

    # Yaw calculation weights (must sum to 1.0)
    'yaw_weight_ear_ratio': float(os.getenv('YAW_WEIGHT_EAR_RATIO', '0.5')),
    'yaw_weight_nose_face': float(os.getenv('YAW_WEIGHT_NOSE_FACE', '0.2')),
    'yaw_weight_nose_shoulder': float(os.getenv('YAW_WEIGHT_NOSE_SHOULDER', '0.3')),

    # Back facing
    'back_facing_threshold': float(os.getenv('BACK_FACING_THRESHOLD', '-0.1')),
}
