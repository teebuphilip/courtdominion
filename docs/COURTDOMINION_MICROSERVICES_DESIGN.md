# COURTDOMINION - MICROSERVICES ARCHITECTURE DESIGN
## Launch Strategy: Phase 1 → Microservices → Features 1-7

**Date:** January 2026  
**Version:** 1.0

---

## TL;DR - THE STRATEGY

**Phase 1 (Jan 19):** Launch existing backend + frontend  
**Late Jan:** Add internal API endpoint  
**Feb-Apr:** Build 7 features as greenfield microservices  
**Sep 2026:** Launch all features for draft season  

**Key insight:** Phase 1 backend becomes data API, new features are standalone services that call it.

---

## PART 1: PHASE 1 MISSING FEATURES

### Current Status

**Built but not deployed:**
1. Content endpoint
2. Rookie comparables
3. 2nd pass retry logic

**Action required:** Deploy these before adding internal API

---

### Feature 1: Content Endpoint

**Purpose:** Dynamic homepage/marketing content  
**Status:** Code complete, needs deployment  

**File:** `backend/routers/content.py`  
**Endpoint:** `GET /api/content`  
**Data:** `backend/data/content.json`

**What it returns:**
```json
{
  "homepage": {
    "hero": "Court Dominion - Fantasy Basketball Projections",
    "tagline": "5-year average projections..."
  },
  "projections_page": {...},
  "insights_page": {...},
  "navigation": [...],
  "footer": {...}
}
```

**Deployment:**
```bash
# Already exists, just needs to be enabled
# Verify content.py is imported in main.py
# Deploy to Railway
```

**Time:** 15 minutes  
**Priority:** Medium (nice to have for launch)

---

### Feature 2: Rookie Comparables

**Purpose:** Project rookies using veteran comparisons  
**Status:** CSV built, needs integration  

**File:** `automation/rookie_comparables.csv`

**How it works:**
```
Rookie → Find comparable veteran → Use veteran's stats as baseline
```

**Example:**
```csv
rookie_name,comparable_player,similarity_score
Victor Wembanyama,Kevin Durant (rookie year),0.82
```

**Integration needed:**
```python
# In dbb2_projections.py
if player.is_rookie:
    comparable = get_rookie_comparable(player.name)
    return comparable.baseline_projection
```

**Time:** 2 hours  
**Priority:** Low (only ~8 rookies matter)

---

### Feature 3: 2nd Pass Retry Logic

**Purpose:** Retry failed NBA.com API calls  
**Status:** Code complete, needs integration  

**File:** `automation/retry_failed_players.py`

**How it works:**
```python
# After build_cache.py runs
# Check for players with missing data
# Retry those specific players
# Exponential backoff (1s, 2s, 4s, 8s, 16s)
```

**Integration:**
```bash
# Add to pipeline.sh
python automation/build_cache.py
python automation/retry_failed_players.py  # NEW
python automation/dbb2_projections.py
```

**Time:** 1-2 hours  
**Priority:** Medium (improves data quality)

---

## PART 2: INTERNAL API ENDPOINT

### Purpose

**Enable microservices to consume Phase 1 data**

Phase 1 backend becomes:
- Data service (DBB2 projections)
- Player cache service
- Accessed via private API

---

### Architecture

```
┌─────────────────────────────────┐
│  Phase 1 Backend (Data API)    │
│  courtdominion.up.railway.app   │
└─────────────────────────────────┘
         ↓ Private API call
┌─────────────────────────────────┐
│  Feature 1-7 Microservices      │
│  (Standalone services)          │
└─────────────────────────────────┘
```

---

### New Endpoint Specification

**Endpoint:** `GET /api/internal/baseline-projections`

**Authentication:** API key in header
```
X-API-Key: <secret_key>
```

**Response:**
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

---

### Implementation

**File:** `backend/routers/internal.py` (NEW)

```python
from fastapi import APIRouter, Header, HTTPException
import os

router = APIRouter()

INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")

@router.get("/api/internal/baseline-projections")
async def get_baseline_projections(
    x_api_key: str = Header(...)
):
    """
    Internal API for microservices
    Returns all player projections
    """
    
    # Auth check
    if x_api_key != INTERNAL_API_KEY:
        raise HTTPException(401, "Invalid API key")
    
    # Get data (use existing functions)
    players = get_all_players_with_projections()
    
    return {
        "players": players,
        "last_updated": get_last_cache_update(),
        "count": len(players)
    }
```

