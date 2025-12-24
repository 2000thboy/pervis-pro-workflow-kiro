# Pervis PRO Auto Install - Fixed Version
# Fully automated installation without user interaction

param(
    [switch]$Force,
    [switch]$SkipRestart
)

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Pervis PRO Auto Installation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$projectRoot = $PSScriptRoot
$logFile = "$projectRoot\install_log.txt"

# Log function
function Write-Log {
    param($Message, $Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $Message -ForegroundColor $Color
    Add-Content -Path $logFile -Value $logMessage -Encoding UTF8
}

# Check admin privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin -and -not $Force) {
    Write-Log "Restarting with admin privileges..." "Yellow"
    $arguments = "-ExecutionPolicy Bypass -File `"$PSCommandPath`" -Force"
    if ($SkipRestart) { $arguments += " -SkipRestart" }
    Start-Process PowerShell -Verb RunAs -ArgumentList $arguments
    exit
}

Write-Log "Starting auto installation..." "Green"

# Create download directory
$downloadDir = "$env:TEMP\PervisPRO_Install"
if (Test-Path $downloadDir) {
    Remove-Item $downloadDir -Recurse -Force
}
New-Item -ItemType Directory -Path $downloadDir -Force | Out-Null

# Download function with retry
function Download-FileWithRetry {
    param($url, $output, $name, $maxRetries = 3)
    
    for ($i = 1; $i -le $maxRetries; $i++) {
        try {
            Write-Log "Downloading $name (attempt $i/$maxRetries)..." "Yellow"
            
            # Use WebClient for better compatibility
            $webClient = New-Object System.Net.WebClient
            $webClient.DownloadFile($url, $output)
            Write-Log "Downloaded $name successfully" "Green"
            return $true
        } catch {
            Write-Log "Download failed (attempt $i): $($_.Exception.Message)" "Red"
            if ($i -eq $maxRetries) {
                Write-Log "Failed to download $name after $maxRetries attempts" "Red"
                return $false
            }
            Start-Sleep -Seconds 5
        }
    }
    return $false
}

# Install function with retry
function Install-WithRetry {
    param($installer, $args, $name, $maxRetries = 2)
    
    for ($i = 1; $i -le $maxRetries; $i++) {
        try {
            Write-Log "Installing $name (attempt $i/$maxRetries)..." "Yellow"
            
            if ($args -and $args.Count -gt 0) {
                $process = Start-Process -FilePath $installer -ArgumentList $args -Wait -PassThru -NoNewWindow
            } else {
                $process = Start-Process -FilePath $installer -Wait -PassThru -NoNewWindow
            }
            
            if ($process.ExitCode -eq 0 -or $process.ExitCode -eq 3010) {
                Write-Log "Installed $name successfully" "Green"
                return $true
            } else {
                throw "Installation failed with exit code: $($process.ExitCode)"
            }
        } catch {
            Write-Log "Installation failed (attempt $i): $($_.Exception.Message)" "Red"
            if ($i -eq $maxRetries) {
                Write-Log "Failed to install $name" "Red"
                return $false
            }
            Start-Sleep -Seconds 3
        }
    }
    return $false
}

# Refresh environment variables
function Refresh-Environment {
    Write-Log "Refreshing environment variables..." "Yellow"
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

# 1. Install Python
Write-Log ""
Write-Log "[1/6] Installing Python..." "Green"
try {
    python --version 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Python already installed" "Green"
    } else {
        throw "Python not found"
    }
} catch {
    $pythonUrl = "https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe"
    $pythonInstaller = "$downloadDir\python-installer.exe"
    
    if (Download-FileWithRetry $pythonUrl $pythonInstaller "Python 3.11") {
        $pythonArgs = @("/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_test=0")
        Install-WithRetry $pythonInstaller $pythonArgs "Python"
        Refresh-Environment
    }
}

# 2. Install Node.js
Write-Log ""
Write-Log "[2/6] Installing Node.js..." "Green"
try {
    node --version 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Node.js already installed" "Green"
    } else {
        throw "Node.js not found"
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

# 3. Install Git
Write-Log ""
Write-Log "[3/6] Installing Git..." "Green"
try {
    git --version 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Git already installed" "Green"
    } else {
        throw "Git not found"
    }
} catch {
    $gitUrl = "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe"
    $gitInstaller = "$downloadDir\git-installer.exe"
    
    if (Download-FileWithRetry $gitUrl $gitInstaller "Git") {
        $gitArgs = @("/VERYSILENT", "/NORESTART", "/NOCANCEL", "/SP-")
        Install-WithRetry $gitInstaller $gitArgs "Git"
        Refresh-Environment
    }
}

# 4. Install Chocolatey and FFmpeg
Write-Log ""
Write-Log "[4/6] Installing Chocolatey and FFmpeg..." "Green"
try {
    choco --version 2>&1 | Out-Null
    Write-Log "Chocolatey already installed" "Green"
} catch {
    Write-Log "Installing Chocolatey..." "Yellow"
    try {
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        
        $webClient = New-Object System.Net.WebClient
        $chocoScript = $webClient.DownloadString('https://chocolatey.org/install.ps1')
        Invoke-Expression $chocoScript
        
        Refresh-Environment
        Write-Log "Chocolatey installed successfully" "Green"
    } catch {
        Write-Log "Chocolatey installation failed, skipping FFmpeg" "Yellow"
    }
}

# Install FFmpeg
try {
    ffmpeg -version 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Log "FFmpeg already installed" "Green"
    } else {
        throw "FFmpeg not found"
    }
} catch {
    try {
        choco install ffmpeg -y --no-progress
        Refresh-Environment
        Write-Log "FFmpeg installed successfully" "Green"
    } catch {
        Write-Log "FFmpeg installation failed" "Yellow"
    }
}

# Wait for environment variables to take effect
Write-Log ""
Write-Log "Waiting for environment variables..." "Yellow"
Start-Sleep -Seconds 5
Refresh-Environment

# 5. Install project dependencies
Write-Log ""
Write-Log "[5/6] Installing project dependencies..." "Green"

# Backend dependencies
Write-Log "Installing backend dependencies..." "Yellow"
Set-Location "$projectRoot\backend"

if (!(Test-Path "venv")) {
    Write-Log "Creating Python virtual environment..." "Yellow"
    try {
        python -m venv venv
        Write-Log "Virtual environment created successfully" "Green"
    } catch {
        Write-Log "Virtual environment creation failed, using global Python" "Yellow"
    }
}

# Activate virtual environment and install dependencies
if (Test-Path "venv\Scripts\Activate.ps1") {
    try {
        & ".\venv\Scripts\Activate.ps1"
        Write-Log "Virtual environment activated" "Green"
    } catch {
        Write-Log "Virtual environment activation failed" "Yellow"
    }
}

Write-Log "Installing Python packages..." "Yellow"
try {
    python -m pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
    Write-Log "Backend dependencies installed successfully" "Green"
} catch {
    Write-Log "Backend dependencies installation failed" "Red"
}

# Frontend dependencies
Write-Log ""
Write-Log "Installing frontend dependencies..." "Yellow"
Set-Location "$projectRoot\frontend"

try {
    npm install --silent
    Write-Log "Frontend dependencies installed successfully" "Green"
} catch {
    Write-Log "Frontend dependencies installation failed" "Red"
}

# Launcher dependencies
Write-Log ""
Write-Log "Installing launcher dependencies..." "Yellow"
Set-Location $projectRoot

try {
    pip install customtkinter pillow --quiet
    Write-Log "Launcher dependencies installed successfully" "Green"
} catch {
    Write-Log "Launcher dependencies installation failed" "Red"
}

# 6. Install AI components
Write-Log ""
Write-Log "[6/6] Installing AI components..." "Green"

# Install Ollama
Write-Log "Installing Ollama..." "Yellow"
try {
    ollama --version 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Ollama already installed" "Green"
    } else {
        throw "Ollama not found"
    }
} catch {
    $ollamaUrl = "https://ollama.com/download/OllamaSetup.exe"
    $ollamaInstaller = "$downloadDir\OllamaSetup.exe"
    
    if (Download-FileWithRetry $ollamaUrl $ollamaInstaller "Ollama") {
        Install-WithRetry $ollamaInstaller @("/S") "Ollama"
        Refresh-Environment
        
        # Start Ollama service
        try {
            Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
            Start-Sleep -Seconds 5
            Write-Log "Ollama service started" "Green"
        } catch {
            Write-Log "Ollama service start failed" "Yellow"
        }
    }
}

# Download AI models
Write-Log "Downloading AI models..." "Yellow"
try {
    $modelList = ollama list 2>&1
    if ($modelList -like "*qwen2.5:7b*") {
        Write-Log "Qwen2.5:7b model already exists" "Green"
    } else {
        Write-Log "Downloading Qwen2.5:7b model (about 4GB)..." "Yellow"
        ollama pull qwen2.5:7b
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Qwen2.5:7b model downloaded successfully" "Green"
        }
    }
} catch {
    Write-Log "AI model download failed" "Yellow"
}

# Install Python AI libraries
Write-Log "Installing Python AI libraries..." "Yellow"
try {
    # Install PyTorch (CPU version)
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu --quiet
    
    # Install other AI libraries
    pip install opencv-python transformers aioredis --quiet
    
    # Try to install CLIP
    pip install git+https://github.com/openai/CLIP.git --quiet
    
    Write-Log "Python AI libraries installed successfully" "Green"
} catch {
    Write-Log "Python AI libraries installation failed" "Yellow"
}

# Create/update configuration file
Write-Log ""
Write-Log "Creating configuration file..." "Green"
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
Write-Log "Configuration file created" "Green"

# Clean up download files
Write-Log ""
Write-Log "Cleaning up temporary files..." "Yellow"
Remove-Item $downloadDir -Recurse -Force -ErrorAction SilentlyContinue

# Final verification
Write-Log ""
Write-Log "========================================" "Cyan"
Write-Log "  Installation Verification" "Cyan"
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
            Write-Log "$($component.Name): $result" "Green"
            $successCount++
        } else {
            Write-Log "$($component.Name): Not working properly" "Red"
        }
    } catch {
        Write-Log "$($component.Name): Not installed" "Red"
    }
}

# Final report
Write-Log ""
Write-Log "========================================" "Cyan"
Write-Log "  Installation Complete!" "Green"
Write-Log "========================================" "Cyan"
Write-Log ""
Write-Log "Installation result: $successCount/5 components successfully installed" $(if ($successCount -ge 4) { "Green" } else { "Yellow" })
Write-Log ""
Write-Log "Next steps:" "Yellow"
Write-Log "1. For cloud AI, get Gemini API key: https://makersuite.google.com/app/apikey" "White"
Write-Log "2. Edit backend\.env to set API key or use local AI" "White"
Write-Log "3. Start project: python 启动_Pervis_PRO.py" "White"
Write-Log ""
Write-Log "Installation log saved to: $logFile" "Cyan"

Set-Location $projectRoot

if (-not $SkipRestart) {
    Write-Log ""
    Write-Log "Installation complete! Press any key to exit..." "Green"
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}