# download-chatgpt-invoice.ps1
# Orchestrates Claude Code (Chrome) and Python script to download ChatGPT invoices

$downloadPath = "$env:USERPROFILE\Downloads"
$scriptDir = $PSScriptRoot

# Step 1: Use Claude to extract invoice link
$prompt = @"
This is an automated task. Proceed without asking for confirmation.

Task: Extract the latest ChatGPT invoice link from Stripe billing portal.

Steps:
1. Go to https://chatgpt.com/#settings/Account
2. In the Payment area, click "Manage" to open pay.openai.com
3. Scroll to "INVOICE HISTORY" section
4. Find the latest invoice row. IMPORTANT: Do NOT click anything. Right-click the invoice link and select "Copy link address" to get the URL.
5. Output the date and URL in the format below

Output format - respond with ONLY these two lines:
DATE: YYYYMMDD
URL: <the full invoice URL>

6. FINALLY: Press Ctrl+W to close the current tab. This step is REQUIRED.

Execute all steps including closing tabs. Do not skip any steps.
"@

Write-Host "=== ChatGPT Invoice Downloader ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Step 1: Extracting invoice link with Claude..." -ForegroundColor Yellow
$claudeOutput = claude -p $prompt --chrome --dangerously-skip-permissions 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Claude failed to extract invoice link" -ForegroundColor Red
    Write-Host $claudeOutput -ForegroundColor Red
    exit 1
}

# Parse the output to extract date and URL
$dateMatch = [regex]::Match($claudeOutput, 'DATE:\s*(\d{8})')
$urlMatch = [regex]::Match($claudeOutput, 'URL:\s*(https://[^\s]+)')

# Fallback: try to find any Stripe invoice URL in output
if (-not $urlMatch.Success) {
    $urlMatch = [regex]::Match($claudeOutput, '(https://invoice\.stripe\.com/[^\s\)]+)')
}

if (-not $urlMatch.Success) {
    Write-Host "Error: Could not find invoice URL in Claude's output" -ForegroundColor Red
    Write-Host "Output was:" -ForegroundColor Gray
    Write-Host $claudeOutput -ForegroundColor Gray
    exit 1
}

$invoiceUrl = $urlMatch.Groups[1].Value
$invoiceDate = if ($dateMatch.Success) { $dateMatch.Groups[1].Value } else { (Get-Date).ToString("yyyyMMdd") }

# Save to file (without BOM to avoid URL parsing issues)
$linkFile = Join-Path $downloadPath "$invoiceDate-stripe-link.txt"
[System.IO.File]::WriteAllText($linkFile, $invoiceUrl)
Write-Host "Saved invoice link to: $linkFile" -ForegroundColor Green

Write-Host ""
Write-Host "Step 2: Downloading invoice PDF..." -ForegroundColor Yellow
python "$scriptDir\download-stripe-from-url.py" --latest

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to download invoice PDF" -ForegroundColor Red
    exit 1
}

# Step 3: Clean up - delete the link file
Write-Host ""
Write-Host "Step 3: Cleaning up temporary files..." -ForegroundColor Yellow
$linkFiles = Get-ChildItem -Path $downloadPath -Filter "*-stripe-link.txt" | Sort-Object LastWriteTime -Descending
if ($linkFiles) {
    $latestLinkFile = $linkFiles[0].FullName
    Remove-Item $latestLinkFile -Force
    Write-Host "Deleted: $latestLinkFile" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Done! Invoice downloaded successfully." -ForegroundColor Green
