# Pervis PRO Auto Install Script
# Automatically installs all required dependencies

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Pervis PRO Auto Installation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$projectRoot = $PSScriptRoot
$tempDir = "$env:TEMP\PervisPRO_Install"

# Create temp directory
if (!(Test-Path $tempDir)) {
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
}

# Download function
function Download-File {
    param($url, $output)
    try {
        Write-Host "Downloading: $(Split-Path $output -Leaf)..." -ForegroundColor Yellow
        Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing
        return $true
    } catch {
        Write-Host "Download failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Install function
function Install-Silently {
    param($installer, $args)
    try {
        Write-Host "Installing..." -ForegroundColor Yellow
        $process = Start-Process -FilePath $installer -ArgumentList $args -Wait -PassThru -WindowStyle Hidden
        return $process.ExitCode -eq 0
    } catch {
        Write-Host "Installation failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Check and install Python
Write-Host ""
Write-Host "[1/4] Checking Python..." -ForegroundColor Green
try {
    $pythonCheck = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Python already installed: $pythonCheck" -ForegroundColor Green
    } else {
        throw "Python not found"
    }
} catch {
    Write-Host "Installing Python 3.11..." -ForegroundColor Yellow
    $pythonUrl = "https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe"
    $pythonInstaller = "$tempDir\python-installer.exe"
    
    if (Download-File $pythonUrl $pythonInstaller) {
        $pythonArgs = @("/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_test=0")
        if (Install-Silently $pythonInstaller $pythonArgs) {
            Write-Host "Python installed successfully" -ForegroundColor Green
            # Refresh PATH
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        }
    }
}

# Check and install Node.js
Write-Host ""
Write-Host "[2/4] Checking Node.js..." -ForegroundColor Green
try {
    $nodeCheck = node --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Node.js already installed: $nodeCheck" -ForegroundColor Green
    } else {
        throw "Node.js not found"
    }
} catch {
    Write-Host "Installing Node.js..." -ForegroundColor Yellow
    $nodeUrl = "https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi"
    $nodeInstaller = "$tempDir\node-installer.msi"
    
    if (Download-File $nodeUrl $nodeInstaller) {
        $nodeArgs = @("/i", $nodeInstaller, "/quiet", "/norestart")
        if (Install-Silently "msiexec.exe" $nodeArgs) {
            Write-Host "Node.js installed successfully" -ForegroundColor Green
            # Refresh PATH
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        }
    }
}

# Check and install Git
Write-Host ""
Write-Host "[3/4] Checking Git..." -ForegroundColor Green
try {
    $gitCheck = git --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Git already installed: $gitCheck" -ForegroundColor Green
    } else {
        throw "Git not found"
    }
} catch {
    Write-Host "Installing Git..." -ForegroundColor Yellow
    $gitUrl = "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe"
    $gitInstaller = "$tempDir\git-installer.exe"
    
    if (Download-File $gitUrl $gitInstaller) {
        $gitArgs = @("/VERYSILENT", "/NORESTART", "/NOCANCEL", "/SP-")
        if (Install-Silently $gitInstaller $gitArgs) {
            Write-Host "Git installed successfully" -ForegroundColor Green
            # Refresh PATH
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        }
    }
}

# Install FFmpeg
Write-Host ""
Write-Host "[4/4] Installing FFmpeg..." -ForegroundColor Green
try {
    $ffmpegCheck = ffmpeg -version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "FFmpeg already installed" -ForegroundColor Green
    } else {
        throw "FFmpeg not found"
    }
} catch {
    Write-Host "Downloading FFmpeg..." -ForegroundColor Yellow
    $ffmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    $ffmpegZip = "$tempDir\ffmpeg.zip"
    
    if (Download-File $ffmpegUrl $ffmpegZip) {
        Write-Host "Extracting FFmpeg..." -ForegroundColor Yellow
        $ffmpegDir = "C:\ffmpeg"
        
        # Extract
        Expand-Archive -Path $ffmpegZip -DestinationPath $tempDir -Force
        $extractedDir = Get-ChildItem -Path $tempDir -Directory | Where-Object { $_.Name -like "ffmpeg-*" } | Select-Object -First 1
        
        if ($extractedDir) {
            # Move to target directory
            if (Test-Path $ffmpegDir) {
                Remove-Item $ffmpegDir -Recurse -Force
            }
            Move-Item $extractedDir.FullName $ffmpegDir
            
            # Add to PATH
            $currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
            $ffmpegBinPath = "$ffmpegDir\bin"
            
            if ($currentPath -notlike "*$ffmpegBinPath*") {
                $newPath = "$currentPath;$ffmpegBinPath"
                [Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")
                $env:Path = "$env:Path;$ffmpegBinPath"
            }
            
            Write-Host "FFmpeg installed successfully" -ForegroundColor Green
        }
    }
}

# Wait for environment variables to take effect
Write-Host ""
Write-Host "Waiting for environment variables..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

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
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host "Backend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "Backend installation failed" -ForegroundColor Red
}

# Frontend dependencies
Write-Host ""
Write-Host "Installing frontend dependencies..." -ForegroundColor Green
Set-Location "$projectRoot\frontend"

npm install --silent

if ($LASTEXITCODE -eq 0) {
    Write-Host "Frontend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "Frontend installation failed" -ForegroundColor Red
}

# Launcher dependencies
Write-Host ""
Write-Host "Installing launcher dependencies..." -ForegroundColor Green
Set-Location $projectRoot
pip install customtkinter pillow --quiet

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
    Write-Host "Please edit this file to set GEMINI_API_KEY" -ForegroundColor Yellow
} else {
    Write-Host "Configuration file already exists" -ForegroundColor Green
}

# Cleanup
Write-Host ""
Write-Host "Cleaning up temporary files..." -ForegroundColor Yellow
Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue

# Complete
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Get Gemini API key: https://makersuite.google.com/app/apikey" -ForegroundColor White
Write-Host "2. Edit backend\.env file and set GEMINI_API_KEY" -ForegroundColor White
Write-Host "3. Run project: python 启动_Pervis_PRO.py" -ForegroundColor White
Write-Host ""

Set-Location $projectRoot