**Add to main.py:**
```python
from routers import internal
app.include_router(internal.router)
```

**Environment variable:**
```bash
# Railway environment
INTERNAL_API_KEY=cd_internal_2026_secret_key_xyz
```

**Time:** 1 hour  
**Priority:** Critical (needed for microservices)

---

### Security

**Private API key:**
- Set in Railway environment
- Shared with Feature 1-7 services
- Not exposed to public

**Rate limiting:** Not needed (internal only)

**CORS:** Not applicable (server-to-server)

---

## PART 3: GREENFIELD MICROSERVICES (FEATURES 1-7)

### Architecture Overview

**Each feature = standalone service**

```
Service 1: Risk Projections
Service 2: Auction Values
Service 3: Tiers & Inflation
Service 4: Draft Assistant
Service 5: Practice Mode
Service 6: Historical Context
Service 7: Season Assist
```

**Each service:**
- Independent FastAPI app
- Independent Railway deployment
- Independent database (if needed)
- Calls other services via HTTP

---

### Feature 1: Risk-Aware Projections Service

**Purpose:** Add risk modeling to baseline projections

**Input:** Calls Phase 1 internal API  
**Output:** Risk-adjusted projections

**Endpoint:** `GET /api/v2/risk-projections`

**What it adds:**
- Minutes distribution (probability-based)
- Injury probability
- Confidence intervals (90% CI)
- Volatility rating
- Risk-adjusted expected value

**Example output:**
```json
{
  "player_id": "203999",
  "name": "Nikola Jokic",
  "baseline_fp": 58.3,
  "expected_fp": 56.8,
  "ci_lower": 48.2,
  "ci_upper": 64.5,
  "volatility": "low",
  "injury_risk": "low",
  "expected_games": 72
}
```

**Tech stack:**
- FastAPI
- NumPy/SciPy (statistical modeling)
- httpx (API calls)

**Deployment:** `risk-projections.up.railway.app`

**FounderOps build time:** 1 week

---

### Feature 2: Auction Values Service

**Purpose:** Convert projections to auction dollar values

**Input:** Calls Feature 1 API  
**Output:** Auction prices

**Endpoint:** `GET /api/v2/auction-values`

**Query params:**
- `budget` (default: 200)
- `teams` (default: 12)
- `roster_spots` (default: 13)

**What it calculates:**
- Replacement level by position
- Value Above Replacement (VAR)
- Risk discounts
- Position scarcity premiums
- Price ranges (floor/value/ceiling)

**Example output:**
```json
{
  "player_id": "203999",
  "name": "Nikola Jokic",
  "var": 35.8,
  "base_value": 68,
  "risk_discount": 0,
  "scarcity_premium": 5,
  "final_value": 73,
  "floor_price": 66,
  "ceiling_price": 80,
  "recommended_max": 77
}
```

**Tech stack:**
- FastAPI
- NumPy (calculations)
- httpx (API calls)

**Deployment:** `auction-values.up.railway.app`

**FounderOps build time:** 1 week

---

### Feature 3: Tiers & Inflation Service

**Purpose:** Group players into tiers, track auction inflation

**Input:** Calls Feature 2 API  
**Output:** Tier groupings + inflation data

**Endpoints:**
- `GET /api/v2/tiers` - Get tier groupings
- `POST /api/v2/track-purchase` - Track auction purchase

**What it does:**
- Detect natural tier breaks
- Alert on last-in-tier
- Track room-level inflation
- Track position-specific inflation
- Recommend bid adjustments

**Example output:**
```json
{
  "tiers": [
    {
      "tier_number": 1,
      "avg_value": 68,
      "players": ["Jokic", "Giannis", "Doncic"],
      "gap_to_next": 8
    }
  ],
  "inflation": {
    "overall_pct": 12.5,
    "status": "hot",
    "recommendation": "Reduce bids 10%"
  }
}
```

**Tech stack:**
- FastAPI
- PostgreSQL (track purchases)
- httpx (API calls)

**Deployment:** `tiers.up.railway.app`

**FounderOps build time:** 1 week

---

### Feature 4: Draft Assistant Service

**Purpose:** Live draft YES/NO/CAUTION recommendations

**Input:** Calls Features 1, 2, 3 APIs  
**Output:** Real-time bidding guidance

**Protocol:** WebSocket (`/ws/draft/{session_id}`)

