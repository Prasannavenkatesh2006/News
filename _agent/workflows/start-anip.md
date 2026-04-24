---
description: Start the entire ANIP Platform (API + Scrapers + Frontend)
---

This workflow automates the startup of the ANIP (Automated News Intelligence Pipeline) platform.

### Prerequisites
- Docker Desktop must be running.
- PostgreSQL must be running locally on port 5432 with credentials `anip/3006`.
- Python 3.10+ installed and on PATH.

### Steps

1. **Clean Stale Processes**
   The system will automatically clear ports 8000 (API) and 3000 (Frontend) to prevent "Address already in use" errors.

2. **Start Infrastructure Services**
   // turbo
   Run `docker compose up -d redis redpanda` to start the message queue and cache.

3. **Launch API Backend**
   // turbo
   Run `powershell -ExecutionPolicy Bypass -File .\start_project.ps1` to start the local Python API and monitor its health.

4. **Verify System Health**
   Run the following script to check the live post feed:
   `python check_feed_utf8.py`

5. **Access the Platform**
   - Frontend: [http://localhost:3000](http://localhost:3000)
   - API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
