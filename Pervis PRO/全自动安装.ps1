# Pervis PRO 全自动环境安装脚本
# 无需用户交互，自动下载并安装所有依赖

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Pervis PRO 全自动环境安装" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = $PSScriptRoot
$tempDir = "$env:TEMP\PervisPRO_Install"

# 创建临时目录
if (!(Test-Path $tempDir)) {
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
}

# 下载文件函数
function Download-File {
    param($url, $output)
    try {
        Write-Host "  下载: $(Split-Path $output -Leaf)..." -ForegroundColor Yellow
        Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing
        return $true
    } catch {
        Write-Host "  下载失败: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# 静默安装函数
function Install-Silently {
    param($installer, $args)
    try {
        Write-Host "  安装中..." -ForegroundColor Yellow
        $process = Start-Process -FilePath $installer -ArgumentList $args -Wait -PassThru -WindowStyle Hidden
        return $process.ExitCode -eq 0
    } catch {
        Write-Host "  安装失败: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# 检查并安装 Python
Write-Host "[1/4] 检查并安装 Python..." -ForegroundColor Green
try {
    python --version 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Python 已安装" -ForegroundColor Green
    } else {
        throw "Python 未安装"
    }
} catch {
    Write-Host "  正在下载 Python 3.11..." -ForegroundColor Yellow
    $pythonUrl = "https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe"
    $pythonInstaller = "$tempDir\python-installer.exe"
    
    if (Download-File $pythonUrl $pythonInstaller) {
        Write-Host "  正在安装 Python..." -ForegroundColor Yellow
        $pythonArgs = @("/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_test=0")
        if (Install-Silently $pythonInstaller $pythonArgs) {
            Write-Host "✓ Python 安装完成" -ForegroundColor Green
            # 刷新环境变量
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        } else {
            Write-Host "✗ Python 安装失败" -ForegroundColor Red
        }
    }
}

# 检查并安装 Node.js
Write-Host ""
Write-Host "[2/4] 检查并安装 Node.js..." -ForegroundColor Green
try {
    node --version 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Node.js 已安装" -ForegroundColor Green
    } else {
        throw "Node.js 未安装"
    }
} catch {
    Write-Host "  正在下载 Node.js..." -ForegroundColor Yellow
    $nodeUrl = "https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi"
    $nodeInstaller = "$tempDir\node-installer.msi"
    
    if (Download-File $nodeUrl $nodeInstaller) {
        Write-Host "  正在安装 Node.js..." -ForegroundColor Yellow
        $nodeArgs = @("/i", $nodeInstaller, "/quiet", "/norestart")
        if (Install-Silently "msiexec.exe" $nodeArgs) {
            Write-Host "✓ Node.js 安装完成" -ForegroundColor Green
            # 刷新环境变量
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        } else {
            Write-Host "✗ Node.js 安装失败" -ForegroundColor Red
        }
    }
}

# 检查并安装 Git
Write-Host ""
Write-Host "[3/4] 检查并安装 Git..." -ForegroundColor Green
try {
    git --version 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Git 已安装" -ForegroundColor Green
    } else {
        throw "Git 未安装"
    }
} catch {
    Write-Host "  正在下载 Git..." -ForegroundColor Yellow
    $gitUrl = "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe"
    $gitInstaller = "$tempDir\git-installer.exe"
    
    if (Download-File $gitUrl $gitInstaller) {
        Write-Host "  正在安装 Git..." -ForegroundColor Yellow
        $gitArgs = @("/VERYSILENT", "/NORESTART", "/NOCANCEL", "/SP-", "/CLOSEAPPLICATIONS", "/RESTARTAPPLICATIONS")
        if (Install-Silently $gitInstaller $gitArgs) {
            Write-Host "✓ Git 安装完成" -ForegroundColor Green
            # 刷新环境变量
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        } else {
            Write-Host "✗ Git 安装失败" -ForegroundColor Red
        }
    }
}

# 安装 FFmpeg (可选)
Write-Host ""
Write-Host "[4/4] 安装 FFmpeg..." -ForegroundColor Green
try {
    ffmpeg -version 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ FFmpeg 已安装" -ForegroundColor Green
    } else {
        throw "FFmpeg 未安装"
    }
} catch {
    Write-Host "  正在下载 FFmpeg..." -ForegroundColor Yellow
    $ffmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    $ffmpegZip = "$tempDir\ffmpeg.zip"
    
    if (Download-File $ffmpegUrl $ffmpegZip) {
        Write-Host "  正在解压 FFmpeg..." -ForegroundColor Yellow
        $ffmpegDir = "C:\ffmpeg"
        
        # 解压
        Expand-Archive -Path $ffmpegZip -DestinationPath $tempDir -Force
        $extractedDir = Get-ChildItem -Path $tempDir -Directory | Where-Object { $_.Name -like "ffmpeg-*" } | Select-Object -First 1
        
        if ($extractedDir) {
            # 移动到目标目录
            if (Test-Path $ffmpegDir) {
                Remove-Item $ffmpegDir -Recurse -Force
            }
            Move-Item $extractedDir.FullName $ffmpegDir
            
            # 添加到 PATH
            $currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
            $ffmpegBinPath = "$ffmpegDir\bin"
            
            if ($currentPath -notlike "*$ffmpegBinPath*") {
                $newPath = "$currentPath;$ffmpegBinPath"
                [Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")
                $env:Path = "$env:Path;$ffmpegBinPath"
            }
            
            Write-Host "✓ FFmpeg 安装完成" -ForegroundColor Green
        } else {
            Write-Host "✗ FFmpeg 解压失败" -ForegroundColor Red
        }
    }
}

# 等待环境变量生效
Write-Host ""
Write-Host "等待环境变量生效..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# 安装项目依赖
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  安装项目依赖" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 安装后端依赖
Write-Host ""
Write-Host "安装后端依赖..." -ForegroundColor Green
Set-Location "$projectRoot\backend"

if (!(Test-Path "venv")) {
    Write-Host "  创建虚拟环境..." -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "  激活虚拟环境并安装依赖..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 后端依赖安装完成" -ForegroundColor Green
} else {
    Write-Host "✗ 后端依赖安装失败" -ForegroundColor Red
}

# 安装前端依赖
Write-Host ""
Write-Host "安装前端依赖..." -ForegroundColor Green
Set-Location "$projectRoot\frontend"

npm install --silent

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 前端依赖安装完成" -ForegroundColor Green
} else {
    Write-Host "✗ 前端依赖安装失败" -ForegroundColor Red
}

