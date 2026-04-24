# Docker Portability Guide - ANIP Project

## ✅ Cross-Platform Compatibility

Your ANIP project is **fully containerized and portable** across Windows, macOS, and Linux systems. All dependencies are isolated in Docker containers.

---

## 🚀 Running on Different Systems

### Prerequisites (All Systems)
```bash
# Required:
- Docker Desktop (v4.0+)
- Docker Compose (v2.0+)
- 8GB+ RAM
- Stable internet connection (for pulling Docker images)

# Optional (for local development):
- Git
- Node.js v20+ (if developing frontend locally)
- Python 3.11+ (if running scrapers locally)
```

### Windows
**Status**: ✅ Fully Supported

1. **Install Docker Desktop for Windows**
   - Download: https://www.docker.com/products/docker-desktop
   - WSL 2 backend recommended
   - Allocate at least 4GB RAM to Docker

2. **Clone & Setup**
   ```powershell
   git clone https://github.com/poov77/Pulse---ANIP.git
   cd Pulse---ANIP
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Start Services**
   ```powershell
   # Using the startup script
   powershell -ExecutionPolicy Bypass -File .\start_project.ps1
   
   # OR manually with Docker Compose
   docker compose up -d
   ```

4. **Verify Containers**
   ```powershell
   docker compose ps
   ```

### macOS
**Status**: ✅ Fully Supported

1. **Install Docker Desktop for Mac**
   - Download: https://www.docker.com/products/docker-desktop
   - Intel or Apple Silicon (both supported)
   - Allocate 4GB+ RAM to Docker

2. **Clone & Setup**
   ```bash
   git clone https://github.com/poov77/Pulse---ANIP.git
   cd Pulse---ANIP
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Start Services**
   ```bash
   # Using Docker Compose (cross-platform)
   docker compose up -d
   
   # View logs
   docker compose logs -f api frontend
   ```

4. **Verify Setup**
   ```bash
   docker compose ps
   curl http://localhost:8000/health
   ```

### Linux
**Status**: ✅ Fully Supported (Recommended for Production)

