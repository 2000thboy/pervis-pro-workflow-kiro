# Pervis PRO 最终自动安装脚本
# 解决所有安装问题的完整脚本

param(
    [switch]$Force,
    [switch]$SkipRestart
)

# 设置执行策略
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

# 创建日志函数
function Write-Log {
    param($Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage
    Add-Content -Path "install_log.txt" -Value $logMessage
}

# 检查管理员权限
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# 如果不是管理员，重新以管理员身份运行
if (-not (Test-Administrator)) {
    Write-Log "需要管理员权限，重新启动..."
    $arguments = "-ExecutionPolicy Bypass -File `"$($MyInvocation.MyCommand.Path)`""
    if ($Force) { $arguments += " -Force" }
    if ($SkipRestart) { $arguments += " -SkipRestart" }
    Start-Process PowerShell -Verb RunAs -ArgumentList $arguments
    exit
}

Write-Log "开始Pervis PRO最终自动安装..."

# 1. 安装Python
Write-Log "=== 安装Python ==="
$pythonInstalled = $false
try {
    $pythonVersion = python --version 2>$null
    if ($pythonVersion -match "Python 3\.") {
        Write-Log "Python已安装: $pythonVersion"
        $pythonInstalled = $true
    }
} catch {}

if (-not $pythonInstalled) {
    Write-Log "下载并安装Python 3.11..."
    $pythonUrl = "https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe"
    $pythonInstaller = "$env:TEMP\python-installer.exe"
    
    try {
        Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonInstaller -UseBasicParsing
        Write-Log "Python下载完成"
        
        # 静默安装Python
        $installArgs = "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0"
        Start-Process -FilePath $pythonInstaller -ArgumentList $installArgs -Wait
        Write-Log "Python安装完成"
        
        # 刷新环境变量
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        Remove-Item $pythonInstaller -Force
    } catch {
        Write-Log "Python安装失败: $($_.Exception.Message)"
    }
}

# 2. 安装Node.js
Write-Log "=== 安装Node.js ==="
$nodeInstalled = $false
try {
    $nodeVersion = node --version 2>$null
    if ($nodeVersion -match "v\d+") {
        Write-Log "Node.js已安装: $nodeVersion"
        $nodeInstalled = $true
    }
} catch {}

if (-not $nodeInstalled) {
    Write-Log "下载并安装Node.js..."
    $nodeUrl = "https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi"
    $nodeInstaller = "$env:TEMP\node-installer.msi"
    
    try {
        Invoke-WebRequest -Uri $nodeUrl -OutFile $nodeInstaller -UseBasicParsing
        Write-Log "Node.js下载完成"
        
        # 静默安装Node.js
        Start-Process -FilePath "msiexec.exe" -ArgumentList "/i `"$nodeInstaller`" /quiet /norestart" -Wait
        Write-Log "Node.js安装完成"
        
        # 刷新环境变量
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        Remove-Item $nodeInstaller -Force
    } catch {
        Write-Log "Node.js安装失败: $($_.Exception.Message)"
    }
}

# 3. 安装FFmpeg
Write-Log "=== 安装FFmpeg ==="
$ffmpegInstalled = $false
try {
    $ffmpegVersion = ffmpeg -version 2>$null
    if ($ffmpegVersion -match "ffmpeg version") {
        Write-Log "FFmpeg已安装"
        $ffmpegInstalled = $true
    }
} catch {}

if (-not $ffmpegInstalled) {
    Write-Log "下载并安装FFmpeg..."
    $ffmpegDir = "$PWD\ffmpeg"
    $ffmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    $ffmpegZip = "$env:TEMP\ffmpeg.zip"
    
    try {
        if (-not (Test-Path $ffmpegDir)) {
            New-Item -ItemType Directory -Path $ffmpegDir -Force | Out-Null
        }
        
        Invoke-WebRequest -Uri $ffmpegUrl -OutFile $ffmpegZip -UseBasicParsing
        Write-Log "FFmpeg下载完成"
        
        # 解压FFmpeg
        Expand-Archive -Path $ffmpegZip -DestinationPath $ffmpegDir -Force
        
        # 找到ffmpeg.exe并添加到PATH
        $ffmpegExe = Get-ChildItem -Path $ffmpegDir -Name "ffmpeg.exe" -Recurse | Select-Object -First 1
        if ($ffmpegExe) {
            $ffmpegBinPath = Split-Path (Get-ChildItem -Path $ffmpegDir -Name "ffmpeg.exe" -Recurse | Select-Object -First 1).FullName
            
            # 添加到用户PATH
            $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
            if ($userPath -notlike "*$ffmpegBinPath*") {
                [Environment]::SetEnvironmentVariable("Path", "$userPath;$ffmpegBinPath", "User")
                $env:Path += ";$ffmpegBinPath"
                Write-Log "FFmpeg已添加到PATH: $ffmpegBinPath"
            }
        }
        
        Remove-Item $ffmpegZip -Force
        Write-Log "FFmpeg安装完成"
    } catch {
        Write-Log "FFmpeg安装失败: $($_.Exception.Message)"
    }
}

# 4. 安装Ollama
Write-Log "=== 安装Ollama ==="
$ollamaInstalled = $false
try {
    $ollamaVersion = ollama --version 2>$null
    if ($ollamaVersion -match "ollama version") {
        Write-Log "Ollama已安装: $ollamaVersion"
        $ollamaInstalled = $true
    }
} catch {}

