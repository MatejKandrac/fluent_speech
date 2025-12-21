set -a
source ../.env
set +a

echo Starting Video Analysis microservice
python manage.py runserver ${VIDEO_ANALYSIS_PORT:8001}
