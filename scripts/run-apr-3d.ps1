param(
  [int]$Port = 8080,
  [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

Write-Host ""
Write-Host "APR 3D CONTROL PLANE" -ForegroundColor Cyan
Write-Host "CLAIM != PROOF" -ForegroundColor DarkCyan
Write-Host ""

if (-not $SkipInstall) {
  Write-Host "[1/4] Installing APR editable package..." -ForegroundColor DarkGray
  python -m pip install -e .

  Write-Host "[2/4] Installing frontend dependencies..." -ForegroundColor DarkGray
  Push-Location frontend
  try {
    npm ci
  } finally {
    Pop-Location
  }
}

Write-Host "[3/4] Building 3D frontend..." -ForegroundColor DarkGray
Push-Location frontend
try {
  npm run build
} finally {
  Pop-Location
}

$apr = Get-Command apr -ErrorAction SilentlyContinue
if (-not $apr) {
  throw "Command 'apr' was not found after installation. Ensure the Python Scripts directory is on PATH."
}

$url = "http://127.0.0.1:$Port/control-plane"
$health = "http://127.0.0.1:$Port/health"

Write-Host "[4/4] Starting real APR backend on port $Port..." -ForegroundColor DarkGray
$server = Start-Process -FilePath $apr.Source -ArgumentList @(
  "mission-control",
  "--missions-dir", "missions",
  "--runs-dir", ".runs",
  "--host", "127.0.0.1",
  "--port", "$Port"
) -PassThru -NoNewWindow

try {
  $ready = $false
  for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Milliseconds 250
    try {
      $response = Invoke-WebRequest -UseBasicParsing -Uri $health -TimeoutSec 1
      if ($response.StatusCode -eq 200) {
        $ready = $true
        break
      }
    } catch {
      if ($server.HasExited) {
        throw "APR Mission Control exited before becoming healthy."
      }
    }
  }

  if (-not $ready) {
    throw "APR Mission Control did not become healthy at $health"
  }

  Write-Host ""
  Write-Host "READY" -ForegroundColor Green
  Write-Host "Control Plane: $url" -ForegroundColor Cyan
  Write-Host "Health:        $health" -ForegroundColor DarkGray
  Write-Host ""
  Write-Host "The browser will open now. Close this window or press Ctrl+C to stop the local runtime." -ForegroundColor Gray

  Start-Process $url
  Wait-Process -Id $server.Id
}
finally {
  if ($server -and -not $server.HasExited) {
    Stop-Process -Id $server.Id -Force
  }
}