**What it does:**
- Track draft state (budget, roster, needs)
- Evaluate each nomination
- Return YES/NO/CAUTION
- Provide suggested max bid
- One-line rationale

**Example WebSocket message:**
```json
{
  "type": "recommendation",
  "player": "Anthony Davis",
  "current_bid": 52,
  "recommendation": "CAUTION",
  "max_bid": 55,
  "rationale": "High injury risk + overpaying $7. Pass unless desperate for C."
}
```

**Tech stack:**
- FastAPI
- WebSockets
- PostgreSQL (draft state)
- httpx (API calls)

**Deployment:** `draft-assistant.up.railway.app`

**FounderOps build time:** 2 weeks (most complex)

---

### Feature 5: Practice Mode Service

**Purpose:** Simulated auction drafts with AI opponents

**Input:** Calls Feature 2 API  
**Output:** Draft simulation + scorecard

**Endpoints:**
- `POST /api/v2/practice/start` - Start draft
- `POST /api/v2/practice/bid` - Place bid
- `GET /api/v2/practice/scorecard` - Get results

**What it does:**
- Simulate complete auction draft
- 4 AI opponent personalities
- Real-time feedback on decisions
- Post-draft performance scorecard
- Grade: A/B/C/D/F

**Example scorecard:**
```json
{
  "overall_grade": "B+",
  "value_score": 85,
  "roster_balance_score": 78,
  "decision_quality_score": 82,
  "key_mistakes": [
    "Overpaid $8 for Kawhi Leonard"
  ],
  "improvement_tips": [
    "Trust the engine - you ignored 3 NO recommendations"
  ]
}
```

**Tech stack:**
- FastAPI
- PostgreSQL (practice sessions)
- httpx (API calls)

**Deployment:** `practice-mode.up.railway.app`

**FounderOps build time:** 1.5 weeks

---

### Feature 6: Historical Context Service

**Purpose:** Historical player comparisons + risk narratives

**Input:** Calls Phase 1 API + historical database  
**Output:** Player comparables + outcomes

**Endpoint:** `GET /api/v2/historical/{player_id}`

**What it does:**
- Match current player to historical comparables
- Calculate outcome ranges (P10/P50/P90)
- Generate risk narrative
- Identify primary risk factors

**Example output:**
```json
{
  "player": "Anthony Davis",
  "comparables": [
    {
      "historical_player": "Blake Griffin 2018-19",
      "similarity": 0.87,
      "outcome": {
        "projected": 45.2,
        "actual": 38.7,
        "games_played": 56
      }
    }
  ],
  "narrative": {
    "headline": "AD is 85% similar to 2019 Blake Griffin",
    "primary_risk": "injury_risk",
    "recommendation": "Injury risk. Griffin, Love, Bosh all missed significant time. Build in 20% discount."
  }
}
```

**Tech stack:**
- FastAPI
- PostgreSQL (historical database)
- httpx (API calls)

**Deployment:** `historical-context.up.railway.app`

**FounderOps build time:** 1 week

---

### Feature 7: Season Assist Service

**Purpose:** Sleeper league integration + roster management

**Input:** Sleeper API + Phase 1 API  
**Output:** Waiver/trade recommendations

**Endpoints:**
- `POST /api/v2/season/import` - Import Sleeper league
- `GET /api/v2/season/waivers` - Waiver suggestions
- `GET /api/v2/season/trades` - Trade suggestions

**What it does:**
- Import Sleeper roster
- Analyze strengths/weaknesses
- Scan waiver wire
- Suggest trades
- User-selectable risk tone

**Example output:**
```json
{
  "waiver_opportunities": [
    {
      "player": "De'Andre Hunter",
      "score": 0.85,
      "reason": "Hot streak: 45 FP last 7 days | Fills SF shortage",
      "drop_candidates": ["Player X", "Player Y"]
    }
  ],
  "trade_opportunities": [
    {
      "give": ["Player A"],
      "get": ["Player B"],
      "rationale": "Trade your blocks strength for their assists strength"
    }
  ]
}
```

**Tech stack:**
- FastAPI
- PostgreSQL (user leagues)
- httpx (Sleeper API + Phase 1 API)

**Deployment:** `season-assist.up.railway.app`

**FounderOps build time:** 1 week

---

## PART 4: IMPLEMENTATION TIMELINE

### January 2026

**Week 1-2: Launch Phase 1**
- Deploy existing backend + frontend
- Enable content endpoint
- Get users, build mailing list

