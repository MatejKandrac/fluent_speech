@echo off
echo Starting Hand Movement Analysis Microservice...
echo.

REM Start Django server
cd hand_movement_analysis_ms
echo Starting Django server on port 8002...
python manage.py runserver 8002
