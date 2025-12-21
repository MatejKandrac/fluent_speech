set -a
source ../.env
set +a

echo Starting Eye contact microservice
python manage.py runserver ${EYE_CONTACT_PORT:8003}
