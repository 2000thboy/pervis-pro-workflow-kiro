# Pervis PRO 修复安装脚本
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

Write-Log "开始Pervis PRO修复安装..."

# 1. 检查Python
Write-Log "=== 检查Python ==="
$pythonInstalled = $false
try {
    $pythonCheck = python --version 2>&1
    if ($pythonCheck -match "Python 3\.") {
        Write-Log "Python已安装: $pythonCheck"
        $pythonInstalled = $true
    }
} catch {
    Write-Log "Python检查失败"
}

if (-not $pythonInstalled) {
    Write-Log "Python未正确安装，尝试修复..."
    # 尝试使用py命令
    try {
        $pyCheck = py --version 2>&1
        if ($pyCheck -match "Python 3\.") {
            Write-Log "找到py命令: $pyCheck"
            # 创建python别名
            $pythonPath = (Get-Command py).Source
            $pythonDir = Split-Path $pythonPath
            $env:Path = "$pythonDir;$env:Path"
            Write-Log "已修复Python路径"
            $pythonInstalled = $true
        }
    } catch {
        Write-Log "py命令也不可用"
    }
}

# 2. 检查Node.js
Write-Log "=== 检查Node.js ==="
$nodeInstalled = $false
try {
    $nodeCheck = node --version 2>&1
    if ($nodeCheck -match "v\d+") {
        Write-Log "Node.js已安装: $nodeCheck"
        $nodeInstalled = $true
    }
} catch {
    Write-Log "Node.js未安装"
}

# 3. 检查Git
Write-Log "=== 检查Git ==="
$gitInstalled = $false
try {
    $gitCheck = git --version 2>&1
    if ($gitCheck -match "git version") {
        Write-Log "Git已安装: $gitCheck"
        $gitInstalled = $true
    }
} catch {
    Write-Log "Git未安装"
}

# 4. 检查FFmpeg
Write-Log "=== 检查FFmpeg ==="
$ffmpegInstalled = $false
try {
    $ffmpegCheck = ffmpeg -version 2>&1 | Select-Object -First 1
    if ($ffmpegCheck -match "ffmpeg version") {
        Write-Log "FFmpeg已安装: $ffmpegCheck"
        $ffmpegInstalled = $true
    }
} catch {
    Write-Log "FFmpeg未安装"
}

# 5. 检查Ollama
Write-Log "=== 检查Ollama ==="
$ollamaInstalled = $false
try {
    $ollamaCheck = ollama --version 2>&1
    if ($ollamaCheck -match "ollama version") {
        Write-Log "Ollama已安装: $ollamaCheck"
        $ollamaInstalled = $true
    }
} catch {
    Write-Log "Ollama未安装"
}

# 6. 安装Python依赖（如果Python可用）
Write-Log "=== 安装Python依赖 ==="
if ($pythonInstalled -and (Test-Path "backend\requirements.txt")) {
    try {
        Write-Log "创建Python虚拟环境..."
        if (-not (Test-Path "backend\venv")) {
            if (Get-Command py -ErrorAction SilentlyContinue) {
                py -m venv backend\venv
            } else {
                python -m venv backend\venv
            }
        }
        
        Write-Log "安装Python依赖..."
        if (Test-Path "backend\venv\Scripts\pip.exe") {
            & "backend\venv\Scripts\pip.exe" install -r backend\requirements.txt
            Write-Log "Python依赖安装完成"
        }
    } catch {
        Write-Log "Python依赖安装失败: $($_.Exception.Message)"
    }
} else {
    Write-Log "跳过Python依赖安装（Python不可用或requirements.txt不存在）"
}

# 7. 安装前端依赖（如果Node.js可用）
Write-Log "=== 安装前端依赖 ==="
if ($nodeInstalled -and (Test-Path "frontend\package.json")) {
    try {
        Push-Location frontend
        Write-Log "安装前端依赖..."
        npm install
        Pop-Location
        Write-Log "前端依赖安装完成"
    } catch {
        Write-Log "前端依赖安装失败: $($_.Exception.Message)"
        Pop-Location
    }
} else {
    Write-Log "跳过前端依赖安装（Node.js不可用或package.json不存在）"
}

# 8. 安装启动器依赖（如果Node.js可用）
Write-Log "=== 安装启动器依赖 ==="
if ($nodeInstalled -and (Test-Path "launcher\package.json")) {
    try {
        Push-Location launcher
        Write-Log "安装启动器依赖..."
        npm install
        Pop-Location
        Write-Log "启动器依赖安装完成"
    } catch {
        Write-Log "启动器依赖安装失败: $($_.Exception.Message)"
        Pop-Location
    }
} else {
    Write-Log "跳过启动器依赖安装（Node.js不可用或package.json不存在）"
}

# 9. 下载AI模型（如果Ollama可用）
Write-Log "=== 下载AI模型 ==="
if ($ollamaInstalled) {
    try {
        Write-Log "检查Ollama服务状态..."
        $ollamaProcess = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
        if (-not $ollamaProcess) {
            Write-Log "启动Ollama服务..."
            Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
            Start-Sleep -Seconds 10
        }
        
        Write-Log "下载Qwen2.5:7b模型（约4GB）..."
        ollama pull qwen2.5:7b
        Write-Log "AI模型下载完成"
    } catch {
        Write-Log "AI模型下载失败: $($_.Exception.Message)"
    }
} else {
    Write-Log "跳过AI模型下载（Ollama不可用）"
}

# 10. 创建配置文件
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
    try {
        Set-Content -Path $envFile -Value $envContent -Encoding UTF8
        Write-Log "创建了backend\.env配置文件"
    } catch {
        Write-Log "配置文件创建失败: $($_.Exception.Message)"
    }
}

# 11. 最终验证
Write-Log "========================================"
Write-Log "  最终安装验证"
Write-Log "========================================"

$components = @{
    "Python" = $pythonInstalled
    "Node.js" = $nodeInstalled
    "Git" = $gitInstalled
    "FFmpeg" = $ffmpegInstalled
    "Ollama" = $ollamaInstalled
}

$installedCount = 0
$totalCount = $components.Count

foreach ($component in $components.GetEnumerator()) {
    $status = if ($component.Value) { "已安装" } else { "未安装" }
    Write-Log "$($component.Key): $status"
    if ($component.Value) { $installedCount++ }
}

Write-Log "========================================"
Write-Log "  安装完成！"
Write-Log "========================================"
Write-Log "安装结果: $installedCount/$totalCount 组件成功安装"

if ($installedCount -ge 3) {
    Write-Log "基本组件已安装，可以尝试启动项目"
    Write-Log "下一步："
    if ($pythonInstalled) {
        Write-Log "1. 启动项目: python 启动_Pervis_PRO.py"
    } else {
        Write-Log "1. 需要先安装Python才能启动项目"
    }
    Write-Log "2. 查看详细状态: 安装报告.md"
} else {
    Write-Log "需要安装更多组件才能正常运行"
}

Write-Log "安装日志已保存到: install_log.txt"

if (-not $SkipRestart) {
    Write-Log "按任意键退出..."
    Read-Host
}