# Pervis PRO 完整环境安装脚本
# 适用于 Windows 系统

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Pervis PRO 环境安装向导" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Continue"
$projectRoot = $PSScriptRoot

# 检查 Python
Write-Host "[1/7] 检查 Python 环境..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ 已安装: $pythonVersion" -ForegroundColor Green
    
    # 检查版本是否 >= 3.10
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
            Write-Host "⚠ 警告: Python 版本过低，建议 3.10+，当前: $pythonVersion" -ForegroundColor Red
        }
    }
} catch {
    Write-Host "✗ 未检测到 Python！" -ForegroundColor Red
    Write-Host "  请从 https://www.python.org/downloads/ 下载并安装 Python 3.10+" -ForegroundColor Red
    Write-Host "  安装时请勾选 'Add Python to PATH'" -ForegroundColor Yellow
    exit 1
}

# 检查 Node.js
Write-Host ""
Write-Host "[2/7] 检查 Node.js 环境..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✓ 已安装: $nodeVersion" -ForegroundColor Green
    
    # 检查版本是否 >= 18
    if ($nodeVersion -match "v(\d+)\.") {
        $major = [int]$matches[1]
        if ($major -lt 18) {
            Write-Host "⚠ 警告: Node.js 版本过低，建议 18+，当前: $nodeVersion" -ForegroundColor Red
        }
    }
} catch {
    Write-Host "✗ 未检测到 Node.js！" -ForegroundColor Red
    Write-Host "  请从 https://nodejs.org/ 下载并安装 Node.js 18+" -ForegroundColor Red
    exit 1
}

# 检查 FFmpeg
Write-Host ""
Write-Host "[3/7] 检查 FFmpeg..." -ForegroundColor Yellow
try {
    $ffmpegVersion = ffmpeg -version 2>&1 | Select-Object -First 1
    Write-Host "✓ 已安装: $ffmpegVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠ 未检测到 FFmpeg（视频处理需要）" -ForegroundColor Yellow
    Write-Host "  建议安装: https://www.ffmpeg.org/download.html" -ForegroundColor Yellow
    Write-Host "  或使用 Chocolatey: choco install ffmpeg" -ForegroundColor Yellow
}

# 安装后端依赖
Write-Host ""
Write-Host "[4/7] 安装后端 Python 依赖..." -ForegroundColor Yellow
Set-Location "$projectRoot\backend"

if (Test-Path "venv") {
    Write-Host "  检测到现有虚拟环境" -ForegroundColor Cyan
} else {
    Write-Host "  创建 Python 虚拟环境..." -ForegroundColor Cyan
    python -m venv venv
}

Write-Host "  激活虚拟环境并安装依赖..." -ForegroundColor Cyan
& ".\venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 后端依赖安装完成" -ForegroundColor Green
} else {
    Write-Host "✗ 后端依赖安装失败" -ForegroundColor Red
}

# 安装前端依赖
Write-Host ""
Write-Host "[5/7] 安装前端 Node.js 依赖..." -ForegroundColor Yellow
Set-Location "$projectRoot\frontend"

npm install

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 前端依赖安装完成" -ForegroundColor Green
} else {
    Write-Host "✗ 前端依赖安装失败" -ForegroundColor Red
}

# 安装启动器依赖
Write-Host ""
Write-Host "[6/7] 安装启动器依赖..." -ForegroundColor Yellow
Set-Location $projectRoot
pip install customtkinter pillow

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 启动器依赖安装完成" -ForegroundColor Green
} else {
    Write-Host "✗ 启动器依赖安装失败" -ForegroundColor Red
}

# 检查配置文件
Write-Host ""
Write-Host "[7/7] 检查配置文件..." -ForegroundColor Yellow
Set-Location $projectRoot

if (Test-Path "backend\.env") {
    Write-Host "✓ 检测到 backend\.env 配置文件" -ForegroundColor Green
} else {
    Write-Host "⚠ 未找到 backend\.env 配置文件" -ForegroundColor Yellow
    Write-Host "  请配置以下环境变量:" -ForegroundColor Yellow
    Write-Host "  - GEMINI_API_KEY (Google Gemini API 密钥)" -ForegroundColor Yellow
    Write-Host "  - LLM_PROVIDER (gemini 或 local)" -ForegroundColor Yellow
}

# 完成
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  环境安装完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步操作:" -ForegroundColor Yellow
Write-Host "1. 配置 backend\.env 文件（设置 API 密钥）" -ForegroundColor White
Write-Host "2. 运行启动脚本: python 启动_Pervis_PRO.py" -ForegroundColor White
Write-Host ""
Write-Host "可选安装:" -ForegroundColor Yellow
Write-Host "- Ollama (本地 AI): https://ollama.com" -ForegroundColor White
Write-Host "- Redis (任务队列): https://redis.io/download" -ForegroundColor White
Write-Host ""

Set-Location $projectRoot
