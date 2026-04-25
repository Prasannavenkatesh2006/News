# ============================================================
#  ANIP Platform - LOCAL V2 (Port 3002)
#  Run: powershell -ExecutionPolicy Bypass -File .\start_local_v2.ps1
# ============================================================

$Root = Get-Location
Set-Location "$Root"

# ── Step 0: Kill any stale processes on ports 8000 & 3002 ───
Write-Host '[0/5] Clearing ports 8000 and 3002...' -ForegroundColor Yellow
$ports = @('8000', '3002')
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
    Write-Host '  Failed to start Docker services. Please ensure Docker Desktop is running.' -ForegroundColor Red
    # We continue anyway as the user might have them running differently, but warn.
} else {
    Write-Host '  Docker dependencies started.' -ForegroundColor Green
}

# ── Step 2: Start API Backend locally ───────────────────────
Write-Host ''
Write-Host '[2/5] Starting API server on http://127.0.0.1:8000 ...' -ForegroundColor Yellow

# Load Environment from .env
$envFile = "$Root\.env"
if (Test-Path $envFile) {
    Write-Host "  Loading credentials from .env..." -ForegroundColor Gray
    Get-Content $envFile | Where-Object { $_ -match '^\w+=' } | ForEach-Object {
        $name, $value = $_ -split '=', 2
        Set-Item -Path "Env:$($name.Trim())" -Value $value.Trim()
    }
}

$env:POSTGRES_HOST = "127.0.0.1"
$env:PYTHONPATH = "$Root\src;$Root\services\api"

$apiProc = Start-Process powershell -ArgumentList @(
    '-ExecutionPolicy', 'Bypass',
    '-Command', "
        Set-Location '$Root';
        if (Test-Path '.venv\Scripts\Activate.ps1') { . .venv\Scripts\Activate.ps1 }
        Set-Location 'services\api';
        uvicorn app.main:app --host 127.0.0.1 --port 8000
    "
) -PassThru -NoNewWindow
Write-Host "  API started (PID $($apiProc.Id))" -ForegroundColor Green

# ── Step 3: Start All Scrapers for Real-Time Data ──────────
Write-Host ''
Write-Host '[3/5] Starting scraper swarm...' -ForegroundColor Yellow
$scraperPath = "$Root\backend\scrapers"
if (Test-Path $scraperPath) {
    Start-Process powershell -ArgumentList @(
        '-ExecutionPolicy', 'Bypass',
        '-Command', "
            Set-Location '$scraperPath';
            .\run_scrapers.ps1
        "
    ) -NoNewWindow
    Write-Host '  Scrapers launched in background.' -ForegroundColor Green
}

# ── Step 4: Start Frontend locally on Port 3002 ────────────
Write-Host ''
Write-Host '[4/5] Starting Frontend on http://localhost:3002 ...' -ForegroundColor Yellow
$frontendProc = Start-Process powershell -ArgumentList @(
    '-ExecutionPolicy', 'Bypass',
    '-Command', "
        Set-Location '$Root\frontend';
        npm run dev:3002
    "
) -PassThru -NoNewWindow
Write-Host "  Frontend started (PID $($frontendProc.Id))" -ForegroundColor Green

# ── Done ─────────────────────────────────────────────────────
Write-Host ''
Write-Host '================================================' -ForegroundColor Cyan
Write-Host "   ANIP PLATFORM IS RUNNING!" -ForegroundColor Green
Write-Host '   - Frontend:  http://localhost:3002' -ForegroundColor White
Write-Host '   - API:       http://localhost:8000' -ForegroundColor White
Write-Host '   - Docs:      http://localhost:8000/docs' -ForegroundColor White
Write-Host '================================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Opening app in 3 seconds...' -ForegroundColor Gray
Start-Sleep -Seconds 3
Start-Process 'http://localhost:3002/login'
