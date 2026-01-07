# COURTDOMINION API DOCUMENTATION
## Complete Endpoint Reference with Examples

**Version:** 1.0  
**Base URL (Local):** `http://localhost:8000`  
**Base URL (Production):** `https://courtdominion.up.railway.app`  
**Protocol:** HTTP/HTTPS  
**Format:** JSON

---

## TABLE OF CONTENTS

1. [Authentication](#authentication)
2. [Health Check](#health-check)
3. [Players Endpoints](#players-endpoints)
4. [Projections Endpoints](#projections-endpoints)
5. [Insights Endpoints](#insights-endpoints)
6. [Risk Endpoints](#risk-endpoints)
7. [Injuries Endpoints](#injuries-endpoints)
8. [Error Handling](#error-handling)
9. [Rate Limiting](#rate-limiting)
10. [Code Examples](#code-examples)

---

## AUTHENTICATION

**Current:** No authentication required (Phase 1)

All endpoints are publicly accessible. Future phases will require API keys.

---

## HEALTH CHECK

### Check API Status

**Endpoint:** `GET /health`

**Description:** Verify backend is running and responsive

**Request:**
```bash
curl http://localhost:8000/health
```

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2025-12-18T15:30:00Z",
  "version": "1.0.0"
}
```

**Use Cases:**
- Frontend initialization check
- Monitoring/uptime checks
- Load balancer health probes

---

## PLAYERS ENDPOINTS

### 1. Get All Players

**Endpoint:** `GET /api/players`

**Description:** Retrieve list of all active NBA players

**Parameters:** None

**Request:**
```bash
curl http://localhost:8000/api/players
```

**Response:** `200 OK`
```json
{
  "players": [
    {
      "id": "203507",
      "name": "Giannis Antetokounmpo",
      "team": "MIL",
      "position": "F",
      "age": 29,
      "height": "6-11",
      "weight": 242,
      "jersey": "34",
      "status": "active"
    },
    {
      "id": "1629029",
      "name": "Luka Dončić",
      "team": "DAL",
      "position": "G-F",
      "age": 24,
      "height": "6-7",
      "weight": 230,
      "jersey": "77",
      "status": "active"
    }
    // ... 396 more players
  ],
  "count": 398,
  "last_updated": "2025-12-18T06:00:00Z"
}
```

**Use Cases:**
- Populate player dropdown menus
- Enable autocomplete search
- Build player database for frontend

---

### 2. Get Single Player

**Endpoint:** `GET /api/players/{player_id}`

**Description:** Get detailed information for a specific player

**Path Parameters:**
- `player_id` (required): NBA player ID

**Request:**
```bash
curl http://localhost:8000/api/players/203507
```

**Response:** `200 OK`
```json
{
  "id": "203507",
  "name": "Giannis Antetokounmpo",
  "team": "MIL",
  "position": "F",
  "age": 29,
  "height": "6-11",
  "weight": 242,
  "jersey": "34",
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
    "field_goals_made": 10.3,
    "field_goals_attempted": 17.6,
    "fg_pct": 0.583,
    "free_throws_made": 5.9,
    "free_throws_attempted": 9.1,
    "ft_pct": 0.652,
    "three_pointers_made": 0.8,
    "three_pointers_attempted": 2.9,
    "three_point_pct": 0.285,
    "confidence": 0.95
  },
  "insight": {
    "player_id": "203507",
    "value_score": 9.2,
    "recommendation": "Must start in all formats",
    "reasoning": "Elite across-the-board production with high usage",
    "trending": "stable",
    "ownership_estimate": "100%",
    "insight_type": "elite"
  },
  "risk": {
    "player_id": "203507",
    "injury_risk": "low",
    "consistency": 92,
    "ceiling": 68.5,
    "floor": 38.2,
    "volatility": 0.15,
    "recommendation": "Safe first-round pick"
  }
}
```

**Error Response:** `404 Not Found`
```json
{
  "error": {
    "code": "PLAYER_NOT_FOUND",
    "message": "Player with ID '999999' not found",
    "status": 404
  }
}
```

**Use Cases:**
- Player detail pages
- Player comparison tool
- Lineup optimizer

---

### 3. Search Players

**Endpoint:** `GET /api/players/search`

**Description:** Search for players by name, team, or position

**Query Parameters:**
- `q` (required): Search query
- `limit` (optional): Max results (default: 10, max: 50)

**Request:**
```bash
curl "http://localhost:8000/api/players/search?q=giannis&limit=5"
```

**Response:** `200 OK`
```json
{
  "results": [
    {
      "id": "203507",
      "name": "Giannis Antetokounmpo",
      "team": "MIL",
      "position": "F",
      "match_score": 1.0
    },
    {
      "id": "1630828",
      "name": "Thanasis Antetokounmpo",
      "team": "MIL",
      "position": "F",
      "match_score": 0.85
    }
  ],
  "query": "giannis",
  "count": 2,
  "limit": 5
}
```

**Use Cases:**
- Search bar implementation
- Autocomplete suggestions
- Team/position filters

---

## PROJECTIONS ENDPOINTS

### 4. Get All Projections

**Endpoint:** `GET /api/projections`

**Description:** Retrieve fantasy projections for all players

**Query Parameters:**
- `limit` (optional): Max results (default: 100, max: 500)
- `offset` (optional): Pagination offset (default: 0)
- `sort_by` (optional): Sort field (default: "fantasy_points")
  - Options: "fantasy_points", "points", "rebounds", "assists", "steals", "blocks"
- `order` (optional): "asc" or "desc" (default: "desc")
- `position` (optional): Filter by position ("G", "F", "C", "G-F", "F-C")
- `team` (optional): Filter by team code ("LAL", "MIL", etc.)

**Request:**
```bash
curl "http://localhost:8000/api/projections?limit=50&sort_by=fantasy_points&order=desc"
```

**Response:** `200 OK`
```json
{
  "projections": [
    {
      "player_id": "203507",
      "name": "Giannis Antetokounmpo",
      "team": "MIL",
      "position": "F",
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
    {
      "player_id": "1629029",
      "name": "Luka Dončić",
      "team": "DAL",
      "position": "G-F",
      "fantasy_points": 51.8,
      "minutes": 36.2,
      "points": 28.4,
      "rebounds": 8.7,
      "assists": 8.8,
      "steals": 1.4,
      "blocks": 0.5,
      "turnovers": 4.1,
      "fg_pct": 0.486,
      "ft_pct": 0.742,
      "three_pointers": 3.2,
      "confidence": 0.93
    }
    // ... 48 more players
  ],
  "total": 398,
  "limit": 50,
  "offset": 0,
  "sort_by": "fantasy_points",
  "order": "desc",
  "last_updated": "2025-12-18T06:00:00Z"
}
```

**Pagination Example:**
```bash
# Page 1 (players 1-50)
curl "http://localhost:8000/api/projections?limit=50&offset=0"

# Page 2 (players 51-100)
curl "http://localhost:8000/api/projections?limit=50&offset=50"

# Page 3 (players 101-150)
curl "http://localhost:8000/api/projections?limit=50&offset=100"
```

**Filter Examples:**
```bash
# Only guards
curl "http://localhost:8000/api/projections?position=G"

# Only Lakers
curl "http://localhost:8000/api/projections?team=LAL"

# Top 20 rebounders
curl "http://localhost:8000/api/projections?sort_by=rebounds&limit=20"
```

**Use Cases:**
- Main projections table
- Sortable leaderboards
- Position-specific rankings

---

### 5. Get Top Performers

**Endpoint:** `GET /api/projections/top`

**Description:** Get top N players in a specific category

**Query Parameters:**
- `limit` (optional): Number of players (default: 10, max: 50)
- `category` (optional): Stat category (default: "fantasy_points")
  - Options: "fantasy_points", "points", "rebounds", "assists", "steals", "blocks", "three_pointers"

**Request:**
```bash
curl "http://localhost:8000/api/projections/top?limit=10&category=fantasy_points"
```

**Response:** `200 OK`
```json
{
  "top_performers": [
    {
      "player_id": "203507",
      "name": "Giannis Antetokounmpo",
      "team": "MIL",
      "position": "F",
      "fantasy_points": 52.3,
      "rank": 1
    },
    {
      "player_id": "1629029",
      "name": "Luka Dončić",
      "team": "DAL",
      "position": "G-F",
      "fantasy_points": 51.8,
      "rank": 2
    },
    {
      "player_id": "203954",
      "name": "Joel Embiid",
      "team": "PHI",
      "position": "C",
      "fantasy_points": 50.6,
      "rank": 3
    }
    // ... 7 more players
  ],
  "category": "fantasy_points",
  "limit": 10
}
```

**Category Examples:**
```bash
# Top 10 scorers
curl "http://localhost:8000/api/projections/top?category=points"

# Top 20 rebounders
curl "http://localhost:8000/api/projections/top?category=rebounds&limit=20"

# Top 15 three-point shooters
curl "http://localhost:8000/api/projections/top?category=three_pointers&limit=15"
```

**Use Cases:**
- Homepage highlights
- "Top 10 Today" widgets
- Category leaders

---

## INSIGHTS ENDPOINTS

### 6. Get Insights

**Endpoint:** `GET /api/insights`

**Description:** Get waiver wire recommendations and strategic insights

**Query Parameters:**
- `category` (optional): Filter by type (default: "all")
  - Options: "sleepers", "waiver_wire", "streaming", "trade_targets", "all"
- `limit` (optional): Max results (default: 20, max: 100)
- `min_value` (optional): Minimum value score (0-10)

**Request:**
```bash
curl "http://localhost:8000/api/insights?category=waiver_wire&limit=20"
```

**Response:** `200 OK`
```json
{
  "insights": [
    {
      "player_id": "1630567",
      "name": "Tyrese Maxey",
      "team": "PHI",
      "position": "G",
      "insight_type": "waiver_wire",
      "value_score": 8.7,
      "recommendation": "Add immediately",
      "reasoning": "High usage rate with efficient scoring across the board",
      "trending": "up",
      "ownership_estimate": "45%",
      "fantasy_points": 38.2
    },
    {
      "player_id": "1630596",
      "name": "Deni Avdija",
      "team": "POR",
      "position": "F",
      "insight_type": "streaming",
      "value_score": 7.2,
      "recommendation": "Stream for rebounds/assists",
      "reasoning": "Strong all-around game with 4+ games this week",
      "trending": "stable",
      "ownership_estimate": "28%",
      "fantasy_points": 32.1
    }
    // ... 18 more insights
  ],
  "category": "waiver_wire",
  "count": 20,
  "limit": 20
}
```

**Category Examples:**
```bash
# Deep sleepers only
curl "http://localhost:8000/api/insights?category=sleepers"

# Streaming candidates
curl "http://localhost:8000/api/insights?category=streaming&limit=10"

# High-value targets only
curl "http://localhost:8000/api/insights?min_value=8.0"
```

**Use Cases:**
- Waiver wire page
- Strategic recommendations
- Weekly add/drop suggestions

---

## RISK ENDPOINTS

### 7. Get Risk Assessments

**Endpoint:** `GET /api/risk`

**Description:** Get risk analysis for players (consistency, ceiling, floor)

**Query Parameters:**
- `player_id` (optional): Specific player
- `risk_level` (optional): Filter by risk ("low", "medium", "high")
- `limit` (optional): Max results (default: 50, max: 500)

**Request (All Players):**
```bash
curl "http://localhost:8000/api/risk?limit=50"
```

**Response:** `200 OK`
```json
{
  "risk_assessments": [
    {
      "player_id": "203507",
      "name": "Giannis Antetokounmpo",
      "team": "MIL",
      "injury_risk": "low",
      "consistency": 92,
      "ceiling": 68.5,
      "floor": 38.2,
      "volatility": 0.15,
      "recommendation": "Safe first-round pick"
    },
    {
      "player_id": "1630567",
      "name": "Tyrese Maxey",
      "team": "PHI",
      "injury_risk": "low",
      "consistency": 78,
      "ceiling": 55.3,
      "floor": 22.8,
      "volatility": 0.35,
      "recommendation": "High upside with some volatility"
    }
    // ... 48 more assessments
  ],
  "count": 50,
  "limit": 50
}
```

**Request (Single Player):**
```bash
curl "http://localhost:8000/api/risk?player_id=203507"
```

**Response:** `200 OK`
```json
{
  "player_id": "203507",
  "name": "Giannis Antetokounmpo",
  "team": "MIL",
  "injury_risk": "low",
  "consistency": 92,
  "ceiling": 68.5,
  "floor": 38.2,
  "volatility": 0.15,
  "recommendation": "Safe first-round pick",
  "risk_factors": [
    "High minutes load",
    "Playoff rest risk"
  ],
  "confidence": 0.95
}
```

**Filter Examples:**
```bash
# Only high-risk players
curl "http://localhost:8000/api/risk?risk_level=high"

# Only safe players
curl "http://localhost:8000/api/risk?risk_level=low&limit=20"
```

**Use Cases:**
- Risk analysis tool
- Player comparison
- Draft strategy

---

## INJURIES ENDPOINTS

### 8. Get Injuries

**Endpoint:** `GET /api/injuries`

**Description:** Get current injury report for all players

**Query Parameters:**
- `status` (optional): Filter by status ("Out", "Questionable", "Doubtful", "GTD")
- `team` (optional): Filter by team code

**Request:**
```bash
curl "http://localhost:8000/api/injuries"
```

**Response:** `200 OK`
```json
{
  "injuries": [
    {
      "player_id": "202695",
      "name": "Kawhi Leonard",
      "team": "LAC",
      "injury_status": "Out",
      "injury_type": "Knee",
      "details": "Right knee injury management",
      "return_date": "2025-12-25",
      "impact": "High",
      "fantasy_impact": "Do not start"
    },
    {
      "player_id": "1628983",
      "name": "Shai Gilgeous-Alexander",
      "team": "OKC",
      "injury_status": "Questionable",
      "injury_type": "Ankle",
      "details": "Left ankle sprain",
      "return_date": "2025-12-19",
      "impact": "Medium",
      "fantasy_impact": "Monitor closely"
    }
    // ... 45 more injuries
  ],
  "count": 47,
  "last_updated": "2025-12-18T06:00:00Z"
}
```

**Filter Examples:**
```bash
# Only players ruled out
curl "http://localhost:8000/api/injuries?status=Out"

# Lakers injuries only
curl "http://localhost:8000/api/injuries?team=LAL"
```

**Use Cases:**
- Injury report page
- Lineup alerts
- Waiver wire opportunities

---

## ERROR HANDLING

### Standard Error Response

All errors follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "status": 400
  }
}
```

### Common Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `INVALID_PARAMETER` | Query parameter is invalid |
| 404 | `RESOURCE_NOT_FOUND` | Player/resource doesn't exist |
| 500 | `INTERNAL_ERROR` | Server error |
| 503 | `SERVICE_UNAVAILABLE` | Data not ready/backend down |

### Error Examples

**404 - Player Not Found:**
```json
{
  "error": {
    "code": "PLAYER_NOT_FOUND",
    "message": "Player with ID '999999' not found",
    "status": 404
  }
}
```

**400 - Invalid Parameter:**
```json
{
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "Parameter 'limit' must be between 1 and 500",
    "status": 400
  }
}
```

**503 - Service Unavailable:**
```json
{
  "error": {
    "code": "DATA_NOT_READY",
    "message": "Projections are being generated. Try again in a few minutes.",
    "status": 503
  }
}
```

---

## RATE LIMITING

**Current:** No rate limiting (Phase 1)

**Future:** 100 requests/minute per IP

**Headers (Future):**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640000000
```

---

## CODE EXAMPLES

### JavaScript / React

```javascript
// Fetch all projections
async function getProjections() {
  const response = await fetch('http://localhost:8000/api/projections?limit=50');
  const data = await response.json();
  return data.projections;
}

// Fetch single player
async function getPlayer(playerId) {
  const response = await fetch(`http://localhost:8000/api/players/${playerId}`);
  if (!response.ok) {
    throw new Error('Player not found');
  }
  return await response.json();
}

// Search players
async function searchPlayers(query) {
  const response = await fetch(`http://localhost:8000/api/players/search?q=${encodeURIComponent(query)}`);
  const data = await response.json();
  return data.results;
}
```

### React Query

```javascript
import { useQuery } from 'react-query';

// Hook for projections
function useProjections(limit = 50) {
  return useQuery('projections', async () => {
    const res = await fetch(`http://localhost:8000/api/projections?limit=${limit}`);
    const data = await res.json();
    return data.projections;
  });
}

// Usage in component
function ProjectionsTable() {
  const { data, isLoading, error } = useProjections(50);
  
  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error loading data</div>;
  
  return (
    <table>
      {data.map(player => (
        <tr key={player.player_id}>
          <td>{player.name}</td>
          <td>{player.fantasy_points}</td>
        </tr>
      ))}
    </table>
  );
}
```

### Python

```python
import requests

# Get projections
response = requests.get('http://localhost:8000/api/projections', params={'limit': 50})
projections = response.json()['projections']

# Get player
player_id = '203507'
response = requests.get(f'http://localhost:8000/api/players/{player_id}')
player = response.json()

# Search
response = requests.get('http://localhost:8000/api/players/search', params={'q': 'giannis'})
results = response.json()['results']
```

### cURL

```bash
# Health check
curl http://localhost:8000/health

# Get all projections
curl "http://localhost:8000/api/projections?limit=50"

# Get single player
curl http://localhost:8000/api/players/203507

# Search players
curl "http://localhost:8000/api/players/search?q=giannis"

# Get top 10
curl "http://localhost:8000/api/projections/top?limit=10"

# Get insights
curl "http://localhost:8000/api/insights?category=waiver_wire"

# Get injuries
curl http://localhost:8000/api/injuries
```

---

## CORS CONFIGURATION

Backend allows requests from any origin during development:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: *
```

Frontend can make requests without CORS issues.

---

## BEST PRACTICES

### Caching

**Recommended:** Cache responses on frontend for 5-10 minutes

```javascript
// React Query example with caching
useQuery('projections', fetchProjections, {
  staleTime: 5 * 60 * 1000, // 5 minutes
  cacheTime: 10 * 60 * 1000  // 10 minutes
});
```

### Error Handling

Always handle errors gracefully:

```javascript
async function getPlayer(id) {
  try {
    const res = await fetch(`/api/players/${id}`);
    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.error.message);
    }
    return await res.json();
  } catch (error) {
    console.error('Failed to fetch player:', error);
    return null;
  }
}
```

### Pagination

For large datasets, use pagination:

```javascript
function useProjections(page = 1, limit = 50) {
  const offset = (page - 1) * limit;
  return useQuery(['projections', page], async () => {
    const res = await fetch(`/api/projections?limit=${limit}&offset=${offset}`);
    return await res.json();
  });
}
```

---

## TESTING ENDPOINTS

### Using Browser

1. Open `http://localhost:8000/health` - should see JSON response
2. Open `http://localhost:8000/api/projections?limit=10` - should see 10 projections
3. Open `http://localhost:8000/api/players/203507` - should see Giannis

### Using Postman

1. Import endpoint collection (if available)
2. Set base URL to `http://localhost:8000`
3. Test each endpoint
4. Save example responses

### Using Code

```javascript
// Quick test script
async function testAPI() {
  const tests = [
    '/health',
    '/api/players',
    '/api/projections?limit=10',
    '/api/insights?category=waiver_wire'
  ];
  
  for (const endpoint of tests) {
    const res = await fetch(`http://localhost:8000${endpoint}`);
    console.log(`${endpoint}: ${res.status}`);
  }
}

testAPI();
```

---

## CHANGELOG

### Version 1.0 (2025-12-18)
- Initial production release
- 398 players with projections
- 8 core endpoints
- Real NBA data integration
- Content generation support

---

**END OF API DOCUMENTATION**

**Questions?** Reference the complete backend documentation for architecture details.
