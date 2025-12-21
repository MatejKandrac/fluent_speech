set -a
source ../.env
set +a

echo Starting Arm Analysis Service
python manage.py runserver ${ARM_MOVEMENT_PORT:8002}
