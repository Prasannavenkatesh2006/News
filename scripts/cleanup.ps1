# ============================================================
# ANIP Weekly Docker Cleanup Script
# Run this every Sunday to keep disk space under control.
# Usage: powershell -ExecutionPolicy Bypass -File K:\ANIP\anip\scripts\cleanup.ps1
# ============================================================

$ProjectDir = "K:\ANIP\anip"
$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "   ANIP Docker Cleanup — $(Get-Date -Format 'yyyy-MM-dd HH:mm')" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Show current disk usage ──────────────────────────
Write-Host "[1/5] Current Docker disk usage:" -ForegroundColor Yellow
docker system df
Write-Host ""

# ── Step 2: Backup the database ──────────────────────────────
Write-Host "[2/5] Backing up PostgreSQL database..." -ForegroundColor Yellow
$BackupFile = "K:\ANIP\backup_$(Get-Date -Format 'yyyyMMdd_HHmm').sql"

$pgRunning = docker ps --filter "name=anip-postgres" --format "{{.Names}}" 2>$null
if ($pgRunning -eq "anip-postgres") {
    docker exec anip-postgres pg_dump -U anip anip | Out-File -FilePath $BackupFile -Encoding utf8
    Write-Host "   ✅ Database backed up to: $BackupFile" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  PostgreSQL container not running — skipping backup." -ForegroundColor DarkYellow
}
Write-Host ""

# ── Step 3: Stop all containers ──────────────────────────────
Write-Host "[3/5] Stopping all ANIP containers..." -ForegroundColor Yellow
Set-Location $ProjectDir
docker compose stop
Write-Host "   ✅ All containers stopped." -ForegroundColor Green
Write-Host ""

# ── Step 4: Prune unused Docker resources ────────────────────
Write-Host "[4/5] Cleaning up unused images, containers, and build cache..." -ForegroundColor Yellow
Write-Host "   (Named volumes like 'postgres data' are KEPT safe)" -ForegroundColor DarkGray
docker system prune -f
Write-Host "   ✅ Cleanup complete." -ForegroundColor Green
Write-Host ""

# ── Step 5: Show new disk usage ──────────────────────────────
Write-Host "[5/5] Docker disk usage AFTER cleanup:" -ForegroundColor Yellow
docker system df
Write-Host ""

# ── Done ─────────────────────────────────────────────────────
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "   Cleanup finished! Your containers are stopped." -ForegroundColor Cyan
Write-Host "   To restart ANIP, run:  docker compose up -d" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

# Ask if user wants to restart now
$Restart = Read-Host "Do you want to start ANIP now? (y/n)"
if ($Restart -eq "y" -or $Restart -eq "Y") {
    Write-Host "Starting ANIP..." -ForegroundColor Green
    docker compose up -d
    Write-Host ""
    Write-Host "✅ ANIP is running! Open: http://localhost:3000" -ForegroundColor Green
}
