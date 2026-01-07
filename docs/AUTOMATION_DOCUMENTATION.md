# COURTDOMINION AUTOMATION DOCUMENTATION
## Pipeline, Cache System, and Content Generation

**Version:** 1.0  
**Date:** December 18, 2025  
**Status:** Production-Ready

---

## TABLE OF CONTENTS

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Cache System](#cache-system)
4. [Daily Pipeline](#daily-pipeline)
5. [Content Generation](#content-generation)
6. [File Descriptions](#file-descriptions)
7. [Running Locally](#running-locally)
8. [Deployment & Scheduling](#deployment--scheduling)
9. [Troubleshooting](#troubleshooting)

---

## OVERVIEW

The CourtDominion automation system is responsible for:
- **Data Collection:** Fetching NBA player stats from NBA.com
- **Cache Management:** Building and maintaining player stats cache
- **Projection Generation:** Running dbb2 projection engine
- **Insight Analysis:** Identifying waiver wire targets and value plays
- **Risk Assessment:** Calculating consistency, ceiling, floor for each player
- **Content Creation:** Generating platform-specific content (Twitter, Reddit, etc.)

**Key Features:**
- Runs completely autonomously
- Handles NBA.com rate limiting with aggressive backoff (5s → 10s → 300s)
- Incremental cache saves (every 10 players)
- Resume capability (continues from last save)
- Content generation with superstar filtering

---

## ARCHITECTURE

### High-Level Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    AUTOMATION PIPELINE                        │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Step 1: BUILD CACHE (Once per week)                         │
│  ┌─────────────────────────────────────────────┐            │
│  │  build_cache.py                              │            │
│  │  • Fetch 530 active NBA players              │            │
│  │  • Get 5-year stats from NBA.com             │            │
│  │  • Retry with exponential backoff            │            │
│  │  • Save incrementally every 10 players       │            │
│  │  • Result: 398 players cached (302KB)        │            │
│  └─────────────────────────────────────────────┘            │
│                      │                                        │
│                      ▼                                        │
│  Step 2: DAILY PIPELINE (Every day at 5am)                   │
│  ┌─────────────────────────────────────────────┐            │
│  │  pipeline.py                                  │            │
│  │  • Load cache                                 │            │
│  │  • Fetch active players list                 │            │
│  │  • Fetch injuries from ESPN                  │            │
│  │  • Generate projections (dbb2 engine)        │            │
│  │  • Generate insights                          │            │
│  │  • Calculate risk metrics                    │            │
│  │  • Validate all outputs                      │            │
│  │  • Write JSON files to /data/outputs/        │            │
│  │  • Generate content (OpenAI)                 │            │
│  └─────────────────────────────────────────────┘            │
│                      │                                        │
│                      ▼                                        │
│  Step 3: BACKEND SERVES DATA                                 │
│  ┌─────────────────────────────────────────────┐            │
│  │  Backend reads JSON files                    │            │
│  │  • players.json                              │            │
│  │  • projections.json                          │            │
│  │  • insights.json                             │            │
│  │  • risk.json                                 │            │
│  │  • injuries.json                             │            │
│  └─────────────────────────────────────────────┘            │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## CACHE SYSTEM

### Purpose

The cache system solves NBA.com's aggressive rate limiting by:
1. Fetching all player stats ONCE per week
2. Storing them locally
3. Daily pipeline reads from cache (instant, no API calls)

**Result:** 40x faster automation (22 min → 1 min)

---

### Cache Builder: `build_cache.py`

**What it does:**
1. Fetches list of 530 active NBA players
2. For each player, gets 5-year career averages from NBA.com
3. Saves player stats to cache file
4. Handles rate limiting with aggressive backoff

**Retry Strategy:**

```
Attempt 1: Fetch (2-4s random delay)
  ↓ (fails)
Attempt 2: Wait 5s → Retry
  ↓ (fails)
Attempt 3: Wait 10s → Retry
  ↓ (fails)
Attempt 4: Wait 300s (5 minutes!) → Retry
  ↓ (succeeds)
```

**Incremental Saves:**
- Saves cache every 10 players
- Maximum loss if interrupted: 9 players
- Resume capability: Skips already-cached players on restart

**Output:**
- File: `/data/outputs/player_stats_cache.json`
- Size: ~302KB
- Players: 398 (with sufficient data)
- Skipped: ~132 (rookies, insufficient data)

**Example Cache Entry:**

```json
{
  "metadata": {
    "cached_at": "2025-12-17T17:06:25.960359",
    "player_count": 398
  },
  "players": {
    "203507": {
      "player_id": "203507",
      "name": "Giannis Antetokounmpo",
      "team": "MIL",
      "position": "Forward",
      "age": 29,
      "minutes": 34.5,
      "points": 28.2,
      "rebounds": 11.1,
      "assists": 5.8,
      "steals": 1.2,
      "blocks": 1.4,
      "field_goals_made": 10.3,
      "field_goals_attempted": 17.6,
      "fg_pct": 0.583,
      "three_pointers_made": 0.8,
      "three_pointers_attempted": 2.9,
      "free_throws_made": 5.9,
      "free_throws_attempted": 9.1,
      "ft_pct": 0.652,
      "turnovers": 3.1,
      "confidence": 0.95,
      "cached_at": "2025-12-17T17:06:21.950428"
    }
  }
}
```

**Running Cache Builder:**

```bash
# Local (takes 30-60 minutes)
docker compose run --rm automation python build_cache.py

# Output
[1/530] Precious Achiuwa (ID: 1630173)... ✓
[2/530] Steven Adams (ID: 203500)... ✓
[3/530] Bam Adebayo (ID: 1628389)... ✓
...
    💾 Progress saved (10 players cached)
[11/530] Cole Anthony (ID: 1630175)... ✓
...
[340/530] Aaron Nesmith (ID: 203956)... ⚠ (retry in 5s) ⚠ (retry in 10s) ⚠ (retry in 5min) ✓
...
✓ Cache build complete: 398 players cached
```

**Schedule:**
- **Initial:** Run once to build cache
- **Maintenance:** Weekly rebuild (Sunday 2am)
- **Emergency:** Rebuild if cache corrupted

---

## DAILY PIPELINE

### Pipeline Orchestrator: `pipeline.py`

**What it does:**
1. Loads player stats from cache
2. Fetches active players list (530 players)
3. Fetches injuries from ESPN
4. Generates projections using dbb2 engine
5. Generates insights (waiver wire targets)
6. Calculates risk metrics
7. Validates all outputs
8. Writes JSON files
9. Generates content for 5 platforms

**Runtime:** 1-2 minutes (using cache)

**Steps in Detail:**

#### Step 1: Load Cache
```python
# Reads player_stats_cache.json
cache = load_cache()
# Result: 398 players with 5-year averages
```

#### Step 2: Fetch Active Players
```python
# Gets current NBA roster (530 players)
players = fetch_real_players()
# Includes rookies, recent signups, etc.
```

#### Step 3: Fetch Injuries
```python
# Gets injury data from ESPN API
injuries = fetch_real_injuries()
# Result: ~47 injured players
```

#### Step 4: Generate Projections
```python
# dbb2 projection engine (1500+ lines)
projections = generate_projections(players, cache)
# Uses 5-year averages to project today's performance
# Result: 398 projections
```

#### Step 5: Generate Insights
```python
# Identifies waiver wire targets, sleepers
insights = generate_insights(projections)
# Calculates value scores, recommendations
# Result: 398 insights
```

#### Step 6: Calculate Risk Metrics
```python
# Consistency, ceiling, floor analysis
risk = calculate_risk(projections)
# Result: 398 risk assessments
```

#### Step 7: Validate Outputs
```python
# Ensures all data is valid JSON
# Checks schema compliance
# Verifies no missing fields
```

#### Step 8: Write JSON Files
```python
# /data/outputs/players.json (69KB)
# /data/outputs/projections.json (212KB)
# /data/outputs/insights.json (59KB)
# /data/outputs/risk.json (42KB)
# /data/outputs/injuries.json (5KB)
```

#### Step 9: Generate Content
```python
# Calls OpenAI API
# Creates Twitter, Reddit, Discord, LinkedIn, Email content
# Filters out superstars (uses blacklist)
# Result: 5 text files + manifest
```

**Running Daily Pipeline:**

```bash
# Local
docker compose run --rm automation python pipeline.py

# Output
======================================================================
  STARTING AUTOMATION PIPELINE - 2025-12-18
======================================================================

Step 1: Load cache...
Loaded cache: 398 players (cached at 2025-12-17T17:06:25.960359)
✓ Cache loaded

Step 2: Fetch active players...
✓ Fetched 530 active NBA players

Step 3: Fetch injuries...
✓ Fetched 47 injuries from ESPN

Step 4: Generate projections...
✓ Generated 398 real projections (DBB2 engine)

Step 5: Generate insights...
✓ Generated 398 insights

Step 6: Calculate risk metrics...
✓ Generated 398 risk assessments

Step 7: Validate outputs...
✓ All outputs valid

Step 8: Write outputs...
✓ Successfully wrote players.json | size_bytes=68976
✓ Successfully wrote projections.json | size_bytes=211948
✓ Successfully wrote insights.json | size_bytes=59319
✓ Successfully wrote risk.json | size_bytes=41591
✓ Successfully wrote injuries.json | size_bytes=4532
✓ All outputs written successfully

Step 9: Generate content...
✓ Loaded blacklist: 20 superstars excluded from content
✓ Filtered out 20 superstars, focusing on 378 deep sleepers
✓ Narrative: Grab these waiver wire gems before your league does...
✓ twitter: 956 chars → twitter_draft.txt
✓ reddit: 2154 chars → reddit_draft.txt
✓ discord: 1212 chars → discord_draft.txt
✓ linkedin: 1344 chars → linkedin_draft.txt
✓ email: 2043 chars → email_draft.txt
✓ Content generated successfully

======================================================================
  PIPELINE COMPLETED SUCCESSFULLY - REAL NBA DATA + CONTENT
======================================================================

Total time: 1m 24s
```

**Schedule:**
- **Development:** Run manually when needed
- **Production:** Daily at 5am EST (via GitHub Actions)

---

## CONTENT GENERATION

### Content Generator: `generator.py`

**What it does:**
1. Filters out superstars (Jokić, Giannis, etc.)
2. Identifies top waiver wire targets
3. Calls OpenAI API to generate content
4. Creates platform-specific versions

**Superstar Blacklist:**

File: `superstar_blacklist.txt`

```
Nikola Jokić
Luka Dončić
Giannis Antetokounmpo
Victor Wembanyama
LeBron James
Stephen Curry
Kevin Durant
Anthony Davis
Joel Embiid
Shai Gilgeous-Alexander
Jayson Tatum
Damian Lillard
Kawhi Leonard
Jimmy Butler
Kyrie Irving
Donovan Mitchell
Devin Booker
Trae Young
Anthony Edwards
Tyrese Haliburton
```

**Why Filter Superstars?**
- Everyone already knows about them
- Owned in 100% of leagues
- Not waiver wire targets
- Content should focus on actionable picks

**Content Flow:**

```
1. Load blacklist
   ↓
2. Filter projections (remove superstars)
   → 398 players → 378 actionable targets
   ↓
3. Select top performers (from filtered list)
   → Top 5 by fantasy points
   ↓
4. Select value plays (high upside)
   → Top 3 by fantasy points / consistency ratio
   ↓
5. Generate narrative
   → OpenAI creates 2-3 sentence hook
   ↓
6. Generate platform content
   → Twitter: 4-tweet thread (280 chars each)
   → Reddit: Post with analysis (~300 words)
   → Discord: Community message (~200 words)
   → LinkedIn: Professional post (~250 words)
   → Email: Newsletter (~300 words)
   ↓
7. Save all content to /data/outputs/generated/YYYY-MM-DD/
```

**Example Generated Content:**

**Twitter:**
```
1/ 🚨 #FantasyBasketball Alert! Don't sleep on these waiver wire gems 
today! Tyrese Maxey is projecting 38.2 FP with elite efficiency. Grab him 
NOW before your league catches on! #NBA

2/ Deni Avdija is flying under the radar with 32.1 FP projected. Strong 
all-around game with 4+ games this week. Perfect streaming candidate for 
rebounds and assists! 💎

3/ Jalen Williams looking like a league winner at 35.8 FP. High usage, 
efficient scoring, and contributing across the board. This is your chance 
to make a championship move! 🏆

4/ The clock is ticking! ⏰ These opportunities won't last. Make your moves 
now and dominate your league. Fortune favors the bold! #FantasyBasketball 
🔥
```

**OpenAI Configuration:**

```python
Model: gpt-4 (or gpt-3.5-turbo for cost savings)
Temperature: 0.7 (creative but consistent)
Max Tokens: 600 per platform
System Prompt: "You are a fantasy basketball expert who writes engaging, 
actionable content focusing on waiver wire targets and streaming 
candidates. Never mention obvious superstars."
```

**Cost:**
- GPT-4: ~$0.20 per run (5 platforms)
- Daily: $6/month
- GPT-3.5-turbo: ~$0.01 per run
- Daily: $0.30/month

**Generated Files:**

```
/data/outputs/generated/2025-12-18/
├── twitter_draft.txt      (956 bytes)
├── reddit_draft.txt       (2154 bytes)
├── discord_draft.txt      (1212 bytes)
├── linkedin_draft.txt     (1344 bytes)
├── email_draft.txt        (2043 bytes)
├── rationale.json         (858 bytes)
└── manifest.json          (957 bytes)
```

**Usage:**
1. Run pipeline (generates content)
2. Check `/data/outputs/generated/YYYY-MM-DD/`
3. Copy content to respective platforms
4. Post manually (or automate with APIs in future)

---

## FILE DESCRIPTIONS

### Core Files

| File | Purpose | Lines | Runtime |
|------|---------|-------|---------|
| `build_cache.py` | Build player stats cache | 300 | 30-60 min |
| `pipeline.py` | Main automation orchestrator | 400 | 1-2 min |
| `dbb2_projections.py` | Projection engine (reads cache) | 200 | <1 sec |
| `generator.py` | Content generation with OpenAI | 400 | 30-60 sec |
| `fetch_real_players.py` | Get active NBA players | 150 | 5 sec |
| `fetch_real_injuries.py` | Get ESPN injuries | 120 | 5 sec |
| `insights_generator.py` | Waiver wire analysis | 200 | 2 sec |
| `risk_metrics.py` | Risk assessment | 180 | 2 sec |
| `projection_generator.py` | Wrapper for dbb2 | 150 | <1 sec |

### Supporting Files

| File | Purpose |
|------|---------|
| `superstar_blacklist.txt` | Players to exclude from content |
| `requirements.txt` | Python dependencies |
| `Dockerfile` | Container definition |
| `schemas/*.json` | JSON validation schemas |
| `utils/file_writer.py` | JSON file writing |
| `utils/validators.py` | Data validation |
| `utils/logger.py` | Logging utilities |

---

## RUNNING LOCALLY

### Prerequisites

```bash
# 1. Docker installed
docker --version

# 2. OpenAI API key in .env
echo "OPENAI_API_KEY=sk-..." > .env

# 3. Backend running (for data sharing)
docker compose up -d backend
```

### Build Cache (First Time Only)

```bash
# Takes 30-60 minutes
docker compose run --rm automation python build_cache.py

# Watch progress
docker compose logs -f automation

# Verify cache created
docker compose run --rm automation ls -la /data/outputs/player_stats_cache.json
```

### Run Daily Pipeline

```bash
# Takes 1-2 minutes
docker compose run --rm automation python pipeline.py

# Check outputs
docker compose run --rm automation ls -la /data/outputs/
docker compose run --rm automation ls -la /data/outputs/generated/$(date +%Y-%m-%d)/
```

### View Generated Content

```bash
# Today's content
docker compose run --rm automation cat /data/outputs/generated/$(date +%Y-%m-%d)/twitter_draft.txt

# Or on your Mac (if using local volumes)
cat data/outputs/generated/$(date +%Y-%m-%d)/twitter_draft.txt
```

### Rebuild Container (After Code Changes)

```bash
# Clean rebuild
docker compose build --no-cache automation

# Test
docker compose run --rm automation python pipeline.py
```

---

## DEPLOYMENT & SCHEDULING

### Local Development

**Manual Execution:**
```bash
# Run when needed
docker compose run --rm automation python pipeline.py
```

**Scheduled (Cron on Mac):**
```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 5am)
0 5 * * * cd ~/Downloads/courtdominion && docker compose run --rm automation python pipeline.py
```

---

### Production (GitHub Actions)

**File:** `.github/workflows/daily-automation.yml`

```yaml
name: Daily Automation

on:
  schedule:
    - cron: '0 10 * * *'  # 5am EST = 10am UTC
  workflow_dispatch:  # Manual trigger

jobs:
  run-pipeline:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd courtdominion-app/automation
          pip install -r requirements.txt
      
      - name: Run pipeline
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          cd courtdominion-app/automation
          python pipeline.py
      
      - name: Upload outputs to Railway
        run: |
          # Deploy updated JSON files to Railway
          railway up
```

**Weekly Cache Rebuild:** `.github/workflows/build-cache.yml`

```yaml
name: Weekly Cache Rebuild

on:
  schedule:
    - cron: '0 7 * * 0'  # Sunday 2am EST = 7am UTC
  workflow_dispatch:

jobs:
  rebuild-cache:
    runs-on: ubuntu-latest
    timeout-minutes: 90
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd courtdominion-app/automation
          pip install -r requirements.txt
      
      - name: Build cache
        run: |
          cd courtdominion-app/automation
          python build_cache.py
      
      - name: Upload cache to Railway
        run: |
          railway up
```

---

## TROUBLESHOOTING

### Issue: "Cache file not found"

**Symptom:**
```
WARNING: Cache file not found: /data/outputs/player_stats_cache.json
Generated 0 projections
```

**Fix:**
```bash
# Build cache first
docker compose run --rm automation python build_cache.py
```

---

### Issue: Rate Limited by NBA.com

**Symptom:**
```
[340/530] Aaron Nesmith... ⚠ (retry in 5s) ⚠ (retry in 10s) ⚠ (retry in 5min) ✗ (skipped)
```

**Fix:**
- Wait for cache build to complete (handles this automatically)
- Missed players will be caught in next rebuild
- Or run 2nd pass retry script (future feature)

---

### Issue: OpenAI API Key Not Set

**Symptom:**
```
⚠️  WARNING: OPENAI_API_KEY not set!
Content generation will use fallback templates
```

**Fix:**
```bash
# Set in .env file
echo "OPENAI_API_KEY=sk-your-key-here" >> .env

# Restart container
docker compose restart automation
```

---

### Issue: Content Mentions Superstars

**Symptom:**
Content talks about Jokić, Giannis, etc.

**Fix:**
```bash
# Check blacklist file exists
docker compose run --rm automation ls -la /app/superstar_blacklist.txt

# If missing, add player names to blacklist
# Rebuild container
docker compose build --no-cache automation
```

---

### Issue: Pipeline Takes Too Long

**Symptom:**
Pipeline runs for 20+ minutes instead of 1-2 minutes

**Cause:** Not using cache, hitting NBA.com directly

**Fix:**
- Ensure cache file exists
- Check `dbb2_projections.py` uses cache path

---

## MONITORING

### Check Last Run

```bash
# View pipeline logs
docker compose logs automation | tail -100

# Check file timestamps
docker compose run --rm automation ls -la /data/outputs/
```

### Verify Outputs

```bash
# Count projections
docker compose run --rm automation python -c "import json; print(len(json.load(open('/data/outputs/projections.json'))['projections']))"

# Expected: 398
```

### Health Check

```bash
# Quick validation
docker compose run --rm automation python -c "
import json
from pathlib import Path

files = ['players.json', 'projections.json', 'insights.json', 'risk.json', 'injuries.json']
for f in files:
    path = Path(f'/data/outputs/{f}')
    if path.exists():
        size = path.stat().st_size
        print(f'✓ {f}: {size} bytes')
    else:
        print(f'✗ {f}: MISSING')
"
```

---

## PERFORMANCE METRICS

| Metric | Value |
|--------|-------|
| Cache build time | 30-60 minutes |
| Daily pipeline time | 1-2 minutes |
| Players cached | 398 |
| Projections generated | 398 |
| Content pieces | 5 platforms |
| OpenAI API calls | 6 per run |
| Total files created | 11 JSON + 7 content files |
| Disk usage | ~700KB per day |

---

## FUTURE ENHANCEMENTS

### Planned Features

1. **2nd Pass Retry System**
   - Catches veterans missed due to rate limiting
   - Runs 1 hour after initial build
   - Estimated: 5-10% coverage improvement

2. **Rookie Comparables**
   - Maps rookies to veteran comparisons
   - Example: Cooper Flagg → Anthony Davis (75%)
   - Enables rookie projections

3. **Incremental Cache Updates**
   - Only update players who played yesterday
   - Reduces build time from 30 min to 2-5 min
   - Keeps cache always fresh

4. **Automated Content Posting**
   - Direct Twitter API integration
   - Reddit bot posting
   - Discord webhook
   - Email list management

---

**END OF AUTOMATION DOCUMENTATION**

**Status:** Production-ready automation running successfully  
**Next:** Deploy GitHub Actions for daily scheduling
