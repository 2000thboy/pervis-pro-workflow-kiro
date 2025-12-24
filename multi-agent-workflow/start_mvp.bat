@echo off
echo ========================================
echo Multi-Agent Workflow MVP 启动脚本
echo ========================================
echo.

cd /d "%~dp0backend"

echo 检查Python环境...
py --version
if errorlevel 1 (
    echo 错误: 未找到Python，请确保已安装Python 3.11+
    pause
    exit /b 1
)

echo.
echo 启动MVP服务...
echo 访问 http://localhost:8000/docs 查看API文档
echo 按 Ctrl+C 停止服务
echo.

py start_mvp.py

pause
