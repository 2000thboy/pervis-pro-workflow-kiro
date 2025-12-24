@echo off
chcp 65001 >nul
echo ========================================
echo   Pervis PRO Environment Check
echo ========================================
echo.

echo Checking Python...
python --version 2>nul
if %errorlevel% neq 0 (
    echo Python: Not installed
    py --version 2>nul
    if %errorlevel% neq 0 (
        echo py command: Not available
    ) else (
        echo py command: Available
    )
) else (
    echo Python: Installed
)
echo.

echo Checking Node.js...
node --version 2>nul
if %errorlevel% neq 0 (
    echo Node.js: Not installed
) else (
    echo Node.js: Installed
)
echo.

echo Checking Git...
git --version 2>nul
if %errorlevel% neq 0 (
    echo Git: Not installed
) else (
    echo Git: Installed
)
echo.

echo Checking FFmpeg...
ffmpeg -version 2>nul | findstr "ffmpeg version" >nul
if %errorlevel% neq 0 (
    echo FFmpeg: Not installed
) else (
    echo FFmpeg: Installed
)
echo.

echo Checking Ollama...
ollama --version 2>nul
if %errorlevel% neq 0 (
    echo Ollama: Not installed
) else (
    echo Ollama: Installed
)
echo.

echo ========================================
echo   Directory Structure Check
echo ========================================
if exist "backend" (
    echo Backend folder: Found
    if exist "backend\requirements.txt" (
        echo requirements.txt: Found
    ) else (
        echo requirements.txt: Not found
    )
    if exist "backend\venv" (
        echo Virtual environment: Found
    ) else (
        echo Virtual environment: Not found
    )
) else (
    echo Backend folder: Not found
)

if exist "frontend" (
    echo Frontend folder: Found
    if exist "frontend\package.json" (
        echo package.json: Found
    ) else (
        echo package.json: Not found
    )
) else (
    echo Frontend folder: Not found
)

if exist "launcher" (
    echo Launcher folder: Found
) else (
    echo Launcher folder: Not found
)
echo.

echo ========================================
echo   Next Steps
echo ========================================
echo 1. Install missing components manually
echo 2. Run: python setup_environment.py
echo 3. Or run: python 启动_Pervis_PRO.py
echo.
pause