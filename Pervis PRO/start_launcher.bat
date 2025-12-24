@echo off
echo Starting Pervis PRO Launcher...
echo.

REM Check if Python is available
py --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python not found. Please install Python 3.11 or later.
    echo You can download it from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if required packages are installed
py -c "import customtkinter, requests, psutil" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing required packages...
    py -m pip install -r launcher/requirements.txt
)

REM Start the launcher
echo Starting launcher...
py launcher/main.py

if %errorlevel% neq 0 (
    echo.
    echo Launcher failed to start. Check the error messages above.
    pause
)