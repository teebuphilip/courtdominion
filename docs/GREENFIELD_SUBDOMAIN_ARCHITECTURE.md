# COURTDOMINION - GREENFIELD SUBDOMAIN ARCHITECTURE

**Date:** January 2026  
**Version:** 1.0

---

## TL;DR

**Phase 1 = projections subdomain (basic DBB2)**  
**Feature 0 = main site (marketing + auth)**  
**Features 1-7 = feature subdomains (mini-sites)**  

Every feature is a standalone website. Truly greenfield. FounderOps builds all 8.

---

## THE ARCHITECTURE

### Main Domain
```
courtdominion.com
└─ Feature 0: Marketing + Auth + CTA
   - Landing page
   - Pricing
   - Sign up / Login
   - User dashboard
```

### Phase 1 Subdomain
```
projections.courtdominion.com
└─ Basic DBB2 projections (launched Jan 19)
   - Simple player list
   - Fantasy points projections
   - Manual copy/paste landing page
   - No fancy features
```

### Feature Subdomains (1-7)
```
risk.courtdominion.com          → Feature 1: Risk-Aware Projections
auction.courtdominion.com       → Feature 2: Auction Values
tiers.courtdominion.com         → Feature 3: Tiers & Inflation
draft.courtdominion.com         → Feature 4: Draft Assistant
practice.courtdominion.com      → Feature 5: Practice Mode
history.courtdominion.com       → Feature 6: Historical Context
season.courtdominion.com        → Feature 7: Season Assist
```

---

## WHY THIS IS TRULY GREENFIELD

### Each Feature = Complete Standalone Website

**Every subdomain is:**
- Own React frontend codebase
- Own backend API
- Own database (if needed)
- Own Railway deployment
- Own repository

**Zero shared code between features.**

---

### How Features Connect

**NOT via code imports:**
```python
# ❌ This is brownfield
from risk_projections import calculate_risk
```

**Via HTTP API calls:**
```python
# ✅ This is greenfield
import httpx

response = await httpx.get('https://risk.courtdominion.com/api/projections')
data = response.json()
```

**External HTTP calls = greenfield** ✅

---

### Shared Elements (Not Code)

**What's shared:**
1. **Auth token:** JWT passed between subdomains
2. **Design system:** Tailwind config (copy/paste, not import)
3. **API keys:** For inter-service calls

**What's NOT shared:**
- No shared code libraries
- No monorepo
- No shared database
- No shared deployment

---

## THE 9 PROJECTS

### Project 0: Main Site (Feature 0)
**Domain:** courtdominion.com  
**Purpose:** Marketing + Authentication  
**Tech:** React + Auth0/Supabase  
**FounderOps:** Greenfield ✅

**Pages:**
- Landing page
- Pricing
- Features overview
- Sign up / Login
- User dashboard (links to features)

**Auth flow:**
```
User logs in → Gets JWT token → Token works on all subdomains
```

---

### Project 1: Phase 1 Projections
**Domain:** projections.courtdominion.com  
**Purpose:** Basic DBB2 projections (existing)  
**Tech:** React + FastAPI backend  
**Status:** Launching Jan 19

**Pages:**
- Player list
- Player detail
- Basic projections

**Backend API:**
- `/api/projections`
- `/api/players/{id}`
- `/api/internal/baseline-projections` (for Features 1-7)

---

### Project 2: Risk Projections (Feature 1)
**Domain:** risk.courtdominion.com  
**Purpose:** Risk-aware projections  
**Tech:** React + FastAPI  
**FounderOps:** Greenfield ✅

**What it does:**
- Calls `projections.courtdominion.com/api/internal/baseline-projections`
- Adds risk modeling
- Displays confidence intervals, volatility, injury risk

**Pages:**
- Risk projections list
- Player risk detail
- Risk comparison tool

---

### Project 3: Auction Values (Feature 2)
**Domain:** auction.courtdominion.com  
**Purpose:** Dollar auction values  
**Tech:** React + FastAPI  
**FounderOps:** Greenfield ✅

**What it does:**
- Calls `risk.courtdominion.com/api/projections`
- Calculates auction values
- Displays price ranges

