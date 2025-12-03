@echo off
echo Starting Eye Contact Analysis Microservice...
echo .

REM Run Django development server
cd eye_contact_analysis_ms
python manage.py runserver 8003

pause
