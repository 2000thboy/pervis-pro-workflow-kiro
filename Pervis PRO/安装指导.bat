@echo off
chcp 65001 >nul
echo ===============================================
echo     Pervis PRO 安装指导
echo ===============================================
echo.
echo 检测结果：系统缺少以下必需组件
echo ❌ Python 未安装
echo ❌ Node.js 未安装  
echo ❌ Git 未安装
echo ❌ FFmpeg 未安装
echo.
echo ===============================================
echo     立即安装以下组件：
echo ===============================================
echo.
echo 1. Python 3.10+
echo    下载地址: https://www.python.org/downloads/
echo    重要：安装时勾选 "Add Python to PATH"
echo.
echo 2. Node.js 18+
echo    下载地址: https://nodejs.org/
echo    选择 LTS 版本
echo.
echo 3. Git
echo    下载地址: https://git-scm.com/
echo.
echo 4. FFmpeg (可选，用于视频处理)
echo    下载地址: https://www.ffmpeg.org/download.html
echo.
echo ===============================================
echo     安装完成后的步骤：
echo ===============================================
echo.
echo 1. 重启命令行 (重要！)
echo.
echo 2. 运行环境安装脚本:
echo    python setup_environment.py
echo.
echo 3. 配置 API 密钥:
echo    编辑 backend\.env 文件，添加:
echo    GEMINI_API_KEY=your_api_key_here
echo.
echo 4. 启动项目:
echo    python 启动_Pervis_PRO.py
echo.
echo ===============================================
echo     获取 Gemini API 密钥：
echo ===============================================
echo.
echo 访问: https://makersuite.google.com/app/apikey
echo 创建新的 API 密钥
echo.
echo ===============================================
echo.
echo 正在打开详细安装说明...
start "" "README_安装说明.md"
echo.
pause