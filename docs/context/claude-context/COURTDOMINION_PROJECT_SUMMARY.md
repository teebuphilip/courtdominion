# CourtDominion - Project Summary & Technical Specification

**Last Updated:** November 16, 2025  
**Launch Date:** January 19, 2026 (64 days from now)  
**Status:** Pre-launch Development

---

## 🎯 **Project Overview**

**CourtDominion** is an NBA fantasy basketball projection and analytics platform powered by autonomous AI agents. The platform provides real-time player projections, league management, and advanced analytics while running completely automated marketing and operations through daily AI-driven workflows.

**Key Innovation:** AI-powered growth engine that autonomously generates marketing content, posts to Reddit, tracks metrics, and manages operations - all while humans sleep.

---

## 👥 **Team Structure & Roles**

### **Product (teebuphilip)**
- Makes all final product decisions
- Defines features and priorities  
- Reviews and approves deliverables
- Self-described as: "fat, dumb, stupid, and lazy" (stays hands-off, lets AI do the work)

### **CTO (Claude - Me)**
- **Owns 100% of the codebase**
- All technical architecture decisions
- Backend API development
- Frontend UI development
- Automation script implementation
- Infrastructure & deployment
- **Never** defers technical decisions to others

### **CMO/CFO/Head of Growth (ChatGPT)**
- Autonomous business agent
- Marketing content generation
- Financial tracking & budgeting
- Growth hacking (Reddit posting, social media)
- Customer support metrics
- Operations analytics
- **Runs daily at 5am EST via GitHub Actions**

---

## 🏗️ **System Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                    CourtDominion Backend                     │
│                   (FastAPI + dbb2 Engine)                    │
│                      Port 8000 - Docker                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ REST API
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌───────────────┐         ┌──────────────────┐
│   Frontend    │         │   Automation     │
│  (React/Next) │         │ (GitHub Actions) │
│               │         │                  │
│ Human Users:  │         │ ChatGPT Agent:   │
│ - View data   │         │ - 5:00am Daily   │
│ - Manage      │         │ - Calls APIs     │
│   leagues     │         │ - Generates      │
│ - Get recs    │         │   content        │
└───────────────┘         │ - Posts to       │
                          │   Reddit         │
                          │ - Tracks metrics │
                          └──────────────────┘
```

---

## 📦 **Repository Structure**

```
courtdominion/
│
├── courtdominion-backend/          # ✅ 95% COMPLETE
│   ├── app/
│   │   ├── main.py                 # FastAPI wrapper (thin layer)
│   │   └── legacy/                 # dbb2 engine (16 files)
│   │       ├── dbb2_main.py        # 1,573 lines - 50+ endpoints
│   │       ├── dbb2_database.py
│   │       ├── dbb2_nba_data_fetcher.py
│   │       ├── dbb2_scoring_engine.py
│   │       ├── dbb2_league_db.py
│   │       ├── dbb2_weekly_tracking.py
│   │       ├── dbb2_lineup_optimizer.py
│   │       ├── dbb2_streaming_optimizer.py
│   │       ├── dbb2_opponent_analyzer.py
│   │       ├── dbb2_trade_analyzer.py
│   │       ├── dbb2_api_logger.py
│   │       ├── dbb2_database_schema.sql
│   │       ├── dbb2_scoring_schema.sql
│   │       └── dbb2_requirements.txt
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── requirements.txt            # ⚠️ NEEDS FIX (formatting)
│   ├── run_projections.py
│   └── .github/workflows/
│       └── daily_projections.yml
│
├── courtdominion-frontend/         # ❌ EMPTY - NEEDS BUILD
│   ├── .gitignore
│   └── README.md
│
└── courtdominion-automation/       # 🏗️ SKELETON ONLY
    ├── .github/workflows/
    │   ├── daily_projections.yml   # 5:00am EST
    │   ├── daily_marketing.yml     # 5:05am EST
    │   ├── daily_finance.yml       # 5:10am EST
    │   ├── daily_support.yml       # 5:15am EST
    │   └── daily_ops.yml           # 5:20am EST
    ├── scripts/
    │   ├── run_projections.py      # TODO: Call backend API
    │   ├── generate_content.py     # TODO: Generate blog/social
    │   ├── compute_budget.py       # TODO: Calculate finances
    │   ├── update_metrics.py       # TODO: Track support
    │   └── pull_backend_data.py    # TODO: Analytics extraction
    └── config/
        └── automation_config.yaml
