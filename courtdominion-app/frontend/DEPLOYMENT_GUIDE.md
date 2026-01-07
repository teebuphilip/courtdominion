# CourtDominion Frontend - Deployment Guide

Complete guide for local testing and production deployment.

## Table of Contents

1. [Local Development (Docker)](#local-development-docker)
2. [Local Development (No Docker)](#local-development-no-docker)
3. [Production Deployment (Vercel)](#production-deployment-vercel)
4. [Backend Integration](#backend-integration)
5. [Environment Configuration](#environment-configuration)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

---

## Local Development (Docker)

### Prerequisites
- Docker installed
- Docker Compose installed

### Steps

1. **Navigate to project directory:**
```bash
cd courtdominion-frontend
```

2. **Build and start container:**
```bash
docker compose up --build
```

3. **Access application:**
```
http://localhost:3000
```

4. **Hot reload is enabled** - edit files and see changes immediately

5. **Stop container:**
```bash
# Ctrl+C, then:
docker compose down
```

### Docker Commands Reference

```bash
# Start (without rebuild)
docker compose up

# Start in background
docker compose up -d

# View logs
docker compose logs -f

# Rebuild after package changes
docker compose up --build

# Stop and remove containers
docker compose down

# Remove volumes too
docker compose down -v
```

---

## Local Development (No Docker)

### Prerequisites
- Node.js 18+ installed
- npm installed

### Steps

1. **Install dependencies:**
```bash
npm install
```

2. **Start development server:**
```bash
npm run dev
```

3. **Access application:**
```
http://localhost:3000
```

4. **Build for production:**
```bash
npm run build
```

5. **Preview production build:**
```bash
npm run preview
```

---

## Production Deployment (Vercel)

### Option A: Vercel CLI

1. **Install Vercel CLI:**
```bash
npm i -g vercel
```

2. **Login to Vercel:**
```bash
vercel login
```

3. **Deploy (preview):**
```bash
vercel
```

4. **Set environment variable:**
```bash
vercel env add VITE_API_BASE_URL production
# When prompted, enter: https://courtdominion.up.railway.app
```

5. **Deploy to production:**
```bash
vercel --prod
```

6. **Done!** Your site is live at the Vercel URL

### Option B: GitHub Integration (Recommended)

1. **Push code to GitHub:**
```bash
git init
git add .
git commit -m "Initial commit - CourtDominion frontend"
git remote add origin <your-repo-url>
git push -u origin main
```

2. **Go to [vercel.com](https://vercel.com)**

3. **Click "Import Project"**

4. **Select your GitHub repository**

5. **Configure project:**
   - **Framework Preset:** Vite
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
   - **Install Command:** `npm install`

6. **Add Environment Variables:**
   - Click "Environment Variables"
   - Add variable:
     - Name: `VITE_API_BASE_URL`
     - Value: `https://courtdominion.up.railway.app`
     - Environment: Production

7. **Click "Deploy"**

8. **Wait for deployment** (~2-3 minutes)

9. **Your site is live!**

### Custom Domain Setup (Optional)

1. In Vercel dashboard, go to your project
2. Click "Settings" → "Domains"
3. Add domain: `courtdominion.com`
4. Follow DNS configuration instructions
5. Wait for DNS propagation (5-30 minutes)

---

## Backend Integration

### Required Backend Changes

The frontend expects a `/api/content` endpoint that doesn't exist yet.

**Add this file to your backend:**

**File:** `courtdominion-app/backend/routers/content.py`

```python
from fastapi import APIRouter
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
        "subtitle": "398 NBA players with risk-adjusted fantasy points"
    },
    "insights_page": {
        "title": "Waiver Wire Insights",
        "subtitle": "Deep sleepers and value plays"
    }
}

@router.get("/api/content")
async def get_content():
    content_file = Path("/data/outputs/content.json")
    if content_file.exists():
        with open(content_file) as f:
            return json.load(f)
    return DEFAULT_CONTENT
```

**Update main.py:**

```python
# Add this import
from routers import content

# Add this line after other router includes
app.include_router(content.router)
```

**Restart backend:**

```bash
docker compose restart backend
```

**Test endpoint:**

```bash
curl http://localhost:8000/api/content
```

---

## Environment Configuration

### Local Development

**File:** `.env.local`
```bash
VITE_API_BASE_URL=http://localhost:8000
```

This file is used automatically when running `npm run dev` or `docker compose up`.

### Production

**File:** `.env.production`
```bash
VITE_API_BASE_URL=https://courtdominion.up.railway.app
```

This file is used when building for production (`npm run build`).

**For Vercel:** Set as environment variable in dashboard (not in file).

### Mock Data Toggle

**File:** `src/services/api.js`

Line 8:
```javascript
const USE_MOCK_DATA = true  // Set to false to use real API
```

**When to use mock data:**
- Testing frontend without backend
- Local development
- Vercel preview deployments

**When to use real API:**
- Production deployment
- Integration testing
- Final QA before launch

---

## Testing

### Functionality Checklist

```bash
# Start the app
docker compose up
# or
npm run dev
```

Visit `http://localhost:3000` and verify:

- [ ] **Homepage:**
  - [ ] Loads without errors
  - [ ] Hero section displays
  - [ ] Value props show
  - [ ] Email capture form renders
  - [ ] CTA buttons work

- [ ] **Projections Page:**
  - [ ] Table loads with players
  - [ ] Search filters players
  - [ ] Sort by clicking column headers
  - [ ] Pagination works
  - [ ] Risk badges display
  - [ ] Click player → goes to detail page

- [ ] **Player Detail Page:**
  - [ ] Player info loads
  - [ ] Stats display correctly
  - [ ] Risk analysis shows
  - [ ] Back button works

- [ ] **Insights Page:**
  - [ ] Insights load
  - [ ] Filter by category works
  - [ ] Value scores display
  - [ ] Trending icons show

- [ ] **Navigation:**
  - [ ] Header links work
  - [ ] Mobile menu works
  - [ ] Footer displays

### Responsive Testing

Test at these viewport sizes:

- [ ] **Mobile:** 375px width
- [ ] **Tablet:** 768px width
- [ ] **Desktop:** 1280px width

### Browser Testing

- [ ] Chrome
- [ ] Firefox
- [ ] Safari
- [ ] Edge
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

### Performance Testing

```bash
npm run build
npm run preview
```

Check:
- [ ] Initial load < 3 seconds
- [ ] No console errors
- [ ] No 404s in network tab
- [ ] Bundle size < 500KB

---

## Troubleshooting

### Issue: Port 3000 already in use

**Solution:**
```bash
# Option 1: Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Option 2: Change port in vite.config.js
server: {
  port: 3001
}
```

### Issue: Docker container won't start

**Solution:**
```bash
# Clean rebuild
docker compose down
docker compose up --build

# If still failing, remove volumes
docker compose down -v
docker compose up --build
```

### Issue: "Module not found" errors

**Solution:**
```bash
# Clean install
rm -rf node_modules package-lock.json
npm install
```

### Issue: API calls returning 404

**Check:**
1. Is mock data enabled? (`USE_MOCK_DATA = true` in `api.js`)
2. Is backend running? (`curl http://localhost:8000/health`)
3. Is `/api/content` endpoint added to backend?
4. Is CORS configured on backend?

**Solution:**
```bash
# Enable mock data temporarily
# Edit src/services/api.js line 8
const USE_MOCK_DATA = true
```

### Issue: Blank page in production

**Check:**
1. Environment variable set in Vercel
2. Build completed successfully
3. No console errors (open DevTools)

**Solution:**
```bash
# Test production build locally
npm run build
npm run preview
# Check for errors
```

### Issue: Styles not loading

**Solution:**
```bash
# Rebuild Tailwind
npm run build
```

### Issue: Changes not reflecting

**Docker:**
```bash
# Restart container
docker compose restart
```

**Local:**
```bash
# Hard refresh browser
Cmd+Shift+R (Mac)
Ctrl+Shift+R (Windows)
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] All tests pass
- [ ] No console errors
- [ ] Mock data disabled (`USE_MOCK_DATA = false`)
- [ ] Environment variables configured
- [ ] Backend `/api/content` endpoint added
- [ ] Backend deployed to Railway
- [ ] CORS enabled on backend

### Vercel Deployment

- [ ] GitHub repo created and pushed
- [ ] Vercel project created
- [ ] Environment variable `VITE_API_BASE_URL` set
- [ ] Build succeeds
- [ ] Preview deployment works
- [ ] Production deployment works
- [ ] Custom domain configured (optional)

### Post-Deployment

- [ ] Visit live URL
- [ ] Test all pages
- [ ] Test on mobile device
- [ ] Check API calls in Network tab
- [ ] Verify analytics (if configured)
- [ ] Share URL with team

---

## Quick Commands Reference

```bash
# Local development
npm run dev

# Docker development
docker compose up

# Build for production
npm run build

# Preview production
npm run preview

# Deploy to Vercel
vercel --prod

# Check for errors
npm run build && npm run preview
```

---

## Success Criteria

✅ Frontend loads without errors  
✅ All 4 pages functional  
✅ Projections table shows 398 players  
✅ Risk badges visible  
✅ Mobile responsive  
✅ API integration works  
✅ Email capture renders  
✅ Deployed to Vercel  
✅ Custom domain configured (optional)

---

**Launch Target:** January 19, 2026  
**Status:** Ready for deployment ✅