if (-not $ollamaInstalled) {
    Write-Log "下载并安装Ollama..."
    $ollamaUrl = "https://ollama.com/download/OllamaSetup.exe"
    $ollamaInstaller = "$env:TEMP\OllamaSetup.exe"
    
    try {
        Invoke-WebRequest -Uri $ollamaUrl -OutFile $ollamaInstaller -UseBasicParsing
        Write-Log "Ollama下载完成"
        
        # 静默安装Ollama
        Start-Process -FilePath $ollamaInstaller -ArgumentList "/S" -Wait
        Write-Log "Ollama安装完成"
        
        # 刷新环境变量
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        Remove-Item $ollamaInstaller -Force
        
        # 启动Ollama服务
        Write-Log "启动Ollama服务..."
        Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 5
    } catch {
        Write-Log "Ollama安装失败: $($_.Exception.Message)"
    }
}

# 5. 安装Python依赖
Write-Log "=== 安装Python依赖 ==="
if (Test-Path "backend\requirements.txt") {
    try {
        # 创建虚拟环境
        if (-not (Test-Path "backend\venv")) {
            Write-Log "创建Python虚拟环境..."
            python -m venv backend\venv
        }
        
        # 激活虚拟环境并安装依赖
        Write-Log "安装Python依赖..."
        & "backend\venv\Scripts\pip.exe" install -r backend\requirements.txt
        Write-Log "Python依赖安装完成"
    } catch {
        Write-Log "Python依赖安装失败: $($_.Exception.Message)"
    }
} else {
    Write-Log "未找到backend\requirements.txt"
}

# 6. 安装前端依赖
Write-Log "=== 安装前端依赖 ==="
if (Test-Path "frontend\package.json") {
    try {
        Set-Location frontend
        Write-Log "安装前端依赖..."
        npm install
        Set-Location ..
        Write-Log "前端依赖安装完成"
    } catch {
        Write-Log "前端依赖安装失败: $($_.Exception.Message)"
        Set-Location ..
    }
} else {
    Write-Log "未找到frontend\package.json"
}

# 7. 安装启动器依赖
Write-Log "=== 安装启动器依赖 ==="
if (Test-Path "launcher\package.json") {
    try {
        Set-Location launcher
        Write-Log "安装启动器依赖..."
        npm install
        Set-Location ..
        Write-Log "启动器依赖安装完成"
    } catch {
        Write-Log "启动器依赖安装失败: $($_.Exception.Message)"
        Set-Location ..
    }
} else {
    Write-Log "未找到launcher\package.json"
}

# 8. 下载AI模型
Write-Log "=== 下载AI模型 ==="
try {
    Write-Log "下载Qwen2.5:7b模型（约4GB，请耐心等待）..."
    ollama pull qwen2.5:7b
    Write-Log "AI模型下载完成"
} catch {
    Write-Log "AI模型下载失败: $($_.Exception.Message)"
}

# 9. 创建配置文件
Write-Log "=== 创建配置文件 ==="
$envFile = "backend\.env"
if (-not (Test-Path $envFile)) {
    $envContent = @"
# Pervis PRO Configuration
DATABASE_URL=sqlite:///./pervis_director.db
SECRET_KEY=pervis-pro-secret-key-2024
DEBUG=True

# AI Configuration
USE_LOCAL_AI=True
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b

# Cloud AI (optional)
GEMINI_API_KEY=your-gemini-api-key-here
OPENAI_API_KEY=your-openai-api-key-here

# File Storage
UPLOAD_FOLDER=./storage/uploads
MAX_CONTENT_LENGTH=100MB
"@
    Set-Content -Path $envFile -Value $envContent -Encoding UTF8
    Write-Log "创建了backend\.env配置文件"
}

# 10. 最终验证
Write-Log "=== 最终验证 ==="
$components = @{
    "Python" = { python --version 2>$null }
    "Node.js" = { node --version 2>$null }
    "Git" = { git --version 2>$null }
    "FFmpeg" = { ffmpeg -version 2>$null | Select-Object -First 1 }
    "Ollama" = { ollama --version 2>$null }
}

$installedCount = 0
$totalCount = $components.Count

Write-Log "========================================"
Write-Log "  最终安装验证"
Write-Log "========================================"

foreach ($component in $components.GetEnumerator()) {
    try {
        $result = & $component.Value
        if ($result) {
            Write-Log "$($component.Key): $result"
            $installedCount++
        } else {
            Write-Log "$($component.Key): 未安装"
        }
    } catch {
        Write-Log "$($component.Key): 未安装"
    }
}

Write-Log "========================================"
Write-Log "  安装完成！"
Write-Log "========================================"
Write-Log ""
Write-Log "安装结果: $installedCount/$totalCount 组件成功安装"
Write-Log ""

if ($installedCount -eq $totalCount) {
    Write-Log "🎉 所有组件安装成功！"
    Write-Log ""
    Write-Log "下一步："
    Write-Log "1. 启动项目: python 启动_Pervis_PRO.py"
    Write-Log "2. 或使用启动器: python 创建桌面快捷方式.py"
} else {
    Write-Log "⚠️ 部分组件安装失败，请检查错误日志"
    Write-Log "可以重新运行此脚本或手动安装缺失组件"
}

Write-Log ""
Write-Log "安装日志已保存到: install_log.txt"
Write-Log "安装完成！按任意键退出..."

if (-not $SkipRestart) {
    Read-Host
}