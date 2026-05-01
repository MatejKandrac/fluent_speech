import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY_FILLER', 'django-insecure-filler-words-dev-key-2024')

DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS_FILLER', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'rest_framework',
    'speech_api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'filler_words_service.urls'

WSGI_APPLICATION = 'filler_words_service.wsgi.application'

POSTGRES_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'fluent'),
    'user': os.getenv('DB_USERNAME', ''),
    'password': os.getenv('DB_PASSWORD', ''),
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

PITCH_ANALYSIS_SERVICE_URL = os.getenv('PITCH_ANALYSIS_SERVICE_URL', 'http://localhost:8005')
SEGMENTATION_SERVICE_URL = os.getenv('SEGMENTATION_SERVICE_URL', 'http://localhost:8010')

FILLER_WORDS_CONFIG = {
    'slovak_fillers': ['ehm', 'ehh', 'emm', 'hm', 'hmm', 'teda', 'akože', 'takže', 'vlastne', 'viete', 'no', 'proste', 'čiže', 'inak', 'vieš', 'skrátka'],
    'english_fillers': ['uh', 'um', 'hmm', 'like', 'you know', 'so', 'actually', 'basically', 'literally', 'well'],

    # Analysis thresholds
    'high_filler_threshold_per_minute': float(os.getenv('HIGH_FILLER_THRESHOLD', '5')),
    'min_speech_duration': float(os.getenv('MIN_SPEECH_DURATION', '10')),
    'min_word_probability': float(os.getenv('FILLER_MIN_WORD_PROBABILITY', '0.7')),

    # Sliding-window stable-pitch candidate detection
    'uhh_window_ms': float(os.getenv('UHH_WINDOW_MS', '200')),
    'uhh_min_voiced_fraction': float(os.getenv('UHH_MIN_VOICED_FRACTION', '0.5')),
    'uhh_pitch_std_threshold': float(os.getenv('UHH_PITCH_STD_THRESHOLD', '8.0')),
    'uhh_min_voiced_duration_ms': float(os.getenv('UHH_MIN_VOICED_DURATION_MS', '150')),
    'uhh_max_run_duration_ms': float(os.getenv('UHH_MAX_RUN_DURATION_MS', '800')),
    'uhh_flux_max': float(os.getenv('UHH_FLUX_MAX', '0')),  # 0 = disabled
    # Bottom-up zone detection
    'segmentation_bin_size': float(os.getenv('FILLER_SEGMENTATION_BIN_SIZE', '10.0')),
    'bottom_up_merge_k': float(os.getenv('FILLER_BOTTOM_UP_MERGE_K', '1.0')),
    'peak_zone_threshold_multiplier': float(os.getenv('FILLER_PEAK_ZONE_MULTIPLIER', '2.0')),
}
