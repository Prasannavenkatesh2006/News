# ============================================================
#  ANIP Platform - FULL Master Launcher
#  Orchestrates local Python processes with Docker services
#  Run: powershell -ExecutionPolicy Bypass -File .\start_project.ps1
# ============================================================

$Root = Get-Location
Set-Location "$Root"

# ── Step 0: Kill any stale processes on ports 8000 & 8001 ───
Write-Host '[0/5] Clearing ports 8000 and 8001...' -ForegroundColor Yellow
$ports = @('8000', '8001')
foreach ($p in $ports) {
    $lines = netstat -ano | Select-String ":$p.*LISTEN"
    foreach ($line in $lines) {
        $parts = ($line -replace '\s+', ' ').Trim() -split ' '
        $foundPid = $parts[-1]
        if ($foundPid -match '^\d+$' -and $foundPid -ne '0') {
            taskkill /F /PID $foundPid 2>$null | Out-Null
            Write-Host "  Freed port $p (PID $foundPid)" -ForegroundColor Gray
        }
    }
}
Start-Sleep -Seconds 1

# ── Step 1: Start Core Infrastructure in Docker ───────────
Write-Host ''
Write-Host '[1/5] Starting Docker dependencies (Postgres, Redis, Redpanda)...' -ForegroundColor Yellow
docker compose up -d postgres redis redpanda
if ($LASTEXITCODE -ne 0) {
    Write-Host '  Failed to start Docker services. Check if Docker Desktop is running.' -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host '  Docker dependencies started.' -ForegroundColor Green

# ── Step 2: Start API Backend locally ───────────────────────
Write-Host ''
Write-Host '[2/5] Starting API server on http://127.0.0.1:8000 ...' -ForegroundColor Yellow

# ---- Load Environment from .env ----
$envFile = "$Root\.env"
if (Test-Path $envFile) {
    Write-Host "  Loading database and API credentials from .env..." -ForegroundColor Gray
    Get-Content $envFile | Where-Object { $_ -match '^\w+=' } | ForEach-Object {
        $name, $value = $_ -split '=', 2
        Set-Item -Path "Env:$($name.Trim())" -Value $value.Trim()
    }
}

# Local networking overrides for processes outside of Docker
$env:POSTGRES_HOST = "127.0.0.1"
$env:PYTHONPATH = "$Root\src;$Root\services\api"
$env:REDIS_URL = 'redis://127.0.0.1:6379/0'
$env:KAFKA_BOOTSTRAP_SERVERS = '127.0.0.1:19092'

$apiProc = Start-Process powershell -ArgumentList @(
    '-ExecutionPolicy', 'Bypass',
    '-Command', "
        Set-Location '$Root';
        if (Test-Path '.venv\Scripts\Activate.ps1') { . .venv\Scripts\Activate.ps1 }
        Set-Location 'services\api';
        uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
    "
) -PassThru -NoNewWindow
Write-Host "  API started (PID $($apiProc.Id))" -ForegroundColor Green

# Wait for API readiness
Write-Host '  Verifying API status...' -ForegroundColor Gray
$apiReady = $false
for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Seconds 2
    try {
        $resp = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 2 -ErrorAction Stop
        if ($resp.StatusCode -eq 200) { $apiReady = $true; break }
    }
    catch { }
}
if (-not $apiReady) { Write-Host '  API start-up is slow, continuing...' -ForegroundColor Yellow }

# ── Step 3: Start All Scrapers ─────────────────────────────
Write-Host ''
Write-Host '[3/5] Starting scraper swarm...' -ForegroundColor Yellow
$env:API_URL = 'http://localhost:8000'
$env:KAFKA_BOOTSTRAP_SERVERS = 'localhost:19092'
$env:RSS_ITEMS_PER_SOURCE = '5'
$env:RSS_INTERVAL_MINUTES = '10'

# Update run_scrapers.ps1 to use port 8000 and local Kafka
$scraperPath = "$Root\backend\scrapers"
Set-Location "$scraperPath"
# Running the script we updated earlier
powershell -ExecutionPolicy Bypass -File .\run_scrapers.ps1

# ── Step 4: Start Frontend in Docker ───────────────────────
Write-Host ''
Write-Host '[4/5] Starting Frontend in Docker (port 3000)...' -ForegroundColor Yellow
docker compose up -d frontend
Write-Host '  Frontend started via Docker.' -ForegroundColor Green

# ── Done ─────────────────────────────────────────────────────
Write-Host ''
Write-Host '================================================' -ForegroundColor Cyan
Write-Host "   ANIP PLATFORM IS READY!" -ForegroundColor Green
Write-Host '   - Frontend:  http://localhost:3000' -ForegroundColor White
Write-Host '   - API:       http://localhost:8000' -ForegroundColor White
Write-Host '   - Docs:      http://localhost:8000/docs' -ForegroundColor White
Write-Host "   - API PID:   $($apiProc.Id)" -ForegroundColor White
Write-Host '================================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Opening app in 3 seconds...' -ForegroundColor Gray
Start-Sleep -Seconds 3
Start-Process 'http://localhost:3000'
