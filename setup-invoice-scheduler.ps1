# setup-invoice-scheduler.ps1
# Creates a Windows scheduled task to download ChatGPT invoices monthly

$taskName = "ChatGPT Invoice Downloader"
$scriptPath = "$PSScriptRoot\src\download-chatgpt-invoice.ps1"

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Task '$taskName' already exists." -ForegroundColor Yellow
    $response = Read-Host "Do you want to replace it? (y/n)"
    if ($response -ne 'y') {
        Write-Host "Cancelled." -ForegroundColor Gray
        exit 0
    }
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "Removed existing task." -ForegroundColor Gray
}

# Create task via XML to avoid quoting issues with paths containing spaces
$startDate = (Get-Date -Day 26 -Hour 14 -Minute 0 -Second 0)
if ($startDate -lt (Get-Date)) { $startDate = $startDate.AddMonths(1) }
$startBoundary = $startDate.ToString("yyyy-MM-ddTHH:mm:ss")

$taskXml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>$startBoundary</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByMonth>
        <DaysOfMonth><Day>26</Day></DaysOfMonth>
        <Months><January/><February/><March/><April/><May/><June/><July/><August/><September/><October/><November/><December/></Months>
      </ScheduleByMonth>
    </CalendarTrigger>
  </Triggers>
  <Settings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
  </Settings>
  <Actions>
    <Exec>
      <Command>powershell.exe</Command>
      <Arguments>-ExecutionPolicy Bypass -File "$scriptPath"</Arguments>
    </Exec>
  </Actions>
</Task>
"@

try {
    Register-ScheduledTask -TaskName $taskName -Xml $taskXml -Force -ErrorAction Stop | Out-Null
} catch {
    Write-Host ""
    Write-Host "Failed to create scheduled task!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Scheduled task created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Task details:" -ForegroundColor Cyan
Write-Host "  Name:      $taskName"
Write-Host "  Schedule:  26th of every month at 2:00 PM"
Write-Host "  Script:    $scriptPath"
Write-Host ""
Write-Host "To manage this task:" -ForegroundColor Gray
Write-Host "  View:      Get-ScheduledTask -TaskName '$taskName'"
Write-Host "  Run now:   Start-ScheduledTask -TaskName '$taskName'"
Write-Host "  Disable:   Disable-ScheduledTask -TaskName '$taskName'"
Write-Host "  Remove:    Unregister-ScheduledTask -TaskName '$taskName'"
