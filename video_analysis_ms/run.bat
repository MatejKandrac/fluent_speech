@echo off
echo Starting Video Analysis Microservice...
echo.

@REM REM Activate virtual environment
@REM if exist venv\Scripts\activate.bat (
@REM     call venv\Scripts\activate.bat
@REM ) else (
@REM     echo ERROR: Virtual environment not found!
@REM     echo Please run: python -m venv venv
@REM     echo Then run: venv\Scripts\activate.bat
@REM     echo Then run: pip install -r requirements.txt
@REM     paus
@REM     exit /b 1
@REM )

REM Start Django server
cd video_analysis_ms
echo Starting Django server on port 8001...
python manage.py runserver 8001
