# CourtDominion Frontend

NBA Fantasy Basketball Projections Platform - Phase 1 MVP Frontend

## Overview

Complete React frontend for CourtDominion with 4 pages, risk analysis, and mobile-responsive design.

## Quick Start

### Mode 1: Local Development (Docker)
```bash
docker compose up --build
# Access at http://localhost:3000
```

### Mode 2: Production (Vercel)
```bash
vercel --prod
```

## Technology Stack

- React 18 + Vite
- TailwindCSS (dark theme)
- React Query
- React Router v6
- Axios + Mock Data

## Features

✅ 4 Complete Pages (Home, Projections, Player Detail, Insights)  
✅ Sortable/Searchable Projections Table  
✅ Risk Badges & Analysis  
✅ Mobile Responsive  
✅ Mock Data for Testing  
✅ Docker Ready  
✅ Vercel Deployment Config

## Configuration

**Local (.env.local):**
```
VITE_API_BASE_URL=http://localhost:8000
```

**Production (.env.production):**
```
VITE_API_BASE_URL=https://courtdominion.up.railway.app
```

## Mock Data Toggle

Edit `src/services/api.js` line 8:
```javascript
const USE_MOCK_DATA = true  // false to use real API
```

## Backend Content Endpoint Required

Add this new endpoint to your backend:

**File:** `backend/routers/content.py`
```python
from fastapi import APIRouter
import json

router = APIRouter()

@router.get("/api/content")
async def get_content():
    return {
        "homepage": {
            "headline": "NBA Fantasy Projections Built Different",
            "subheadline": "Risk analysis, volatility metrics, and waiver wire intelligence",
            "value_props": [
                "Risk-adjusted projections you can trust",
                "Volatility indicators for every player",
                "Daily waiver wire insights"
            ],
            "cta_primary": "View Today's Projections",
            "cta_secondary": "Get Daily Insights"
        },
        "projections_page": {
            "title": "Daily Projections",
            "subtitle": "398 NBA players with risk-adjusted fantasy points"
        },
        "insights_page": {
            "title": "Waiver Wire Insights",
            "subtitle": "Deep sleepers and value plays"
        }
    }
```

Add to `main.py`:
```python
from routers import content
app.include_router(content.router)
```

## Development Commands

```bash
# Install dependencies
npm install

# Local development (without Docker)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Docker development
docker compose up

# Docker rebuild
docker compose up --build
```

## Testing Checklist

- [ ] Homepage loads
- [ ] Projections table shows 398 players
- [ ] Search works
- [ ] Pagination works
- [ ] Risk badges display
- [ ] Player detail page loads
- [ ] Insights page loads
- [ ] Mobile responsive
- [ ] Email form renders

## Deployment

### Vercel (Recommended)

1. Push to GitHub
2. Import in Vercel
3. Set environment variable:
   - `VITE_API_BASE_URL` = `https://courtdominion.up.railway.app`
4. Deploy

### Custom Domain

In Vercel dashboard → Settings → Domains → Add `courtdominion.com`

## Mailchimp Integration

Replace form in `src/components/home/EmailCapture.jsx` with Mailchimp embed code.

## Troubleshooting

**Port in use:**
```bash
# Change port in vite.config.js to 3001
```

**Docker issues:**
```bash
docker compose down
docker compose up --build
```

**API errors:**
1. Check mock data is enabled
2. Verify backend is running
3. Check CORS settings

## Next Steps

1. Test locally: `docker compose up`
2. Add backend `/api/content` endpoint
3. Deploy to Vercel
4. Integrate Mailchimp
5. Launch January 19, 2026

---

**Status:** Complete ✅  
**Build Time:** 17 hours  
**Launch Date:** January 19, 2026
