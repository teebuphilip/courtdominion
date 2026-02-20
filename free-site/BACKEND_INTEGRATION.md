# Backend Integration for CourtDominion Frontend

## Required Backend Changes

The frontend expects a `/api/content` endpoint that currently doesn't exist in your backend.

---

## Step 1: Create Content Router

Create a new file in your backend:

**File:** `courtdominion-app/backend/routers/content.py`

```python
from fastapi import APIRouter, HTTPException
from pathlib import Path
import json

router = APIRouter()

DEFAULT_CONTENT = {
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
        "subtitle": "398 NBA players with risk-adjusted fantasy points",
        "email_gate": {
            "headline": "Want the full projections list?",
            "subheadline": "Get daily NBA fantasy insights delivered to your inbox",
            "cta": "Get Free Access"
        }
    },
    "insights_page": {
        "title": "Waiver Wire Insights",
        "subtitle": "Deep sleepers and value plays"
    }
}

@router.get("/content")
async def get_content():
    """
    Return dynamic content for frontend pages.
    
    This allows you to update website copy without redeploying the frontend.
    Content can be stored in a JSON file or returned as default values.
    """
    
    # Try to load from file first (if you want dynamic updates)
    content_file = Path("/data/outputs/content.json")
    if content_file.exists():
        try:
            with open(content_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading content file: {e}")
            # Fall back to default if file is corrupted
    
    # Return default content
    return DEFAULT_CONTENT
```

---

## Step 2: Register Router in Main App

Add the content router to your `main.py`:

**File:** `courtdominion-app/backend/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import your existing routers
from routers import players, projections, insights, health
from routers import content  # ADD THIS LINE

app = FastAPI(title="CourtDominion API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router, tags=["health"])
app.include_router(players.router, prefix="/api", tags=["players"])
app.include_router(projections.router, prefix="/api", tags=["projections"])
app.include_router(insights.router, prefix="/api", tags=["insights"])
app.include_router(content.router, prefix="/api", tags=["content"])  # ADD THIS LINE
```

---

## Step 3: Test the Endpoint

After adding the endpoint, restart your backend:

```bash
# If using Docker
docker compose restart backend

# If running locally
# Stop and restart your FastAPI server
```

Test that it works:

```bash
curl http://localhost:8000/api/content
```

You should see the JSON content returned.

---

## Optional: Dynamic Content Updates

If you want to update website copy without redeploying:

1. Create a content file at `/data/outputs/content.json`:

```json
{
  "homepage": {
    "headline": "Your Custom Headline Here",
    "subheadline": "Your custom subheadline",
    "value_props": [
      "Custom value prop 1",
      "Custom value prop 2",
      "Custom value prop 3"
    ],
    "cta_primary": "Your CTA",
    "cta_secondary": "Secondary CTA"
  },
  "projections_page": {
    "title": "Custom Projections Title",
    "subtitle": "Custom subtitle"
  },
  "insights_page": {
    "title": "Custom Insights Title",
    "subtitle": "Custom subtitle"
  }
}
```

2. The backend will automatically load this file instead of using defaults

3. To update copy:
   - Edit `/data/outputs/content.json`
   - Restart backend
   - Frontend will fetch new content on next page load

---

## Verification Checklist

- [ ] Created `content.py` router file
- [ ] Imported `content` router in `main.py`
- [ ] Registered router with app
- [ ] Restarted backend
- [ ] Tested endpoint with curl
- [ ] Frontend can fetch content successfully

---

## Troubleshooting

**Error:** `ModuleNotFoundError: No module named 'routers.content'`

**Solution:** Make sure you created the file in the correct location:
```
courtdominion-app/
└── backend/
    └── routers/
        └── content.py  # Must be here
```

**Error:** `404 Not Found` when accessing `/api/content`

**Solution:** Check that you added the router registration in `main.py`

---

## Complete Backend File Structure

After adding the content endpoint, your backend should look like:

```
courtdominion-app/backend/
├── main.py                  # FastAPI app (includes content router)
├── routers/
│   ├── health.py
│   ├── players.py
│   ├── projections.py
│   ├── insights.py
│   └── content.py           # NEW FILE
├── models/
├── services/
└── shared/
```

---

**That's it!** Once you add this endpoint, the frontend will be fully functional.
