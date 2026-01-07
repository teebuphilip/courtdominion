# COURTDOMINION BACKEND - TL;DR FOR TEEBU
## What You Have & What It Does

**Date:** December 18, 2025  
**Status:** ✅ Production Ready

---

## THE BIG PICTURE

You have a working NBA fantasy basketball backend that:
- Gets real NBA player stats every day
- Makes projections for 398 players
- Tells you who to pick up (waiver wire targets)
- Generates content for Twitter/Reddit/etc
- Serves everything via API for frontend to use

**Think of it like:** A vending machine full of NBA data. Frontend presses buttons (API calls), backend gives back snacks (JSON data).

---

## WHAT THE BACKEND DOES

### 1. Data Collection (Behind the Scenes)
- Hits NBA.com every day at 5am
- Gets stats for 398 active NBA players
- Gets injury data from ESPN
- Saves everything to files

### 2. Data Processing (The Smart Part)
- Runs your dbb2 projection engine (the 1500+ line code)
- Calculates fantasy points for each player
- Figures out who's a good waiver wire target
- Assesses risk (consistent vs boom/bust)

### 3. Content Generation (The Marketing Part)
- Uses ChatGPT to write content
- Creates Twitter threads, Reddit posts, Discord messages
- Filters out superstars (Jokić, Giannis) - focuses on deep sleepers
- Saves drafts for you to post

### 4. API Server (What Frontend Talks To)
- Runs on port 8000
- Answers questions like "give me all projections"
- Returns JSON data
- Always available (as long as Docker is running)

---

## THE API - SUPER SIMPLE VERSION

**What is an API?**
Think of it like a waiter at a restaurant. Frontend (customer) asks for something, API (waiter) brings it back.

### Main Requests Frontend Will Make:

**1. "Are you alive?"**
```
GET /health
→ "Yes, I'm healthy"
```

**2. "Give me all projections"**
```
GET /api/projections
→ Here's 398 players with their projected stats
```

**3. "Tell me about this specific player"**
```
GET /api/players/203507
→ Here's everything about Giannis
```

**4. "Who are the top 10 players today?"**
```
GET /api/projections/top?limit=10
→ Here's the top 10 by fantasy points
```

**5. "Who should I pick up off waivers?"**
```
GET /api/insights
→ Here are 20 waiver wire targets
```

**That's it.** Those 5 requests can build an entire frontend.

---

## THE DATA - WHAT YOU GET BACK

### Projection Data (The Main Thing)

For each player, you get:
- **Name:** "Giannis Antetokounmpo"
- **Fantasy Points:** 52.3 (how good they are)
- **Stats:** Points, rebounds, assists, etc.
- **Team:** "MIL"
- **Confidence:** 0.95 (how sure we are)

**Example:**
```json
{
  "name": "Giannis Antetokounmpo",
  "fantasy_points": 52.3,
  "points": 28.2,
  "rebounds": 11.1,
  "assists": 5.8
}
```

### Insight Data (The Advice)

For waiver wire targets:
- **Name:** "Tyrese Maxey"
- **Why:** "High usage with efficient scoring"
- **Recommendation:** "Add immediately"
- **Value Score:** 8.7 out of 10

---

## HOW FRONTEND USES THIS

**Step 1:** User opens your website  
**Step 2:** Frontend asks backend "give me projections"  
**Step 3:** Backend sends back 398 players  
**Step 4:** Frontend shows them in a nice table  
**Step 5:** User clicks a player  
**Step 6:** Frontend asks "tell me about this player"  
**Step 7:** Backend sends detailed info  
**Step 8:** Frontend shows player detail page  

**That's the whole flow.**

---

## WHAT FILES EXIST

### On Your Mac (data/outputs/)

```
players.json          ← All 398 players
projections.json      ← All projections
insights.json         ← Waiver wire recs
risk.json             ← Risk analysis
injuries.json         ← Who's hurt
generated/            ← Twitter/Reddit content
```