# 安装启动器依赖
Write-Host ""
Write-Host "安装启动器依赖..." -ForegroundColor Green
Set-Location $projectRoot
pip install customtkinter pillow --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 启动器依赖安装完成" -ForegroundColor Green
} else {
    Write-Host "✗ 启动器依赖安装失败" -ForegroundColor Red
}

# 创建配置文件
Write-Host ""
Write-Host "创建配置文件..." -ForegroundColor Green
$envFile = "$projectRoot\backend\.env"
if (!(Test-Path $envFile)) {
    $envContent = @"
# AI 配置
GEMINI_API_KEY=your_gemini_api_key_here
LLM_PROVIDER=gemini

# 数据库配置
DATABASE_URL=sqlite:///./pervis_director.db

# 存储配置
ASSET_ROOT=./storage/assets
STORAGE_ROOT=./storage

# 网络配置
NETWORK_DRIVE=L
NETWORK_DRIVE_NAME=影片参考
"@
    
    Set-Content -Path $envFile -Value $envContent -Encoding UTF8
    Write-Host "✓ 配置文件已创建: backend\.env" -ForegroundColor Green
    Write-Host "  请编辑此文件设置 GEMINI_API_KEY" -ForegroundColor Yellow
} else {
    Write-Host "✓ 配置文件已存在" -ForegroundColor Green
}

# 清理临时文件
Write-Host ""
Write-Host "清理临时文件..." -ForegroundColor Yellow
Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue

# 完成
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  安装完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步操作:" -ForegroundColor Yellow
Write-Host "1. 获取 Gemini API 密钥: https://makersuite.google.com/app/apikey" -ForegroundColor White
Write-Host "2. 编辑 backend\.env 文件，设置 GEMINI_API_KEY" -ForegroundColor White
Write-Host "3. 运行项目: python 启动_Pervis_PRO.py" -ForegroundColor White
Write-Host ""
Write-Host "安装日志已保存，如有问题请检查上述输出" -ForegroundColor Cyan

Set-Location $projectRoot