# Pervis PRO Complete Auto Installation
# Downloads and installs everything automatically

param(
    [switch]$Force
)

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin -and -not $Force) {
    Write-Host "Restarting as Administrator..." -ForegroundColor Yellow
    Start-Process PowerShell -Verb RunAs -ArgumentList "-ExecutionPolicy Bypass -File `"$PSCommandPath`" -Force"
    exit
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Pervis PRO Complete Auto Installation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$projectRoot = $PSScriptRoot
$downloads = @()

# Download URLs
$pythonUrl = "https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe"
$nodeUrl = "https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi"
$gitUrl = "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe"

# Create downloads directory
$downloadDir = "$env:TEMP\PervisPRO"
if (!(Test-Path $downloadDir)) {
    New-Item -ItemType Directory -Path $downloadDir -Force | Out-Null
}

# Download function with progress
function Download-WithProgress {
    param($url, $output, $name)
    
    Write-Host "Downloading $name..." -ForegroundColor Yellow
    
    try {
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($url, $output)
        Write-Host "✓ $name downloaded" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "✗ Failed to download $name" -ForegroundColor Red
        return $false
    }
}

# Install function
function Install-Package {
    param($installer, $args, $name)
    
    Write-Host "Installing $name..." -ForegroundColor Yellow
    
    try {
        if ($args) {
            $process = Start-Process -FilePath $installer -ArgumentList $args -Wait -PassThru -NoNewWindow
        } else {
            $process = Start-Process -FilePath $installer -Wait -PassThru -NoNewWindow
        }
        
        if ($process.ExitCode -eq 0) {
            Write-Host "✓ $name installed successfully" -ForegroundColor Green
            return $true
        } else {
            Write-Host "✗ $name installation failed (Exit code: $($process.ExitCode))" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "✗ $name installation error: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Check and install Python
Write-Host ""
Write-Host "[1/4] Python Installation" -ForegroundColor Green
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Python already installed: $pythonVersion" -ForegroundColor Green
    } else {
        throw "Python not found"
    }
} catch {
    $pythonInstaller = "$downloadDir\python-installer.exe"
    if (Download-WithProgress $pythonUrl $pythonInstaller "Python 3.11") {
        $pythonArgs = @("/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_test=0", "Include_doc=0")
        Install-Package $pythonInstaller $pythonArgs "Python"
    }
}

# Check and install Node.js
Write-Host ""
Write-Host "[2/4] Node.js Installation" -ForegroundColor Green
try {
    $nodeVersion = node --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Node.js already installed: $nodeVersion" -ForegroundColor Green
    } else {
        throw "Node.js not found"
    }
} catch {
    $nodeInstaller = "$downloadDir\node-installer.msi"
    if (Download-WithProgress $nodeUrl $nodeInstaller "Node.js 20") {
        $nodeArgs = @("/i", "`"$nodeInstaller`"", "/quiet", "/norestart")
        Install-Package "msiexec.exe" $nodeArgs "Node.js"
    }
}

# Check and install Git
Write-Host ""
Write-Host "[3/4] Git Installation" -ForegroundColor Green
try {
    $gitVersion = git --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Git already installed: $gitVersion" -ForegroundColor Green
    } else {
        throw "Git not found"
    }
} catch {
    $gitInstaller = "$downloadDir\git-installer.exe"
    if (Download-WithProgress $gitUrl $gitInstaller "Git") {
        $gitArgs = @("/VERYSILENT", "/NORESTART", "/NOCANCEL", "/SP-", "/CLOSEAPPLICATIONS", "/RESTARTAPPLICATIONS", "/COMPONENTS=`"icons,ext\reg\shellhere,assoc,assoc_sh`"")
        Install-Package $gitInstaller $gitArgs "Git"
    }
}

# Install FFmpeg using Chocolatey
Write-Host ""
Write-Host "[4/4] FFmpeg Installation" -ForegroundColor Green
try {
    $ffmpegVersion = ffmpeg -version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ FFmpeg already installed" -ForegroundColor Green
    } else {
        throw "FFmpeg not found"
    }
} catch {
    # Try to install Chocolatey first
    try {
        choco --version | Out-Null
        Write-Host "✓ Chocolatey found, installing FFmpeg..." -ForegroundColor Yellow
        choco install ffmpeg -y
    } catch {
        Write-Host "Installing Chocolatey..." -ForegroundColor Yellow
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Installing FFmpeg via Chocolatey..." -ForegroundColor Yellow
            choco install ffmpeg -y
        } else {
            Write-Host "⚠ FFmpeg installation skipped (Chocolatey failed)" -ForegroundColor Yellow
        }
    }
}

# Refresh environment variables
Write-Host ""
Write-Host "Refreshing environment variables..." -ForegroundColor Yellow
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Wait a moment for installations to complete
Start-Sleep -Seconds 5

# Verify installations
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Verifying Installations" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$components = @(
    @{Name="Python"; Command="python --version"},
    @{Name="Node.js"; Command="node --version"},
    @{Name="Git"; Command="git --version"},
    @{Name="FFmpeg"; Command="ffmpeg -version"}
)

foreach ($component in $components) {
    try {
        $result = Invoke-Expression $component.Command 2>&1
        if ($LASTEXITCODE -eq 0) {
            $version = ($result | Select-Object -First 1).ToString().Trim()
            Write-Host "✓ $($component.Name): $version" -ForegroundColor Green
        } else {
            Write-Host "✗ $($component.Name): Not working" -ForegroundColor Red
        }
    } catch {
        Write-Host "✗ $($component.Name): Not found" -ForegroundColor Red
    }
}

# Install project dependencies
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installing Project Dependencies" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Backend
Write-Host ""
Write-Host "Installing backend dependencies..." -ForegroundColor Green
Set-Location "$projectRoot\backend"

if (!(Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "Installing Python packages..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip
pip install -r requirements.txt

# Frontend
Write-Host ""
Write-Host "Installing frontend dependencies..." -ForegroundColor Green
Set-Location "$projectRoot\frontend"
npm install

# Launcher
Write-Host ""
Write-Host "Installing launcher dependencies..." -ForegroundColor Green
Set-Location $projectRoot
pip install customtkinter pillow

# Create config
Write-Host ""
Write-Host "Creating configuration..." -ForegroundColor Green
$envFile = "$projectRoot\backend\.env"
if (!(Test-Path $envFile)) {
    @"
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
"@ | Out-File -FilePath $envFile -Encoding UTF8
    Write-Host "✓ Configuration file created" -ForegroundColor Green
}

# Cleanup
Remove-Item $downloadDir -Recurse -Force -ErrorAction SilentlyContinue

# Complete
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Get Gemini API key: https://makersuite.google.com/app/apikey" -ForegroundColor White
Write-Host "2. Edit backend\.env and set GEMINI_API_KEY" -ForegroundColor White
Write-Host "3. Restart PowerShell to refresh PATH" -ForegroundColor White
Write-Host "4. Run: python 启动_Pervis_PRO.py" -ForegroundColor White
Write-Host ""

Set-Location $projectRoot

if (-not $Force) {
    Write-Host "Press any key to exit..." -ForegroundColor Cyan
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}