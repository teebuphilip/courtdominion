# CourtDominion Docker Setup Instructions

Complete Docker setup for backend + automation with shared data volume.

---

## 📋 PREREQUISITES

- Docker Desktop installed
- Docker Compose V2 (included in Docker Desktop)
- 2GB free RAM
- 5GB free disk space

---

## 📂 DIRECTORY STRUCTURE

Your project should look like this:

```
courtdominion/
├── docker-compose.yml          # Main orchestration file
├── .env.example                # Environment variables template
├── .env                        # Your environment variables (create this)
│
├── backend/                    # Backend service
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── routers/
│   ├── services/
│   ├── models/
│   ├── shared/
│   └── utils/
│
└── automation/                 # Automation service
    ├── Dockerfile
    ├── requirements.txt
    ├── pipeline.py
    ├── ingest_injuries.py
    ├── projection_generator.py
    ├── insights_generator.py
    ├── risk_metrics.py
    ├── utils/
    └── schemas/
```

---

## 🚀 QUICK START

### 1. Setup Environment

```bash
# Copy environment variables template
cp .env.example .env

# Edit .env if needed (defaults work for local development)
nano .env
```

### 2. Build Services

```bash
# Build all services
docker compose build

# Or build specific service
docker compose build backend
docker compose build automation
```

### 3. Start Services

```bash
# Start all services (backend + db)
docker compose up -d backend db

# Check status
docker compose ps

# View logs
docker compose logs -f backend
```

### 4. Run Automation

```bash
# Run automation once
docker compose run --rm automation

# Or start automation service
docker compose up automation
```

### 5. Verify

```bash
# Check backend health
curl http://localhost:8000/health

# Check if data was generated
docker compose exec backend ls -la /data/outputs

# View generated files
docker compose exec backend cat /data/outputs/players.json
```

---

## 📊 DATA FLOW

```
┌─────────────┐
│ Automation  │
│   Service   │
└──────┬──────┘
       │
       │ Writes JSON files
       ▼
┌──────────────────┐
│  Shared Volume   │
│  /data/outputs   │
└──────┬───────────┘
       │
       │ Reads JSON files
       ▼
┌──────────────┐
│   Backend    │
│   Service    │
└──────────────┘
```

---

## 🔄 COMMON COMMANDS

### Starting Services

```bash
# Start all services
docker compose up -d

# Start specific services
docker compose up -d backend
docker compose up -d backend db

# Start in foreground (see logs)
docker compose up backend
```

### Stopping Services

```bash
# Stop all services
docker compose down

# Stop and remove volumes (DELETES DATA)
docker compose down -v

# Stop specific service
docker compose stop backend
```

### Rebuilding

```bash
# Rebuild after code changes
docker compose up -d --build backend

# Force rebuild (no cache)
docker compose build --no-cache backend
```

### Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f automation

# Last 100 lines
docker compose logs --tail=100 backend
```

### Running Commands

```bash
# Execute command in running container
docker compose exec backend ls /data/outputs

# Run one-off command
docker compose run --rm backend python -c "print('hello')"

# Run automation manually
docker compose run --rm automation python pipeline.py
```

---

## 🧪 TESTING SETUP

### 1. Verify Backend

```bash
# Health check
curl http://localhost:8000/health
# Expected: {"status":"ok","timestamp":"..."}

# Root endpoint
curl http://localhost:8000/
# Expected: Service info with endpoints

# Players endpoint (before automation runs)
curl http://localhost:8000/players
# Expected: []
```

### 2. Run Automation

```bash
# Run automation
docker compose run --rm automation

# Expected output:
# ======================================================================
#   COURTDOMINION AUTOMATION PIPELINE
# ======================================================================
# ...
# ======================================================================
#   PIPELINE COMPLETED SUCCESSFULLY
# ======================================================================
```

### 3. Verify Data Generated

```bash
# List generated files
docker compose exec backend ls -la /data/outputs

# Expected files:
# players.json
# injuries.json
# projections.json
# risk.json
# insights.json
# manifest.json
```

### 4. Test Backend Reads Data

```bash
# Get players
curl http://localhost:8000/players | jq

# Get projections
curl http://localhost:8000/projections | jq

# Get insights
curl http://localhost:8000/insights | jq

# Get risk metrics
curl http://localhost:8000/risk-metrics | jq
```

---

## 🔧 TROUBLESHOOTING

### Backend Won't Start

```bash
# Check logs
docker compose logs backend

# Common issues:
# - Port 8000 already in use → Stop other services
# - Import errors → Rebuild: docker compose build backend
# - Missing files → Check directory structure
```

### Automation Fails

```bash
# Check logs
docker compose logs automation

