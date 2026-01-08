# CourtDominion Code Breakdown (TL;DR)
## For When You Forgot What The Hell You Built

---

## What Is This?

**CourtDominion** = NBA fantasy basketball projections that update daily with real data from the NBA API.

---

## The Big Picture (3 Parts)

```
┌─────────────────────────────────────────────────────────┐
│  1. AUTOMATION (Python)                                 │
│  Runs daily, fetches NBA data, makes projections        │
│  Output: JSON files with player stats                   │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  2. BACKEND (FastAPI/Python)                            │
│  API server that reads JSON files, serves to frontend   │
│  Runs 24/7 on port 8000                                 │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│  3. FRONTEND (React/JavaScript)                         │
│  Website UI that shows projections to users             │
│  Runs on port 3000, talks to backend                    │
└─────────────────────────────────────────────────────────┘
```

**Data Flow:**
NBA API → Automation → JSON files → Backend → Frontend → User's Browser

---

## Directory Structure (What's Where)

```
courtdominion/
├── courtdominion-app/
│   ├── automation/          ← Python scripts that fetch NBA data
│   ├── backend/             ← FastAPI server (the API)
│   └── frontend/            ← React website (the UI)
│
├── docs/                    ← All documentation
├── DOCKER_CHEATSHEET.md     ← Your 2am best friend
├── TESTING.md               ← How to run tests
└── .env                     ← Secret keys (NEVER commit this)
```

---

## Part 1: AUTOMATION (The Data Fetcher)

**Location:** `courtdominion-app/automation/`

### What It Does
Runs daily to fetch fresh NBA data and generate projections.

### Key Files

| File | What It Does | When You Need It |
|------|--------------|------------------|
| `pipeline.py` | **MAIN SCRIPT** - Runs everything in order | Run this daily |
| `build_cache.py` | Fetches NBA stats for all players, saves to cache | Run once a week |
| `dbb2_projections.py` | Makes fantasy projections using ML | Rarely touch this |
| `generator.py` | Writes Twitter/blog/newsletter content | Customize content here |
| `rookie_comparables.csv` | Maps rookies to similar NBA players | Add new rookies here |
| `requirements.txt` | Python packages needed | Add new packages here |
| `Dockerfile` | Recipe to build automation Docker image | Touch only if adding system dependencies |

### How to Run (from project root)

```bash
# Build cache (once per week or when new season starts)
docker compose run --rm automation python build_cache.py

# Run daily automation (generates projections + content)
docker compose run --rm automation python pipeline.py

# Check what was generated
docker compose run --rm automation ls -la /data/outputs/generated/
```

### What Gets Generated

- `player_stats_cache.json` - All NBA player stats (huge file, 30-60 min to build)
- `projections.json` - Today's fantasy projections for all players
- `generated/YYYY-MM-DD/twitter_draft.txt` - Twitter thread content
- `generated/YYYY-MM-DD/blog_draft.txt` - Blog post content
- `generated/YYYY-MM-DD/newsletter_draft.txt` - Email newsletter content

---

## Part 2: BACKEND (The API Server)

**Location:** `courtdominion-app/backend/`

### What It Does
Serves player data and projections to the frontend via HTTP endpoints.

### Key Files

| File | What It Does | When You Need It |
|------|--------------|------------------|
| `main.py` | **MAIN API SERVER** - All endpoints defined here | Add new endpoints here |
| `requirements.txt` | Python packages for backend | Add new packages here |
| `Dockerfile` | Recipe to build backend Docker image | Rarely touch |
| `tests/` | Automated tests (21 tests) | Run after code changes |

### How to Run

```bash
# Start backend server (runs in background)
docker compose up -d backend

# Check if it's running
curl http://localhost:8000/health

# View logs
docker compose logs -f backend

# Stop server
docker compose down
```

### API Endpoints (What You Built)

**Public Endpoints:**
- `GET /health` - Is server alive?
- `GET /api/players` - List all NBA players
- `GET /api/players/{player_id}` - Get one player's details
- `GET /api/projections/top` - Top 50 players by fantasy points
- `GET /api/content/latest` - Today's generated content (Twitter/blog/newsletter)

