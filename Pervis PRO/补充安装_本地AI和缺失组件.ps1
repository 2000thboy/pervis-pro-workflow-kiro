# Pervis PRO 补充安装 - 本地AI和缺失组件
# 安装 Ollama, Redis, CLIP模型等高级组件

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Pervis PRO 补充安装" -ForegroundColor Cyan
Write-Host "  本地AI和高级组件" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$projectRoot = $PSScriptRoot

# 检查基础环境
Write-Host ""
Write-Host "检查基础环境..." -ForegroundColor Yellow
try {
    python --version | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Python not found" }
    Write-Host "✓ Python 已安装" -ForegroundColor Green
} catch {
    Write-Host "❌ Python 未安装，请先运行基础安装脚本" -ForegroundColor Red
    exit 1
}

# 1. 安装 Ollama (本地大模型)
Write-Host ""
Write-Host "[1/6] 安装 Ollama (本地大模型)..." -ForegroundColor Green

try {
    ollama --version | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Ollama 已安装" -ForegroundColor Green
    } else {
        throw "Ollama not found"
    }
} catch {
    Write-Host "正在下载 Ollama..." -ForegroundColor Yellow
    
    $ollamaUrl = "https://ollama.com/download/windows"
    $ollamaInstaller = "$env:TEMP\OllamaSetup.exe"
    
    try {
        Invoke-WebRequest -Uri "https://ollama.com/download/OllamaSetup.exe" -OutFile $ollamaInstaller -UseBasicParsing
        Write-Host "正在安装 Ollama..." -ForegroundColor Yellow
        Start-Process -FilePath $ollamaInstaller -ArgumentList "/S" -Wait
        
        # 刷新环境变量
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        Write-Host "✓ Ollama 安装完成" -ForegroundColor Green
    } catch {
        Write-Host "⚠ Ollama 自动安装失败，请手动安装:" -ForegroundColor Yellow
        Write-Host "  下载地址: https://ollama.com/download" -ForegroundColor White
    }
}

# 2. 下载本地模型
Write-Host ""
Write-Host "[2/6] 下载本地AI模型..." -ForegroundColor Green

try {
    # 检查 Ollama 服务是否运行
    $ollamaProcess = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
    if (-not $ollamaProcess) {
        Write-Host "启动 Ollama 服务..." -ForegroundColor Yellow
        Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 5
    }
    
    Write-Host "下载 Qwen2.5:14b 模型（这可能需要较长时间）..." -ForegroundColor Yellow
    Write-Host "模型大小约 8GB，请确保有足够的磁盘空间和网络带宽" -ForegroundColor Cyan
    
    # 检查模型是否已存在
    $modelList = ollama list 2>&1
    if ($modelList -like "*qwen2.5:14b*") {
        Write-Host "✓ Qwen2.5:14b 模型已存在" -ForegroundColor Green
    } else {
        Write-Host "正在下载模型，请耐心等待..." -ForegroundColor Yellow
        ollama pull qwen2.5:14b
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Qwen2.5:14b 模型下载完成" -ForegroundColor Green
        } else {
            Write-Host "⚠ 模型下载失败，可以稍后手动执行: ollama pull qwen2.5:14b" -ForegroundColor Yellow
        }
    }
    
    # 下载备用小模型
    Write-Host "下载备用轻量模型 Qwen2.5:7b..." -ForegroundColor Yellow
    if ($modelList -like "*qwen2.5:7b*") {
        Write-Host "✓ Qwen2.5:7b 模型已存在" -ForegroundColor Green
    } else {
        ollama pull qwen2.5:7b
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Qwen2.5:7b 备用模型下载完成" -ForegroundColor Green
        }
    }
    
} catch {
    Write-Host "⚠ 本地模型下载失败: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "  可以稍后手动执行:" -ForegroundColor White
    Write-Host "  ollama pull qwen2.5:14b" -ForegroundColor White
    Write-Host "  ollama pull qwen2.5:7b" -ForegroundColor White
}

# 3. 安装 Redis (任务队列)
Write-Host ""
Write-Host "[3/6] 安装 Redis..." -ForegroundColor Green

try {
    redis-server --version | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Redis 已安装" -ForegroundColor Green
    } else {
        throw "Redis not found"
    }
} catch {
    Write-Host "正在通过 Chocolatey 安装 Redis..." -ForegroundColor Yellow
    
    try {
        choco install redis-64 -y
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Redis 安装完成" -ForegroundColor Green
        } else {
            throw "Chocolatey install failed"
        }
    } catch {
        Write-Host "⚠ Redis 自动安装失败" -ForegroundColor Yellow
        Write-Host "  Windows 用户可以使用 WSL 或 Docker 运行 Redis" -ForegroundColor White
        Write-Host "  或下载 Redis for Windows: https://github.com/microsoftarchive/redis/releases" -ForegroundColor White
    }
}

# 4. 安装 Python AI/ML 依赖
Write-Host ""
Write-Host "[4/6] 安装 Python AI/ML 依赖..." -ForegroundColor Green

Set-Location "$projectRoot\backend"

