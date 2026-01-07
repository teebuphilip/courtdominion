# DOCKER CHEAT SHEET - CourtDominion
## Tailored for 2015 MacBook Pro / Docker 4.24.2

---

## BASIC CONTAINER OPERATIONS

### Build Container (After Code Changes)
```bash
# Normal build (uses cache)
docker compose build automation

# Clean build (ignores cache, use after major changes)
docker compose build --no-cache automation
```

### Run Commands in Container
```bash
# Run a single Python script
docker compose run --rm automation python pipeline.py

# Run cache builder
docker compose run --rm automation python build_cache.py

# Run bash shell (interactive)
docker compose run --rm automation bash

# List files inside container
docker compose run --rm automation ls -la /data/outputs/
```

---

## VIEWING LOGS & FILES

### Check Container Logs
```bash
# View backend logs (live)
docker compose logs -f backend

# View automation logs (last run)
docker compose logs automation

# View last 50 lines
docker compose logs --tail=50 automation
```

### View Files Inside Container
```bash
# Read a file
docker compose run --rm automation cat /data/outputs/projections.json

# List directory
docker compose run --rm automation ls -la /data/outputs/

# View first 20 lines
docker compose run --rm automation head -20 /app/pipeline.py

# View specific line range
docker compose run --rm automation sed -n '90,110p' /app/generator.py
```

### Search Inside Container
```bash
# Find text in a file
docker compose run --rm automation grep "CACHE_FILE" /app/dbb2_projections.py

# Find text with line numbers
docker compose run --rm automation grep -n "CACHE_FILE" /app/dbb2_projections.py

# Search all Python files
docker compose run --rm automation grep -r "some_text" /app/
```

---

## CONTAINER LIFECYCLE

### Start Services
```bash
# Start backend (runs in background)
docker compose up -d backend

# Start and view logs
docker compose up backend
```

### Stop Services
```bash
# Stop all services
docker compose down

# Stop and remove volumes (DANGEROUS - deletes data!)
docker compose down -v
```

### Check Status
```bash
# See running containers
docker compose ps

# See all containers (including stopped)
docker ps -a
```

---

## CLEANUP COMMANDS

### Remove Old Containers
```bash
# Remove stopped containers
docker compose rm

# Force remove all
docker compose rm -f
```

### Clean Up Docker System
```bash
# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Remove everything unused (CAREFUL!)
docker system prune

# Nuclear option (removes EVERYTHING)
docker system prune -a --volumes
```

---

## VOLUME OPERATIONS

### Inspect Volumes
```bash
# List all volumes
docker volume ls

# See volume details
docker volume inspect courtdominion_shared-data
```

### Access Volume Data
```bash
# List files in shared-data volume
docker compose run --rm automation ls -la /data/outputs/

# Copy file FROM volume to Mac
docker compose run --rm automation cat /data/outputs/projections.json > projections.json
```

---

## DEBUGGING

### Container Won't Start
```bash
# Check logs
docker compose logs backend

# Try running bash
docker compose run --rm automation bash

# Rebuild from scratch
docker compose build --no-cache automation
```

### File Not Found Errors
```bash
# Check what files exist
docker compose run --rm automation ls -la /app/

# Check volume contents
docker compose run --rm automation ls -la /data/outputs/
```

### Python Import Errors
```bash
# Check installed packages
docker compose run --rm automation pip list

# Rebuild container
docker compose build --no-cache automation
```

---

## COURTDOMINION SPECIFIC COMMANDS

### Daily Workflow
```bash
# 1. Build cache (once per week)
docker compose run --rm automation python build_cache.py

# 2. Run automation (daily)
docker compose run --rm automation python pipeline.py

# 3. Check results
docker compose run --rm automation ls -la /data/outputs/generated/
```

### Check Generated Content
```bash
# List today's content
docker compose run --rm automation ls -la /data/outputs/generated/$(date +%Y-%m-%d)/

# Read Twitter content
docker compose run --rm automation cat /data/outputs/generated/$(date +%Y-%m-%d)/twitter_draft.txt

# Read all content
docker compose run --rm automation cat /data/outputs/generated/$(date +%Y-%m-%d)/*.txt
```

### Verify System Health
```bash
# Check cache exists
docker compose run --rm automation ls -la /data/outputs/player_stats_cache.json

# Check projections
docker compose run --rm automation head -50 /data/outputs/projections.json

# Check backend is running
curl http://localhost:8000/health
```

---

## SAVE LOGS TO FILES

### Redirect Output to File
```bash
# Save pipeline output
docker compose run --rm automation python pipeline.py > pipeline.log 2>&1

# Save cache build output
docker compose run --rm automation python build_cache.py > cache_build.log 2>&1

# Save container logs
docker compose logs automation > automation.log

# Append to existing log
docker compose run --rm automation python pipeline.py >> pipeline.log 2>&1
```

---

## COMMON ERROR FIXES

### "Cache file not found"
```bash
# Check if cache exists
docker compose run --rm automation ls -la /data/outputs/player_stats_cache.json

# If missing, rebuild
docker compose run --rm automation python build_cache.py
```

### "ModuleNotFoundError"
```bash
# Rebuild container
docker compose build --no-cache automation
```

### "Port already in use"
```bash
# Stop all services
docker compose down

# Check what's using the port
lsof -i :8000
```

---

## DOCKER DESKTOP MANAGEMENT

### Memory Issues (2015 MacBook)
```bash
# Stop Docker Desktop when not in use
# (Click Docker icon in menu bar → Quit Docker Desktop)

# Reduce memory in Docker Desktop settings
# Docker Desktop → Preferences → Resources → Memory: 2GB
```

### Disk Space Issues
```bash
# See disk usage
docker system df

# Clean up
docker system prune -a
```

---

## QUICK REFERENCE

| Task | Command |
|------|---------|
| Build container | `docker compose build automation` |
| Run pipeline | `docker compose run --rm automation python pipeline.py` |
| View logs | `docker compose logs automation` |
| Save logs to file | `docker compose run --rm automation python pipeline.py > log.txt 2>&1` |
| List files in volume | `docker compose run --rm automation ls -la /data/outputs/` |
| Start backend | `docker compose up -d backend` |
| Stop all | `docker compose down` |
| Clean up | `docker system prune` |

---

## IMPORTANT NOTES FOR YOUR SETUP

⚠️ **Always use `docker compose run --rm`** 
- The `--rm` flag removes container after running
- Prevents accumulation of stopped containers
- Saves memory on your 2015 MacBook

⚠️ **Stop Docker Desktop when not coding**
- Docker uses 2-4GB RAM constantly
- Your MacBook only has so much to give

⚠️ **Use `--no-cache` after major code changes**
- Ensures Docker picks up your edits
- Takes longer but guarantees fresh build

⚠️ **Never delete `shared-data` volume**
- Contains your cache (30-60 min to rebuild)
- Contains all generated content
- Only delete if you know what you're doing

---

**END OF CHEAT SHEET**
