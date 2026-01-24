@echo off
REM Garden Tracker Quick Start Script for Windows
REM This script sets up and runs the Garden Tracker application

echo =============================
echo Garden Tracker Setup
echo =============================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python 3 is not installed or not in PATH.
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

echo [OK] Python found
python --version
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo [OK] Virtual environment activated
echo.

REM Install dependencies
echo Installing dependencies...
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo [OK] Dependencies installed
echo.

REM Check if .env file exists
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env >nul
    echo.
    echo ========================================
    echo IMPORTANT: Please edit .env file!
    echo ========================================
    echo Update DATABASE_URL with your PostgreSQL credentials
    echo.
    echo For PostgreSQL:
    echo   DATABASE_URL=postgresql://username:password@localhost:5432/garden_tracker
    echo.
    echo For SQLite (simpler, no PostgreSQL needed):
    echo   DATABASE_URL=sqlite:///garden_tracker.db
    echo.
    pause
)

REM Initialize database with sample data
echo.
set /p INIT="Would you like to initialize with sample data? (y/N): "
if /i "%INIT%"=="y" (
    echo.
    echo Initializing database with sample data...
    python init_db.py
    echo.
)

echo =============================
echo Starting Garden Tracker...
echo =============================
echo.
echo The app will be available at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

REM Run the application
python app.py

pause
