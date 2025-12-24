@echo off
chcp 65001 >nul
title Pervis PRO - 检查并启动

echo ===============================================
echo     Pervis PRO 环境检查与启动
echo ===============================================
echo.

REM 检查基础环境
echo [1/2] 检查环境...
echo.

set MISSING=0

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✓ Python 已安装
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo   %%i
) else (
    echo ❌ Python 未安装
    set MISSING=1
)

REM 检查 Node.js
node --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✓ Node.js 已安装
    for /f "tokens=*" %%i in ('node --version 2^>^&1') do echo   %%i
) else (
    echo ❌ Node.js 未安装
    set MISSING=1
)

REM 检查 Git
git --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✓ Git 已安装
    for /f "tokens=*" %%i in ('git --version 2^>^&1') do echo   %%i
) else (
    echo ❌ Git 未安装
    set MISSING=1
)

REM 检查项目依赖
echo.
echo [2/2] 检查项目依赖...
echo.

if exist "backend\venv" (
    echo ✓ 后端虚拟环境已创建
) else (
    echo ❌ 后端虚拟环境未创建
    set MISSING=1
)

if exist "frontend\node_modules" (
    echo ✓ 前端依赖已安装
) else (
    echo ❌ 前端依赖未安装
    set MISSING=1
)

if exist "backend\.env" (
    echo ✓ 配置文件存在
    
    REM 检查 API 密钥
    findstr /C:"your_gemini_api_key_here" "backend\.env" >nul
    if %errorlevel% == 0 (
        echo ⚠ 需要配置 Gemini API 密钥
        echo   请编辑 backend\.env 文件
    ) else (
        echo ✓ API 密钥已配置
    )
) else (
    echo ❌ 配置文件不存在
    set MISSING=1
)

echo.
echo ===============================================

if %MISSING% == 1 (
    echo     需要完成环境安装
    echo ===============================================
    echo.
    echo 请先运行以下安装脚本之一：
    echo.
    echo 1. 完全自动安装（推荐）:
    echo    以管理员身份运行 PowerShell
    echo    执行: .\完全自动安装.ps1 -Force
    echo.
    echo 2. 简单安装:
    echo    双击: simple_install.bat
    echo.
    echo 3. 手动安装:
    echo    查看: README_安装说明.md
    echo.
    echo 详细指南请查看: 开始这里.md
    echo.
    goto :end
) else (
    echo     环境检查通过！
    echo ===============================================
    echo.
    echo 正在启动 Pervis PRO...
    echo.
    
    REM 启动项目
    if exist "启动_Pervis_PRO.py" (
        python "启动_Pervis_PRO.py"
    ) else (
        echo 启动文件不存在，请手动启动：
        echo.
        echo 终端 1 - 后端:
        echo cd backend
        echo python -m uvicorn main:app --reload --port 8000
        echo.
        echo 终端 2 - 前端:
        echo cd frontend  
        echo npm run dev
        echo.
    )
)

:end
echo.
pause