**Frontend doesn't touch these files directly.** Frontend only talks to the API.

---

## WHAT'S RUNNING

### Backend (Port 8000)
- FastAPI web server
- Answers API requests
- Always running via Docker

### Automation (Runs Daily)
- Builds cache of NBA stats
- Generates projections
- Creates content
- Updates all JSON files

**You don't need to think about automation when building frontend.** It just happens automatically.

---

## WHAT FRONTEND NEEDS TO BUILD

### Minimum Viable Product (MVP)

**3 Pages:**

1. **Homepage**
   - Table of all 398 projections
   - Sortable columns
   - Search bar

2. **Player Detail Page**
   - Full stats for one player
   - Projection + insight + risk
   - Charts/graphs optional

3. **Waiver Wire Page**
   - Top 20 recommendations
   - Why each player is good
   - "Add to watchlist" button (future)

**That's it.** That's the MVP.

---

## TECHNICAL STUFF (FOR CHATGPT)

**Backend Stack:**
- Python + FastAPI
- Docker containers
- File-based storage (no database yet)

**Frontend Stack (Recommended):**
- React
- TailwindCSS for styling
- Fetch API or React Query for API calls

**Deployment:**
- Backend: Railway ($5-10/month)
- Frontend: Vercel/Netlify (free)
- Total cost: $5-10/month

---

## WHAT YOU NEED TO DECIDE

Before building frontend, answer these:

1. **What pages do you want?**
   - Just projections table?
   - Player detail pages?
   - Waiver wire recommendations?
   - Injury report?

2. **What features are must-have?**
   - Search players?
   - Sort by stats?
   - Filter by team/position?
   - Compare players?

3. **What can wait?**
   - User accounts (Phase 2)
   - Save favorites (Phase 2)
   - Email alerts (Phase 2)

**Start simple.** Get a table of projections working first, then add features.

---

## CURRENT LIMITATIONS

**What backend CAN'T do (yet):**
- ❌ User accounts / login
- ❌ Real-time updates (only daily)
- ❌ Rookie projections (coming soon)
- ❌ Historical data
- ❌ Custom scoring

**What backend CAN do:**
- ✅ 398 players with projections
- ✅ Daily updates
- ✅ Waiver wire recommendations
- ✅ Injury data
- ✅ Risk analysis
- ✅ Generated content

---

## QUESTIONS TO ASK CHATGPT

When you give ChatGPT the full backend doc, ask:

1. "Is this backend sufficient for a minimal fantasy basketball frontend?"
2. "What pages should we build first?"
3. "What frontend framework do you recommend?"
4. "Can you create a component structure for the projections table?"
5. "How should we handle API calls efficiently?"

---

## NEXT STEPS

**Today:**
1. ✅ Backend is done
2. ✅ You have this doc
3. → Give full doc to ChatGPT
4. → ChatGPT designs frontend
5. → You approve design
6. → ChatGPT builds frontend
7. → You deploy both

**Timeline:**
- Frontend design: 1-2 days
- Frontend build: 3-5 days
- Testing: 1-2 days
- **Launch: January 19, 2026** ✅

---

## THE BOTTOM LINE

**You have:**
- ✅ Working backend with real NBA data
- ✅ 398 player projections
- ✅ API that serves everything frontend needs
- ✅ Daily automation that keeps data fresh

**You need:**
- React frontend that displays the data
- 3 simple pages (homepage, player detail, waiver wire)
- Basic styling (TailwindCSS)
- Deployment (Vercel)

**Cost:**
- Backend: $5-10/month (Railway)
- Frontend: $0/month (Vercel free tier)
- **Total: $5-10/month**

**You're 80% done.** Frontend is the last 20%.

---

**END OF TL;DR**

**Status:** Backend complete, ready for frontend development  
**Next:** Give complete doc to ChatGPT for frontend design
