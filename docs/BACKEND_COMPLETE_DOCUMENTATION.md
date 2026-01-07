# COURTDOMINION BACKEND - COMPLETE TECHNICAL DOCUMENTATION
## For Frontend Development Planning

**Version:** 1.0 (Production-Ready Baseline)  
**Date:** December 18, 2025  
**Purpose:** Complete backend specification for frontend development

---

## EXECUTIVE SUMMARY

CourtDominion is an NBA fantasy basketball platform that provides daily projections, insights, and waiver wire recommendations. The backend is a FastAPI application serving real NBA data with 398+ player projections, updated daily.

**Current Status:** Production-ready, fully functional, waiting for frontend

**Key Metrics:**
- 398 players with projections
- Real NBA.com data integration
- Daily content generation (5 platforms)
- Response time: <50ms average
- Cost: $5-17/month

---

## SYSTEM ARCHITECTURE

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    COURTDOMINION SYSTEM                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐        ┌──────────────┐                  │
│  │   BACKEND    │◄───────┤  AUTOMATION  │                  │
│  │   FastAPI    │        │   Pipeline   │                  │
│  │  Port 8000   │        │              │                  │
│  └──────┬───────┘        └──────┬───────┘                  │
│         │                       │                           │
│         │                       │                           │
│         ▼                       ▼                           │
│  ┌─────────────────────────────────────┐                   │
│  │     SHARED FILE SYSTEM              │                   │
│  │     /data/outputs/                  │                   │
│  │  - projections.json (398 players)   │                   │
│  │  - insights.json                    │                   │
│  │  - risk.json                        │                   │
│  │  - injuries.json                    │                   │
│  │  - generated/ (content)             │                   │
│  └─────────────────────────────────────┘                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
         │
         │ HTTP/JSON
         ▼
   ┌──────────┐
   │ FRONTEND │  ← TO BE BUILT
   │ (React)  │
   └──────────┘
```

### Technology Stack

**Backend:**
- Python 3.11
- FastAPI (web framework)
- Pydantic (data validation)
- Docker (containerization)

**Data Sources:**
- NBA.com API (player stats)
- ESPN API (injuries)
- OpenAI API (content generation)

**Deployment:**
- Docker Compose (local)
- Railway (production)
- File-based storage (Phase 1, no database)

---

## BACKEND API - COMPLETE ENDPOINT SPECIFICATION

### Base URL

**Local:** `http://localhost:8000`  
**Production:** `https://courtdominion.up.railway.app` (when deployed)

### Health Check

**Endpoint:** `GET /health`

