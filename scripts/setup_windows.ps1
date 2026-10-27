$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root '.venv'
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { throw 'Python was not found. Install Python 3.12 and retry.' }
if (-not (Test-Path (Join-Path $root 'frontend\package.json'))) { throw 'Frontend package.json is missing.' }
if (-not (Test-Path $venv)) {
  if ($python.Name -eq 'py.exe') { & $python.Source -3.12 -m venv $venv } else { & $python.Source -m venv $venv }
}
$venvPython = Join-Path $venv 'Scripts\python.exe'
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $root 'backend\requirements.txt')
& $venvPython -m pip install -r (Join-Path $root 'backend\model\v2_requirements.txt')
if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) { throw 'pnpm was not found. Install pnpm 12+ and retry.' }
pnpm install --dir (Join-Path $root 'frontend') --frozen-lockfile
$envTarget = Join-Path $root 'frontend\.env.local'
if (-not (Test-Path $envTarget)) { Copy-Item (Join-Path $root '.env.example') $envTarget }
Write-Host 'Setup completed. Run scripts\start_all.ps1 or the two start scripts.'
