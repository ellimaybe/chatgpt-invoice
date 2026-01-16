# run.ps1
# Runs the invoice download

$ErrorActionPreference = "Stop"

$scriptDir = $PSScriptRoot

Write-Host "Running invoice download..." -ForegroundColor Cyan
powershell.exe -ExecutionPolicy Bypass -File (Join-Path $scriptDir "src\\download-chatgpt-invoice.ps1")