**Pages:**
- Auction values list
- Customizable league settings
- Auction cheat sheet (print-friendly)

---

### Project 4: Tiers (Feature 3)
**Domain:** tiers.courtdominion.com  
**Purpose:** Tier groupings + inflation tracking  
**Tech:** React + FastAPI + PostgreSQL  
**FounderOps:** Greenfield ✅

**What it does:**
- Calls `auction.courtdominion.com/api/values`
- Detects tier breaks
- Tracks inflation during drafts

**Pages:**
- Tier visualization
- Inflation dashboard
- Draft room tracker

---

### Project 5: Draft Assistant (Feature 4)
**Domain:** draft.courtdominion.com  
**Purpose:** Live draft YES/NO/CAUTION  
**Tech:** React + FastAPI + WebSocket + PostgreSQL  
**FounderOps:** Greenfield ✅

**What it does:**
- Calls multiple APIs (risk, auction, tiers)
- Real-time draft tracking
- YES/NO/CAUTION recommendations

**Pages:**
- Draft room (live)
- Draft history
- Draft analytics

---

### Project 6: Practice Mode (Feature 5)
**Domain:** practice.courtdominion.com  
**Purpose:** Simulated auction drafts  
**Tech:** React + FastAPI + PostgreSQL  
**FounderOps:** Greenfield ✅

**What it does:**
- Calls `auction.courtdominion.com/api/values`
- AI opponent simulation
- Post-draft scorecard

**Pages:**
- Practice draft room
- AI opponent selection
- Scorecard results

---

### Project 7: Historical Context (Feature 6)
**Domain:** history.courtdominion.com  
**Purpose:** Player comparables + risk narratives  
**Tech:** React + FastAPI + PostgreSQL  
**FounderOps:** Greenfield ✅

**What it does:**
- Calls `projections.courtdominion.com/api/internal/baseline-projections`
- Historical player matching
- Outcome analysis

**Pages:**
- Player comparison
- Historical outcomes
- Risk narratives

---

### Project 8: Season Assist (Feature 7)
**Domain:** season.courtdominion.com  
**Purpose:** Sleeper integration + roster management  
**Tech:** React + FastAPI + PostgreSQL  
**FounderOps:** Greenfield ✅

**What it does:**
- Calls Sleeper API
- Calls `projections.courtdominion.com/api/internal/baseline-projections`
- Roster analysis + waiver/trade suggestions

**Pages:**
- League import
- Roster analysis
- Waiver wire radar
- Trade suggestions

---

## DEPLOYMENT MAP

### Railway Services

**Total: 9 services**

1. `courtdominion-main` (Feature 0)
2. `courtdominion-projections` (Phase 1)
3. `courtdominion-risk` (Feature 1)
4. `courtdominion-auction` (Feature 2)
5. `courtdominion-tiers` (Feature 3)
6. `courtdominion-draft` (Feature 4)
7. `courtdominion-practice` (Feature 5)
8. `courtdominion-history` (Feature 6)
9. `courtdominion-season` (Feature 7)

**Cost estimate:** ~$50-60/month total

---

### Domain Setup

**DNS configuration:**
```
courtdominion.com           → Railway service #1
projections.courtdominion.com → Railway service #2
risk.courtdominion.com      → Railway service #3
auction.courtdominion.com   → Railway service #4
tiers.courtdominion.com     → Railway service #5
draft.courtdominion.com     → Railway service #6
practice.courtdominion.com  → Railway service #7
history.courtdominion.com   → Railway service #8
season.courtdominion.com    → Railway service #9
```

**All CNAME records pointing to Railway.**

---

## AUTHENTICATION FLOW

### How JWT Works Across Subdomains

**Step 1: User logs in on main site**
```
courtdominion.com/login
→ Auth0/Supabase authenticates
→ Returns JWT token
→ Token stored in cookie (.courtdominion.com domain)
```

**Step 2: User clicks "Risk Projections"**
```
courtdominion.com
→ Redirects to risk.courtdominion.com
→ JWT cookie automatically sent (same domain)
→ risk.courtdominion.com validates token
→ User authenticated
```

