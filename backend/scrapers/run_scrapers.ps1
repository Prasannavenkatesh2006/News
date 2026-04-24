# ============================================================
# ANIP — Scraper Launcher  (ALL scrapers, FREE + existing)
# Simply run:  .\run_scrapers.ps1
# ============================================================

Set-Location "$PSScriptRoot"

# ---- Load Environment from .env ----
$envFile = "..\..\.env"
if (Test-Path $envFile) {
    Write-Host "Loading credentials from .env..." -ForegroundColor Cyan
    Get-Content $envFile | Where-Object { $_ -match '^\w+=' } | ForEach-Object {
        $name, $value = $_ -split '=', 2
        Set-Item -Path "Env:$($name.Trim())" -Value $value.Trim()
    }
}

# Override specific defaults for local test if needed
$env:API_URL = "http://localhost:8000"
$env:PYTHONPATH = "$PSScriptRoot\..\..\src"
$env:KAFKA_BOOTSTRAP_SERVERS = "localhost:19092"

# Activate Venv
$venvPath = "$PSScriptRoot\..\..\.venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) { . $venvPath }

# Free-scraper tuning (optional — change as needed)
$env:RSS_ITEMS_PER_SOURCE = "5"
$env:RSS_INTERVAL_MINUTES = "10"
$env:YOUTUBE_MAX_AGE_HOURS = "24"
$env:YOUTUBE_INTERVAL_MINUTES = "15"
$env:TRENDS_INTERVAL_MINUTES = "20"
$env:PH_INTERVAL_MINUTES = "30"

Set-Location "$PSScriptRoot"

Write-Host ""
Write-Host '======================================' -ForegroundColor Cyan
Write-Host '  ANIP Scraper Suite - Starting Up   ' -ForegroundColor Cyan
Write-Host '======================================' -ForegroundColor Cyan
Write-Host ''

# ---- Helper to launch a scraper ----
function Start-Scraper {
    param([string]$Script, [string]$Label)
    if (Test-Path $Script) {
        Start-Process python -ArgumentList $Script -NoNewWindow
        Write-Host "  [OK] $Label" -ForegroundColor Green
    }
    else {
        Write-Host "  [!!] $Label - file not found: $Script" -ForegroundColor Yellow
    }
}

# ================================================================
# EXISTING SCRAPERS  (kept as-is, some use API keys as primary
#                     with free fallbacks built-in)
# ================================================================
Write-Host '-- Existing Scrapers --' -ForegroundColor Yellow
Start-Scraper 'hackernews_scraper.py'   'HackerNews'
Start-Scraper 'wikipedia_scraper.py'    'Wikipedia'
Start-Scraper 'reddit_scraper.py'       'Reddit'
Start-Scraper 'github_scraper.py'       'GitHub'
Start-Scraper 'google_trends.py'        'Google Trends'
Start-Scraper 'indian_news_scraper.py'  'Indian News RSS'
Start-Scraper 'tamil_news_scraper.py'   'Tamil Nadu News RSS'
Start-Scraper 'newsapi_aggregator.py'   'NewsAPI GDELT Aggregator'
Start-Scraper 'x_scraper.py'           'X Twitter'
Start-Scraper 'youtube_scraper.py'      'YouTube'

# ================================================================
# NEW FREE SCRAPERS  (zero API keys required)
# ================================================================
Write-Host ''
Write-Host '-- New FREE Scrapers (No API Key) --' -ForegroundColor Green
Start-Scraper 'rss_news_scraper.py'         'RSS News - 50 sources'
Start-Scraper 'x_free_scraper.py'           'X Free - Nitter RSS'
Start-Scraper 'youtube_free_scraper.py'     'YouTube Free - RSS'
Start-Scraper 'google_trends_free.py'       'Google Trends Free'
Start-Scraper 'producthunt_free_scraper.py' 'Product Hunt Free - RSS'

Write-Host ''
Write-Host '======================================' -ForegroundColor Cyan
Write-Host '  All scrapers launched!' -ForegroundColor Cyan
Write-Host '  API:  http://localhost:8001' -ForegroundColor Cyan
Write-Host '  Feed: http://localhost:3000' -ForegroundColor Cyan
Write-Host '======================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Press Ctrl+C to stop monitoring.' -ForegroundColor Gray