**Purpose:** Verify backend is running

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-18T10:00:00Z",
  "version": "1.0.0"
}
```

**Use Case:** Frontend can ping this on load to verify backend connectivity

---

### Get All Players

**Endpoint:** `GET /api/players`

**Purpose:** Retrieve list of all active NBA players

**Response:**
```json
{
  "players": [
    {
      "id": "203507",
      "name": "Giannis Antetokounmpo",
      "team": "MIL",
      "position": "F",
      "age": 29,
      "status": "active"
    },
    // ... 397 more players
  ],
  "count": 398,
  "last_updated": "2025-12-18T06:00:00Z"
}
```

**Use Case:** Populate player dropdown, search functionality

---

### Get Single Player

**Endpoint:** `GET /api/players/{player_id}`

**Parameters:**
- `player_id` (path): NBA player ID (e.g., "203507")

**Response:**
```json
{
  "id": "203507",
  "name": "Giannis Antetokounmpo",
  "team": "MIL",
  "position": "F",
  "age": 29,
  "status": "active",
  "projection": {
    "fantasy_points": 52.3,
    "minutes": 34.5,
    "points": 28.2,
    "rebounds": 11.1,
    "assists": 5.8,
    "steals": 1.2,
    "blocks": 1.4,
    "turnovers": 3.1,
    "fg_pct": 0.583,
    "ft_pct": 0.652,
    "three_pointers": 0.8
  },
  "insight": {
    "value_score": 9.2,
    "recommendation": "Must start",
    "trending": "up"
  },
  "risk": {
    "injury_risk": "low",
    "consistency": 92,
    "ceiling": 68.5,
    "floor": 38.2
  }
}
```

**Use Case:** Player detail page, comparison tool

---

### Get All Projections

**Endpoint:** `GET /api/projections`

**Query Parameters:**
- `limit` (optional): Max results (default: 100, max: 500)
- `offset` (optional): Pagination offset (default: 0)
- `sort_by` (optional): Sort field (default: "fantasy_points")
- `order` (optional): "asc" or "desc" (default: "desc")

**Response:**
```json
{
  "projections": [
    {
      "player_id": "203507",
      "name": "Giannis Antetokounmpo",
      "team": "MIL",
      "fantasy_points": 52.3,
      "minutes": 34.5,
      "points": 28.2,
      "rebounds": 11.1,
      "assists": 5.8,
      "steals": 1.2,
      "blocks": 1.4,
      "turnovers": 3.1,
      "fg_pct": 0.583,
      "ft_pct": 0.652,
      "three_pointers": 0.8,
      "confidence": 0.95
    },
    // ... more projections
  ],
  "total": 398,
  "limit": 100,
  "offset": 0,
  "last_updated": "2025-12-18T06:00:00Z"
}
```

**Use Case:** Main projections table, leaderboards

---

### Get Top Performers

**Endpoint:** `GET /api/projections/top`

**Query Parameters:**
- `limit` (optional): Number of players (default: 10, max: 50)
- `category` (optional): Stat category (default: "fantasy_points")
  - Options: "fantasy_points", "points", "rebounds", "assists", "steals", "blocks"

**Response:**
```json
{
  "top_performers": [
    {
      "player_id": "203507",
      "name": "Giannis Antetokounmpo",
      "team": "MIL",
      "fantasy_points": 52.3,
      "rank": 1
    },
    // ... top 9 more
  ],
  "category": "fantasy_points",
  "limit": 10
}
```

**Use Case:** Homepage highlights, "Top 10 Today" widget

---

### Get Insights

**Endpoint:** `GET /api/insights`

**Query Parameters:**
- `category` (optional): Filter by insight type
  - Options: "sleepers", "waiver_wire", "streaming", "all" (default)
- `limit` (optional): Max results (default: 20)

**Response:**
```json
{
  "insights": [
    {
      "player_id": "1630567",
      "name": "Tyrese Maxey",
      "team": "PHI",
      "insight_type": "waiver_wire",
      "value_score": 8.7,
      "recommendation": "Add immediately",
      "reasoning": "High usage rate with efficient scoring",
      "trending": "up",
      "ownership_estimate": "45%"
    },
    // ... more insights
  ],
  "count": 20,
  "category": "all"
}
```

**Use Case:** Waiver wire recommendations, strategy tips

---

### Get Risk Metrics

**Endpoint:** `GET /api/risk`

**Query Parameters:**
- `player_id` (optional): Specific player
- `risk_level` (optional): Filter by risk ("low", "medium", "high")

**Response (all players):**
```json
{
  "risk_assessments": [
    {
      "player_id": "203507",
      "name": "Giannis Antetokounmpo",
      "injury_risk": "low",
      "consistency": 92,
      "ceiling": 68.5,
      "floor": 38.2,
      "volatility": 0.15,
      "recommendation": "Safe pick"
    },
    // ... more assessments
  ],
  "count": 398
}
```

**Use Case:** Risk analysis tool, player comparison

---

### Get Injuries

**Endpoint:** `GET /api/injuries`

**Response:**
```json
{
  "injuries": [
    {
      "player_id": "202695",
      "name": "Kawhi Leonard",
      "team": "LAC",
      "injury_status": "Out",
      "injury_type": "Knee",
      "return_date": "2025-12-25",
      "impact": "High"
    },
    // ... more injuries
  ],
  "count": 47,
  "last_updated": "2025-12-18T06:00:00Z"
}
```

**Use Case:** Injury report page, lineup alerts

---

### Search Players

**Endpoint:** `GET /api/players/search`

**Query Parameters:**
- `q`: Search query (name, team, position)
- `limit` (optional): Max results (default: 10)

**Response:**
```json
{
  "results": [
    {
      "player_id": "203507",
      "name": "Giannis Antetokounmpo",
      "team": "MIL",
      "position": "F",
      "match_score": 1.0
    },
    // ... more results
  ],
  "query": "giannis",
  "count": 1
}
```

**Use Case:** Search bar, autocomplete

---

## DATA MODELS

### Player Model

```python
{
  "id": str,              # NBA player ID
  "name": str,            # Full name
  "team": str,            # 3-letter team code
  "position": str,        # Position (G, F, C, G-F, F-C)
  "age": int,             # Current age
  "status": str,          # "active", "injured", "out"
  "height": str,          # e.g., "6-11"
  "weight": int,          # pounds
  "jersey": str           # Jersey number
}
```

### Projection Model

```python
{
  "player_id": str,
  "name": str,
  "team": str,
  "fantasy_points": float,    # Total fantasy points
  "minutes": float,           # Minutes per game
  "points": float,            # Points per game
  "rebounds": float,          # Total rebounds
  "assists": float,
  "steals": float,
  "blocks": float,
  "turnovers": float,
  "fg_pct": float,           # Field goal %
  "ft_pct": float,           # Free throw %
  "three_pointers": float,   # 3PM per game
  "confidence": float,       # 0.0-1.0 confidence score
  "last_updated": datetime
}
```

### Insight Model

```python
{
  "player_id": str,
  "name": str,
  "team": str,
  "insight_type": str,        # "sleeper", "waiver_wire", "streaming", "trade_target"
  "value_score": float,       # 0-10 score
  "recommendation": str,      # Brief recommendation
  "reasoning": str,           # Why this recommendation
  "trending": str,            # "up", "down", "stable"
  "ownership_estimate": str   # Estimated ownership %
}
```

### Risk Model

```python
{
  "player_id": str,
  "name": str,
  "injury_risk": str,        # "low", "medium", "high"
  "consistency": float,      # 0-100 consistency score
  "ceiling": float,          # Best-case fantasy points
  "floor": float,            # Worst-case fantasy points
  "volatility": float,       # Statistical volatility
  "recommendation": str      # Risk assessment summary
}
```

### Injury Model

```python
{
  "player_id": str,
  "name": str,
  "team": str,
  "injury_status": str,      # "Out", "Questionable", "Doubtful", "GTD"
  "injury_type": str,        # Body part/injury description
  "return_date": str,        # Estimated return (ISO date or "TBD")
  "impact": str              # "High", "Medium", "Low"
}
```

---

## FILE STRUCTURE

### Backend Directory

```
courtdominion-app/backend/
├── main.py                    # FastAPI application entry point
├── Dockerfile                 # Container definition
├── requirements.txt           # Python dependencies
├── models/
│   ├── player.py             # Player data model
│   ├── projection.py         # Projection data model
│   └── risk.py               # Risk data model
├── routers/
│   ├── health.py             # Health check endpoint
│   ├── players.py            # Player endpoints
│   ├── projections.py        # Projection endpoints
│   └── insights.py           # Insight endpoints
├── services/
│   ├── projections_service.py
│   ├── insights_service.py
│   └── risk_service.py
└── shared/
    └── load_shared_outputs.py  # Reads JSON files from /data/outputs/