# 激活虚拟环境
if (Test-Path "venv\Scripts\Activate.ps1") {
    & ".\venv\Scripts\Activate.ps1"
    Write-Host "✓ 虚拟环境已激活" -ForegroundColor Green
} else {
    Write-Host "⚠ 虚拟环境不存在，使用全局 Python" -ForegroundColor Yellow
}

# 安装 PyTorch (CPU版本，适合大多数用户)
Write-Host "安装 PyTorch (CPU版本)..." -ForegroundColor Yellow
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 安装 CLIP
Write-Host "安装 OpenAI CLIP..." -ForegroundColor Yellow
pip install git+https://github.com/openai/CLIP.git

# 安装其他AI依赖
Write-Host "安装其他AI依赖..." -ForegroundColor Yellow
pip install opencv-python transformers aioredis

# 安装可选的GPU支持（如果用户有NVIDIA GPU）
Write-Host ""
Write-Host "检查GPU支持..." -ForegroundColor Yellow
try {
    $gpuInfo = nvidia-smi 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ 检测到 NVIDIA GPU" -ForegroundColor Green
        Write-Host "如需GPU加速，可手动安装CUDA版本的PyTorch:" -ForegroundColor Cyan
        Write-Host "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118" -ForegroundColor White
    } else {
        Write-Host "✓ 使用CPU版本（适合大多数用户）" -ForegroundColor Green
    }
} catch {
    Write-Host "✓ 使用CPU版本（适合大多数用户）" -ForegroundColor Green
}

# 5. 更新配置文件
Write-Host ""
Write-Host "[5/6] 更新配置文件..." -ForegroundColor Green

$envFile = "$projectRoot\backend\.env"
if (Test-Path $envFile) {
    $envContent = Get-Content $envFile -Raw
    
    # 检查是否需要添加本地AI配置
    if ($envContent -notlike "*OLLAMA_BASE_URL*") {
        Write-Host "添加本地AI配置..." -ForegroundColor Yellow
        
        $additionalConfig = @"

# Local AI Configuration (Ollama)
OLLAMA_BASE_URL=http://localhost:11434/v1
LOCAL_MODEL_NAME=qwen2.5:14b

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Visual Processing
CLIP_MODEL=ViT-B/32
ENABLE_VISUAL_ANALYSIS=true
"@
        
        Add-Content -Path $envFile -Value $additionalConfig -Encoding UTF8
        Write-Host "✓ 配置文件已更新" -ForegroundColor Green
    } else {
        Write-Host "✓ 配置文件已包含本地AI设置" -ForegroundColor Green
    }
} else {
    Write-Host "⚠ 配置文件不存在，请先运行基础安装" -ForegroundColor Yellow
}

# 6. 测试安装
Write-Host ""
Write-Host "[6/6] 测试安装..." -ForegroundColor Green

# 测试 Ollama
Write-Host "测试 Ollama..." -ForegroundColor Yellow
try {
    $ollamaTest = ollama list 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Ollama 工作正常" -ForegroundColor Green
        Write-Host "  已安装的模型:" -ForegroundColor Cyan
        ollama list
    } else {
        Write-Host "⚠ Ollama 测试失败" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ Ollama 测试异常" -ForegroundColor Yellow
}

# 测试 Python 依赖
Write-Host ""
Write-Host "测试 Python AI 依赖..." -ForegroundColor Yellow
$testScript = @"
try:
    import torch
    print("✓ PyTorch:", torch.__version__)
    
    import clip
    print("✓ CLIP: 已安装")
    
    import cv2
    print("✓ OpenCV:", cv2.__version__)
    
    import transformers
    print("✓ Transformers:", transformers.__version__)
    
    try:
        import aioredis
        print("✓ aioredis: 已安装")
    except ImportError:
        print("⚠ aioredis: 未安装")
    
    print("\n🎉 所有AI依赖测试通过！")
    
except ImportError as e:
    print(f"❌ 依赖测试失败: {e}")
"@

python -c $testScript

# 完成
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  补充安装完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "已安装的高级组件:" -ForegroundColor Yellow
Write-Host "✓ Ollama - 本地大模型运行环境" -ForegroundColor White
Write-Host "✓ Qwen2.5 - 中文大语言模型" -ForegroundColor White
Write-Host "✓ PyTorch - 深度学习框架" -ForegroundColor White
Write-Host "✓ CLIP - 视觉-语言理解模型" -ForegroundColor White
Write-Host "✓ OpenCV - 计算机视觉库" -ForegroundColor White
Write-Host "✓ Redis - 缓存和任务队列" -ForegroundColor White
Write-Host ""
Write-Host "配置说明:" -ForegroundColor Yellow
Write-Host "- 编辑 backend\.env 设置 LLM_PROVIDER=local 使用本地AI" -ForegroundColor White
Write-Host "- 或保持 LLM_PROVIDER=gemini 使用云端AI" -ForegroundColor White
Write-Host "- 本地AI无需API密钥，但需要更多计算资源" -ForegroundColor White
Write-Host ""
Write-Host "启动服务:" -ForegroundColor Yellow
Write-Host "1. 启动 Ollama: ollama serve" -ForegroundColor White
Write-Host "2. 启动 Redis: redis-server" -ForegroundColor White
Write-Host "3. 启动项目: python 启动_Pervis_PRO.py" -ForegroundColor White
Write-Host ""

Set-Location $projectRoot