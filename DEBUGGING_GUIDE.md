# 2AM Debugging Guide for CourtDominion
## When Shit Breaks and You're Alone

---

## Emergency Quick Diagnosis

**Start here. Match your symptom to a section.**

| Symptom | Likely Cause | Jump To |
|---------|--------------|---------|
| "Cannot connect to backend" | Backend not running | [Backend Won't Start](#backend-wont-start) |
| "Port already in use" | Something using port 8000/3000 | [Port Conflicts](#port-conflicts) |
| "Module not found" | Missing dependencies | [Dependency Issues](#dependency-issues) |
| "Cache file not found" | Automation didn't run or failed | [Cache Problems](#cache-file-not-found) |
| "No such file or directory" | Docker volume issue | [Volume Problems](#docker-volume-issues) |
| "502 Bad Gateway" | Backend crashed or not responding | [Backend Crashed](#backend-crashed) |
| Frontend shows no data | Backend not running or wrong URL | [Frontend Can't Fetch Data](#frontend-cant-fetch-data) |
| Tests failing | Code broke or test data missing | [Test Failures](#test-failures) |
| Docker build fails | Dependency conflict or syntax error | [Build Failures](#docker-build-failures) |
| Slow performance | Memory issue or large dataset | [Performance Issues](#performance-slow-or-memory-issues) |

---

## Docker Issues

### Docker Won't Start

**Symptoms:**
- `Cannot connect to Docker daemon`
- Docker Desktop not responding

**Fix:**
```bash
# Check if Docker Desktop is running
docker ps

# If error, open Docker Desktop app
# Click icon in menu bar → Open Docker Desktop

# Wait 30-60 seconds for Docker to fully start
# Then try again
docker ps
```

**Nuclear option:**
```bash
# Quit Docker Desktop
# Open Activity Monitor
# Search "docker" and Force Quit all Docker processes
# Restart Docker Desktop
```

---

### Docker Build Failures

**Symptoms:**
- `ERROR: failed to solve`
- `Could not find a version that satisfies the requirement`

**Fix 1: Clear cache and rebuild**
```bash
# Build without cache (forces fresh install)
docker compose build --no-cache automation
docker compose build --no-cache backend
```

**Fix 2: Check Dockerfile syntax**
```bash
# Automation Dockerfile
cat courtdominion-app/automation/Dockerfile

# Backend Dockerfile
cat courtdominion-app/backend/Dockerfile

# Look for typos, missing quotes, wrong paths
```

**Fix 3: Dependency conflict**
```bash
# Check requirements.txt for version conflicts
cat courtdominion-app/backend/requirements.txt

# If multiple versions of same package, keep only one
# Example: DON'T have both
#   requests==2.28.0
#   requests==2.31.0
```

---

### Docker Volume Issues

**Symptoms:**
- `No such file or directory: /data/outputs/projections.json`
- Files disappear after container stops

**Diagnosis:**
```bash
# Check if volume exists
docker volume ls | grep shared-data

# Inspect volume
docker volume inspect courtdominion_shared-data
```

**Fix 1: Volume exists but empty**
```bash
# List what's in volume
docker compose run --rm automation ls -la /data/outputs/

# If empty, run automation to populate
docker compose run --rm automation python build_cache.py
docker compose run --rm automation python pipeline.py
```

**Fix 2: Volume doesn't exist**
```bash
# Stop all containers
docker compose down

# Recreate volume
docker compose up -d backend

# Populate with data
docker compose run --rm automation python build_cache.py
docker compose run --rm automation python pipeline.py
```

**Fix 3: Nuclear option (DELETES ALL DATA)**
```bash
# ⚠️ WARNING: This deletes cache (30-60 min to rebuild)
docker compose down -v
docker compose up -d backend
docker compose run --rm automation python build_cache.py
docker compose run --rm automation python pipeline.py
```

---

### Container Won't Start

**Symptoms:**
- Container starts then immediately exits
- `docker compose ps` shows status "Exited (1)"

**Diagnosis:**
```bash
# Check logs for error
docker compose logs backend
docker compose logs automation

# Try running bash interactively
docker compose run --rm automation bash
```

**Fix 1: Permission issues**
```bash
# Check file permissions
ls -la courtdominion-app/automation/
ls -la courtdominion-app/backend/

# If you see "Permission denied", fix with:
chmod +x courtdominion-app/automation/*.py
chmod +x courtdominion-app/backend/*.py
```

**Fix 2: Syntax error in code**
```bash
# Look at logs for Python traceback
docker compose logs automation | grep "Error"

# Check syntax of the file mentioned
# Fix the error, then rebuild
docker compose build --no-cache automation
```

---

### Port Conflicts

**Symptoms:**
- `Bind for 0.0.0.0:8000 failed: port is already allocated`
- `Address already in use`

**Diagnosis:**
```bash
# See what's using port 8000
lsof -i :8000

# See what's using port 3000
lsof -i :3000
```

**Fix 1: Kill the process**
```bash
# Kill whatever is on port 8000
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Kill whatever is on port 3000
lsof -i :3000 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

**Fix 2: Stop old Docker containers**
```bash
# Stop all containers
docker compose down

# Remove stopped containers
docker compose rm -f

# Start fresh
docker compose up -d backend
```

**Fix 3: Change the port**
```bash
# Edit docker-compose.yml
# Change "8000:8000" to "8001:8000"
# Save, then restart
docker compose up -d backend
```

---

## Backend Issues

### Backend Won't Start

**Symptoms:**
- `curl http://localhost:8000/health` fails
- Container exits immediately

**Diagnosis:**
```bash
# Check if container is running
docker compose ps

# Check logs
docker compose logs backend

# Try to run bash
docker compose run --rm backend bash
```

**Fix 1: Missing environment variables**
```bash
# Check .env file exists
cat .env

# If missing, create it:
cat > .env <<EOF
DATA_DIR=/data/outputs
INTERNAL_API_KEY=change-me-to-something-secret
LOG_LEVEL=INFO
EOF

# Restart backend
docker compose restart backend
```

**Fix 2: Missing dependencies**
```bash
# Rebuild with fresh dependencies
docker compose build --no-cache backend
docker compose up -d backend
```

**Fix 3: Python syntax error**
```bash
# Check logs for traceback
docker compose logs backend | grep -A 10 "Error"

# Fix the file mentioned
# Rebuild and restart
docker compose build backend
docker compose up -d backend
```

---

### Backend Crashed

**Symptoms:**
- Frontend was working, now shows errors
- Backend logs show exception

**Diagnosis:**
```bash
# Check if backend is still running
docker compose ps

# Look at last 50 log lines
docker compose logs --tail=50 backend
```

**Fix 1: Restart backend**
```bash
docker compose restart backend

# If that fails
docker compose down
docker compose up -d backend
```

**Fix 2: Memory issue**
```bash
# Check Docker memory usage
docker stats

# If memory is maxed out:
# Open Docker Desktop → Settings → Resources → Memory
# Increase to 4GB (from 2GB)
# Restart Docker Desktop
docker compose up -d backend
```

**Fix 3: File corruption**
```bash
# Check if data files are valid JSON
docker compose run --rm backend python -m json.tool /data/outputs/projections.json

# If error, regenerate
docker compose run --rm automation python pipeline.py
docker compose restart backend
```

---

### API Endpoint Returns 500 Error

**Symptoms:**
- `curl http://localhost:8000/api/players` returns 500
- Swagger UI shows "Internal Server Error"

**Diagnosis:**
```bash
# Check logs for exception
docker compose logs backend | grep -A 20 "ERROR"

# Test health endpoint
curl http://localhost:8000/health
```

**Fix 1: Missing data file**
```bash
# Check if projections.json exists
docker compose run --rm backend ls -la /data/outputs/projections.json

# If missing, generate it
docker compose run --rm automation python pipeline.py
docker compose restart backend
```

**Fix 2: Malformed JSON**
```bash
# Validate JSON
docker compose run --rm backend python -m json.tool /data/outputs/projections.json > /dev/null

# If error, regenerate
docker compose run --rm automation python pipeline.py
```

**Fix 3: Code bug**
```bash
# Look at traceback in logs
docker compose logs backend | grep -A 30 "Traceback"

# Fix the bug in main.py
# Restart
docker compose restart backend
```

---

### API Returns Empty Data

**Symptoms:**
- `GET /api/players` returns `[]`
- `GET /api/projections/top` returns `{"data": []}`

**Diagnosis:**
```bash
# Check if data file exists and has content
docker compose run --rm backend cat /data/outputs/projections.json | head -50
```

**Fix:**
```bash
# Regenerate data
docker compose run --rm automation python build_cache.py
docker compose run --rm automation python pipeline.py

# Restart backend
docker compose restart backend

# Test again
curl http://localhost:8000/api/projections/top
```

---

### CORS Errors

**Symptoms:**
- Browser console shows "CORS policy: No 'Access-Control-Allow-Origin' header"
- Frontend can't fetch data

**Fix:**
```bash
# Check backend CORS config
docker compose run --rm backend grep -n "CORS" main.py

# Should see:
#   app.add_middleware(
#       CORSMiddleware,
#       allow_origins=["*"],
#   )

# If missing, add to main.py:
# (lines 15-20)
```

**Quick test:**
```bash
# Should return CORS headers
curl -I http://localhost:8000/api/players

# Look for:
#   access-control-allow-origin: *
```

---

## Frontend Issues

### Frontend Won't Start

**Symptoms:**
- `npm run dev` fails
- Port 3000 already in use

**Diagnosis:**
```bash
cd courtdominion-app/frontend

# Check for errors
npm run dev

# Check if port 3000 is taken
lsof -i :3000
```

**Fix 1: Missing dependencies**
```bash
# Delete node_modules and reinstall
rm -rf node_modules
npm install --legacy-peer-deps

# Try again
npm run dev
```

**Fix 2: Port conflict**
```bash
# Kill process on port 3000
lsof -i :3000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Or use different port
# Edit package.json, change dev script:
#   "dev": "vite --port 3001"

npm run dev
```

**Fix 3: Node version issue**
```bash
# Check Node version
node --version

# Should be v18+
# If older, install newer Node:
# https://nodejs.org/en/download/
```

---

### Frontend Can't Fetch Data

**Symptoms:**
- Frontend loads but shows "No data" or spinning loader
- Browser console shows `Failed to fetch` or `Network Error`

**Diagnosis:**
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check browser console (F12 → Console tab)
# Look for red errors
```

**Fix 1: Backend not running**
```bash
# Start backend
docker compose up -d backend

# Verify it's working
curl http://localhost:8000/api/projections/top

# Refresh frontend
```

**Fix 2: Wrong API URL**
```bash
# Check frontend API config
cat courtdominion-app/frontend/src/utils/api.js | grep baseURL

# Should be:
#   const API_BASE_URL = 'http://localhost:8000'

# If wrong, edit api.js and save
# Frontend hot-reloads automatically
```

**Fix 3: CORS issue**
```bash
# Check browser console for CORS error
# If CORS error, see [CORS Errors](#cors-errors) section above
```

---

### Frontend Shows Old/Cached Data

**Symptoms:**
- Data doesn't update after running automation
- Old projections still showing

**Fix:**
```bash
# Hard refresh browser (clears cache)
# Mac: Cmd + Shift + R
# Windows: Ctrl + Shift + R

# Or clear browser cache:
# Chrome → Settings → Privacy → Clear browsing data → Cached images
```

**If still wrong:**
```bash
# Verify backend has new data
curl http://localhost:8000/api/projections/top | head -50

# If backend has old data, regenerate
docker compose run --rm automation python pipeline.py
docker compose restart backend
```

---

### Frontend Build Fails

**Symptoms:**
- `npm run build` fails
- Production deployment fails

**Diagnosis:**
```bash
cd courtdominion-app/frontend

# Try to build
npm run build

# Look for errors
```

**Fix 1: Linting/type errors**
```bash
# Check for syntax errors
npm run build 2>&1 | grep "error"

# Fix the file mentioned
# Try again
npm run build
```

**Fix 2: Missing dependencies**
```bash
# Reinstall
rm -rf node_modules dist
npm install --legacy-peer-deps
npm run build
```

**Fix 3: Out of memory**
```bash
# Increase Node memory
export NODE_OPTIONS="--max-old-space-size=4096"
npm run build
```

---

### Component Not Rendering

**Symptoms:**
- Page is blank or missing sections
- Browser console shows component error

**Diagnosis:**
```bash
# Check browser console (F12)
# Look for red errors

# Common issues:
# - Undefined prop
# - Missing import
# - Typo in component name
```

**Fix:**
```bash
# Check the component file
cat courtdominion-app/frontend/src/components/player/PlayerCard.jsx

# Look for:
# - Correct imports at top
# - Props are used correctly
# - No syntax errors (missing brackets, etc.)

# Fix the error, save
# Frontend auto-reloads
```

---

## Automation Issues

### Cache File Not Found

**Symptoms:**
- `pipeline.py` fails with `FileNotFoundError: player_stats_cache.json`
- Automation can't find cache

**Diagnosis:**
```bash
# Check if cache exists
docker compose run --rm automation ls -la /data/outputs/player_stats_cache.json
```

**Fix:**
```bash
# Build cache (takes 30-60 minutes)
docker compose run --rm automation python build_cache.py

# Verify it exists
docker compose run --rm automation ls -lh /data/outputs/player_stats_cache.json

# Should show file size ~50MB+
```

---

### Automation Script Fails

**Symptoms:**
- `python pipeline.py` exits with error
- No projections generated

**Diagnosis:**
```bash
# Run with verbose output
docker compose run --rm automation python pipeline.py

# Look for traceback
```

**Fix 1: Import error**
```bash
# Error: ModuleNotFoundError: No module named 'X'

# Add to requirements.txt
echo "X==1.0.0" >> courtdominion-app/automation/requirements.txt

# Rebuild
docker compose build --no-cache automation

# Try again
docker compose run --rm automation python pipeline.py
```

**Fix 2: NBA API rate limit**
```bash
# Error: 429 Too Many Requests

# Wait 60 seconds
sleep 60

# Try again
docker compose run --rm automation python pipeline.py
```

**Fix 3: Invalid player data**
```bash
# Error: KeyError: 'points_per_game'

# Cache might be corrupted, rebuild
docker compose run --rm automation python build_cache.py

# Then run pipeline
docker compose run --rm automation python pipeline.py
```

---

### Generated Content Is Missing

**Symptoms:**
- `generated/YYYY-MM-DD/` folder is empty
- Twitter/blog drafts not created

**Diagnosis:**
```bash
# Check if pipeline completed successfully
docker compose run --rm automation python pipeline.py 2>&1 | grep -i error

# Check generated directory
docker compose run --rm automation ls -la /data/outputs/generated/$(date +%Y-%m-%d)/
```

**Fix:**
```bash
# If pipeline failed, check logs above

# If pipeline succeeded but no files, check generator.py
docker compose run --rm automation grep -n "open(" generator.py

# Make sure output paths are correct
# Should be writing to /data/outputs/generated/
```

---

### Rookie Comparables Not Working

**Symptoms:**
- Rookies show "No comparable player"
- Projection confidence is 0.0 for rookies

**Diagnosis:**
```bash
# Check CSV file
docker compose run --rm automation cat rookie_comparables.csv
```

**Fix 1: Rookie not in CSV**
```bash
# Edit CSV file
cat >> courtdominion-app/automation/rookie_comparables.csv <<EOF
Cooper Flagg,Anthony Davis,0.84
EOF

# Rebuild
docker compose build automation

# Run pipeline
docker compose run --rm automation python pipeline.py
```

**Fix 2: CSV formatting issue**
```bash
# Make sure CSV has headers
# First line should be:
#   rookie_name,comparable_player,similarity_score

# Each row should be:
#   Rookie Name,NBA Player Name,0.XX
```

---

## Data Issues

### Invalid JSON File

**Symptoms:**
- Backend returns 500 error
- `json.tool` fails to parse

**Diagnosis:**
```bash
# Test if JSON is valid
docker compose run --rm automation python -m json.tool /data/outputs/projections.json > /dev/null

# If error, JSON is corrupted
```

**Fix:**
```bash
# Regenerate JSON
docker compose run --rm automation python pipeline.py

# Verify it's valid
docker compose run --rm automation python -m json.tool /data/outputs/projections.json | head -20

# Restart backend
docker compose restart backend
```

---

### Outdated Data

**Symptoms:**
- Projections are from yesterday
- Player stats not current

**Fix:**
```bash
# Check when cache was last updated
docker compose run --rm automation ls -lh /data/outputs/player_stats_cache.json

# If older than 7 days, rebuild
docker compose run --rm automation python build_cache.py

# Generate new projections
docker compose run --rm automation python pipeline.py

# Restart backend
docker compose restart backend
```

---

### Missing Players

**Symptoms:**
- Specific player not in list
- Top 50 has fewer than 50 players

**Diagnosis:**
```bash
# Check if player is in cache
docker compose run --rm automation python -c "
import json
with open('/data/outputs/player_stats_cache.json') as f:
    data = json.load(f)
    players = [p['player_name'] for p in data.get('players', {}).values()]
    print('\n'.join([p for p in players if 'LeBron' in p]))
"
```

**Fix:**
```bash
# Rebuild cache to get latest roster
docker compose run --rm automation python build_cache.py

# Generate projections
docker compose run --rm automation python pipeline.py
```

---

## Network Issues

### Cannot Reach NBA API

**Symptoms:**
- `build_cache.py` hangs or times out
- Error: `requests.exceptions.ConnectionError`

**Diagnosis:**
```bash
# Test internet connection
ping -c 3 google.com

# Test NBA API
curl -I https://stats.nba.com/
```

**Fix 1: Network is down**
```bash
# Wait for internet to come back
# Or use your phone's hotspot

# Try again
docker compose run --rm automation python build_cache.py
```

**Fix 2: NBA API is down**
```bash
# Check status
curl -I https://stats.nba.com/

# If 500/503, wait 15-30 minutes
# NBA API occasionally goes down

# Try again later
```

**Fix 3: Rate limited**
```bash
# Wait 60 seconds between retries
sleep 60
docker compose run --rm automation python build_cache.py
```

---

### Frontend Can't Reach Backend

**Symptoms:**
- Browser console: `net::ERR_CONNECTION_REFUSED`
- Frontend shows "Failed to fetch"

**Diagnosis:**
```bash
# Test backend from terminal
curl http://localhost:8000/health

# If fails, backend not running
```

**Fix:**
```bash
# Start backend
docker compose up -d backend

# Wait 10 seconds for startup
sleep 10

# Test
curl http://localhost:8000/health

# Refresh frontend
```

---

## Test Failures

### Backend Tests Fail

**Symptoms:**
- `pytest tests/ -v` shows FAILED

**Diagnosis:**
```bash
# Run tests with verbose output
docker compose run --rm backend pytest tests/ -vv

# Look at specific failure
```

**Fix 1: Test data missing**
```bash
# Check conftest.py fixtures
docker compose run --rm backend cat tests/conftest.py | grep "@pytest.fixture"

# Make sure test data files are created
# Re-run tests
```

**Fix 2: Code changed, tests outdated**
```bash
# Update test to match new code
# Edit tests/test_*.py
# Re-run
docker compose run --rm backend pytest tests/ -v
```

---

### Frontend Tests Fail

**Symptoms:**
- `npm test` shows failures

**Diagnosis:**
```bash
cd courtdominion-app/frontend
npm test 2>&1 | grep FAIL
```

**Fix 1: Component props changed**
```bash
# Check test file
cat src/__tests__/RiskBadge.test.jsx

# Make sure props match component definition
cat src/components/projections/RiskBadge.jsx

# Update test, save
# Tests auto-rerun
```

**Fix 2: Missing test dependencies**
```bash
# Reinstall
npm install --legacy-peer-deps

# Re-run
npm test
```

---

### Automation Tests Fail

**Symptoms:**
- `pytest tests/` in automation container fails

**Diagnosis:**
```bash
# Run with verbose output
docker compose run --rm automation pytest tests/ -vv
```

**Fix:**
```bash
# Common issue: CSV newline formatting
# Edit test file
# Change \\n to \n

# Re-run
docker compose run --rm automation pytest tests/ -v
```

---

## Performance Issues

### Performance Slow or Memory Issues

**Symptoms:**
- API responses take >5 seconds
- Docker Desktop uses >4GB RAM
- Mac fans running loud

**Fix 1: Restart Docker**
```bash
# Stop all containers
docker compose down

# Quit Docker Desktop
# Wait 30 seconds
# Open Docker Desktop
# Wait for it to fully start

# Start backend
docker compose up -d backend
```

**Fix 2: Clean up Docker**
```bash
# Remove stopped containers
docker compose rm -f

# Remove unused images (saves disk space)
docker image prune -f

# Remove unused volumes (CAREFUL - deletes data)
docker volume prune
```

**Fix 3: Reduce Docker memory**
```bash
# Open Docker Desktop → Settings → Resources
# Reduce Memory to 2GB
# Reduce CPUs to 2
# Click Apply & Restart
```

**Fix 4: Optimize data files**
```bash
# Check file sizes
docker compose run --rm automation du -sh /data/outputs/*

# If cache is huge (>500MB), might be corrupted
# Rebuild
docker compose run --rm automation python build_cache.py
```

---

### Build Takes Forever

**Symptoms:**
- `docker compose build` hangs or takes 10+ minutes

**Fix:**
```bash
# Check network speed
ping -c 5 pypi.org

# If slow, wait for better network
# Or use phone hotspot

# Use cache
docker compose build automation
# (Don't use --no-cache unless necessary)
```

---

## Emergency Procedures

### Nuclear Reset (When All Else Fails)

**⚠️ WARNING: This deletes ALL data including cache (30-60 min to rebuild)**

```bash
# 1. Stop everything
docker compose down -v

# 2. Remove ALL Docker data
docker system prune -a --volumes

# 3. Delete node_modules
rm -rf courtdominion-app/frontend/node_modules

# 4. Rebuild everything
cd courtdominion-app/frontend
npm install --legacy-peer-deps
cd ../..

docker compose build --no-cache automation
docker compose build --no-cache backend

# 5. Recreate cache
docker compose run --rm automation python build_cache.py

# 6. Generate projections
docker compose run --rm automation python pipeline.py

# 7. Start backend
docker compose up -d backend

# 8. Start frontend
cd courtdominion-app/frontend
npm run dev
```

---

### Rollback to Last Working Version

**If you broke something and need to undo:**

```bash
# See recent commits
git log --oneline -10

# Find the last working commit (e.g., abc1234)
# Reset to that commit
git reset --hard abc1234

# Rebuild everything
docker compose build --no-cache automation
docker compose build --no-cache backend

# Restart
docker compose up -d backend
```

**If you already pushed broken code:**
```bash
# DON'T force push to main
# Instead, create a revert commit
git revert HEAD
git push

# Or create a new branch with the fix
git checkout -b HOTFIX_$(date +%m%d%y)
# Fix the code
git add .
git commit -m "Fix critical bug"
git push -u origin HOTFIX_$(date +%m%d%y)
# Merge via GUI
```

---

## Common Error Messages Decoded

### `ModuleNotFoundError: No module named 'X'`

**Cause:** Missing Python package

**Fix:**
```bash
# Add to requirements.txt
echo "X>=1.0.0" >> courtdominion-app/automation/requirements.txt

# Rebuild
docker compose build --no-cache automation
```

---

### `FileNotFoundError: [Errno 2] No such file or directory: '/data/outputs/X'`

**Cause:** Missing data file or wrong path

**Fix:**
```bash
# Check if file exists
docker compose run --rm automation ls -la /data/outputs/

# If missing, generate it
docker compose run --rm automation python pipeline.py
```

---

### `JSONDecodeError: Expecting value: line 1 column 1 (char 0)`

**Cause:** Empty or corrupted JSON file

**Fix:**
```bash
# Regenerate JSON
docker compose run --rm automation python pipeline.py

# Restart backend
docker compose restart backend
```

---

### `PermissionError: [Errno 13] Permission denied`

**Cause:** File permissions wrong

**Fix:**
```bash
# Fix permissions
chmod -R 755 courtdominion-app/automation/
chmod -R 755 courtdominion-app/backend/

# Rebuild
docker compose build automation
docker compose build backend
```

---

### `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Cause:** Port 8000 already in use

**Fix:**
```bash
# Kill whatever is using port 8000
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Or stop old containers
docker compose down

# Start fresh
docker compose up -d backend
```

---

### `exec: "pytest": executable file not found in $PATH`

**Cause:** pytest not installed in container

**Fix:**
```bash
# Add to requirements.txt
echo "pytest>=7.4.3" >> courtdominion-app/automation/requirements.txt

# Rebuild
docker compose build --no-cache automation

# Try again
docker compose run --rm automation pytest tests/ -v
```

---

### `Cannot connect to the Docker daemon`

**Cause:** Docker Desktop not running

**Fix:**
```bash
# Open Docker Desktop
# Wait 60 seconds for full startup
# Check status
docker ps
```

---

### `ERROR: Service 'backend' failed to build`

**Cause:** Syntax error in Dockerfile or missing dependency

**Fix:**
```bash
# Check Dockerfile syntax
cat courtdominion-app/backend/Dockerfile

# Look for:
# - Typos
# - Missing quotes
# - Wrong paths

# Fix errors, then
docker compose build --no-cache backend
```

---

### `CORS policy: No 'Access-Control-Allow-Origin' header`

**Cause:** Backend CORS not configured

**Fix:**
```bash
# Add CORS middleware to main.py (should already exist)
# Check it's there:
docker compose run --rm backend grep -A 5 "CORSMiddleware" main.py

# If missing, add after imports:
# from fastapi.middleware.cors import CORSMiddleware
# app.add_middleware(CORSMiddleware, allow_origins=["*"])

# Restart
docker compose restart backend
```

---

## Debugging Checklist (Work Through This)

When shit's broken and you don't know why:

```
☐ 1. Is Docker Desktop running?
     docker ps

☐ 2. Is backend running?
     curl http://localhost:8000/health

☐ 3. Does cache file exist?
     docker compose run --rm automation ls -la /data/outputs/player_stats_cache.json

☐ 4. Do projections exist?
     docker compose run --rm automation ls -la /data/outputs/projections.json

☐ 5. Are tests passing?
     docker compose run --rm backend pytest tests/ -v
     docker compose run --rm automation pytest tests/ -v
     cd frontend && npm test

☐ 6. Check logs for errors
     docker compose logs backend | grep -i error
     docker compose logs automation | grep -i error

☐ 7. Is network working?
     ping -c 3 google.com
     curl -I https://stats.nba.com/

☐ 8. Are ports free?
     lsof -i :8000
     lsof -i :3000

☐ 9. Is .env file configured?
     cat .env

☐ 10. When was the last successful run?
      docker compose run --rm automation ls -lt /data/outputs/generated/ | head -5
```

If all ☐ are checked and it's still broken: [Nuclear Reset](#nuclear-reset-when-all-else-fails)

---

## Quick Fixes (Common Issues)

```bash
# Backend not responding
docker compose restart backend

# Frontend showing old data
# Hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)

# Tests failing
docker compose build --no-cache automation
docker compose build --no-cache backend

# Cache missing
docker compose run --rm automation python build_cache.py

# Projections outdated
docker compose run --rm automation python pipeline.py
docker compose restart backend

# Port conflict
docker compose down
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9
docker compose up -d backend

# Everything is fucked
# See: Nuclear Reset section
```

---

## Getting Help

### Check Documentation First

1. `DOCKER_CHEATSHEET.md` - Docker commands
2. `CODEBASE_TLDR.md` - What everything does
3. `TESTING.md` - How to run tests
4. `DEPLOYMENT_STRATEGY.md` - Production deployment
5. Backend docs: http://localhost:8000/docs

### Still Stuck?

1. Check backend logs: `docker compose logs backend | tail -100`
2. Check automation logs: `docker compose logs automation | tail -100`
3. Check browser console: F12 → Console tab
4. Search error message on Google/StackOverflow
5. Check GitHub issues: https://github.com/teebuphilip/courtdominion/issues

---

## Prevention (Avoid 2AM Debugging)

### Daily Checklist

```bash
# 1. Run tests before committing
docker compose run --rm backend pytest tests/ -v
docker compose run --rm automation pytest tests/ -v
cd frontend && npm test

# 2. Run automation to verify it works
docker compose run --rm automation python pipeline.py

# 3. Check backend responds
curl http://localhost:8000/health
curl http://localhost:8000/api/projections/top | head

# 4. Commit with clear message
git add .
git commit -m "Clear description of what you changed"
git push
```

### Weekly Maintenance

```bash
# 1. Rebuild cache
docker compose run --rm automation python build_cache.py

# 2. Clean up Docker
docker system prune -f

# 3. Update dependencies (if needed)
cd courtdominion-app/frontend
npm update
cd ../..

# 4. Check disk space
df -h
docker system df
```

---

## Useful Debugging Commands

```bash
# See all running containers
docker compose ps

# See Docker resource usage
docker stats

# See disk space
docker system df

# Follow backend logs live
docker compose logs -f backend

# Search logs for error
docker compose logs backend | grep -i error

# Check file exists
docker compose run --rm automation test -f /data/outputs/projections.json && echo "EXISTS" || echo "MISSING"

# Validate JSON
docker compose run --rm automation python -m json.tool /data/outputs/projections.json > /dev/null && echo "VALID" || echo "INVALID"

# Check Python syntax
docker compose run --rm automation python -m py_compile pipeline.py

# Interactive Python shell
docker compose run --rm automation python

# Interactive bash shell
docker compose run --rm automation bash

# Copy file from container to Mac
docker compose run --rm automation cat /data/outputs/projections.json > projections_backup.json

# Check environment variables
docker compose run --rm backend env | grep DATA_DIR
```

---

## Remember

1. **ALWAYS check logs first** - 90% of issues are in the logs
2. **Docker fixes most things** - When in doubt, `docker compose down` then `docker compose up -d backend`
3. **Tests catch bugs** - Run tests before committing
4. **Cache is expensive** - Don't delete `player_stats_cache.json` unless you have 60 minutes to rebuild
5. **Git is your friend** - Commit often, you can always rollback

---

**You got this. Breathe. Check the logs. Follow the steps. You'll fix it.**

---

**END OF 2AM DEBUGGING GUIDE**
