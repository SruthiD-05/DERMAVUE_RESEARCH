$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $venvPython)) { throw 'Python environment is missing. Run scripts\setup_windows.ps1 first.' }
$run = Join-Path $root '.run'; New-Item -ItemType Directory -Force -Path $run | Out-Null
if (Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue) { throw 'Port 8000 is already in use.' }
$env:DERMAVUE_RESEARCH_INFERENCE_ENABLED = 'true'
$p = Start-Process -FilePath $venvPython -ArgumentList @('-m','backend.app.server') -WorkingDirectory $root -RedirectStandardOutput (Join-Path $run 'backend.out.log') -RedirectStandardError (Join-Path $run 'backend.err.log') -PassThru
Set-Content -LiteralPath (Join-Path $run 'backend.pid') -Value $p.Id
Write-Host "Backend started with PID $($p.Id); research inference is loopback-only and production serving remains disabled."