**Step 3: User navigates to another feature**
```
risk.courtdominion.com
→ User clicks "Auction Values"
→ Redirects to auction.courtdominion.com
→ JWT cookie automatically sent
→ auction.courtdominion.com validates token
→ User authenticated
```

**Single sign-on across all subdomains** ✅

---

### JWT Validation (Per Subdomain)

**Each feature validates JWT independently:**

```python
# Every subdomain backend has this

from fastapi import Header, HTTPException
import jwt

SECRET_KEY = os.getenv("JWT_SECRET")

def verify_token(authorization: str = Header(...)):
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload  # Contains user_id
    except:
        raise HTTPException(401, "Invalid token")

@router.get("/api/projections")
async def get_projections(user=Depends(verify_token)):
    # User is authenticated
    return get_user_projections(user['user_id'])
```

**Shared secret key, independent validation.**

---

## WHY THIS IS GREENFIELD

### Traditional Brownfield (What We're Avoiding)

```
monorepo/
├── frontend/
│   ├── components/
│   │   ├── RiskProjections.tsx     ← Feature 1
│   │   ├── AuctionValues.tsx       ← Feature 2
│   │   └── DraftAssistant.tsx      ← Feature 4
│   └── App.tsx  ← Routes to all features
├── backend/
│   ├── routers/
│   │   ├── risk.py      ← Feature 1
│   │   ├── auction.py   ← Feature 2
│   │   └── draft.py     ← Feature 4
│   └── main.py  ← Imports all routers
└── shared/
    ├── models.py
    └── utils.py

❌ Shared code = brownfield
❌ Single deployment = tightly coupled
❌ FounderOps can't build this
```

---

### Our Greenfield Approach

```
feature-0-main/          (standalone repo)
├── frontend/
│   └── src/
│       └── App.tsx
├── backend/
│   └── main.py
└── README.md

feature-1-risk/          (standalone repo)
├── frontend/
│   └── src/
│       └── App.tsx
├── backend/
│   └── main.py
└── README.md

feature-2-auction/       (standalone repo)
├── frontend/
│   └── src/
│       └── App.tsx
├── backend/
│   └── main.py
└── README.md

✅ Zero shared code
✅ Independent repos
✅ Independent deployments
✅ FounderOps can build each one
```

---

### How Features "Share" Code (They Don't)

**Example: Both Feature 1 and Feature 2 need player data**

**Brownfield approach (BAD):**
```python
# Feature 1
from shared.players import get_player_data

# Feature 2  
from shared.players import get_player_data

❌ Shared import = brownfield
```

**Greenfield approach (GOOD):**
```python
# Feature 1
async def get_player_data():
    response = await httpx.get('https://projections.courtdominion.com/api/internal/baseline-projections')
    return response.json()

# Feature 2
async def get_player_data():
    response = await httpx.get('https://projections.courtdominion.com/api/internal/baseline-projections')
    return response.json()

✅ Duplicated code = greenfield
✅ HTTP call = external dependency
```

**Yes, code is duplicated. That's the point.**

Each feature is completely standalone.

---

## FOUNDEROPS BUILD SEQUENCE

### Option A: Serial (Safe)

**Build order if dependencies matter:**

```
Week 1:  Feature 0 (main site) → Provides auth
Week 2:  Phase 1 frontend (uses auth)
Week 3:  Feature 1 (risk) → Calls Phase 1 API
Week 4:  Feature 2 (auction) → Calls Feature 1 API
Week 5:  Feature 3 (tiers) → Calls Feature 2 API
Week 6:  Feature 4 (draft) → Calls Features 1,2,3
Week 7:  Feature 5 (practice) → Calls Feature 2 API
Week 8:  Feature 6 (history) → Calls Phase 1 API
Week 9:  Feature 7 (season) → Calls Phase 1 API
```

**Total: 9 weeks**

---

### Option B: Parallel (Fast)

**Build all simultaneously (if FounderOps can mock APIs):**

```
Week 1-2: ALL 9 projects built in parallel
Week 3:   Integration testing
Week 4:   Deploy all
```

**Total: 4 weeks**