**Internal Endpoint (for microservices):**
- `GET /api/internal/baseline-projections` - Protected by API key

### Environment Variables

Set these in `.env` file:
```bash
DATA_DIR=/data/outputs              # Where JSON files live
INTERNAL_API_KEY=your-secret-key    # For microservices
LOG_LEVEL=INFO                      # DEBUG, INFO, WARNING, ERROR
```

---

## Part 3: FRONTEND (The Website)

**Location:** `courtdominion-app/frontend/`

### What It Does
React website that shows projections in a pretty UI.

### Directory Structure

```
frontend/
├── src/
│   ├── components/          ← Reusable UI pieces
│   │   ├── home/           ← Homepage sections
│   │   ├── player/         ← Player cards/lists
│   │   ├── projections/    ← Projection tables
│   │   └── layout/         ← Header, footer, navigation
│   │
│   ├── pages/              ← Full page components
│   │   ├── HomePage.jsx    ← Landing page
│   │   ├── ProjectionsPage.jsx  ← Top 50 list
│   │   └── PlayerPage.jsx  ← Individual player view
│   │
│   ├── utils/              ← Helper functions
│   │   ├── api.js         ← Backend API calls
│   │   ├── formatters.js  ← Number/percentage formatting
│   │   └── constants.js   ← App-wide constants
│   │
│   ├── App.jsx             ← Main app component (routes)
│   └── main.jsx            ← Entry point
│
├── package.json            ← JavaScript dependencies
├── vite.config.js          ← Build tool config
└── tailwind.config.js      ← CSS styling config
```

### How to Run

```bash
# Install dependencies (first time only)
cd courtdominion-app/frontend
npm install --legacy-peer-deps

# Start dev server
npm run dev

# Build for production
npm run build

# Run tests
npm test
```

### Key Components

| Component | What It Shows | File |
|-----------|---------------|------|
| `HomePage` | Landing page with hero + email capture | `pages/HomePage.jsx` |
| `ProjectionsPage` | Top 50 players table | `pages/ProjectionsPage.jsx` |
| `PlayerPage` | Individual player details | `pages/PlayerPage.jsx` |
| `PlayerCard` | Single player card with stats | `components/player/PlayerCard.jsx` |
| `RiskBadge` | Injury risk badge (LOW/MEDIUM/HIGH) | `components/projections/RiskBadge.jsx` |
| `EmailCapture` | Newsletter signup form (not functional yet) | `components/home/EmailCapture.jsx` |

### How Frontend Talks to Backend

**File:** `src/utils/api.js`

```javascript
// Example: Fetch top projections
const response = await fetch('http://localhost:8000/api/projections/top')
const data = await response.json()
```

All API calls go through functions in `api.js`:
- `fetchPlayers()` - Get all players
- `fetchPlayer(id)` - Get one player
- `fetchTopProjections()` - Get top 50
- `fetchLatestContent()` - Get generated content

---

## How Data Flows (The Whole Story)

### Daily Automation Flow

```
1. NBA API
   ↓ (automation fetches stats)
2. player_stats_cache.json
   ↓ (ML model processes)
3. projections.json
   ↓ (generator creates content)
4. generated/YYYY-MM-DD/*.txt files
```

### User Request Flow

```
1. User opens browser → http://localhost:3000
2. Frontend requests data → http://localhost:8000/api/projections/top
3. Backend reads file → /data/outputs/projections.json
4. Backend sends JSON → Frontend
5. Frontend renders UI → User sees pretty tables
```

---

## Key Concepts (Explained Like You're 5)

### Docker
- **What:** Packages your code + dependencies into a container
- **Why:** Works the same on your Mac, production server, anywhere
- **Commands:** See `DOCKER_CHEATSHEET.md`

### FastAPI
- **What:** Python framework for building APIs
- **Why:** Fast, automatic documentation, easy to use
- **Docs:** http://localhost:8000/docs (when backend is running)

