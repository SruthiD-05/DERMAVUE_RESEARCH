$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) { throw 'pnpm was not found. Run setup_windows.ps1 first.' }
$run = Join-Path $root '.run'; New-Item -ItemType Directory -Force -Path $run | Out-Null
if (Get-NetTCPConnection -State Listen -LocalPort 3000 -ErrorAction SilentlyContinue) { throw 'Port 3000 is already in use.' }
$env:NEXT_PUBLIC_DERMAVUE_API_URL = 'http://127.0.0.1:8000'
$env:NEXT_PUBLIC_DERMAVUE_DATA_MODE = 'local'
$p = Start-Process -FilePath 'pnpm.cmd' -ArgumentList @('dev','--hostname','127.0.0.1') -WorkingDirectory (Join-Path $root 'frontend') -RedirectStandardOutput (Join-Path $run 'frontend.out.log') -RedirectStandardError (Join-Path $run 'frontend.err.log') -PassThru
Set-Content -LiteralPath (Join-Path $run 'frontend.pid') -Value $p.Id
Write-Host "Frontend started with PID $($p.Id): http://127.0.0.1:3000"
