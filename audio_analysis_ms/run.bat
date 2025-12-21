set -a
source ../.env
set +a

echo Starting Audio Analysis Microservice...
python manage.py runserver ${AUDIO_ANALYSIS_PORT:8004}