# Run in foreground to see errors
docker compose run --rm automation

# Common issues:
# - Import errors → Check Python path
# - Permission errors → Check volume mounts
# - Missing schemas → Check schemas/ directory copied
```

### No Data Generated

```bash
# Check automation logs
docker compose logs automation

# Check shared volume
docker compose exec backend ls -la /data/outputs

# Verify volume exists
docker volume ls | grep shared-data

# Inspect volume
docker volume inspect courtdominion_shared-data
```

### Backend Returns Empty Arrays

```bash
# Check if files exist
docker compose exec backend ls /data/outputs

# If no files, run automation
docker compose run --rm automation

# Check file contents
docker compose exec backend cat /data/outputs/players.json
```

### Port Conflicts

```bash
# If port 8000 is in use
# Option 1: Change port in docker-compose.yml
ports:
  - "8001:8000"  # External:Internal

# Option 2: Stop conflicting service
lsof -ti:8000 | xargs kill -9
```

---

## 🗑️ CLEANUP

### Remove Containers (Keep Data)

```bash
docker compose down
```

### Remove Everything (INCLUDING DATA)

```bash
# Remove containers, networks, volumes
docker compose down -v

# Remove images
docker compose down --rmi all
```

### Clean Docker System

```bash
# Remove unused containers, images, volumes
docker system prune -a --volumes
```

---

## 📅 SCHEDULED AUTOMATION

### Option 1: Cron (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Run automation daily at 5am
0 5 * * * cd /path/to/courtdominion && docker compose run --rm automation
```

### Option 2: Docker with Restart Policy

```yaml
# In docker-compose.yml
automation:
  restart: on-failure
  command: |
    sh -c "
      while true; do
        python pipeline.py
        sleep 86400  # 24 hours
      done
    "
```

### Option 3: External Scheduler (GitHub Actions)

```yaml
# .github/workflows/automation.yml
name: Daily Automation
on:
  schedule:
    - cron: '0 5 * * *'  # 5am UTC daily
jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: docker compose run --rm automation
```

---

## 🌐 PRODUCTION DEPLOYMENT (Railway)

### 1. Data Persistence Issue

**Problem:** Railway uses ephemeral filesystem - data lost on restart.

**Solutions:**

**A. Run Automation on Schedule (Recommended for Phase 1)**
```yaml
# Railway will restart automation daily
# Data regenerated each time
# Accept data loss between runs
```

**B. Use External Storage**
```python
# Store outputs in S3/Google Cloud Storage
# Backend fetches from cloud storage
```

**C. Use Database (Phase 2)**
```python
# Store all data in PostgreSQL
# Backend reads from database
```

### 2. Railway Configuration

```bash
# Deploy backend
railway up --service backend

# Deploy automation
railway up --service automation

# Set environment variables in Railway dashboard
ENVIRONMENT=production
DATA_DIR=/data/outputs
```

### 3. Railway Volumes (Paid Feature)

```yaml
# railway.json
{
  "build": {
    "builder": "DOCKERFILE"
  },
  "deploy": {
    "volumeMounts": [
      {
        "mountPath": "/data/outputs",
        "volumeName": "shared-data"
      }
    ]
  }
}
```

---

## 📊 MONITORING

### Health Checks

```bash
# Backend health
watch -n 5 curl -s http://localhost:8000/health

# Container status
watch -n 5 docker compose ps

# Resource usage
docker stats
```

### Logs

```bash
# Follow all logs
docker compose logs -f

# Export logs
docker compose logs > logs.txt
```

---

## 🎯 SUCCESS CRITERIA

✅ Backend responds at http://localhost:8000  
✅ Health check returns `{"status":"ok"}`  
✅ Automation completes without errors  
✅ All 5 JSON files generated in shared volume  
✅ Backend returns data from endpoints  
✅ No container crashes or restarts  

---

## 📚 ADDITIONAL RESOURCES

- Docker Compose docs: https://docs.docker.com/compose/
- FastAPI in Docker: https://fastapi.tiangolo.com/deployment/docker/
- Docker volumes: https://docs.docker.com/storage/volumes/
- Railway deployment: https://docs.railway.app/

---

## 🆘 SUPPORT

If you encounter issues:

1. Check logs: `docker compose logs -f`
2. Verify volumes: `docker volume ls`
3. Rebuild: `docker compose up -d --build`
4. Clean start: `docker compose down -v && docker compose up --build`

---

**Setup Version:** 1.0.0  
**Last Updated:** November 24, 2025  
**Status:** ✅ Production Ready
