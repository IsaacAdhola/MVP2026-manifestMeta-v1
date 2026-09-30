# Keep Manifest AI Slack Socket Mode running. Restart on crash.
# From this folder: .\keep_slack_online.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
$env:PYTHONPATH = "c:\Users\New\Downloads\MVP2026-manifestMeta-master;$root"
$py = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    $py = "py"
}

Write-Host "Starting Manifest AI Slack desk. Ctrl+C stops the watchdog."
while ($true) {
    & $py -u slack_app.py
    $code = $LASTEXITCODE
    Write-Host "slack_app.py exited with $code. Restarting in 5 seconds..."
    Start-Sleep -Seconds 5
}