**Week 3-4: Add Internal API**
- Create `/api/internal/baseline-projections` endpoint
- Deploy to Railway
- Test with curl/Postman

**Deliverable:** Phase 1 running + internal API ready

---

### February 2026

**FounderOps builds all 7 services (parallel)**

**Week 1:**
- Feature 1: Risk Projections
- Feature 5: Practice Mode
- Feature 6: Historical Context

**Week 2:**
- Feature 2: Auction Values
- Feature 7: Season Assist

**Week 3:**
- Feature 3: Tiers & Inflation
- Feature 4: Draft Assistant (Part 1)

**Week 4:**
- Feature 4: Draft Assistant (Part 2)
- Testing all services

**Deliverable:** 7 greenfield services built

---

### March 2026

**Testing & Integration**

**Week 1-2:** Standalone testing
- Test each service independently
- Mock API calls
- Unit tests + integration tests

**Week 3-4:** Service-to-service integration
- Test API call chains
- Verify data flows
- Performance testing

**Deliverable:** All services tested and working

---

### April 2026

**Deployment**

**Week 1-2:** Deploy to Railway
- 7 separate Railway services
- Configure API keys
- Setup monitoring

**Week 3-4:** Frontend integration
- Update frontend to call new APIs
- Build UI for new features
- End-to-end testing

**Deliverable:** Production-ready system

---

### May-June 2026

**Beta Testing**
- 20-50 beta users
- Real drafts
- Collect feedback
- Bug fixes

---

### July-August 2026

**Marketing & Launch Prep**
- Marketing campaign
- Content creation
- Early access sales

---

### September 2026

**💰 LAUNCH - DRAFT SEASON 💰**

All 7 features live for draft season

---

## PART 5: SERVICE DEPENDENCIES

### Dependency Graph

```
Phase 1 Backend (Data API)
    ↓
    ├─→ Feature 1 (Risk Projections)
    │       ↓
    │       └─→ Feature 2 (Auction Values)
    │               ↓
    │               ├─→ Feature 3 (Tiers)
    │               │       ↓
    │               │       └─→ Feature 4 (Draft Assistant)
    │               │
    │               └─→ Feature 5 (Practice Mode)
    │
    ├─→ Feature 6 (Historical Context)
    │
    └─→ Feature 7 (Season Assist)
```

**Build order (if sequential):**
1. Phase 1 internal API
2. Feature 1
3. Feature 2
4. Features 3, 5 (parallel)
5. Feature 4
6. Features 6, 7 (parallel)

**With FounderOps (parallel):** All at once

---

## PART 6: INFRASTRUCTURE

### Railway Services

**Total: 8 services**

1. `courtdominion-phase1` (existing)
2. `risk-projections`
3. `auction-values`
4. `tiers`
5. `draft-assistant`
6. `practice-mode`
7. `historical-context`
8. `season-assist`

**Cost estimate:**
- Phase 1: $5-10/month
- Each microservice: $5/month
- Total: ~$50/month

**Scaling:**
- Auto-scale during draft season (Sep-Oct)
- Scale down during off-season

---

### Databases

**Phase 1:** PostgreSQL (existing)
- Player cache
- Projections

**Feature 3:** PostgreSQL
- Draft sessions
- Inflation tracking

**Feature 4:** PostgreSQL
- Draft state

**Feature 5:** PostgreSQL
- Practice sessions
- Scorecards

**Feature 6:** PostgreSQL
- Historical seasons (10 years)

**Feature 7:** PostgreSQL
- User leagues
- Recommendations

**Total databases:** 5 PostgreSQL instances

---

### API Keys / Secrets

**Environment variables needed:**

```bash
# Phase 1
INTERNAL_API_KEY=<secret>

# All microservices
PHASE1_API_URL=https://courtdominion-phase1.up.railway.app
PHASE1_API_KEY=<secret>

# Feature 1
FEATURE1_API_URL=https://risk-projections.up.railway.app

# Feature 2
FEATURE2_API_URL=https://auction-values.up.railway.app

# Feature 7
SLEEPER_API_URL=https://api.sleeper.app/v1
```

---

## PART 7: TESTING STRATEGY

### Per-Service Testing

**Each FounderOps build includes:**
- Unit tests (pytest)
- Integration tests
- Mock API responses
- 90%+ code coverage

