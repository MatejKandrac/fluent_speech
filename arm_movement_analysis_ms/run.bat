@echo off
echo Starting Arm Movement Analysis Microservice...
echo.

REM Start Django server
cd arm_movement_analysis_ms
echo Starting Django server on port 8002...
python manage.py runserver 8002
