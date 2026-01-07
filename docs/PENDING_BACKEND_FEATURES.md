# COURTDOMINION - PENDING BACKEND FEATURES

**Date:** January 2026

---

## TL;DR

**4 backend features need work before microservices:**
1. Content endpoint (deploy existing code)
2. Rookie comparables (integrate CSV)
3. 2nd pass retry (integrate existing code)
4. Internal API endpoint (new code - CRITICAL)

**Time:** 1 day total

---

## FEATURE 1: CONTENT ENDPOINT

### Status
**Built:** ✅  
**Deployed:** ❌  
**Priority:** Low

### What It Is
Dynamic content API for marketing copy

### Files
- `backend/routers/content.py` (exists)
- `backend/data/content.json` (exists)

### What's Needed
```python
# In backend/main.py
from routers import content  # Add this import
app.include_router(content.router)  # Add this line
```

### Deploy
```bash
git add backend/routers/content.py backend/data/content.json
git commit -m "Add content endpoint"
git push
# Railway auto-deploys
```

### Test
```bash
curl https://courtdominion.up.railway.app/api/content
```

**Time:** 15 minutes

---

## FEATURE 2: ROOKIE COMPARABLES

### Status
**CSV Built:** ✅  
**Integrated:** ❌  
**Priority:** Low (only ~8 rookies matter)

### What It Is
Project rookies using veteran comparisons

### Files
- `automation/rookie_comparables.csv` (exists)

### What's Needed
```python
# In automation/dbb2_projections.py

import pandas as pd

def get_rookie_comparable(player_name):
    """Get comparable veteran for rookie"""
    df = pd.read_csv('automation/rookie_comparables.csv')
    match = df[df['rookie_name'] == player_name]
    
    if match.empty:
        return None
    
    comparable_name = match.iloc[0]['comparable_player']
    return get_player_projection(comparable_name)

# In calculate_projection() function
if player.is_rookie:
    comparable = get_rookie_comparable(player.name)
    if comparable:
        return comparable  # Use comparable's stats
```

### CSV Format
```csv
rookie_name,comparable_player,similarity_score
Victor Wembanyama,Kevin Durant,0.82
Scoot Henderson,De'Aaron Fox,0.75
```

**Time:** 1-2 hours

---

## FEATURE 3: 2ND PASS RETRY LOGIC

### Status
**Code Complete:** ✅  
**Integrated:** ❌  
**Priority:** Medium (improves data quality)

### What It Is
Retry failed NBA.com API calls with exponential backoff

### Files
- `automation/retry_failed_players.py` (exists)

### What's Needed
```bash
# In automation/pipeline.sh

python automation/build_cache.py
python automation/retry_failed_players.py  # ADD THIS LINE
python automation/dbb2_projections.py
```

### How It Works
```
build_cache.py runs
  ↓
Some players fail (API timeout, 404, etc)
  ↓
retry_failed_players.py detects failures
  ↓
Retries with exponential backoff: 1s, 2s, 4s, 8s, 16s
  ↓
Updates cache with successful retries
```

### Test
```bash
# Run manually first
python automation/retry_failed_players.py --dry-run

# Check output
cat logs/retry_results.log
```

**Time:** 1-2 hours

---

## FEATURE 4: INTERNAL API ENDPOINT (CRITICAL)

### Status
**Built:** ❌  
**Priority:** CRITICAL (needed for Features 1-7)

### What It Is
Private API endpoint for microservices to consume Phase 1 data

### What's Needed

**Create new file:** `backend/routers/internal.py`

```python
from fastapi import APIRouter, Header, HTTPException
from typing import List
import os

router = APIRouter()

# Secret API key (Railway environment variable)
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")

@router.get("/api/internal/baseline-projections")
async def get_baseline_projections(
    x_api_key: str = Header(...)
):
    """
    Internal API for microservices
    
    Returns all player projections + historical data
    Used by Features 1-7 to get baseline data
    """
    
    # Validate API key
    if x_api_key != INTERNAL_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    # Get all players (use existing function)
    players = get_all_players_with_projections()
    
    # Format response
    return {
        "players": [
            {
                "player_id": p.player_id,
                "name": p.name,
                "team": p.team,
                "position": p.position,
                "age": p.age,
                
                # Projections
                "fantasy_points": p.fantasy_points,
                "points": p.points,
                "rebounds": p.rebounds,
                "assists": p.assists,
                "steals": p.steals,
                "blocks": p.blocks,
                "turnovers": p.turnovers,
                "three_pointers": p.three_pm,
                "fg_pct": p.fg_pct,
                "ft_pct": p.ft_pct,
                "minutes": p.minutes,
                
                # Historical data (for risk modeling)
                "games_played_3yr": p.games_played_history,
                "injury_history": {
                    "total_games_missed_3yr": p.total_games_missed,
                    "severe_injuries": p.severe_injury_count
                }
            }
            for p in players
        ],
        "last_updated": get_last_cache_update(),
        "count": len(players)
    }
```

