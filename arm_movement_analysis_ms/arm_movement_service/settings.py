import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY_ARM', 'django-insecure-change-this-in-production')

DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS_ARM', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
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

MOVEMENT_ANALYSIS_CONFIG = {
    'acceleration_threshold': float(os.getenv('ACCELERATION_THRESHOLD', '2.0')),
    'min_segment_length': int(os.getenv('MIN_SEGMENT_LENGTH', '3')),
    'change_point_penalty': float(os.getenv('CHANGE_POINT_PENALTY', '3')),

    'no_movement_velocity_threshold': float(os.getenv('NO_MOVEMENT_VELOCITY_THRESHOLD', '0.01')),
    'excessive_movement_velocity_threshold': float(os.getenv('EXCESSIVE_MOVEMENT_VELOCITY_THRESHOLD', '0.15')),
    'min_consecutive_frames': int(os.getenv('MIN_CONSECUTIVE_FRAMES', '3')),  # Minimum frames to consider a pattern

    'segmentation_window_size': int(os.getenv('SEGMENTATION_WINDOW_SIZE', '15')),  # Frames in sliding window
    'average_change_threshold': float(os.getenv('AVERAGE_CHANGE_THRESHOLD', '0.08')),  # Significant average change
    'trend_change_threshold': float(os.getenv('TREND_CHANGE_THRESHOLD', '0.008')),  # Significant trend change
    'min_segment_gap': int(os.getenv('MIN_SEGMENT_GAP', '20')),  # Minimum frames between segments
}
