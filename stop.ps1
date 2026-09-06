$serverExecutables = @((Join-Path $PSScriptRoot 'runtime\audiocpp_server.exe'), (Join-Path $PSScriptRoot 'runtime-stream\audiocpp_server.exe'))
Get-CimInstance Win32_Process -Filter "Name='audiocpp_server.exe'" | Where-Object { $_.ExecutablePath -in $serverExecutables } | ForEach-Object { Stop-Process -Id $_.ProcessId }
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like "*$PSScriptRoot*web_server.py*" } | ForEach-Object { Stop-Process -Id $_.ProcessId }
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like "*$PSScriptRoot*warmup.py*" } | ForEach-Object { Stop-Process -Id $_.ProcessId }
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like "*$PSScriptRoot*gpu_keepalive.py*" } | ForEach-Object { Stop-Process -Id $_.ProcessId }
