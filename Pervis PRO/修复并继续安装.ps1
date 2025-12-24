# 修复PATH问题并继续安装

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  修复PATH并继续安装" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$projectRoot = $PSScriptRoot

# 修复Python PATH
Write-Host "修复Python PATH..." -ForegroundColor Yellow
$pythonPaths = @(
    "$env:LOCALAPPDATA\Programs\Python\Python311",
    "$env:LOCALAPPDATA\Programs\Python\Python311\Scripts",
    "$env:ProgramFiles\Python311",
    "$env:ProgramFiles\Python311\Scripts"
)

foreach ($path in $pythonPaths) {
    if (Test-Path $path) {
        if ($env:Path -notlike "*$path*") {
            $env:Path = "$env:Path;$path"
            Write-Host "添加到PATH: $path" -ForegroundColor Green
        }
    }
}

# 测试Python
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Python: $pythonVersion" -ForegroundColor Green
    } else {
        # 尝试直接路径
        $pythonExe = "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
        if (Test-Path $pythonExe) {
            $pythonVersion = &$pythonExe --version
            Write-Host "✓ Python (直接路径): $pythonVersion" -ForegroundColor Green
            # 创建别名
            Set-Alias -Name python -Value $pythonExe -Scope Global
            Set-Alias -Name pip -Value "$env:LOCALAPPDATA\Programs\Python\Python311\Scripts\pip.exe" -Scope Global
        }
    }
} catch {
    Write-Host "✗ Python 仍然无法访问" -ForegroundColor Red
}

# 手动安装Node.js
Write-Host ""
Write-Host "检查Node.js..." -ForegroundColor Yellow
try {
    node --version | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Node.js 已安装" -ForegroundColor Green
    } else {
        throw "Node.js 未找到"
    }
} catch {
    Write-Host "尝试手动安装Node.js..." -ForegroundColor Yellow
    
    # 使用winget安装Node.js
    try {
        winget install OpenJS.NodeJS --silent --accept-package-agreements --accept-source-agreements
        Write-Host "✓ Node.js 通过winget安装成功" -ForegroundColor Green
        
        # 刷新PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    } catch {
        Write-Host "⚠ Node.js 自动安装失败" -ForegroundColor Yellow
    }
}

# 安装项目依赖
Write-Host ""
Write-Host "安装项目依赖..." -ForegroundColor Green

# 后端依赖
Write-Host "安装后端依赖..." -ForegroundColor Yellow
Set-Location "$projectRoot\backend"

# 使用直接路径创建虚拟环境
$pythonExe = "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
if (Test-Path $pythonExe) {
    if (!(Test-Path "venv")) {
        Write-Host "创建虚拟环境..." -ForegroundColor Yellow
        &$pythonExe -m venv venv
    }
    
    # 激活虚拟环境并安装依赖
    if (Test-Path "venv\Scripts\python.exe") {
        Write-Host "安装Python包..." -ForegroundColor Yellow
        &".\venv\Scripts\python.exe" -m pip install --upgrade pip
        &".\venv\Scripts\pip.exe" install -r requirements.txt
        Write-Host "✓ 后端依赖安装成功" -ForegroundColor Green
    }
} else {
    Write-Host "⚠ Python路径未找到，跳过后端依赖" -ForegroundColor Yellow
}

# 前端依赖
Write-Host ""
Write-Host "安装前端依赖..." -ForegroundColor Yellow
Set-Location "$projectRoot\frontend"

try {
    npm install
    Write-Host "✓ 前端依赖安装成功" -ForegroundColor Green
} catch {
    Write-Host "⚠ 前端依赖安装失败" -ForegroundColor Yellow
}

# 启动器依赖
Write-Host ""
Write-Host "安装启动器依赖..." -ForegroundColor Yellow
Set-Location $projectRoot

if (Test-Path "$env:LOCALAPPDATA\Programs\Python\Python311\Scripts\pip.exe") {
    try {
        &"$env:LOCALAPPDATA\Programs\Python\Python311\Scripts\pip.exe" install customtkinter pillow
        Write-Host "✓ 启动器依赖安装成功" -ForegroundColor Green
    } catch {
        Write-Host "⚠ 启动器依赖安装失败" -ForegroundColor Yellow
    }
}

# 创建配置文件
Write-Host ""
Write-Host "创建配置文件..." -ForegroundColor Green
$envFile = "$projectRoot\backend\.env"

if (!(Test-Path $envFile)) {
    $envContent = @"
# AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here
LLM_PROVIDER=gemini

# Database Configuration
DATABASE_URL=sqlite:///./pervis_director.db

# Storage Configuration
ASSET_ROOT=./storage/assets
STORAGE_ROOT=./storage

# Server Configuration
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173", "http://localhost:3001"]

# Logging
LOG_LEVEL=INFO
"@
    
    Set-Content -Path $envFile -Value $envContent -Encoding UTF8
    Write-Host "✓ 配置文件已创建" -ForegroundColor Green
}

# 最终检查
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  环境检查" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$components = @(
    @{Name="Python"; Path="$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"},
    @{Name="Git"; Command="git --version"},
    @{Name="Backend venv"; Path="$projectRoot\backend\venv\Scripts\python.exe"},
    @{Name="Frontend deps"; Path="$projectRoot\frontend\node_modules"},
    @{Name="Config file"; Path="$projectRoot\backend\.env"}
)

$successCount = 0
foreach ($component in $components) {
    if ($component.Path) {
        if (Test-Path $component.Path) {
            Write-Host "✓ $($component.Name): 存在" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "✗ $($component.Name): 不存在" -ForegroundColor Red
        }
    } elseif ($component.Command) {
        try {
            Invoke-Expression $component.Command | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ $($component.Name): 可用" -ForegroundColor Green
                $successCount++
            } else {
                Write-Host "✗ $($component.Name): 不可用" -ForegroundColor Red
            }
        } catch {
            Write-Host "✗ $($component.Name): 不可用" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "检查结果: $successCount/5 个组件可用" $(if ($successCount -ge 3) { "Green" } else { "Yellow" })
Write-Host "========================================" -ForegroundColor Cyan

if ($successCount -ge 3) {
    Write-Host ""
    Write-Host "🎉 基础环境已就绪！" -ForegroundColor Green
    Write-Host ""
    Write-Host "下一步:" -ForegroundColor Yellow
    Write-Host "1. 获取Gemini API密钥: https://makersuite.google.com/app/apikey" -ForegroundColor White
    Write-Host "2. 编辑 backend\.env 设置 GEMINI_API_KEY" -ForegroundColor White
    Write-Host "3. 启动项目: python 启动_Pervis_PRO.py" -ForegroundColor White
    Write-Host ""
    Write-Host "或者运行: .\检查并启动.bat" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "⚠ 部分组件缺失，请检查上述错误" -ForegroundColor Yellow
}

Set-Location $projectRoot