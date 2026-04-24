# ANIP Deployment Checklist

## Pre-Deployment (5-10 minutes)

### System Requirements
- [ ] Docker Desktop/Engine installed (v20.10+)
- [ ] Docker Compose installed (v2.0+)
- [ ] 8GB+ RAM available
- [ ] 20GB+ free disk space
- [ ] Stable internet connection (for API keys & image downloads)

### Repository Setup
- [ ] Project cloned: `git clone https://github.com/poov77/Pulse---ANIP.git`
- [ ] Navigate to project: `cd Pulse---ANIP`
- [ ] Create `.env`: `cp .env.example .env`
- [ ] API keys added to `.env`:
  - [ ] `POSTGRES_PASSWORD` (change from default)
  - [ ] `NEWSAPI_KEY`
  - [ ] `NEWSDATA_KEY`
  - [ ] `OPENAI_API_KEY` (for chat features)

### Volume Setup
```bash
# Create required volumes
mkdir -p volumes/postgres volumes/mlruns volumes/logs
chmod 755 volumes/*  # Only on Linux/macOS
```
- [ ] PostgreSQL volume: `volumes/postgres/`
- [ ] MLflow volume: `volumes/mlruns/`
- [ ] Logs volume: `volumes/logs/`

---

## Initial Deployment

### Start Services
```bash
# OPTION 1: Using Docker Compose (Recommended for all systems)
docker compose up -d

# OPTION 2: Windows PowerShell script
powershell -ExecutionPolicy Bypass -File .\start_project.ps1
```

### Verify Services (Wait 30-60 seconds)
```bash
# Check all containers running
docker compose ps

# Expected output (all with "Up" status):
✅ anip-postgres (healthy)
✅ anip-redis (running)
✅ anip-redpanda (healthy)
✅ anip-api (running)
✅ anip-frontend (running)
✅ anip-mlflow (running)
✅ anip-embedding-service (running)
✅ spark-master (running)
✅ spark-worker (running)
```

### Test Connectivity
```bash
# Test API health
curl http://localhost:8000/health

# Expected response:
{"status": "ok"}
```

### Access Services
- [ ] **Frontend UI**: http://localhost:3000
- [ ] **API**: http://localhost:8000
- [ ] **API Docs**: http://localhost:8000/docs
- [ ] **MLflow**: http://localhost:5000
- [ ] **Spark Master**: http://localhost:9090

---

## Post-Deployment (First Run)

### Database Initialization
- [ ] PostgreSQL container started
- [ ] Database migrations applied automatically
- [ ] Tables created (newsarticle, users, posts, etc.)

Verify with:
```bash
docker compose exec postgres psql -U anip -d anip -c "\dt"
```

### Scrapers (Optional - Already Running)
- [ ] Monitor scraper logs:
```bash
docker compose logs -f scraper-hackernews scraper-reddit
```

Expected: Articles being published to Kafka → Database

### Frontend Data Loading
- [ ] Visit http://localhost:3000/telangana
- [ ] Articles should appear in 30-60 seconds
- [ ] Try other regional pages

---

## Production Deployment

### Security Hardening
- [ ] Change all default passwords in `.env`
- [ ] Set `DEBUG=false` in services
- [ ] Configure CORS_ORIGINS (not `*`)
- [ ] Use strong API keys
- [ ] Enable HTTPS/SSL (if exposing to internet)

### Performance Tuning
```bash
# Allocate specific resources to Docker Compose
# Adjust in docker-compose.yml:
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

### Backup Strategy
```bash
# Backup PostgreSQL
docker compose exec postgres pg_dump -U anip anip > backup.sql

# Backup volumes
tar -czf backup-volumes.tar.gz volumes/

# Backup .env (securely!)
gpg --encrypt .env
```

### Monitoring & Logs
```bash
# View all logs
docker compose logs -f

# View specific service
docker compose logs -f api --tail=100

# Check container health
docker compose exec api curl http://localhost:8000/health
docker compose exec postgres pg_isready -U anip
```

---

## Troubleshooting

### Containers Won't Start

**Check Docker daemon**:
```bash
docker ps
```

If fails, restart Docker Desktop.

**Check logs**:
```bash
docker compose logs api
docker compose logs postgres
```

**Common issues**:
- Port already in use → Change in `.env`
- Insufficient memory → Allocate more RAM
- Stale volumes → `docker compose down -v && docker compose up -d`

### API Returning 500 Errors

**Check database connection**:
```bash
docker compose exec api curl -v http://postgres:5432
# Should timeout (not refused) if DB is up
```

**Restart API container**:
```bash
docker compose restart api
```

**Check API logs**:
```bash
docker compose logs api --tail=50
```

### Frontend Not Loading Articles

**Check if API is responding**:
```bash
curl http://localhost:8000/api/v1/social/feed?state=Telangana&limit=5
```

**Clear browser cache**:
- Ctrl+Shift+Delete (Windows/Linux)
- Cmd+Shift+Delete (macOS)

**Restart frontend**:
```bash
docker compose restart frontend
```

### Database Connection Refused

**Wait for PostgreSQL to initialize** (first run takes 30-60s):
```bash
docker compose logs postgres
# Look for: "database system is ready to accept connections"
```

**Reset database**:
```bash
docker compose down -v
docker compose up -d postgres
# Wait 60 seconds
docker compose up -d
```

---

## Scaling & Maintenance

### Scaling Scrapers
```bash
# Run scraper independently
docker run -e POSTGRES_HOST=localhost anip-scraper-hackernews

# Or use Airflow to schedule (see dags/)
```

### Upgrading Services
```bash
# Pull latest images
docker compose pull

# Rebuild without cache
docker compose build --no-cache

# Restart services
docker compose up -d
```

### Cleaning Up

**Remove stopped containers**:
```bash
docker container prune -f
```

**Remove unused images**:
```bash
docker image prune -a
```

**Reset everything** (WARNING: deletes data):
```bash
docker compose down -v
rm -rf volumes/*
```

---

## Monitoring Checklist (Daily)

- [ ] All containers running: `docker compose ps`
- [ ] No critical errors: `docker compose logs api | grep ERROR`
- [ ] Database size: `docker compose exec postgres du -sh /var/lib/postgresql/data`
- [ ] Available disk: `docker system df`
- [ ] API responsive: `curl http://localhost:8000/health`
- [ ] Articles being fetched: `docker compose logs -f scraper-*`

---

## Support Commands

| Issue | Command |
|-------|---------|
| See all logs | `docker compose logs -f` |
| Restart everything | `docker compose restart` |
| Stop all services | `docker compose down` |
| View service details | `docker inspect anip-api` |
| Access database shell | `docker compose exec postgres psql -U anip` |
| Check resource usage | `docker stats` |

---

## Final Verification

When everything is running:

✅ **Frontend loads**: http://localhost:3000  
✅ **Articles visible**: http://localhost:3000/telangana  
✅ **API responsive**: http://localhost:8000/health  
✅ **Database healthy**: `docker compose ps` shows ✓ for postgres  
✅ **Logs clean**: No repeated errors in `docker compose logs`  

**You're ready to deploy!** 🚀
