$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$ps = (Get-Process -Id $PID).Path
Start-Process -FilePath $ps -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $PSScriptRoot 'start_backend.ps1')) -WorkingDirectory $root -WindowStyle Minimized | Out-Null
Start-Sleep -Seconds 2
Start-Process -FilePath $ps -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $PSScriptRoot 'start_frontend.ps1')) -WorkingDirectory $root -WindowStyle Minimized | Out-Null
Write-Host 'Startup scripts launched. Check .run\*.log and the health URLs if either service does not respond.'
