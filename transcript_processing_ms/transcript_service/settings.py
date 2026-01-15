import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY_TRANSCRIPT', 'django-insecure-transcript-processing-dev-key-2024')

DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS_TRANSCRIPT', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'rest_framework',
    'transcript_api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'transcript_service.urls'

WSGI_APPLICATION = 'transcript_service.wsgi.application'

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

WHISPER_CONFIG = {
    # Whisper model configuration
    'whisper_model': os.getenv('WHISPER_MODEL', 'base'),  # tiny, base, small, medium, large
    'word_timestamps': os.getenv('WHISPER_WORD_TIMESTAMPS', 'True') == 'True',
    'temperature': float(os.getenv('WHISPER_TEMPERATURE', '0.0')),
    'no_speech_threshold': float(os.getenv('WHISPER_NO_SPEECH_THRESHOLD', '0.2')),
    'logprob_threshold': float(os.getenv('WHISPER_LOGPROB_THRESHOLD', '-1.0')),
    'compression_ratio_threshold': float(os.getenv('WHISPER_COMPRESSION_RATIO_THRESHOLD', '3.0')),

    # Token suppression - empty string = no suppression (preserves filler words)
    'suppress_tokens': os.getenv('WHISPER_SUPPRESS_TOKENS', '').strip(),  # Empty = preserve all tokens

    # Processing configuration
    'min_audio_duration': float(os.getenv('MIN_AUDIO_DURATION', '1.0')),  # minimum seconds for processing
    'save_transcript_to_file': os.getenv('SAVE_TRANSCRIPT_TO_FILE', 'True') == 'True',
}
