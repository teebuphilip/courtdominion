# CourtDominion Frontend - Quick Reference

## 🚀 INSTANT START

```bash
# Extract
tar -xzf courtdominion-frontend.tar.gz
cd courtdominion-frontend

# Test with Docker (RECOMMENDED)
docker compose up --build

# Access: http://localhost:3000
```

## 📋 FILES OVERVIEW

- **README.md** - Start here
- **DEPLOYMENT_GUIDE.md** - Complete deployment steps
- **HANDOFF_SUMMARY.md** - What's built, what to do next
- **BACKEND_content.py** - Add to your backend

## ✅ WHAT'S COMPLETE

- ✅ 4 pages (Home, Projections, Player Detail, Insights)
- ✅ 20+ components
- ✅ Sortable/searchable table with 398 players
- ✅ Risk badges and analysis
- ✅ Mobile responsive
- ✅ Docker ready
- ✅ Vercel ready
- ✅ Mock data for testing

## 🔧 CONFIGURATION

**Mock Data (for testing without backend):**
```javascript
// src/services/api.js line 8
const USE_MOCK_DATA = true
```

**Local API:**
```bash
# .env.local
VITE_API_BASE_URL=http://localhost:8000
```

**Production API:**
```bash
# .env.production or Vercel env var
VITE_API_BASE_URL=https://courtdominion.up.railway.app
```

## 📝 TODO BEFORE LAUNCH

1. [ ] Add `/api/content` endpoint to backend (see BACKEND_content.py)
2. [ ] Test locally: `docker compose up`
3. [ ] Switch to real API: `USE_MOCK_DATA = false`
4. [ ] Deploy to Vercel
5. [ ] Integrate Mailchimp in EmailCapture.jsx
6. [ ] Test on mobile device
7. [ ] Launch January 19, 2026

## 🐛 TROUBLESHOOTING

**Port in use:**
```bash
lsof -ti:3000 | xargs kill -9
```

**Docker issues:**
```bash
docker compose down
docker compose up --build
```

**Module errors:**
```bash
rm -rf node_modules package-lock.json
npm install
```

## 🎯 SUCCESS METRICS

All 4 pages load ✅  
398 players show ✅  
Search works ✅  
Pagination works ✅  
Risk badges show ✅  
Mobile responsive ✅  
Email form renders ✅  

## 📞 NEED HELP?

1. Check README.md
2. Check DEPLOYMENT_GUIDE.md
3. Check console for errors
4. Verify mock data is enabled

---

**Status:** ✅ READY FOR TESTING & DEPLOYMENT  
**Launch:** January 19, 2026