```

### Data Directory

```
data/outputs/
├── players.json               # 398 players (69KB)
├── projections.json           # All projections (212KB)
├── insights.json              # Insights (59KB)
├── risk.json                  # Risk metrics (42KB)
├── injuries.json              # Current injuries (5KB)
├── player_stats_cache.json    # Cache (302KB, internal)
└── generated/                 # Daily content
    └── YYYY-MM-DD/
        ├── twitter_draft.txt
        ├── reddit_draft.txt
        ├── discord_draft.txt
        ├── linkedin_draft.txt
        ├── email_draft.txt
        ├── rationale.json
        └── manifest.json
```

---

## PERFORMANCE CHARACTERISTICS

### Response Times

| Endpoint | Avg Response | Max Payload |
|----------|--------------|-------------|
| /health | 5ms | 100 bytes |
| /api/players | 25ms | 69KB |
| /api/projections | 40ms | 212KB |
| /api/insights | 30ms | 59KB |
| /api/players/{id} | 15ms | 2KB |

### Update Frequency

- **Player Stats:** Daily at 5am EST
- **Projections:** Daily at 5am EST
- **Injuries:** Daily at 5am EST
- **Content:** Daily at 5am EST

### Data Freshness

All data is regenerated daily with:
- 398 active NBA players
- Real stats from NBA.com (5-year averages)
- Live injury data from ESPN
- AI-generated waiver wire content

---

## CORS CONFIGURATION

Backend is configured with permissive CORS for frontend development:

```python
allow_origins=["*"]  # All origins allowed (restrict in production)
allow_methods=["GET", "POST", "PUT", "DELETE"]
allow_headers=["*"]
```

Frontend can make requests from any domain during development.

---

## ERROR HANDLING

### Standard Error Response

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Player with ID '999999' not found",
    "status": 404
  }
}
```

