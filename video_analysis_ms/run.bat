@echo off
echo Starting Video Analysis Microservice...
echo.

REM Start Django server
cd video_analysis_ms
echo Starting Django server on port 8001...
python manage.py runserver 8001
