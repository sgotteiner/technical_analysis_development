# Kill existing TradingView instances
Stop-Process -Name "TradingView" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Search for TradingView.exe inside LocalAppData
$exe = (Get-ChildItem -Path $env:LOCALAPPDATA -Filter "TradingView.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1).FullName

if (-not $exe) {
    $exe = (Get-ChildItem -Path $env:ProgramFiles -Filter "TradingView.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1).FullName
}

Write-Output "TradingView Executable Path: $exe"

if ($exe -and (Test-Path $exe)) {
    Write-Output "Starting TradingView Desktop with --remote-debugging-port=9222..."
    [System.Diagnostics.Process]::Start($exe, "--remote-debugging-port=9222")
    Start-Sleep -Seconds 5
    Write-Output "SUCCESS: TradingView launched with CDP port 9222!"
} else {
    Write-Error "Could not locate TradingView.exe on system."
}
