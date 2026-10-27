$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$run = Join-Path $root '.run'
foreach ($name in @('backend','frontend')) {
  $pidFile = Join-Path $run "$name.pid"
  if (-not (Test-Path $pidFile)) { continue }
  $id = [int](Get-Content $pidFile -Raw).Trim()
  $proc = Get-Process -Id $id -ErrorAction SilentlyContinue
  if ($proc) {
    $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId=$id").CommandLine
    if ($cmd -and $cmd.Contains($root)) { Stop-Process -Id $id -Force; Write-Host "Stopped $name PID $id" }
    else { Write-Warning "PID $id no longer matches this package; left it running." }
  }
  Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
}
