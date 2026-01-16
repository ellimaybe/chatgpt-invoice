# setup.ps1
# One-time setup for ChatGPT invoice downloader on Windows

$ErrorActionPreference = "Stop"

$scriptDir = $PSScriptRoot
$venvDir = Join-Path $scriptDir ".venv"
$pythonExe = Join-Path $venvDir "Scripts\python.exe"

Write-Host "=== Setup: ChatGPT Invoice Downloader ===" -ForegroundColor Cyan

function Ensure-Winget {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Host "winget is not available. Please install App Installer from the Microsoft Store." -ForegroundColor Yellow
        return $false
    }
    return $true
}

function Ensure-Python {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return $true
    }

    if (-not (Ensure-Winget)) {
        return $false
    }

    Write-Host "Installing Python 3.12 via winget..." -ForegroundColor Yellow
    winget install --id Python.Python.3.12 -e --source winget
    return (Get-Command python -ErrorAction SilentlyContinue)
}

if (-not (Ensure-Python)) {
    Write-Host "Python install failed or not found. Please install Python 3.12 manually and re-run setup.ps1." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $venvDir)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $venvDir
}

Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install -r (Join-Path $scriptDir "requirements.txt")

Write-Host "Installing Playwright browsers..." -ForegroundColor Yellow
& $pythonExe -m playwright install chromium

Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Next: run .\run.ps1" -ForegroundColor Gray
