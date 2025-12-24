# Pervis PRO 快速核心安装
# 只安装最核心的组件，确保快速完成

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Pervis PRO 快速核心安装" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$projectRoot = $PSScriptRoot

# 简单的下载函数
function Quick-Download {
    param($url, $output, $name)
    try {
        Write-Host "下载 $name..." -ForegroundColor Yellow
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($url, $output)
        Write-Host "✓ $name 下载完成" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "✗ $name 下载失败: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# 简单的安装函数
function Quick-Install {
    param($installer, $args, $name)
    try {
        Write-Host "安装 $name..." -ForegroundColor Yellow
        if ($args) {
            $process = Start-Process -FilePath $installer -ArgumentList $args -Wait -PassThru -WindowStyle Hidden
        } else {
            $process = Start-Process -FilePath $installer -Wait -PassThru -WindowStyle Hidden
        }
        
        if ($process.ExitCode -eq 0 -or $process.ExitCode -eq 3010) {
            Write-Host "✓ $name 安装成功" -ForegroundColor Green
            return $true
        } else {
            Write-Host "✗ $name 安装失败 (退出代码: $($process.ExitCode))" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "✗ $name 安装异常: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

$downloadDir = "$env:TEMP\PervisPRO_Quick"
if (Test-Path $downloadDir) {
    Remove-Item $downloadDir -Recurse -Force
}
New-Item -ItemType Directory -Path $downloadDir -Force | Out-Null

# 检查并安装 Python
Write-Host ""
Write-Host "[1/4] Python..." -ForegroundColor Green
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Python 已安装: $pythonVersion" -ForegroundColor Green
    } else {
        throw "Python 未找到"
    }
} catch {
    $pythonUrl = "https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe"
    $pythonInstaller = "$downloadDir\python.exe"
    
    if (Quick-Download $pythonUrl $pythonInstaller "Python") {
        $pythonArgs = @("/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_test=0")
        Quick-Install $pythonInstaller $pythonArgs "Python"
        
        # 刷新环境变量
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    }
}

# 检查并安装 Node.js
Write-Host ""
Write-Host "[2/4] Node.js..." -ForegroundColor Green
try {
    $nodeVersion = node --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Node.js 已安装: $nodeVersion" -ForegroundColor Green
    } else {
        throw "Node.js 未找到"
    }
} catch {
    $nodeUrl = "https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi"
    $nodeInstaller = "$downloadDir\node.msi"
    
    if (Quick-Download $nodeUrl $nodeInstaller "Node.js") {
        $nodeArgs = @("/i", "`"$nodeInstaller`"", "/quiet", "/norestart")
        Quick-Install "msiexec.exe" $nodeArgs "Node.js"
        
        # 刷新环境变量
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    }
}

# 检查并安装 Git
Write-Host ""
Write-Host "[3/4] Git..." -ForegroundColor Green
try {
    $gitVersion = git --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Git 已安装: $gitVersion" -ForegroundColor Green
    } else {
        throw "Git 未找到"
    }
} catch {
    $gitUrl = "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe"
    $gitInstaller = "$downloadDir\git.exe"
    
    if (Quick-Download $gitUrl $gitInstaller "Git") {
        $gitArgs = @("/VERYSILENT", "/NORESTART", "/NOCANCEL", "/SP-")
        Quick-Install $gitInstaller $gitArgs "Git"
        
        # 刷新环境变量
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    }
}

# 等待环境变量生效
Write-Host ""
Write-Host "等待环境变量生效..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 安装项目依赖
Write-Host ""
Write-Host "[4/4] 项目依赖..." -ForegroundColor Green

# 后端依赖
Write-Host "安装后端依赖..." -ForegroundColor Yellow
Set-Location "$projectRoot\backend"

if (!(Test-Path "venv")) {
    Write-Host "创建虚拟环境..." -ForegroundColor Yellow
    try {
        python -m venv venv
        Write-Host "✓ 虚拟环境创建成功" -ForegroundColor Green
    } catch {
        Write-Host "⚠ 虚拟环境创建失败" -ForegroundColor Yellow
    }
}

if (Test-Path "venv\Scripts\Activate.ps1") {
    try {
        & ".\venv\Scripts\Activate.ps1"
        Write-Host "✓ 虚拟环境激活成功" -ForegroundColor Green
    } catch {
        Write-Host "⚠ 虚拟环境激活失败" -ForegroundColor Yellow
    }
}

try {
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    Write-Host "✓ 后端依赖安装成功" -ForegroundColor Green
} catch {
    Write-Host "⚠ 后端依赖安装失败" -ForegroundColor Red
}

# 前端依赖
Write-Host ""
Write-Host "安装前端依赖..." -ForegroundColor Yellow
Set-Location "$projectRoot\frontend"

try {
    npm install
    Write-Host "✓ 前端依赖安装成功" -ForegroundColor Green
} catch {
    Write-Host "⚠ 前端依赖安装失败" -ForegroundColor Red
}

# 启动器依赖
Write-Host ""
Write-Host "安装启动器依赖..." -ForegroundColor Yellow
Set-Location $projectRoot

try {
    pip install customtkinter pillow
    Write-Host "✓ 启动器依赖安装成功" -ForegroundColor Green
} catch {
    Write-Host "⚠ 启动器依赖安装失败" -ForegroundColor Red
}

# 创建基础配置文件
Write-Host ""
Write-Host "创建配置文件..." -ForegroundColor Green
$envFile = "$projectRoot\backend\.env"

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

# 清理
Remove-Item $downloadDir -Recurse -Force -ErrorAction SilentlyContinue

# 验证安装
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  安装验证" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$components = @("python", "node", "git")
$successCount = 0

foreach ($cmd in $components) {
    try {
        $result = Invoke-Expression "$cmd --version 2>&1" | Select-Object -First 1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ $cmd : $result" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "✗ $cmd : 未正常工作" -ForegroundColor Red
        }
    } catch {
        Write-Host "✗ $cmd : 未安装" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  核心安装完成!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "安装结果: $successCount/3 个核心组件成功" $(if ($successCount -eq 3) { "Green" } else { "Yellow" })
Write-Host ""
Write-Host "下一步:" -ForegroundColor Yellow
Write-Host "1. 获取 Gemini API 密钥: https://makersuite.google.com/app/apikey" -ForegroundColor White
Write-Host "2. 编辑 backend\.env 设置 GEMINI_API_KEY" -ForegroundColor White
Write-Host "3. 启动项目: python 启动_Pervis_PRO.py" -ForegroundColor White
Write-Host ""
Write-Host "可选: 运行 '补充安装_本地AI和缺失组件.ps1' 安装AI组件" -ForegroundColor Cyan

Set-Location $projectRoot
Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Green
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")