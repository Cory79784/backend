@echo off
REM GeoGLI Chatbot API - Quick Start Script for Windows
REM This script starts the API server locally

echo ========================================
echo GeoGLI Chatbot API - Starting Server
echo ========================================
echo.

REM Check if we're in the right directory
if not exist "backend\app\main.py" (
    echo ERROR: backend\app\main.py not found!
    echo Please run this script from the API directory.
    pause
    exit /b 1
)

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/4] Checking Python version...
python --version

REM Check if virtual environment exists
if not exist "backend\.venv" (
    echo.
    echo [2/4] Creating virtual environment...
    cd backend
    python -m venv .venv
    cd ..
) else (
    echo.
    echo [2/4] Virtual environment already exists
)

REM Activate virtual environment and install dependencies
echo.
echo [3/4] Installing dependencies...
cd backend
call .venv\Scripts\activate.bat

REM Check if requirements are installed
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Installing Python packages...
    pip install --upgrade pip
    pip install -r requirements.txt
) else (
    echo Dependencies already installed
)

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo.
    echo Creating .env file from .env.example...
    copy .env.example .env
)

REM Start the server
echo.
echo [4/4] Starting API server...
echo.
echo ========================================
echo Server will start at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo Health Check: http://localhost:8000/api/dify/health
echo ========================================
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

REM Deactivate virtual environment on exit
deactivate
cd ..