1. **Install Docker & Docker Compose**
   ```bash
   # Ubuntu/Debian
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   
   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

2. **Create Directories & Permissions**
   ```bash
   cd /path/to/Pulse---ANIP
   mkdir -p volumes/postgres volumes/mlruns volumes/logs
   chmod 755 volumes/*
   ```

3. **Clone & Setup**
   ```bash
   git clone https://github.com/poov77/Pulse---ANIP.git
   cd Pulse---ANIP
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Start Services**
   ```bash
   # Start detached
   docker compose up -d
   
   # Or with logs
   docker compose up
   ```

5. **Verify**
   ```bash
   docker compose ps
   docker compose logs -f api
   ```

---

## 🔧 Environment Configuration

### .env File Management
Create `.env` from template:
```bash
cp .env.example .env
```

**Critical Variables** (required):
```
POSTGRES_USER=anip
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=anip
AIRFLOW_DB_PASSWORD=your_secure_password_here
NEWSAPI_KEY=your_api_key_here
```

**Optional but Recommended**:
- `NEWSDATA_KEY` - Regional news (India)
- `OPENAI_API_KEY` - For AI chat features
- `THENEWSAPI_KEY` - Global news aggregation

**Port Mappings** (edit if conflicts exist):
```
DATABASE_PORT=5432
API_PORT=8000
FRONTEND_PORT=3000
MLFLOW_PORT=5000
SPARK_MASTER_PORT=9090
```

---

## 🐳 Docker Images (Base Compatibility)

| Service | Base Image | Compatibility | Notes |
|---------|-----------|---|---|
| **PostgreSQL** | `pgvector/pgvector:pg16` | All platforms | Intel + ARM64 ✅ |
| **API Backend** | `python:3.11-slim` | All platforms | Auto-compiled |
| **Frontend** | `node:20-alpine` | All platforms | Lightweight |
| **Spark** | `apache/spark:4.0.0` | All platforms | Multi-arch support |
| **Redis** | `redis:7-alpine` | All platforms | Slim image |
| **Kafka** | `redpanda:v23.2.1` | All platforms | Drop-in Kafka replacement |
| **MLflow** | `python:3.11` | All platforms | Auto-built |

**Key Point**: All images support both `linux/amd64` and `linux/arm64` architectures (including Apple Silicon).

---

## 📊 Volume Mounts (Cross-Platform)

Volumes are **relative paths** from project root, making them portable:

```yaml
volumes:
  - ./volumes/postgres:/var/lib/postgresql/data       # Cross-platform ✅
  - ./volumes/mlruns:/mlruns
  - ./volumes/logs:/var/log
```

**On Windows**: Paths automatically converted by Docker Desktop (e.g., `C:\Users\...\volumes` → `/mnt/c/Users/.../volumes`)

---

## 🚨 Common Issues & Solutions

### Issue 1: Port Already in Use
**Symptom**: `bind: permission denied`

**Solution**:
```bash
# Check what's using the port (macOS/Linux)
lsof -i :8000

# On Windows
netstat -ano | findstr :8000

# Kill the process or change port in .env
API_PORT=8001  # Change to different port
```

### Issue 2: Insufficient Disk Space
**Symptom**: `no space left on device`

**Solution**:
```bash
# Remove old volumes
docker compose down -v

# Docker system prune
docker system prune -a --volumes
```

### Issue 3: Memory Issues (especially on Windows)
**Symptom**: Containers crash or restart repeatedly

**Solution**:
1. Increase Docker Desktop RAM allocation:
   - Docker Desktop → Settings → Resources → Memory: 6-8GB
   - CPUs: 4+

2. Or reduce services:
   ```bash
   # Start only essential services
   docker compose up -d postgres api frontend
   ```

### Issue 4: Network Issues
**Symptom**: `Cannot reach localhost:8000`

**Solution**:
```bash
# On Linux, use 127.0.0.1
curl http://127.0.0.1:8000/health

# On Mac/Windows use localhost
curl http://localhost:8000/health

# Check if containers are connected
docker compose exec api curl http://postgres:5432
```

### Issue 5: Database Connection Errors
**Symptom**: `FATAL: the database system is starting up`

**Solution**:
```bash
# Wait for databases to initialize (can take 30-60s on first run)
docker compose logs postgres

# Restart just the API after DB is healthy
docker compose restart api
```

---

## 📈 Performance Optimization by System

### Windows
- ✅ Use WSL 2 backend (not Hyper-V)
- ⚠️ Slower file sync than native
- 💡 Store project in WSL filesystem, not Windows C: drive
  ```bash
  # In WSL terminal
  cd ~/projects/Pulse---ANIP
  docker compose up -d
  ```

### macOS
- ✅ Native Docker support
- ⚠️ Apple Silicon arm64 slower until image compiled
- 💡 First run may take longer (image compilation)

### Linux
- ✅ **Best performance** (native Docker)
- ✅ Full root/permission controls
- 💡 Use `--cpus` and `--memory` limits for safety

---

## 🔄 CI/CD Deployment

### GitHub Actions Example
```yaml
name: Deploy to Docker Hub

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build and Push API
        uses: docker/build-push-action@v4
        with:
          context: .
          dockerfile: services/api/Dockerfile
          push: true
          tags: ${{ secrets.DOCKER_USERNAME }}/anip-api:latest
      
      - name: Deploy
        run: |
          docker compose pull
          docker compose up -d
```

### Local Multi-Stage Builds
```bash
# Build production images locally
docker compose -f docker-compose.yml build --no-cache

# Push to registry
docker push your-registry/anip-api:latest
```

---

## 🛡️ Security Notes for Production

### Before Deploying to Production:

1. **Change Default Passwords**
   ```bash
   # .env
   POSTGRES_PASSWORD=generate_strong_password_here
   AIRFLOW_DB_PASSWORD=generate_strong_password_here
   ```

2. **Use Environment Secrets Manager**
   ```bash
   # Use Docker Secrets (Swarm) or Kubernetes Secrets
   docker secret create postgres_password -
   ```

3. **Network Isolation**
   ```yaml
   networks:
     anip-net:
       driver: bridge
       ipam:
         config:
           - subnet: 172.20.0.0/16
   ```

4. **Disable Debug Mode**
   ```bash
   # services/api/Dockerfile → CMD add --reload=false
   ```

---

## ✅ System-Specific Verification Checklist

### All Systems
- [ ] Docker installed: `docker --version`
- [ ] Docker Compose installed: `docker compose --version`
- [ ] Git cloned repository
- [ ] `.env` configured with API keys
- [ ] Volume directories created: `mkdir -p volumes/{postgres,mlruns,logs}`

### Windows-Specific
- [ ] WSL 2 enabled
- [ ] Docker Desktop 4.0+
- [ ] 4GB+ RAM allocated
- [ ] PowerShell ExecutionPolicy set

### macOS-Specific
- [ ] Docker Desktop for Mac installed
- [ ] Virtualization enabled (Intel) or ARM support ready (Apple Silicon)
- [ ] File sharing enabled in Docker preferences

### Linux-Specific
- [ ] Docker daemon running: `sudo systemctl status docker`
- [ ] User added to docker group: `sudo usermod -aG docker $USER`
- [ ] SELinux/AppArmor configured if needed
- [ ] Firewall allows ports 3000, 8000, 5432

---

## 📚 Additional Resources

- **Docker Official Docs**: https://docs.docker.com/
- **Docker Compose Reference**: https://docs.docker.com/compose/compose-file/
- **PostgreSQL in Docker**: https://hub.docker.com/r/postgres/
- **Node/Python Multi-arch**: https://hub.docker.com/r/library/node

---

## 🎯 Quick Reference

| Task | Command |
|------|---------|
| Start all services | `docker compose up -d` |
| Stop all services | `docker compose down` |
| View logs | `docker compose logs -f service_name` |
| Rebuild images | `docker compose build --no-cache` |
| Check status | `docker compose ps` |
| Access database | `docker compose exec postgres psql -U anip` |
| Clear everything | `docker compose down -v && rm -rf volumes/*` |

---

## 💬 Support

If you encounter issues:
1. Check logs: `docker compose logs -f`
2. Verify Docker version: `docker --version`
3. Check disk space: `docker system df`
4. Restart services: `docker compose restart`

Your ANIP project is fully containerized and production-ready! 🚀
