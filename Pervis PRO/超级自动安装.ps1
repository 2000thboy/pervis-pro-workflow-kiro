# Pervis PRO 超级自动安装脚本
# 完全无人值守，自动安装所有组件

param(
    [switch]$Force,
    [switch]$SkipRestart
)

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

# 设置控制台编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Pervis PRO 超级自动安装" -ForegroundColor Cyan
Write-Host "  完全无人值守安装" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$projectRoot = $PSScriptRoot
$logFile = "$projectRoot\install_log.txt"

# 日志函数
function Write-Log {
    param($Message, $Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $Message -ForegroundColor $Color
    Add-Content -Path $logFile -Value $logMessage -Encoding UTF8
}

# 检查管理员权限
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin -and -not $Force) {
    Write-Log "需要管理员权限，正在重新启动..." "Yellow"
    $arguments = "-ExecutionPolicy Bypass -File `"$PSCommandPath`" -Force"
    if ($SkipRestart) { $arguments += " -SkipRestart" }
    Start-Process PowerShell -Verb RunAs -ArgumentList $arguments
    exit
}

Write-Log "开始超级自动安装..." "Green"

# 创建下载目录
$downloadDir = "$env:TEMP\PervisPRO_SuperInstall"
if (Test-Path $downloadDir) {
    Remove-Item $downloadDir -Recurse -Force
}
New-Item -ItemType Directory -Path $downloadDir -Force | Out-Null

# 下载函数（带重试）
function Download-FileWithRetry {
    param($url, $output, $name, $maxRetries = 3)
    
    for ($i = 1; $i -le $maxRetries; $i++) {
        try {
            Write-Log "下载 $name (尝试 $i/$maxRetries)..." "Yellow"
            
            # 使用多种下载方法
            try {
                # 方法1: Invoke-WebRequest
                Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing -TimeoutSec 300
                Write-Log "✓ $name 下载成功" "Green"
                return $true
            } catch {
                # 方法2: WebClient
                $webClient = New-Object System.Net.WebClient
                $webClient.DownloadFile($url, $output)
                Write-Log "✓ $name 下载成功 (WebClient)" "Green"
                return $true
            }
        } catch {
            Write-Log "下载失败 (尝试 $i): $($_.Exception.Message)" "Red"
            if ($i -eq $maxRetries) {
                Write-Log "✗ $name 下载失败，已达到最大重试次数" "Red"
                return $false
            }
            Start-Sleep -Seconds 5
        }
    }
    return $false
}

# 安装函数（带重试）
function Install-WithRetry {
    param($installer, $args, $name, $maxRetries = 2)
    
    for ($i = 1; $i -le $maxRetries; $i++) {
        try {
            Write-Log "安装 $name (尝试 $i/$maxRetries)..." "Yellow"
            
            if ($args -and $args.Count -gt 0) {
                $process = Start-Process -FilePath $installer -ArgumentList $args -Wait -PassThru -NoNewWindow
            } else {
                $process = Start-Process -FilePath $installer -Wait -PassThru -NoNewWindow
            }
            
            if ($process.ExitCode -eq 0 -or $process.ExitCode -eq 3010) {
                Write-Log "✓ $name 安装成功" "Green"
                return $true
            } else {
                throw "安装失败，退出代码: $($process.ExitCode)"
            }
        } catch {
            Write-Log "安装失败 (尝试 $i): $($_.Exception.Message)" "Red"
            if ($i -eq $maxRetries) {
                Write-Log "✗ $name 安装失败" "Red"
                return $false
            }
            Start-Sleep -Seconds 3
        }
    }
    return $false
}

# 刷新环境变量
function Refresh-Environment {
    Write-Log "刷新环境变量..." "Yellow"
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    # 添加常见路径
    $commonPaths = @(
        "$env:ProgramFiles\Python311",
        "$env:ProgramFiles\Python311\Scripts",
        "$env:ProgramFiles\nodejs",
        "$env:ProgramFiles\Git\cmd",
        "$env:ProgramFiles\Git\bin",
        "$env:LOCALAPPDATA\Programs\Python\Python311",
        "$env:LOCALAPPDATA\Programs\Python\Python311\Scripts"
    )
    
    foreach ($path in $commonPaths) {
        if (Test-Path $path) {
            if ($env:Path -notlike "*$path*") {
                $env:Path = "$env:Path;$path"
            }
        }
    }
}

# 1. 安装 Python
Write-Log ""
Write-Log "[1/6] 安装 Python..." "Green"
try {
    python --version 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Log "✓ Python 已安装" "Green"
    } else {
        throw "Python 未找到"
    }
} catch {
    $pythonUrl = "https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe"
    $pythonInstaller = "$downloadDir\python-installer.exe"
    
    if (Download-FileWithRetry $pythonUrl $pythonInstaller "Python 3.11") {
        $pythonArgs = @("/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_test=0", "Include_doc=0", "SimpleInstall=1")
        Install-WithRetry $pythonInstaller $pythonArgs "Python"
        Refresh-Environment
    }
}

# 2. 安装 Node.js
Write-Log ""
Write-Log "[2/6] 安装 Node.js..." "Green"
try {
    node --version 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Log "✓ Node.js 已安装" "Green"
    } else {
        throw "Node.js 未找到"
    }
} catch {
    $nodeUrl = "https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi"
    $nodeInstaller = "$downloadDir\node-installer.msi"
    
    if (Download-FileWithRetry $nodeUrl $nodeInstaller "Node.js 20") {
        $nodeArgs = @("/i", "`"$nodeInstaller`"", "/quiet", "/norestart")
        Install-WithRetry "msiexec.exe" $nodeArgs "Node.js"
        Refresh-Environment
    }
}

