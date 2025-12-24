# Pervis PRO Quick Install - Using Package Managers
# Faster installation using Chocolatey and Winget

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Pervis PRO Quick Installation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$projectRoot = $PSScriptRoot

# Function to check if running as administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Check if running as administrator
if (!(Test-Administrator)) {
    Write-Host "This script requires administrator privileges." -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Alternative: Run the manual installation steps from README_安装说明.md" -ForegroundColor Cyan
    exit 1
}

# Install Chocolatey if not present
Write-Host ""
Write-Host "[1/5] Checking Chocolatey..." -ForegroundColor Green
try {
    choco --version | Out-Null
    Write-Host "Chocolatey already installed" -ForegroundColor Green
} catch {
    Write-Host "Installing Chocolatey..." -ForegroundColor Yellow
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Chocolatey installed successfully" -ForegroundColor Green
    } else {
        Write-Host "Chocolatey installation failed" -ForegroundColor Red
    }
}

# Install Python
Write-Host ""
Write-Host "[2/5] Installing Python..." -ForegroundColor Green
try {
    python --version | Out-Null
    Write-Host "Python already installed" -ForegroundColor Green
} catch {
    Write-Host "Installing Python via Chocolatey..." -ForegroundColor Yellow
    choco install python -y
    
    # Refresh environment
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Python installed successfully" -ForegroundColor Green
    } else {
        Write-Host "Python installation failed" -ForegroundColor Red
    }
}

# Install Node.js
Write-Host ""
Write-Host "[3/5] Installing Node.js..." -ForegroundColor Green
try {
    node --version | Out-Null
    Write-Host "Node.js already installed" -ForegroundColor Green
} catch {
    Write-Host "Installing Node.js via Chocolatey..." -ForegroundColor Yellow
    choco install nodejs -y
    
    # Refresh environment
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Node.js installed successfully" -ForegroundColor Green
    } else {
        Write-Host "Node.js installation failed" -ForegroundColor Red
    }
}

# Install Git
Write-Host ""
Write-Host "[4/5] Installing Git..." -ForegroundColor Green
try {
    git --version | Out-Null
    Write-Host "Git already installed" -ForegroundColor Green
} catch {
    Write-Host "Installing Git via Chocolatey..." -ForegroundColor Yellow
    choco install git -y
    
    # Refresh environment
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Git installed successfully" -ForegroundColor Green
    } else {
        Write-Host "Git installation failed" -ForegroundColor Red
    }
}

# Install FFmpeg
Write-Host ""
Write-Host "[5/5] Installing FFmpeg..." -ForegroundColor Green
try {
    ffmpeg -version | Out-Null
    Write-Host "FFmpeg already installed" -ForegroundColor Green
} catch {
    Write-Host "Installing FFmpeg via Chocolatey..." -ForegroundColor Yellow
    choco install ffmpeg -y
    
    # Refresh environment
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "FFmpeg installed successfully" -ForegroundColor Green
    } else {
        Write-Host "FFmpeg installation failed" -ForegroundColor Red
    }
}

# Wait for environment variables
Write-Host ""
Write-Host "Refreshing environment variables..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Install project dependencies
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installing Project Dependencies" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Backend dependencies
Write-Host ""
Write-Host "Installing backend dependencies..." -ForegroundColor Green
Set-Location "$projectRoot\backend"

if (!(Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "Installing Python packages..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "Backend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "Backend installation failed" -ForegroundColor Red
}

# Frontend dependencies
Write-Host ""
Write-Host "Installing frontend dependencies..." -ForegroundColor Green
Set-Location "$projectRoot\frontend"

npm install

if ($LASTEXITCODE -eq 0) {
    Write-Host "Frontend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "Frontend installation failed" -ForegroundColor Red
}

# Launcher dependencies
Write-Host ""
Write-Host "Installing launcher dependencies..." -ForegroundColor Green
Set-Location $projectRoot
pip install customtkinter pillow

if ($LASTEXITCODE -eq 0) {
    Write-Host "Launcher dependencies installed" -ForegroundColor Green
} else {
    Write-Host "Launcher installation failed" -ForegroundColor Red
}

# Create config file
Write-Host ""
Write-Host "Creating configuration file..." -ForegroundColor Green
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

# Network Configuration
NETWORK_DRIVE=L
NETWORK_DRIVE_NAME=影片参考
"@
    
    Set-Content -Path $envFile -Value $envContent -Encoding UTF8
    Write-Host "Configuration file created: backend\.env" -ForegroundColor Green
} else {
    Write-Host "Configuration file already exists" -ForegroundColor Green
}

# Complete
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Get Gemini API key: https://makersuite.google.com/app/apikey" -ForegroundColor White
Write-Host "2. Edit backend\.env file and set GEMINI_API_KEY" -ForegroundColor White
Write-Host "3. Restart PowerShell to refresh environment variables" -ForegroundColor White
Write-Host "4. Run project: python 启动_Pervis_PRO.py" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Set-Location $projectRoot