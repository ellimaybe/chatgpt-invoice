# download-chatgpt-invoice.ps1
# Orchestrates Claude Code (Chrome) and Python script to download ChatGPT invoices

$downloadPath = "$env:USERPROFILE\Downloads"
$scriptDir = $PSScriptRoot

# Step 1: Use Claude to extract invoice link
$prompt = @"
This is an automated task. Proceed without asking for confirmation.

Goal: Capture the current Stripe billing portal URL for the latest ChatGPT invoice.

Steps:
1. Open https://chatgpt.com/#settings/Account
2. In the Payment area, click "Manage" to open pay.openai.com
3. Copy the current pay.openai.com URL (the invoice page you are on)
4. Save it to a text file named YYYYMMDD-pay-link.txt where YYYYMMDD is today's date
5. Respond with the format below

Output format - respond with ONLY these two lines:
DATE: YYYYMMDD
URL: <the full invoice URL>

6. Close the current tab with Ctrl+W. This step is REQUIRED.

Execute all steps. Do not skip any steps.
"@

Write-Host "=== ChatGPT Invoice Downloader ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Step 1: Extracting invoice link with Claude..." -ForegroundColor Yellow
$claudeOutput = claude -p $prompt --model sonnet --chrome --dangerously-skip-permissions 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Claude failed to extract invoice link" -ForegroundColor Red
    Write-Host $claudeOutput -ForegroundColor Red
    exit 1
}

# Parse the output to extract date and URL
$dateMatch = [regex]::Match($claudeOutput, 'DATE:\s*(\d{8})')
$urlMatch = [regex]::Match($claudeOutput, 'URL:\s*(https://pay\.openai\.com/[^\s]+)')

# Fallback: try to find any pay.openai.com URL in output
if (-not $urlMatch.Success) {
    $urlMatch = [regex]::Match($claudeOutput, '(https://pay\.openai\.com/[^\s\)]+)')
}

if (-not $urlMatch.Success) {
    Write-Host "Error: Could not find invoice URL in Claude's output" -ForegroundColor Red
    Write-Host "Output was:" -ForegroundColor Gray
    Write-Host $claudeOutput -ForegroundColor Gray
    exit 1
}

$invoiceUrl = $urlMatch.Groups[1].Value
$invoiceDate = if ($dateMatch.Success) { $dateMatch.Groups[1].Value } else { (Get-Date).ToString("yyyyMMdd") }

# Save to temp file (without BOM to avoid URL parsing issues)
$linkFile = Join-Path $downloadPath "$invoiceDate-pay-link.txt"
[System.IO.File]::WriteAllText($linkFile, $invoiceUrl)
Write-Host "Saved pay.openai.com link to: $linkFile" -ForegroundColor Green

Write-Host ""
Write-Host "Step 2: Extracting Stripe invoice link..." -ForegroundColor Yellow
$stripeUrl = python "$scriptDir\extract-stripe-link.py" --latest

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to extract Stripe invoice link" -ForegroundColor Red
    exit 1
}

Write-Host "Stripe URL: $stripeUrl" -ForegroundColor Gray

Write-Host ""
Write-Host "Step 3: Downloading invoice PDF..." -ForegroundColor Yellow
python "$scriptDir\download-stripe-from-url.py" $stripeUrl

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to download invoice PDF" -ForegroundColor Red
    exit 1
}

# Step 4: Clean up - delete the temp link file
Write-Host ""
Write-Host "Step 4: Cleaning up temporary files..." -ForegroundColor Yellow
$linkFiles = Get-ChildItem -Path $downloadPath -Filter "*-pay-link.txt" | Sort-Object LastWriteTime -Descending
if ($linkFiles) {
    $latestLinkFile = $linkFiles[0].FullName
    Remove-Item $latestLinkFile -Force
    Write-Host "Deleted: $latestLinkFile" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Done! Invoice downloaded successfully." -ForegroundColor Green
