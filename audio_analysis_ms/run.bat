@echo off
echo Starting Audio Analysis Microservice...
echo.

REM Run Django development server
cd audio_analysis_ms
python manage.py runserver 8004

pause