### React
- **What:** JavaScript library for building UIs
- **Why:** Components are reusable, state management is easy
- **Learn:** Each `.jsx` file is a component (like a LEGO brick)

### Vitest
- **What:** Testing framework for JavaScript
- **Why:** Make sure UI works before deploying
- **Run:** `npm test` in frontend directory

### pytest
- **What:** Testing framework for Python
- **Why:** Make sure backend/automation works
- **Run:** See `TESTING.md`

### JSON
- **What:** Text format for storing data
- **Why:** Easy for computers to read/write, human-readable
- **Example:** `{"player_name": "LeBron James", "points": 25.7}`

### API
- **What:** A way for programs to talk to each other
- **Why:** Frontend asks backend for data via HTTP requests
- **Example:** `GET /api/players` returns list of players

### Machine Learning (scikit-learn)
- **What:** Code that learns patterns from data
- **Why:** Predicts future fantasy points based on past stats
- **File:** `dbb2_projections.py` (you don't need to touch this much)

---

## Common Files You'll Actually Touch

### When Adding a New Rookie

**File:** `courtdominion-app/automation/rookie_comparables.csv`

```csv
rookie_name,comparable_player,similarity_score
Cooper Flagg,Anthony Davis,0.84
```

Add a line, save, done.

---

### When Changing Content Generation

**File:** `courtdominion-app/automation/generator.py`

Lines 50-150: Twitter thread templates
Lines 200-300: Blog post templates
Lines 350-450: Newsletter templates

Edit the f-string templates to change wording.

---

### When Adding a New API Endpoint

**File:** `courtdominion-app/backend/main.py`

```python
@app.get("/api/your-new-endpoint")
async def your_endpoint():
    return {"message": "Hello"}
```

Add function, restart backend, test at http://localhost:8000/docs

---

### When Styling the Frontend

**File:** `courtdominion-app/frontend/tailwind.config.js`

Change colors, fonts, spacing here.

**Files:** Any `.jsx` file in `src/components/` or `src/pages/`

Tailwind classes in `className=""` props control styling.

---

## Files You Should NEVER Touch

| File | Why Not | What Happens If You Do |
|------|---------|------------------------|
| `.git/` | Git internals | Break entire repo |
| `node_modules/` | Installed packages | Delete = re-install needed |
| `__pycache__/` | Python bytecode | Auto-generated, ignored |
| `dist/` | Build output | Auto-generated |
| `venv/` | Python virtual env | Delete = re-create needed |

---

## Files You Should NEVER Commit to Git

**File:** `.gitignore` already handles this, but FYI:

- `.env` - Contains secret API keys
- `node_modules/` - Huge, reinstall with `npm install`
- `__pycache__/` - Python compiled files
- `dist/` - Build output
- `*.log` - Log files
- `.DS_Store` - Mac system file

---

## Testing (The Safety Net)

### Backend Tests (21 tests)
```bash
docker compose run --rm backend pytest tests/ -v
```

### Frontend Tests (15 tests)
```bash
cd courtdominion-app/frontend
npm test
```

### Automation Tests (11 tests)
```bash
docker compose run --rm automation pytest tests/ -v
```

**When to run:** Before committing code, after bug fixes, before deploying.

---

## Environment Variables Cheat Sheet

**File:** `.env` (in project root)

```bash
# Backend
DATA_DIR=/data/outputs
INTERNAL_API_KEY=super-secret-key-change-me
LOG_LEVEL=INFO

# Frontend (if needed)
VITE_API_URL=http://localhost:8000
```

**How to use in code:**

Python:
```python
import os
api_key = os.environ.get('INTERNAL_API_KEY')
```

JavaScript:
```javascript
const apiUrl = import.meta.env.VITE_API_URL
```

---

## Quick Command Reference

### Most Used Commands

```bash
# Start backend
docker compose up -d backend

# Run automation
docker compose run --rm automation python pipeline.py

# Start frontend
cd courtdominion-app/frontend && npm run dev

# View backend logs
docker compose logs -f backend

# Stop everything
docker compose down

# Rebuild after code changes
docker compose build automation
docker compose build backend

# Run all tests
docker compose run --rm backend pytest tests/ -v
docker compose run --rm automation pytest tests/ -v
cd courtdominion-app/frontend && npm test
```

---

## What Each Docker Service Does

**File:** `docker-compose.yml`

- **backend**: FastAPI server on port 8000
- **automation**: Python scripts (run on-demand, not 24/7)
- **shared-data**: Volume where JSON files live (shared between backend and automation)

---

## Dependency Files (Where Packages Are Listed)

| File | What It's For | How to Install |
|------|---------------|----------------|
| `automation/requirements.txt` | Python packages for automation | `docker compose build automation` |
| `backend/requirements.txt` | Python packages for backend | `docker compose build backend` |
| `frontend/package.json` | JavaScript packages for frontend | `npm install --legacy-peer-deps` |

---

## The Data Files (What Lives Where)

### Inside Docker Volumes

```
/data/outputs/
├── player_stats_cache.json      ← All NBA stats (big file)
├── projections.json             ← Today's projections
└── generated/
    └── 2026-01-08/
        ├── twitter_draft.txt
        ├── blog_draft.txt
        └── newsletter_draft.txt
```

**How to access:**
```bash
# List files
docker compose run --rm automation ls -la /data/outputs/

# Read a file
docker compose run --rm automation cat /data/outputs/projections.json
```

---

## Git Workflow (How You Work)

1. Make code changes
2. Run tests to verify it works
3. Create a branch: `git checkout -b FEATURE_NAME_010726`
4. Commit: `git add . && git commit -m "Add feature X"`
5. Push: `git push -u origin FEATURE_NAME_010726`
6. Merge on GitHub GUI
7. Delete branch after merge

**Branch naming:** `DESCRIPTION_MMDDYY` (e.g., `ROOKIE_FIX_010726`)

---

## URLs When Running Locally

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Backend Docs: http://localhost:8000/docs (Swagger UI)
- Backend Health: http://localhost:8000/health

---

## When Something Breaks

**See:** `DEBUGGING_GUIDE.md` (your 2am lifeline)

---

## Learning Resources

### Backend (FastAPI)
- Official Docs: https://fastapi.tiangolo.com/
- Your API Docs: http://localhost:8000/docs (auto-generated)

### Frontend (React)
- Official Docs: https://react.dev/
- Tailwind CSS: https://tailwindcss.com/docs

### Docker
- Your Cheat Sheet: `DOCKER_CHEATSHEET.md`
- Official Docs: https://docs.docker.com/

### Testing
- pytest: https://docs.pytest.org/
- Vitest: https://vitest.dev/
- Your Guide: `TESTING.md`

---

## Most Important Files (The MVP)

1. **Automation:** `pipeline.py` - Runs daily automation
2. **Backend:** `main.py` - API server
3. **Frontend:** `App.jsx` - Main app component
4. **Data:** `projections.json` - The golden file everyone reads
5. **Docs:** `DEBUGGING_GUIDE.md` - Your 2am savior

---

## Summary (TL;DR of the TL;DR)

**What it is:** NBA fantasy projections app

**How it works:**
1. Automation fetches NBA data daily
2. Backend serves data via API
3. Frontend shows pretty UI to users

**How to run:**
1. `docker compose up -d backend` (starts API)
2. `docker compose run --rm automation python pipeline.py` (generates projections)
3. `cd frontend && npm run dev` (starts website)

**How to test:**
- Backend: `docker compose run --rm backend pytest tests/ -v`
- Frontend: `cd frontend && npm test`
- Automation: `docker compose run --rm automation pytest tests/ -v`

**When stuck:**
- 2am debugging: `DEBUGGING_GUIDE.md`
- Docker commands: `DOCKER_CHEATSHEET.md`
- API endpoints: http://localhost:8000/docs
- Tests: `TESTING.md`

---

**END OF CODEBASE TL;DR**
