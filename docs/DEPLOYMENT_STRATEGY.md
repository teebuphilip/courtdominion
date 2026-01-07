# CourtDominion Production Deployment Strategy

**Version:** 1.0
**Date:** January 7, 2026
**Status:** Ready for Production Deployment

---

## Executive Summary

CourtDominion is ready for production deployment with:
- ✅ Backend API (FastAPI) with 21/21 passing tests
- ✅ Frontend (React + Vite) with 15/15 passing tests
- ✅ Automation Pipeline (Python) with 11/11 passing tests
- ✅ Docker containerization complete
- ✅ Internal API endpoint for microservices ready

**Recommended Timeline:** 2-3 days for initial deployment, 1 week for production stabilization

---

## Table of Contents

1. [Current State Assessment](#current-state-assessment)
2. [Deployment Platform Recommendations](#deployment-platform-recommendations)
3. [Infrastructure Requirements](#infrastructure-requirements)
4. [Deployment Phases](#deployment-phases)
5. [Step-by-Step Deployment Guide](#step-by-step-deployment-guide)
6. [Cost Analysis](#cost-analysis)
7. [Domain and DNS Setup](#domain-and-dns-setup)
8. [Environment Variables](#environment-variables)
9. [Monitoring and Maintenance](#monitoring-and-maintenance)
10. [Rollback Strategy](#rollback-strategy)
11. [Security Checklist](#security-checklist)

---

## Current State Assessment

### What We Have
- **Backend:** FastAPI application with real NBA data integration
- **Frontend:** React + Vite SPA with Tailwind CSS
- **Automation:** Python pipeline for data refresh (nightly scheduled)
- **Testing:** Full test coverage (47/47 tests passing)
- **Documentation:** Complete API and architecture docs
- **Containerization:** Docker + docker-compose ready

### What We Need
- Production hosting platform
- Domain name (if not already owned)
- SSL certificates (handled by platform)
- Environment variable management
- Monitoring/logging setup
- CI/CD pipeline (optional but recommended)

---

## Deployment Platform Recommendations

### Option 1: Railway (RECOMMENDED for MVP)
**Why:** Simplest deployment, excellent Docker support, affordable

**Pros:**
- Direct Docker deployment from GitHub
- Built-in PostgreSQL if needed later
- Automatic SSL certificates
- Simple pricing ($5-20/month to start)
- Excellent logs and metrics
- Zero-config deployments

**Cons:**
- Less mature than AWS/GCP
- Smaller community

**Best For:** Getting to production FAST (recommended for you)

---

### Option 2: Vercel (Frontend) + Render (Backend)
**Why:** Specialized hosting for each stack

**Frontend on Vercel:**
- Best-in-class React/Vite hosting
- Global CDN
- Automatic deployments from GitHub
- Free tier available

**Backend on Render:**
- Docker support
- Automatic SSL
- Free tier for backend
- PostgreSQL addon available

**Pros:**
- Optimized for each service
- Good free tiers
- Simple deployment

**Cons:**
- Managing two platforms
- Need to configure CORS properly

**Best For:** If you want best performance and don't mind managing 2 platforms

---

### Option 3: AWS (ECS + RDS + S3)
**Why:** Enterprise-grade, maximum flexibility

**Pros:**
- Maximum scalability
- Full control
- Industry standard
- Extensive services

**Cons:**
- Steep learning curve
- More expensive
- Complex setup
- Overkill for MVP

**Best For:** Later stage when you need enterprise features

---

## Infrastructure Requirements

### Minimum Requirements (MVP)

**Backend Container:**
- CPU: 0.5 vCPU
- RAM: 512 MB
- Storage: 1 GB
- Expected: handles 100-500 requests/min

**Frontend:**
- Static hosting (CDN)
- 100 GB bandwidth/month

**Automation:**
- Runs once daily (cron job)
- CPU: 1 vCPU during run
- RAM: 1 GB during run
- Runtime: ~5-10 minutes

**Data Storage:**
- JSON file storage: ~50 MB
- Grows ~10 MB/year

---

## Deployment Phases

### Phase 1: Initial Deployment (Day 1-2)
**Goal:** Get production-ready version live

**Tasks:**
1. ✅ Code is ready (DONE)
2. Choose platform (Railway recommended)
3. Set up accounts and billing
4. Deploy backend to production
5. Deploy frontend to production
6. Configure environment variables
7. Test end-to-end in production

**Success Criteria:**
- Site accessible at production URL
- Backend API responding
- Frontend loading player data
- No console errors

---

### Phase 2: Domain & SSL (Day 2-3)
**Goal:** Custom domain with HTTPS

**Tasks:**
1. Purchase/configure domain (e.g., courtdominion.com)
2. Point DNS to hosting platform
3. Configure SSL certificate (automatic on most platforms)
4. Update frontend API URLs to production backend
5. Test with custom domain

**Success Criteria:**
- Site accessible at courtdominion.com
- HTTPS working (green padlock)
- All API calls using production URLs

---

### Phase 3: Automation Setup (Day 3-4)
**Goal:** Automated nightly data refresh

**Tasks:**
1. Set up cron job or scheduled task
2. Configure automation to run at 3 AM EST
3. Set up email/Slack notifications for failures
4. Test automation in production
5. Verify data updates correctly

**Success Criteria:**
- Automation runs successfully every night
- Fresh data visible next morning
- Failure notifications working

---

### Phase 4: Monitoring & Optimization (Week 1)
**Goal:** Production stability and observability

**Tasks:**
1. Set up error tracking (Sentry or similar)
2. Configure uptime monitoring (UptimeRobot)
3. Set up log aggregation
4. Configure alerts for failures
5. Performance testing and optimization
6. Load testing

**Success Criteria:**
- Error tracking capturing issues
- Uptime monitoring alerting you
- Logs accessible and searchable
- Site performing well under load

---

## Step-by-Step Deployment Guide

### Railway Deployment (RECOMMENDED)

#### Step 1: Prepare Repository
```bash
# Ensure main branch is up to date
git checkout main
git pull origin main

# Verify tests pass
cd courtdominion-app/backend
docker-compose run backend pytest tests/ -v
```

#### Step 2: Create Railway Account
1. Go to https://railway.app
2. Sign up with GitHub
3. Authorize Railway to access your repo

#### Step 3: Deploy Backend
1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose `teebuphilip/courtdominion`
4. Railway auto-detects Docker
5. Set root directory: `courtdominion-app/backend`
6. Click "Deploy"

**Environment Variables to Set:**
```bash
DATA_DIR=/data/outputs
INTERNAL_API_KEY=<generate-secure-key>
LOG_LEVEL=INFO
```

**Generate secure API key:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### Step 4: Deploy Frontend
1. Click "New Project" again
2. Select same GitHub repo
3. Set root directory: `courtdominion-app/frontend`
4. Railway auto-detects Vite

**Environment Variables to Set:**
```bash
VITE_API_URL=https://your-backend-url.railway.app
```

#### Step 5: Deploy Automation (Scheduled Job)
1. Click "New Project"
2. Select same GitHub repo
3. Set root directory: `courtdominion-app/automation`
4. Under "Settings" → "Cron Schedule":
   ```
   0 3 * * *
   ```
   (Runs at 3 AM daily)

#### Step 6: Verify Deployment
```bash
# Test backend health
curl https://your-backend-url.railway.app/health

# Test backend players endpoint
curl https://your-backend-url.railway.app/players

# Test frontend loads
open https://your-frontend-url.railway.app
```

---

### Vercel + Render Deployment (ALTERNATIVE)

#### Frontend on Vercel

**Step 1: Deploy Frontend**
1. Go to https://vercel.com
2. Import from GitHub: `teebuphilip/courtdominion`
3. Framework Preset: Vite
4. Root Directory: `courtdominion-app/frontend`
5. Build Command: `npm run build`
6. Output Directory: `dist`

**Environment Variables:**
```bash
VITE_API_URL=https://your-backend.onrender.com
```

**Step 2: Deploy**
- Click "Deploy"
- Vercel builds and deploys automatically
- Frontend will be at: `https://courtdominion.vercel.app`

---

#### Backend on Render

**Step 1: Create Web Service**
1. Go to https://render.com
2. New → Web Service
3. Connect GitHub repo: `teebuphilip/courtdominion`
4. Name: `courtdominion-backend`
5. Root Directory: `courtdominion-app/backend`
6. Environment: Docker
7. Plan: Free (or Starter $7/mo)

**Environment Variables:**
```bash
DATA_DIR=/data/outputs
INTERNAL_API_KEY=<your-secure-key>
LOG_LEVEL=INFO
PORT=8000
```

**Step 2: Deploy**
- Click "Create Web Service"
- Render builds Docker image
- Backend will be at: `https://courtdominion-backend.onrender.com`

---

#### Automation on Render (Cron Job)

**Step 1: Create Cron Job**
1. New → Cron Job
2. Connect same GitHub repo
3. Name: `courtdominion-automation`
4. Root Directory: `courtdominion-app/automation`
5. Environment: Docker
6. Command: `python pipeline.py`
7. Schedule: `0 3 * * *` (3 AM daily)

**Environment Variables:**
```bash
DATA_DIR=/data/outputs
LOG_LEVEL=INFO
```

---

## Cost Analysis

### Railway (Recommended)
| Service | Plan | Cost |
|---------|------|------|
| Backend | Hobby | $5/month |
| Frontend | Hobby | $5/month |
| Automation | Hobby | $5/month |
| **Total** | | **$15/month** |

**Annual:** $180/year

---

### Vercel + Render
| Service | Platform | Plan | Cost |
|---------|----------|------|------|
| Frontend | Vercel | Pro | $20/month |
| Backend | Render | Starter | $7/month |
| Automation | Render | Starter | $7/month |
| **Total** | | | **$34/month** |

**Annual:** $408/year

---

### AWS (Enterprise)
| Service | Type | Cost |
|---------|------|------|
| ECS Fargate | Backend | $15-30/month |
| CloudFront | Frontend CDN | $5-10/month |
| S3 | Frontend hosting | $1/month |
| RDS | Database (future) | $15-30/month |
| Lambda | Automation | $1/month |
| **Total** | | **$37-72/month** |

**Annual:** $444-864/year

---

## Domain and DNS Setup

### Step 1: Purchase Domain
**Recommended Registrars:**
- Namecheap: ~$10/year
- Google Domains: ~$12/year
- Cloudflare: ~$10/year (best DNS performance)

**Suggested Domain:** `courtdominion.com`

---

### Step 2: Configure DNS

**For Railway:**
```
Type: CNAME
Name: @
Value: your-frontend.up.railway.app

Type: CNAME
Name: api
Value: your-backend.up.railway.app
```

**Result:**
- Frontend: https://courtdominion.com
- Backend API: https://api.courtdominion.com

---

**For Vercel + Render:**
```
Type: CNAME
Name: @
Value: cname.vercel-dns.com

Type: CNAME
Name: api
Value: courtdominion-backend.onrender.com
```

---

### Step 3: SSL Certificates
**All platforms provide automatic SSL:**
- Railway: Automatic via Let's Encrypt
- Vercel: Automatic via Let's Encrypt
- Render: Automatic via Let's Encrypt

No manual configuration needed!

---

## Environment Variables

### Backend Environment Variables

**Required:**
```bash
# Data directory for outputs
DATA_DIR=/data/outputs

# Internal API authentication
INTERNAL_API_KEY=<generate-with-secrets.token_urlsafe(32)>

# Logging
LOG_LEVEL=INFO

# Port (if needed by platform)
PORT=8000
```

**Optional:**
```bash
# API rate limiting
RATE_LIMIT_PER_MINUTE=100

# CORS origins
CORS_ORIGINS=https://courtdominion.com,https://www.courtdominion.com
```

---

### Frontend Environment Variables

**Required:**
```bash
# Backend API URL
VITE_API_URL=https://api.courtdominion.com
```

**Optional:**
```bash
# Analytics (future)
VITE_GA_ID=UA-XXXXXXXXX-X

# Feature flags
VITE_ENABLE_INSIGHTS=true
```

---

### Automation Environment Variables

**Required:**
```bash
# Data directory
DATA_DIR=/data/outputs

# Logging
LOG_LEVEL=INFO
```

**Optional:**
```bash
# Notification webhook (Slack, Discord)
WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

---

## Monitoring and Maintenance

### Uptime Monitoring

**Tool:** UptimeRobot (Free)
1. Sign up at https://uptimerobot.com
2. Add monitor for: `https://courtdominion.com`
3. Add monitor for: `https://api.courtdominion.com/health`
4. Set alert email/SMS
5. Check interval: 5 minutes

**Expected Uptime:** 99.9%

---

### Error Tracking

**Tool:** Sentry (Free tier: 5,000 events/month)

**Backend Setup:**
```bash
# Add to requirements.txt
sentry-sdk[fastapi]==1.39.0

# In main.py
import sentry_sdk
sentry_sdk.init(
    dsn="https://your-sentry-dsn",
    traces_sample_rate=0.1,
)
```

**Frontend Setup:**
```bash
npm install @sentry/react

# In main.jsx
import * as Sentry from "@sentry/react";
Sentry.init({
  dsn: "https://your-sentry-dsn",
  integrations: [new Sentry.BrowserTracing()],
  tracesSampleRate: 0.1,
});
```

---

### Log Aggregation

**Platform Logs:**
- Railway: Built-in logs dashboard
- Vercel: Built-in logs (last 24h free)
- Render: Built-in logs dashboard

**External Tool (Optional):** Logtail, Papertrail
- Centralized logs
- Search and filter
- Retention: 7-30 days

---

### Performance Monitoring

**Metrics to Track:**
1. **API Response Times**
   - Target: < 200ms for /players
   - Target: < 300ms for /projections

2. **Frontend Load Time**
   - Target: < 2 seconds first load
   - Target: < 500ms cached load

3. **Automation Success Rate**
   - Target: 99% success rate
   - Alert on failures

---

## Rollback Strategy

### Immediate Rollback (< 5 minutes)

**Railway:**
1. Go to Deployments tab
2. Click on previous successful deployment
3. Click "Redeploy"

**Vercel:**
1. Go to Deployments
2. Find last working deployment
3. Click "Promote to Production"

**Render:**
1. Go to Events
2. Find last successful deploy
3. Click "Rollback to this version"

---

### Planned Rollback

**Using Git:**
```bash
# Create rollback branch
git checkout -b rollback-to-stable

# Reset to known good commit
git reset --hard <commit-hash>

# Force push
git push -f origin rollback-to-stable

# Platform auto-deploys
```

---

## Security Checklist

### Pre-Deployment Security

- [ ] **Secrets Management**
  - [ ] All API keys in environment variables
  - [ ] No secrets in code or Git
  - [ ] .env files in .gitignore

- [ ] **API Security**
  - [ ] CORS configured properly
  - [ ] Rate limiting enabled
  - [ ] Internal API key authentication working

- [ ] **HTTPS**
  - [ ] SSL certificates active
  - [ ] HTTP → HTTPS redirect enabled

- [ ] **Dependencies**
  - [ ] npm audit run and fixed
  - [ ] pip audit run (or safety check)

- [ ] **Input Validation**
  - [ ] API inputs validated
  - [ ] SQL injection prevention (if using DB)
  - [ ] XSS prevention in frontend

---

### Post-Deployment Security

- [ ] **Monitoring**
  - [ ] Error tracking active (Sentry)
  - [ ] Uptime monitoring active
  - [ ] Log aggregation configured

- [ ] **Access Control**
  - [ ] Production credentials secure
  - [ ] GitHub repo access reviewed
  - [ ] Platform admin access limited

- [ ] **Backup Strategy**
  - [ ] Data backup scheduled (if needed)
  - [ ] Database backup (future)
  - [ ] Code in Git (version control)

---

## Recommended Deployment Timeline

### Day 1 (3-4 hours)
**Morning:**
- 9:00 AM - Set up Railway/Vercel account
- 9:30 AM - Deploy backend to Railway
- 10:00 AM - Deploy frontend to Railway
- 10:30 AM - Configure environment variables
- 11:00 AM - Test end-to-end in production

**Afternoon:**
- 1:00 PM - Deploy automation cron job
- 1:30 PM - Set up monitoring (UptimeRobot)
- 2:00 PM - Initial testing and QA
- 3:00 PM - Document production URLs

---

### Day 2 (2-3 hours)
**Morning:**
- 9:00 AM - Purchase domain (if needed)
- 9:30 AM - Configure DNS
- 10:00 AM - Wait for DNS propagation (15-30 min)
- 10:30 AM - Test with custom domain
- 11:00 AM - Update frontend API URLs if needed

**Afternoon:**
- 1:00 PM - Set up error tracking (Sentry)
- 2:00 PM - Configure alerts
- 3:00 PM - Final end-to-end testing

---

### Day 3-7 (Monitoring & Optimization)
- Monitor for errors and performance
- Optimize based on real-world usage
- Fix any issues discovered
- Gather user feedback

---

## Quick Reference Commands

### Check Production Health
```bash
# Backend health
curl https://api.courtdominion.com/health

# Get players
curl https://api.courtdominion.com/players

# Get projections
curl https://api.courtdominion.com/projections
```

### View Logs (Railway)
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# View logs
railway logs
```

### Test Frontend
```bash
# Check if site loads
curl -I https://courtdominion.com

# Check API connectivity from frontend
# Open browser console:
fetch('https://api.courtdominion.com/health')
  .then(r => r.json())
  .then(console.log)
```

---

## Success Metrics

### Week 1 Post-Launch
- [ ] Site accessible 99.9% uptime
- [ ] No critical errors in logs
- [ ] Automation running successfully every night
- [ ] Fresh data visible every morning
- [ ] API response times < 300ms

### Month 1 Post-Launch
- [ ] Zero security incidents
- [ ] API uptime > 99.5%
- [ ] Frontend load time < 2 seconds
- [ ] Automation success rate > 95%
- [ ] Error rate < 1%

---

## Next Steps After Deployment

### Immediate (Week 1-2)
1. Monitor for issues
2. Gather initial user feedback
3. Fix any bugs discovered
4. Optimize performance

### Short-term (Month 1-3)
1. Implement microservices (Features 1-7 from design doc)
2. Add user accounts and authentication
3. Implement email capture
4. Set up analytics

### Long-term (Month 4-12)
1. Mobile app development
2. Premium features
3. API for third parties
4. Advanced analytics

---

## Contact and Support

**Platform Support:**
- Railway: https://railway.app/help
- Vercel: https://vercel.com/support
- Render: https://render.com/docs

**Emergency Contacts:**
- Platform status pages
- Your team contact list
- On-call rotation (future)

---

## Appendix: Platform Comparison Matrix

| Feature | Railway | Vercel + Render | AWS |
|---------|---------|-----------------|-----|
| **Ease of Setup** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Docker Support** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Cost (MVP)** | $15/mo | $34/mo | $37-72/mo |
| **Scalability** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Learning Curve** | Low | Medium | High |
| **Time to Deploy** | 1-2 hours | 2-3 hours | 1-2 days |
| **Free Tier** | No | Yes (limited) | Yes (limited) |
| **Auto SSL** | ✅ | ✅ | ✅ (ACM) |
| **CI/CD** | Built-in | Built-in | Manual setup |
| **Monitoring** | Built-in | Built-in | CloudWatch |
| **Best For** | MVP/Startup | Specialized stacks | Enterprise |

---

**Recommendation:** Start with Railway for fastest time-to-production. Migrate to AWS later when you need advanced features or have enterprise customers.

---

**END OF DEPLOYMENT STRATEGY**
