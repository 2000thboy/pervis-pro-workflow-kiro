@echo off
chcp 65001 >nul
echo ===============================================
echo     Pervis PRO Simple Installation
echo ===============================================
echo.

set PROJECT_ROOT=%~dp0

echo [1/3] Checking current environment...
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✓ Python is installed
    python --version
) else (
    echo ❌ Python not found
    echo Please install Python 3.10+ from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    goto :manual_install
)

REM Check Node.js
node --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✓ Node.js is installed
    node --version
) else (
    echo ❌ Node.js not found
    echo Please install Node.js 18+ from: https://nodejs.org/
    echo.
    goto :manual_install
)

REM Check Git
git --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✓ Git is installed
    git --version
) else (
    echo ❌ Git not found
    echo Please install Git from: https://git-scm.com/
    echo.
    goto :manual_install
)

echo.
echo [2/3] Installing project dependencies...
echo.

REM Install backend dependencies
echo Installing backend dependencies...
cd /d "%PROJECT_ROOT%\backend"

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment and installing packages...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

if %errorlevel% == 0 (
    echo ✓ Backend dependencies installed
) else (
    echo ❌ Backend installation failed
    goto :error
)

REM Install frontend dependencies
echo.
echo Installing frontend dependencies...
cd /d "%PROJECT_ROOT%\frontend"

npm install

if %errorlevel% == 0 (
    echo ✓ Frontend dependencies installed
) else (
    echo ❌ Frontend installation failed
    goto :error
)

REM Install launcher dependencies
echo.
echo Installing launcher dependencies...
cd /d "%PROJECT_ROOT%"
pip install customtkinter pillow

if %errorlevel% == 0 (
    echo ✓ Launcher dependencies installed
) else (
    echo ❌ Launcher installation failed
    goto :error
)

echo.
echo [3/3] Creating configuration file...

REM Create .env file if it doesn't exist
if not exist "backend\.env" (
    echo Creating backend\.env file...
    (
        echo # AI Configuration
        echo GEMINI_API_KEY=your_gemini_api_key_here
        echo LLM_PROVIDER=gemini
        echo.
        echo # Database Configuration
        echo DATABASE_URL=sqlite:///./pervis_director.db
        echo.
        echo # Storage Configuration
        echo ASSET_ROOT=./storage/assets
        echo STORAGE_ROOT=./storage
        echo.
        echo # Network Configuration
        echo NETWORK_DRIVE=L
        echo NETWORK_DRIVE_NAME=影片参考
    ) > backend\.env
    echo ✓ Configuration file created
) else (
    echo ✓ Configuration file already exists
)

echo.
echo ===============================================
echo     Installation Complete!
echo ===============================================
echo.
echo Next steps:
echo 1. Get Gemini API key: https://makersuite.google.com/app/apikey
echo 2. Edit backend\.env file and set GEMINI_API_KEY
echo 3. Run project: python 启动_Pervis_PRO.py
echo.
echo Optional: Install FFmpeg for video processing
echo Download from: https://www.ffmpeg.org/download.html
echo.
goto :end

:manual_install
echo.
echo ===============================================
echo     Manual Installation Required
echo ===============================================
echo.
echo Please install the missing components first:
echo.
echo 1. Python 3.10+: https://www.python.org/downloads/
echo    ⚠ Important: Check "Add Python to PATH"
echo.
echo 2. Node.js 18+: https://nodejs.org/
echo.
echo 3. Git: https://git-scm.com/
echo.
echo After installation, restart this script.
echo.
echo For detailed instructions, see: README_安装说明.md
echo.
goto :end

:error
echo.
echo ===============================================
echo     Installation Error
echo ===============================================
echo.
echo Some dependencies failed to install.
echo Please check the error messages above.
echo.
echo You can try:
echo 1. Run this script as Administrator
echo 2. Check your internet connection
echo 3. Use manual installation from README_安装说明.md
echo.
goto :end

:end
cd /d "%PROJECT_ROOT%"
pause