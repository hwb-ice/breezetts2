$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$serverExe = Join-Path $PSScriptRoot 'runtime-stream\audiocpp_server.exe'
$existing = Get-CimInstance Win32_Process -Filter "Name='audiocpp_server.exe'" | Where-Object { $_.ExecutablePath -eq $serverExe }
if (-not $existing) {
    $process = Start-Process -FilePath $serverExe -ArgumentList '--config', 'server.json', '--ui' -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput 'logs\server.out.log' -RedirectStandardError 'logs\server.err.log' -PassThru
    $process.Id | Set-Content 'logs\server.pid'
    $pythonExe = (Get-Command python.exe).Source
    Start-Process -FilePath $pythonExe -ArgumentList ('"' + (Join-Path $PSScriptRoot 'warmup.py') + '"') -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput 'logs\warmup.out.log' -RedirectStandardError 'logs\warmup.err.log' | Out-Null
}
$webScript = Join-Path $PSScriptRoot 'web_server.py'
$web = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*web_server.py*' -and ($_.CommandLine -like "*$PSScriptRoot*" -or $_.ProcessId -eq (Get-Content "$PSScriptRoot\logs\web.pid" -ErrorAction SilentlyContinue)) }
if (-not $web) {
    $pythonExe = (Get-Command python.exe).Source
    $webProcess = Start-Process -FilePath $pythonExe -ArgumentList ('"' + $webScript + '"') -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput 'logs\web.out.log' -RedirectStandardError 'logs\web.err.log' -PassThru
    $webProcess.Id | Set-Content 'logs\web.pid'
}
Write-Host 'Realtime playback: http://127.0.0.1:7861'
Write-Host 'Full UI / API: http://127.0.0.1:7860'
Write-Host 'First startup loads model weights. Logs: logs\server.err.log'
