# Pervis PRO 环境检查脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Pervis PRO 环境检查" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$missingComponents = @()

# 检查 Python
Write-Host "检查 Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -like "*Python*") {
        Write-Host "✓ Python 已安装: $pythonVersion" -ForegroundColor Green
    } else {
        throw "Python 未找到"
    }
} catch {
    Write-Host "✗ Python 未安装" -ForegroundColor Red
    $missingComponents += "Python"
}

# 检查 Node.js
Write-Host "检查 Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    if ($nodeVersion -like "v*") {
        Write-Host "✓ Node.js 已安装: $nodeVersion" -ForegroundColor Green
    } else {
        throw "Node.js 未找到"
    }
} catch {
    Write-Host "✗ Node.js 未安装" -ForegroundColor Red
    $missingComponents += "Node.js"
}

# 检查 Git
Write-Host "检查 Git..." -ForegroundColor Yellow
try {
    $gitVersion = git --version 2>&1
    if ($gitVersion -like "*git version*") {
        Write-Host "✓ Git 已安装: $gitVersion" -ForegroundColor Green
    } else {
        throw "Git 未找到"
    }
} catch {
    Write-Host "✗ Git 未安装" -ForegroundColor Red
    $missingComponents += "Git"
}

# 检查 FFmpeg (可选)
Write-Host "检查 FFmpeg..." -ForegroundColor Yellow
try {
    $ffmpegVersion = ffmpeg -version 2>&1 | Select-Object -First 1
    if ($ffmpegVersion -like "*ffmpeg version*") {
        Write-Host "✓ FFmpeg 已安装: $ffmpegVersion" -ForegroundColor Green
    } else {
        throw "FFmpeg 未找到"
    }
} catch {
    Write-Host "⚠ FFmpeg 未安装 (可选，用于视频处理)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

if ($missingComponents.Count -eq 0) {
    Write-Host "  环境检查通过！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "可以运行安装脚本: .\setup_environment.ps1" -ForegroundColor White
} else {
    Write-Host "  需要安装以下组件:" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    foreach ($component in $missingComponents) {
        switch ($component) {
            "Python" {
                Write-Host "📦 Python 3.10+" -ForegroundColor Yellow
                Write-Host "   下载地址: https://www.python.org/downloads/" -ForegroundColor White
                Write-Host "   安装时请勾选 'Add Python to PATH'" -ForegroundColor Cyan
                Write-Host ""
            }
            "Node.js" {
                Write-Host "📦 Node.js 18+" -ForegroundColor Yellow
                Write-Host "   下载地址: https://nodejs.org/" -ForegroundColor White
                Write-Host "   选择 LTS 版本" -ForegroundColor Cyan
                Write-Host ""
            }
            "Git" {
                Write-Host "📦 Git" -ForegroundColor Yellow
                Write-Host "   下载地址: https://git-scm.com/" -ForegroundColor White
                Write-Host "   或使用 GitHub Desktop" -ForegroundColor Cyan
                Write-Host ""
            }
        }
    }
    
    Write-Host "安装完成后，重新运行此脚本检查环境" -ForegroundColor Yellow
}

Write-Host ""