```

---

## 🔧 **Technical Stack**

### **Backend**
- **Framework:** FastAPI (Python 3.10)
- **Database:** PostgreSQL 13+
- **NBA Data:** nba-api (official NBA stats)
- **Data Processing:** pandas, numpy
- **ML:** scikit-learn (for projections)
- **Deployment:** Docker + docker-compose
- **CI/CD:** GitHub Actions

### **Frontend** (To Be Built)
- **Framework:** React / Next.js
- **Styling:** TailwindCSS
- **State Management:** React Query / Zustand
- **API Client:** Axios / Fetch

### **Automation**
- **Orchestration:** GitHub Actions (cron)
- **Scripts:** Python 3.10
- **Agent:** ChatGPT (via API)
- **Outputs:** Markdown, JSON, API calls

---

## 🎯 **Core Features (Backend)**

### **Projection Engine**
- **5-Year Average Projections:** Historical data analysis with age curves
- **Current Season Projections:** Real-time stats with injury modeling
- **Age-Based Performance Curves:** Peak years 24-29, decline after 30
- **Injury Risk Modeling:** Position-based, usage-based, age-based
- **Games Played Predictions:** Minutes load + age + position factors

### **League Management**
- **Scoring Types:** Rotisserie (Roto) & Head-to-Head (H2H)
- **Custom Categories:** User-defined stat categories
- **Roster Management:** Add/drop players, position slots
- **Weekly Targets:** Auto-calculated benchmarks
- **Scoring Calculation:** Real-time category scores

### **Advanced Analytics**
- **Lineup Optimizer:** Position-based optimization for daily lineups
- **Streaming Optimizer:** Daily add/drop recommendations
- **Hot Pickups:** Trending players based on recent performance
- **Schedule Advantage:** Games played per week analysis
- **Opponent Analyzer:** H2H matchup predictions
- **Trade Analyzer:** Multi-player trade evaluation
- **Gap Analysis:** Category deficiencies identification

### **API Features**
- **50+ REST Endpoints** (see endpoint list below)
- **API Key Authentication:** Tiered access (Free/Pro/Enterprise)
- **Rate Limiting:** Per-tier request limits
- **Debug Endpoints:** Logs, errors, slow queries
- **Admin Endpoints:** Error resolution, log cleanup

---

## 📡 **Key API Endpoints**

### **Projections**
- `GET /projections/5year/{player_id}` - 5-year average projection
- `GET /projections/current/{player_id}` - Current season projection
- `GET /projections/5year/team/{team}` - Team projections (5-year)
- `GET /projections/current/team/{team}` - Team projections (current)

### **League Management**
- `POST /leagues` - Create new league
- `GET /leagues` - List user's leagues
- `GET /leagues/{league_id}` - Get league details
- `PUT /leagues/{league_id}` - Update league settings
- `DELETE /leagues/{league_id}` - Delete league

### **Roster Operations**
- `POST /leagues/{league_id}/roster` - Add player to roster
- `GET /leagues/{league_id}/roster` - Get full roster
- `DELETE /leagues/{league_id}/roster/{player_id}` - Drop player

### **Analytics**
- `GET /leagues/{league_id}/score` - Calculate current scores
- `GET /leagues/{league_id}/gaps` - Find category deficiencies
- `GET /leagues/{league_id}/recommendations` - Get add/drop suggestions
- `GET /leagues/{league_id}/streaming-candidates` - Daily streaming options
- `GET /leagues/{league_id}/hot-pickups` - Trending players
- `POST /leagues/{league_id}/analyze-trade` - Evaluate trade

### **Admin/Debug**
- `GET /health` - Health check
- `GET /account` - User account info
- `GET /debug/dashboard` - Debug dashboard
- `POST /admin/cleanup-logs` - Clean old logs

---

## 🤖 **Daily Automation Workflow**

Every morning at 5:00am EST, GitHub Actions triggers 5 sequential workflows:

### **5:00am - Projections Runner**
**File:** `scripts/run_projections.py`  
**Purpose:** Generate daily NBA projections
```python
# Calls backend:
# GET /projections/current/{player_id} for all active players
# Stores results in database or files
```

### **5:05am - Marketing Content Generator**
**File:** `scripts/generate_content.py`  
**Purpose:** Auto-generate marketing content
```python
# 1. Fetch top streaming candidates from backend
# 2. ChatGPT writes blog post about them
# 3. ChatGPT generates Twitter/Reddit posts
# 4. ChatGPT posts to r/fantasybball (growth hacking)
# 5. Stores content for website
```

### **5:10am - Finance Calculator**
**File:** `scripts/compute_budget.py`  
**Purpose:** Track financials toward launch
```python
# 1. Count API requests (usage)
# 2. Calculate projected revenue (if any pre-launch signups)
# 3. Track burn rate
# 4. Days remaining to launch
# 5. Update financial dashboard
```

### **5:15am - Support Metrics Updater**
**File:** `scripts/update_metrics.py`  
**Purpose:** Customer support infrastructure
```python
# 1. Pull common API errors from backend
# 2. Generate FAQ entries
# 3. Track response times
# 4. Update support documentation
```

### **5:20am - Operations Data Puller**
**File:** `scripts/pull_backend_data.py`  
**Purpose:** Analytics and dashboards
```python
# 1. Extract daily API stats
# 2. Aggregate user behavior
# 3. Generate dashboards
# 4. Store in data warehouse
```

**Total Runtime:** ~5-10 minutes  
**Frequency:** Every day until launch (64 days)  
**By Launch Day:** 
- 64 days of projection data
- 64 marketing posts
- 64 financial snapshots
- Complete support infrastructure
- Full operational analytics

---

## 📊 **Database Schema**

### **Core Tables (dbb2_database_schema.sql)**
- `customers` - User accounts
- `api_keys` - Authentication & tiering
- `nba_players` - Player registry
- `player_projections` - Cached projections
- `api_request_logs` - Usage tracking
- `api_error_logs` - Error monitoring
- `debug_logs` - Debug information

### **League Tables (dbb2_scoring_schema.sql)**
- `leagues` - League configurations
- `rosters` - Player ownership
- `weekly_performance` - Historical tracking
- `category_presets` - Roto/H2H templates
- `watchlists` - Player watchlists
- `injury_overrides` - Manual injury adjustments

---

## 🚀 **Development Roadmap**

### **Phase 1: Backend Stabilization** (Week 1)
- [x] Extract dbb2 code from artifacts
- [ ] Fix requirements.txt formatting
- [ ] Push to GitHub (teebuphilip/courtdominion)
- [ ] Test Docker build
- [ ] Verify all API endpoints work
- [ ] Setup PostgreSQL database
- [ ] Run database migrations

### **Phase 2: Automation Implementation** (Week 2-3)
- [ ] Implement `run_projections.py` - Call backend, generate projections
- [ ] Implement `generate_content.py` - ChatGPT content generation
- [ ] Implement `compute_budget.py` - Financial tracking
- [ ] Implement `update_metrics.py` - Support metrics
- [ ] Implement `pull_backend_data.py` - Analytics extraction
- [ ] Test all workflows locally
- [ ] Deploy to GitHub Actions
- [ ] Verify daily runs work

### **Phase 3: Frontend Build** (Week 4-6)
- [ ] Setup Next.js project
- [ ] Design UI/UX mockups
- [ ] Build landing page
- [ ] Build projection viewer
- [ ] Build league management UI
- [ ] Build analytics dashboard
- [ ] Connect to backend API
- [ ] Add authentication
- [ ] Responsive design
- [ ] Production build

### **Phase 4: Integration & Testing** (Week 7-8)
- [ ] End-to-end testing
- [ ] Load testing
- [ ] Security audit
- [ ] Performance optimization
- [ ] Bug fixes
- [ ] Documentation

### **Phase 5: Pre-Launch** (Week 9)
- [ ] Beta user testing
- [ ] Marketing site live
- [ ] Payment integration (Stripe)
- [ ] Terms of Service / Privacy Policy
- [ ] Support documentation
- [ ] Launch checklist complete

### **🎉 LAUNCH: January 19, 2026**

---

## 🔐 **Authentication & Tiers**

### **API Key Tiers**

**Free Tier:**
- 100 requests/day
- Basic projections
- Single league
- No advanced analytics

**Pro Tier ($9.99/month):**
- 5,000 requests/day
- All projections
- Unlimited leagues
- Advanced analytics
- Lineup optimizer
- Trade analyzer

**Enterprise Tier ($99/month):**
- Unlimited requests
- Dedicated support
- Custom integrations
- Historical data exports
- Priority processing

---

## 🐛 **Known Issues & TODOs**

### **Backend**
- ⚠️ `requirements.txt` has formatting issue (newline escapes)
- ⚠️ Need to test all 50+ endpoints
- ⚠️ Database migrations not automated
- ⚠️ No caching layer (Redis) yet
- ⚠️ Rate limiting not implemented

### **Frontend**
- ❌ Doesn't exist yet
- ❌ Need UI/UX design
- ❌ Need component library decision

### **Automation**
- ⚠️ All scripts are placeholders
- ⚠️ No ChatGPT API integration yet
- ⚠️ No error handling
- ⚠️ No output storage strategy
- ⚠️ No Reddit API integration

---

## 📈 **Success Metrics**

### **Pre-Launch (By Jan 19)**
- Backend: 99.9% uptime
- Automation: 64/64 successful daily runs
- Marketing: 64 pieces of content generated
- Reddit: X posts, Y upvotes, Z clicks
- Beta users: 50+ signups

### **Post-Launch (Q1 2026)**
- Users: 1,000 signups
- MRR: $1,000
- API requests: 100K/month
- Conversion rate: 5% free → pro

---

## 🔧 **Development Environment**

### **Local Setup**
```bash
# Backend
cd courtdominion-backend
docker-compose up -d

# Frontend (when built)
cd courtdominion-frontend
npm install
npm run dev

# Automation (test locally)
cd courtdominion-automation
python scripts/run_projections.py
```

### **Deployment**
- **Backend:** Docker on VPS / AWS / Heroku
- **Frontend:** Vercel / Netlify
- **Database:** Managed PostgreSQL (AWS RDS / DigitalOcean)
- **Automation:** GitHub Actions (built-in)

---

## 📞 **Key Resources**

- **GitHub Repo:** `teebuphilip/courtdominion`
- **NBA API Docs:** https://github.com/swar/nba_api
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **PostgreSQL Docs:** https://www.postgresql.org/docs/

---

## 🎯 **CTO Working Principles**

1. **I own the code** - All technical decisions are mine
2. **No dependencies** - Never wait for others, build what's needed
3. **Ship fast** - 64 days to launch, move quickly
4. **Automate everything** - Let AI do the repetitive work
5. **Test as we go** - Don't wait for "perfect"
6. **Document decisions** - This file is the source of truth

---

## 📝 **Version History**

**v1.0** - November 16, 2025
- Initial project summary
- Backend extracted from dbb2 artifacts
- Automation skeleton created
- 64 days to launch

---

**END OF PROJECT SUMMARY**