# 3. 安装 Git
Write-Log ""
Write-Log "[3/6] 安装 Git..." "Green"
try {
    git --version 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Log "✓ Git 已安装" "Green"
    } else {
        throw "Git 未找到"
    }
} catch {
    $gitUrl = "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe"
    $gitInstaller = "$downloadDir\git-installer.exe"
    
    if (Download-FileWithRetry $gitUrl $gitInstaller "Git") {
        $gitArgs = @("/VERYSILENT", "/NORESTART", "/NOCANCEL", "/SP-", "/CLOSEAPPLICATIONS", "/RESTARTAPPLICATIONS", "/COMPONENTS=`"icons,ext\reg\shellhere,assoc,assoc_sh`"")
        Install-WithRetry $gitInstaller $gitArgs "Git"
        Refresh-Environment
    }
}

# 4. 安装 Chocolatey 和 FFmpeg
Write-Log ""
Write-Log "[4/6] 安装 Chocolatey 和 FFmpeg..." "Green"
try {
    choco --version 2>&1 | Out-Null
    Write-Log "✓ Chocolatey 已安装" "Green"
} catch {
    Write-Log "安装 Chocolatey..." "Yellow"
    try {
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        
        # 使用备用方法安装 Chocolatey
        $chocoScript = Invoke-WebRequest -Uri "https://chocolatey.org/install.ps1" -UseBasicParsing
        Invoke-Expression $chocoScript.Content
        
        Refresh-Environment
        Write-Log "✓ Chocolatey 安装成功" "Green"
    } catch {
        Write-Log "⚠ Chocolatey 安装失败，跳过 FFmpeg" "Yellow"
    }
}

# 安装 FFmpeg
try {
    ffmpeg -version 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Log "✓ FFmpeg 已安装" "Green"
    } else {
        throw "FFmpeg 未找到"
    }
} catch {
    try {
        choco install ffmpeg -y --no-progress
        Refresh-Environment
        Write-Log "✓ FFmpeg 安装成功" "Green"
    } catch {
        Write-Log "⚠ FFmpeg 安装失败，将手动下载" "Yellow"
        
        # 手动下载 FFmpeg
        $ffmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        $ffmpegZip = "$downloadDir\ffmpeg.zip"
        
        if (Download-FileWithRetry $ffmpegUrl $ffmpegZip "FFmpeg") {
            try {
                Expand-Archive -Path $ffmpegZip -DestinationPath $downloadDir -Force
                $extractedDir = Get-ChildItem -Path $downloadDir -Directory | Where-Object { $_.Name -like "ffmpeg-*" } | Select-Object -First 1
                
                if ($extractedDir) {
                    $ffmpegDir = "C:\ffmpeg"
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
                    
                    Write-Log "✓ FFmpeg 手动安装成功" "Green"
                }
            } catch {
                Write-Log "⚠ FFmpeg 手动安装失败" "Yellow"
            }
        }
    }
}

# 等待环境变量生效
Write-Log ""
Write-Log "等待环境变量生效..." "Yellow"
Start-Sleep -Seconds 5
Refresh-Environment

# 5. 安装项目依赖
Write-Log ""
Write-Log "[5/6] 安装项目依赖..." "Green"

# 后端依赖
Write-Log "安装后端依赖..." "Yellow"
Set-Location "$projectRoot\backend"

if (!(Test-Path "venv")) {
    Write-Log "创建 Python 虚拟环境..." "Yellow"
    try {
        python -m venv venv
        Write-Log "✓ 虚拟环境创建成功" "Green"
    } catch {
        Write-Log "⚠ 虚拟环境创建失败，使用全局 Python" "Yellow"
    }
}

# 激活虚拟环境并安装依赖
if (Test-Path "venv\Scripts\Activate.ps1") {
    try {
        & ".\venv\Scripts\Activate.ps1"
        Write-Log "✓ 虚拟环境已激活" "Green"
    } catch {
        Write-Log "⚠ 虚拟环境激活失败" "Yellow"
    }
}

Write-Log "安装 Python 包..." "Yellow"
try {
    python -m pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
    Write-Log "✓ 后端依赖安装成功" "Green"
} catch {
    Write-Log "⚠ 后端依赖安装失败" "Red"
}

# 前端依赖
Write-Log ""
Write-Log "安装前端依赖..." "Yellow"
Set-Location "$projectRoot\frontend"

try {
    npm install --silent
    Write-Log "✓ 前端依赖安装成功" "Green"
} catch {
    Write-Log "⚠ 前端依赖安装失败" "Red"
}

# 启动器依赖
Write-Log ""
Write-Log "安装启动器依赖..." "Yellow"
Set-Location $projectRoot

try {
    pip install customtkinter pillow --quiet
    Write-Log "✓ 启动器依赖安装成功" "Green"
} catch {
    Write-Log "⚠ 启动器依赖安装失败" "Red"
}

# 6. 安装 AI 组件
Write-Log ""
Write-Log "[6/6] 安装 AI 组件..." "Green"

# 安装 Ollama
Write-Log "安装 Ollama..." "Yellow"
try {
    ollama --version 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Log "✓ Ollama 已安装" "Green"
    } else {
        throw "Ollama 未找到"
    }
} catch {
    $ollamaUrl = "https://ollama.com/download/OllamaSetup.exe"
    $ollamaInstaller = "$downloadDir\OllamaSetup.exe"
    
    if (Download-FileWithRetry $ollamaUrl $ollamaInstaller "Ollama") {
        Install-WithRetry $ollamaInstaller @("/S") "Ollama"
        Refresh-Environment
        
        # 启动 Ollama 服务
        try {
            Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
            Start-Sleep -Seconds 5
            Write-Log "✓ Ollama 服务已启动" "Green"
        } catch {
            Write-Log "⚠ Ollama 服务启动失败" "Yellow"
        }
    }
}

# 下载 AI 模型
Write-Log "下载 AI 模型..." "Yellow"
try {
    $modelList = ollama list 2>&1
    if ($modelList -like "*qwen2.5:7b*") {
        Write-Log "✓ Qwen2.5:7b 模型已存在" "Green"
    } else {
        Write-Log "下载 Qwen2.5:7b 模型（约4GB）..." "Yellow"
        ollama pull qwen2.5:7b
        if ($LASTEXITCODE -eq 0) {
            Write-Log "✓ Qwen2.5:7b 模型下载成功" "Green"
        }
    }
} catch {
    Write-Log "⚠ AI 模型下载失败" "Yellow"
}

# 安装 Python AI 库
Write-Log "安装 Python AI 库..." "Yellow"
try {
    # 安装 PyTorch (CPU版本)
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu --quiet
    
    # 安装其他 AI 库
    pip install opencv-python transformers aioredis --quiet
    
    # 尝试安装 CLIP
    pip install git+https://github.com/openai/CLIP.git --quiet
    
    Write-Log "✓ Python AI 库安装成功" "Green"
} catch {
    Write-Log "⚠ Python AI 库安装失败" "Yellow"
}

# 创建/更新配置文件
Write-Log ""
Write-Log "创建配置文件..." "Green"
$envFile = "$projectRoot\backend\.env"

$envContent = @"
# AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here
LLM_PROVIDER=local

# Local AI Configuration (Ollama)
OLLAMA_BASE_URL=http://localhost:11434/v1
LOCAL_MODEL_NAME=qwen2.5:7b

# Database Configuration
DATABASE_URL=sqlite:///./pervis_director.db

# Storage Configuration
ASSET_ROOT=./storage/assets
STORAGE_ROOT=./storage

# Network Configuration
NETWORK_DRIVE=L
NETWORK_DRIVE_NAME=影片参考

# Visual Processing
CLIP_MODEL=ViT-B/32
ENABLE_VISUAL_ANALYSIS=true

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Server Configuration
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173", "http://localhost:3001"]

# Logging
LOG_LEVEL=INFO
"@

Set-Content -Path $envFile -Value $envContent -Encoding UTF8
Write-Log "✓ 配置文件已创建" "Green"

# 清理下载文件
Write-Log ""
Write-Log "清理临时文件..." "Yellow"
Remove-Item $downloadDir -Recurse -Force -ErrorAction SilentlyContinue

# 最终验证
Write-Log ""
Write-Log "========================================" "Cyan"
Write-Log "  安装验证" "Cyan"
Write-Log "========================================" "Cyan"

$components = @(
    @{Name="Python"; Command="python --version"},
    @{Name="Node.js"; Command="node --version"},
    @{Name="Git"; Command="git --version"},
    @{Name="FFmpeg"; Command="ffmpeg -version"},
    @{Name="Ollama"; Command="ollama --version"}
)

$successCount = 0
foreach ($component in $components) {
    try {
        $result = Invoke-Expression "$($component.Command) 2>&1" | Select-Object -First 1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "✓ $($component.Name): $result" "Green"
            $successCount++
        } else {
            Write-Log "✗ $($component.Name): 未正常工作" "Red"
        }
    } catch {
        Write-Log "✗ $($component.Name): 未安装" "Red"
    }
}

# 完成报告
Write-Log ""
Write-Log "========================================" "Cyan"
Write-Log "  安装完成!" "Green"
Write-Log "========================================" "Cyan"
Write-Log ""
Write-Log "安装结果: $successCount/5 个组件成功安装" $(if ($successCount -ge 4) { "Green" } else { "Yellow" })
Write-Log ""
Write-Log "下一步操作:" "Yellow"
Write-Log "1. 如需云端AI，获取Gemini API密钥: https://makersuite.google.com/app/apikey" "White"
Write-Log "2. 编辑 backend\.env 设置API密钥或使用本地AI" "White"
Write-Log "3. 启动项目: python 启动_Pervis_PRO.py" "White"
Write-Log ""
Write-Log "安装日志已保存到: $logFile" "Cyan"

Set-Location $projectRoot

if (-not $SkipRestart) {
    Write-Log ""
    Write-Log "安装完成！按任意键退出..." "Green"
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}