**Requires:** FounderOps can mock external API calls during build

---

## TIMELINE

### January 2026

**Week 1-2:** Launch Phase 1
- `projections.courtdominion.com` goes live
- Backend API with `/api/internal/baseline-projections` endpoint
- Manual landing page

**Week 3-4:** Plan Feature 0-7
- FounderOps intake for all 8 features
- Get complexity scores
- Decide serial vs parallel

---

### February-March 2026

**Build all 8 greenfield projects**

**Using FounderOps:**
- Feature 0: Main site
- Features 1-7: Feature subdomains

**Timeline:** 4-9 weeks depending on approach

---

### April 2026

**Integration & Testing**
- Wire up auth across subdomains
- Test API calls between features
- End-to-end testing

---

### May-June 2026

**Beta Testing**
- All 9 subdomains live
- 20-50 beta users
- Real drafts

---

### July-August 2026

**Marketing & Launch Prep**

---

### September 2026

**💰 LAUNCH - DRAFT SEASON 💰**

---

## SUCCESS CRITERIA

### Technical

**Each feature must:**
- ✅ Deploy independently
- ✅ Run without other features
- ✅ Authenticate via JWT
- ✅ Call external APIs (not code imports)
- ✅ Have own database (if needed)

**If any feature shares code = NOT greenfield** ❌

---

### User Experience

**Users see:**
- Main site (courtdominion.com)
- Click feature links
- Seamlessly navigate between subdomains
- Single login works everywhere

**Users don't see:**
- Technical architecture
- Separate deployments
- HTTP calls between services

**Feels like one app, built as 9 apps.**

---

## ADVANTAGES

### For Development

**✅ FounderOps can build all 9** (truly greenfield)  
**✅ Parallel development** (faster)  
**✅ Independent testing** (easier)  
**✅ No merge conflicts** (separate repos)  

---

### For Deployment

**✅ Deploy features independently** (no downtime)  
**✅ Roll back one feature** (doesn't affect others)  
**✅ Scale features independently** (draft assistant needs more resources)  
**✅ Kill a feature** (just turn off subdomain)  

---

### For Users

**✅ Faster loading** (only load feature you're using)  
**✅ Better UX** (focused mini-apps vs bloated monolith)  
**✅ Reliable** (one feature down ≠ whole site down)  

---

## DISADVANTAGES (AND MITIGATIONS)

### Disadvantage 1: Code Duplication

**Problem:** Same API call code in multiple features

**Mitigation:** That's fine. Copy/paste is cheaper than shared dependencies.

---

### Disadvantage 2: More Deployments

**Problem:** 9 Railway services vs 1

**Mitigation:** Railway makes this easy. Small cost increase (~$50/month).

---

### Disadvantage 3: API Call Overhead

**Problem:** HTTP calls between features add latency

**Mitigation:** 
- Cache responses (Redis)
- Services on same region (low latency)
- Acceptable for our use case (<500ms total)

---

### Disadvantage 4: Auth Complexity

**Problem:** JWT must work across all subdomains

**Mitigation:** 
- Use `.courtdominion.com` cookie domain
- Standard JWT pattern
- Many sites do this successfully

---

## CONCLUSION

### What We're Building

**9 standalone websites:**
- 1 main site (marketing + auth)
- 1 basic projections site (Phase 1)
- 7 feature sites (Features 1-7)

**Each is truly greenfield:**
- Own codebase
- Own deployment
- Own domain
- Zero shared code

**FounderOps can build all 9.**

---

### Why This Works

**✅ Solves brownfield problem** (no shared code)  
**✅ Enables FounderOps** (greenfield builds)  
**✅ Microservices best practice** (industry standard)  
**✅ Faster development** (parallel builds)  
**✅ Better reliability** (isolated failures)  
**✅ Easier maintenance** (update one feature)  

---

### Next Steps

1. Launch Phase 1 (Jan 19)
2. Add internal API endpoint
3. Run Features 0-7 through FounderOps intake
4. Build all 8 in Feb-Mar
5. Launch Sep 2026

**This is the architecture.** ✅

---

**END OF DOCUMENT**