**Update:** `backend/main.py`

```python
from routers import internal

app.include_router(internal.router)
```

**Railway environment variable:**
```bash
# Set in Railway dashboard
INTERNAL_API_KEY=cd_internal_secret_2026_xyz123abc
```

### Response Example
```json
{
  "players": [
    {
      "player_id": "203999",
      "name": "Nikola Jokic",
      "team": "DEN",
      "position": "C",
      "age": 28,
      "fantasy_points": 58.3,
      "points": 27.0,
      "rebounds": 13.2,
      "assists": 8.8,
      "steals": 1.3,
      "blocks": 0.9,
      "turnovers": 3.1,
      "three_pointers": 0.8,
      "fg_pct": 0.632,
      "ft_pct": 0.817,
      "minutes": 34.5,
      "games_played_3yr": [75, 73, 69],
      "injury_history": {
        "total_games_missed_3yr": 37,
        "severe_injuries": 0
      }
    }
  ],
  "last_updated": "2026-01-15T05:00:00Z",
  "count": 398
}
```

### Test
```bash
# Test with curl
curl -H "X-API-Key: cd_internal_secret_2026_xyz123abc" \
  https://courtdominion.up.railway.app/api/internal/baseline-projections

# Should return JSON with 398 players
```

**Time:** 1 hour

---

## IMPLEMENTATION CHECKLIST

### Before Microservices Launch

- [ ] Deploy content endpoint (15 min)
- [ ] Integrate rookie comparables (1-2 hours)
- [ ] Integrate 2nd pass retry (1-2 hours)
- [ ] **Build internal API endpoint (1 hour) - CRITICAL**
- [ ] Test internal API with curl
- [ ] Set Railway environment variable (INTERNAL_API_KEY)
- [ ] Document API key for Features 1-7

**Total time:** ~4-6 hours (1 day)

---

## PRIORITY ORDER

### If Limited Time

**Must do:**
1. Internal API endpoint (CRITICAL - blocks Features 1-7)

**Should do:**
2. 2nd pass retry (improves data quality)

**Nice to have:**
3. Content endpoint (marketing copy)
4. Rookie comparables (only 8 rookies)

---

## TESTING AFTER COMPLETION

### Smoke Tests

```bash
# 1. Content endpoint
curl https://courtdominion.up.railway.app/api/content

# 2. Rookie in projections
curl https://courtdominion.up.railway.app/api/players | grep "Victor Wembanyama"

# 3. Check retry logs
ssh railway logs | grep "retry_failed"

# 4. Internal API (CRITICAL)
curl -H "X-API-Key: <secret>" \
  https://courtdominion.up.railway.app/api/internal/baseline-projections
```

---

## NOTES

### Internal API Security

**Private API key:**
- Never commit to git
- Set in Railway environment only
- Share with Features 1-7 services only
- Rotate if compromised

**No rate limiting needed:**
- Server-to-server only
- Not exposed to public
- Trust our own services

---

### What Happens After

**Once internal API is live:**
1. Features 1-7 can call it
2. Get all player data + projections
3. Add their layers (risk, auction values, etc.)
4. Return enhanced data to users

**Phase 1 backend becomes pure data service.**

---

## SUMMARY

**4 features to complete:**
1. Content endpoint - deploy (15 min)
2. Rookie comparables - integrate (1-2 hours)  
3. 2nd pass retry - integrate (1-2 hours)
4. **Internal API - build (1 hour) - CRITICAL**

**Total:** 1 day of work

**After this:** Ready for microservices development

---

**END OF DOCUMENT**