**Example:**
```python
# Feature 1: Risk Projections
def test_risk_projection_calculation(mock_phase1_api):
    service = RiskProjectionsService()
    result = service.calculate_risk(mock_phase1_api)
    
    assert result['expected_fp'] > 0
    assert result['ci_lower'] < result['ci_upper']
    assert result['volatility'] in ['low', 'medium', 'high']
```

---

### Integration Testing

**Test service-to-service calls:**

```python
def test_feature2_calls_feature1():
    # Feature 2 should call Feature 1 API
    auction_service = AuctionValuesService()
    result = auction_service.get_auction_values()
    
    # Verify it called Feature 1
    assert feature1_api_was_called
    assert result['auction_value'] > 0
```

---

### End-to-End Testing

**Test complete user flow:**

1. User requests auction values
2. Feature 2 calls Feature 1
3. Feature 1 calls Phase 1
4. Data flows back up
5. User receives response

**Target:** <500ms total response time

---

## PART 8: MIGRATION STRATEGY

### Phase 1 Users

**Current Phase 1 (Jan-Sep 2026):**
- Users access basic projections
- Simple frontend
- Works as-is

**After microservices launch (Sep 2026):**
- Phase 1 frontend deprecated
- Users redirected to new frontend
- New frontend calls microservices
- Old backend stays as data API

**Timeline:**
- Sep 2026: Launch new frontend
- Oct 2026: Redirect old users
- Nov 2026: Deprecate old frontend
- Dec 2026: Shut down old frontend

---

### Data Migration

**No migration needed:**
- Phase 1 backend stays running
- Microservices call it via API
- No database migration required

**Clean separation:**
- Old: Player data + projections
- New: Risk modeling + features

---

## PART 9: FOUNDEROPS REQUIREMENTS

### What FounderOps Needs to Build Each Service

**Input per service:**

1. **Feature specification** (what it does)
2. **API contract** (inputs/outputs)
3. **Dependencies** (which APIs to call)
4. **Tech stack** (FastAPI, PostgreSQL, etc.)

**Output per service:**

1. **Working code** (FastAPI app)
2. **Tests** (pytest suite)
3. **Documentation** (API docs)
4. **Dockerfile** (for Railway)
5. **README** (setup instructions)

**FounderOps 6-pass system:**

1. Spec (Claude + ChatGPT)
2. Code (Claude)
3. Validation (Claude)
4. Tests (Claude)
5. Docs (ChatGPT)
6. Integration check (Claude)

**Time per service:** 3-5 days

---

### FounderOps Configuration

**Per-service template:**

```yaml
service_name: risk-projections
description: Add risk modeling to baseline projections
dependencies:
  - phase1_api: https://courtdominion-phase1.up.railway.app
tech_stack:
  - FastAPI
  - NumPy
  - httpx
  - pytest
database: none
endpoints:
  - GET /api/v2/risk-projections
deployment: railway
```

**FounderOps reads this, generates complete service.**

---

## PART 10: SUCCESS METRICS

### Phase 1 (Jan-Feb)

**Metrics:**
- Users signed up: 100+
- Mailing list: 50+
- Daily API calls: 500+

---

### Beta (May-Jun)

**Metrics:**
- Beta users: 20-50
- Practice drafts completed: 100+
- Bug reports: <20
- Uptime: 99%+

---

### Launch (Sep)

**Metrics:**
- Paying users: 500+
- Draft assistant sessions: 1000+
- Revenue: $5K+ (month 1)
- Uptime: 99.9%+

---

## CONCLUSION

### What Makes This Work

**✅ Clean separation:**
- Phase 1 = data layer
- Microservices = feature layer
- No tangled code

**✅ Greenfield everything:**
- FounderOps can build all 7
- No brownfield complexity
- Parallel development

**✅ Flexible:**
- Can deploy services incrementally
- Can delay non-critical features
- Can scale services independently

**✅ Validates FounderOps:**
- 7 real production services
- Real complexity
- Real customers

**✅ Hits deadline:**
- All 7 features by September
- Ready for draft season
- $$$

---

### Next Steps

**This week:**
1. Launch Phase 1 (Jan 19)
2. Review this design doc
3. Confirm strategy

**Late January:**
1. Add internal API endpoint (1 day)
2. Test with curl
3. Deploy to Railway

**February:**
1. FounderOps builds Feature 1
2. Validate output quality
3. If good → build all 7
4. If not → manual build

**By September:**
- All 7 features live
- Ready for draft season
- 💰💰💰

---

**END OF DESIGN DOCUMENT**

**Ready to execute.**