### HTTP Status Codes

- `200 OK` - Success
- `404 Not Found` - Resource doesn't exist
- `500 Internal Server Error` - Backend error
- `503 Service Unavailable` - Data not ready

---

## DEPLOYMENT ARCHITECTURE

### Current Setup (Local Development)

```
Docker Compose:
  - Backend container (port 8000)
  - Automation container (runs daily pipeline)
  - Shared volume (data/outputs/)
```

### Production Setup (Railway)

```
Railway Service:
  - Single backend deployment
  - Automation via GitHub Actions (daily cron)
  - Persistent volume for data
  - Auto-scaling enabled
```

---

## FRONTEND INTEGRATION REQUIREMENTS

### Minimal Viable Frontend Needs

**Required Endpoints:**
1. `GET /api/projections` - Main data table
2. `GET /api/players/{id}` - Player details
3. `GET /health` - Connectivity check

**Optional (Nice to Have):**
4. `GET /api/insights` - Waiver wire recs
5. `GET /api/injuries` - Injury reports
6. `GET /api/projections/top` - Homepage highlights

### Sample Frontend Flow

```
User Lands on Homepage
  ↓
Frontend: GET /health
  → Backend: {status: "healthy"}
  ↓
Frontend: GET /api/projections?limit=50
  → Backend: {projections: [...50 players]}
  ↓
Display Table of Projections
  ↓
User Clicks Player
  ↓
Frontend: GET /api/players/{player_id}
  → Backend: {player details + projection + insight + risk}
  ↓
Display Player Detail Page
```

### Frontend Technology Suggestions

**Recommended:**
- React (component-based)
- TailwindCSS (styling)
- React Query (API calls)
- React Router (navigation)

**Data Fetching Example:**

```javascript
// Fetch projections
const { data, isLoading } = useQuery('projections', async () => {
  const res = await fetch('http://localhost:8000/api/projections?limit=50');
  return res.json();
});

// Display in table
{data?.projections.map(p => (
  <tr key={p.player_id}>
    <td>{p.name}</td>
    <td>{p.fantasy_points}</td>
    <td>{p.team}</td>
  </tr>
))}
```

---

## AUTHENTICATION & AUTHORIZATION

**Current State:** None (Phase 1)

**Future:** 
- User login (Phase 2)
- Subscription tiers (Phase 3)
- API keys for external access (Phase 3)

For MVP, backend is fully open and public.

---

## RATE LIMITING

**Current:** None

**Production:** 
- 100 requests/minute per IP
- Implemented via Railway

---

## MONITORING & LOGGING

**Local:**
- Docker logs: `docker compose logs backend`
- Pipeline logs: `data/outputs/logs/`

**Production:**
- Railway dashboard
- Error tracking via Sentry (future)

---

## LIMITATIONS & KNOWN ISSUES

1. **No database** - All data is file-based (Phase 1 only)
2. **No real-time updates** - Data refreshes daily, not live
3. **No user accounts** - Everyone sees same data
4. **No caching** - Frontend should implement client-side caching
5. **Rookie projections** - Not yet implemented (coming soon)

---

## NEXT STEPS FOR FRONTEND

1. **Evaluate this spec** - Is it sufficient for MVP frontend?
2. **Design UI/UX** - What pages do you need?
3. **Build components** - Start with projections table
4. **Integrate API** - Connect to backend endpoints
5. **Deploy** - Vercel/Netlify for frontend, Railway for backend

---

## QUESTIONS FOR FRONTEND PLANNING

1. What pages do you want in MVP?
   - Homepage with top performers?
   - Full projections table?
   - Player detail pages?
   - Waiver wire recommendations?
   - Injury report?

2. What features are must-have vs nice-to-have?

3. Do you need any data the backend doesn't currently provide?

4. What's your target launch timeline?

---

## CONTACT & SUPPORT

**Backend Owner:** Claude (CTO)  
**Product Owner:** Teebu  
**Launch Date:** January 19, 2026

---

**END OF BACKEND DOCUMENTATION**

**Status:** Production-ready backend, waiting for frontend to consume API
