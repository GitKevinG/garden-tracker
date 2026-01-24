@echo off
REM Garden Tracker Quick Start Script for Windows (SQLite Version)
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
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated
echo.

REM Install dependencies
echo Installing dependencies...
python -m pip install --upgrade pip --quiet
pip install -r requirements-sqlite.txt --quiet
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

REM Check if .env file exists
if not exist ".env" (
    echo Creating .env file...
    (
        echo DATABASE_URL=sqlite:///garden_tracker.db
        echo SECRET_KEY=dev-secret-key-change-in-production
        echo FLASK_ENV=development
        echo LAST_FROST_DATE=04-15
        echo FIRST_FROST_DATE=10-15
    ) > .env
    echo [OK] .env file created with SQLite configuration
    echo.
) else (
    echo [OK] .env file already exists
    echo.
)

REM Initialize database with sample data
echo.
set /p INIT="Would you like to initialize with sample data? (Y/n): "
if /i not "%INIT%"=="n" (
    echo.
    echo Initializing database with sample data...
    python init_db.py
    if %errorlevel% neq 0 (
        echo WARNING: Database initialization had issues, but continuing...
    )
    echo.
)

echo =============================
echo Starting Garden Tracker...
echo =============================
echo.
echo The app will be available at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.
echo Sample Login Info (if you initialized data):
echo - 7 seed varieties ready to use
echo - 7 grow bags configured
echo - Zone 7a/b planting calendar
echo.

REM Run the application
python app.py

pause
