@echo off
chcp 65001 >nul
title Pervis PRO 启动器

cd /d "%~dp0"

:: 检查 Python
py --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ╔══════════════════════════════════════════════════════════════╗
    echo ║  错误: 未检测到 Python                                       ║
    echo ║                                                              ║
    echo ║  请先安装 Python 3.x:                                        ║
    echo ║  https://www.python.org/downloads/                           ║
    echo ║                                                              ║
    echo ║  安装时请勾选 "Add Python to PATH"                           ║
    echo ╚══════════════════════════════════════════════════════════════╝
    echo.
    pause
    exit /b 1
)

:: 启动图形界面
py 一键启动.py
