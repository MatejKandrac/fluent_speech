@echo off
echo Setting up Eye Contact Analysis Microservice...

REM Create virtual environment
python -m venv venv

REM Activate virtual environment
call venv\Scripts\activate

REM Install dependencies
pip install -r requirements.txt

echo.
echo Setup complete!
echo Run 'run.bat' to start the server
pause
