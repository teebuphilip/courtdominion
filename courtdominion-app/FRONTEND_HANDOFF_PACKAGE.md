# COURTDOMINION FRONTEND BUILD - HANDOFF PACKAGE FOR NEW CLAUDE
## December 18, 2025

**Project:** CourtDominion Phase 1 Frontend  
**Target Launch:** January 19, 2026  
**Build Mode:** Incremental (page by page approval)

---

## YOUR MISSION

Build a minimal viable frontend for CourtDominion NBA fantasy basketball platform.

**Tech Stack:**
- React 18 + Vite
- TailwindCSS
- React Query
- React Router

**Pages:**
1. Marketing Homepage (email capture)
2. Projections Table (top 100 players, risk badges)
3. Player Detail (read-only)
4. Insights/Waiver (simple list)

**Critical Constraints:**
- NO user accounts, NO auth, NO personalization
- ALL text comes from `/api/content` endpoint
- Desktop-first (1440px), mobile-readable
- Email gate REQUIRED before projections
- Risk badges MUST be visible inline in table

---

## PRE-FLIGHT ANSWERS (FROM USER)

### Deployment Modes

**Mode 1: Local Development**
- Frontend: `npm run dev` on Mac (http://localhost:5173)
- Backend: Docker container (http://localhost:8000)
- User tests locally before deploying

**Mode 2: Production**
- Frontend: Vercel (https://courtdominion.vercel.app)
- Backend: Railway (not deployed yet, will be https://courtdominion.up.railway.app)

### Design Decisions

| Question | Answer |
|----------|--------|
| **Mailchimp** | Placeholder with TODO comment, structure for easy drop-in later |
| **Backend URL** | Not deployed yet, use env var |
| **Colors** | Defaults (NBA blue/orange, dark mode) |
| **Logo** | Text-only "CourtDominion" |
| **Work Mode** | **INCREMENTAL** - Build page by page, get approval |
| **Desktop Width** | 1440px optimized |
| **Table Size** | Top 100 players only (simplified, no pagination) |

---

## CRITICAL REQUIREMENTS

### 1. Dynamic Content (NON-NEGOTIABLE)

ALL text content MUST come from `GET /api/content`

**Never hardcode:**
- Headlines
- Subheadlines
- Button text
- Navigation labels
- Footer text
- Page titles

**Always fetch from:**
```javascript
const { data: content } = useQuery('content', () =>
  fetch(`${API_BASE_URL}/api/content`).then(r => r.json())
)

<h1>{content?.homepage?.headline}</h1>
```

### 2. Email Gate (REQUIRED)

User MUST submit email before accessing projections.

**Flow:**
1. User clicks "View Projections" on homepage
2. Show email capture modal/page
3. After email submit (Mailchimp placeholder), allow access
4. Store submission in sessionStorage (no backend needed)
5. Show projections

**Implementation:**
```javascript
// Check if email submitted this session
const hasEmail = sessionStorage.getItem('email_submitted')
if (!hasEmail) {
  // Show email gate
}
```

### 3. Risk Badges (MUST BE VISIBLE)

Risk level MUST be visible directly in projections table.

**Colors:**
- Low: Green (#22c55e)
- Medium: Yellow (#eab308)
- High: Red (#ef4444)

**Format:**
```jsx
<span className="px-2 py-1 rounded text-xs bg-green-500/20 text-green-400">
  LOW
</span>
```

---

## DEPLOYMENT MODE CONFIGURATION

### Environment Files

**Create TWO .env files:**

**File 1:** `.env` (Local development)
```bash
VITE_API_BASE_URL=http://localhost:8000
```

**File 2:** `.env.production` (Vercel deployment)
```bash
VITE_API_BASE_URL=https://courtdominion.up.railway.app
```

### Usage in Code

```javascript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL
```

### Testing Both Modes

**Local mode test:**
```bash
npm run dev
# Should connect to http://localhost:8000
```

**Production mode test:**
```bash
npm run build
npm run preview
# Should use production URL
```

---

## INCREMENTAL BUILD PROCESS

### Phase 1: Setup & Layout (STOP FOR APPROVAL)

**Build:**
1. Initialize Vite project
2. Install dependencies
3. Configure Tailwind
4. Create folder structure
5. Build Layout (Header, Footer)
6. Create API service layer
7. Test `/api/content` connection

**Deliverable:**
- Project compiles
- Layout renders
- Content endpoint works

**STOP - Show user, get approval**

---

### Phase 2: Homepage (STOP FOR APPROVAL)

**Build:**
1. Hero section (headline from `/api/content`)
2. Value props (3 features)
3. Email capture placeholder:
```jsx
<div className="email-capture">
  {/* TODO: Add Mailchimp embed code here */}
  <p className="text-gray-400 text-sm">
    Mailchimp form will be embedded here
  </p>
  <input type="email" placeholder="Enter your email" className="..." />
  <button>Get Free Access</button>
</div>
```
4. Call to action buttons

**Deliverable:**
- Homepage fully designed
- All text from `/api/content`
- Placeholder email form styled
- Links to projections

**STOP - Show user, get approval**

---

### Phase 3: Email Gate (STOP FOR APPROVAL)

**Build:**
1. Modal or full-page email capture
2. Triggers before projections access
3. SessionStorage to track submission
4. Fake submission (no backend):
```javascript
const handleSubmit = (email) => {
  sessionStorage.setItem('email_submitted', 'true')
  sessionStorage.setItem('email_value', email)
  navigate('/projections')
}
```

**Deliverable:**
- Email gate blocks projections
- After submission, allows access
- Persists for session

**STOP - Show user, get approval**

---

### Phase 4: Projections Page (STOP FOR APPROVAL)

**Build:**
1. Fetch top 100 from `/api/projections?limit=100`
2. Fetch risk data from `/api/risk?limit=100`
3. Table with columns:
   - Player Name (clickable → detail page)
   - Team
   - Position
   - Fantasy Points
   - Points
   - Rebounds
   - Assists
   - **Risk Badge** (inline, color-coded)
4. Search bar (filters by name)
5. Sort by column (fantasy points default)

**Risk Badge Integration:**
```javascript
// Merge risk data with projections
const projectionsWithRisk = projections.map(p => {
  const risk = riskData.find(r => r.player_id === p.player_id)
  return { ...p, risk_level: risk?.injury_risk || 'medium' }
})
```

**Deliverable:**
- Table shows top 100 players
- Risk badges visible inline
- Search works
- Sorting works
- Click player → goes to detail page

**STOP - Show user, get approval**

---

### Phase 5: Player Detail Page (STOP FOR APPROVAL)

**Build:**
1. Fetch player data from `/api/players/{id}`
2. Display:
   - Player name, team, position
   - Projected fantasy points
   - Key stats (points, rebounds, assists, etc.)
   - Risk assessment (consistency, ceiling, floor)
   - Injury status if present
3. Back button to projections

**Deliverable:**
- Player detail page shows all stats
- Risk analysis visible
- Clean read-only layout

**STOP - Show user, get approval**

---

### Phase 6: Insights Page (STOP FOR APPROVAL)

**Build:**
1. Fetch from `/api/insights?limit=20`
2. List of insights cards:
   - Player name
   - Recommendation
   - Reasoning
   - Value score
3. Simple list layout (no fancy features)

**Deliverable:**
- Insights page shows waiver wire targets
- Clean, readable layout

**STOP - Show user, get approval**

---

### Phase 7: Polish & Deploy (FINAL)

**Polish:**
1. Mobile responsiveness check
2. Loading states
3. Error handling
4. Final styling pass

**Deploy:**
1. Create Vercel project
2. Connect GitHub repo
3. Set environment variable: `VITE_API_BASE_URL`
4. Deploy
5. Test production URL

**Deliverable:**
- Live site on Vercel
- All pages working
- Backend API connected

**DONE**

---

## API ENDPOINTS REFERENCE

### Content (Dynamic Copy)
```
GET /api/content
→ Returns all text for frontend
```

### Projections
```
GET /api/projections?limit=100&sort_by=fantasy_points&order=desc
→ Returns top 100 players
```

### Player Detail
```
GET /api/players/{player_id}
→ Returns player with projection, insight, risk
```

### Insights
```
GET /api/insights?limit=20
→ Returns waiver wire recommendations
```

### Risk Data
```
GET /api/risk?limit=100
→ Returns risk assessments for players
```

---

## PROJECT STRUCTURE

```
courtdominion-frontend/
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Header.jsx
│   │   │   ├── Footer.jsx
│   │   │   └── Layout.jsx
│   │   ├── projections/
│   │   │   ├── ProjectionsTable.jsx
│   │   │   ├── RiskBadge.jsx
│   │   │   └── SearchBar.jsx
│   │   ├── player/
│   │   │   └── PlayerCard.jsx
│   │   ├── insights/
│   │   │   └── InsightCard.jsx
│   │   └── home/
│   │       ├── Hero.jsx
│   │       ├── ValueProps.jsx
│   │       └── EmailCapture.jsx
│   ├── pages/
│   │   ├── HomePage.jsx
│   │   ├── EmailGatePage.jsx
│   │   ├── ProjectionsPage.jsx
│   │   ├── PlayerDetailPage.jsx
│   │   └── InsightsPage.jsx
│   ├── services/
│   │   └── api.js
│   ├── hooks/
│   │   ├── useContent.js
│   │   ├── useProjections.js
│   │   ├── usePlayer.js
│   │   └── useInsights.js
│   ├── App.jsx
│   └── main.jsx
├── .env
├── .env.production
└── package.json
```

---

## EXAMPLE CODE SNIPPETS

### API Service Layer

```javascript
// src/services/api.js
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
})

export const apiService = {
  getContent: () => api.get('/api/content'),
  getProjections: (params) => api.get('/api/projections', { params }),
  getPlayer: (id) => api.get(`/api/players/${id}`),
  getInsights: (params) => api.get('/api/insights', { params }),
  getRisk: (params) => api.get('/api/risk', { params }),
}
```

### Content Hook

```javascript
// src/hooks/useContent.js
import { useQuery } from '@tanstack/react-query'
import { apiService } from '../services/api'

export function useContent() {
  return useQuery({
    queryKey: ['content'],
    queryFn: async () => {
      const response = await apiService.getContent()
      return response.data
    },
    staleTime: 60 * 60 * 1000, // 1 hour
  })
}
```

### Risk Badge Component

```javascript
// src/components/projections/RiskBadge.jsx
export default function RiskBadge({ risk }) {
  const colors = {
    low: 'bg-green-500/20 text-green-400 border-green-500/30',
    medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    high: 'bg-red-500/20 text-red-400 border-red-500/30'
  }
  
  const color = colors[risk] || colors.medium
  
  return (
    <span className={`px-2 py-1 rounded text-xs border ${color}`}>
      {risk?.toUpperCase()}
    </span>
  )
}
```

---

## TESTING CHECKLIST

After each phase, verify:

- [ ] Component renders without errors
- [ ] All text comes from `/api/content` (no hardcoded strings)
- [ ] API calls work in local mode (localhost:8000)
- [ ] Loading states show during fetch
- [ ] Error states show if API fails
- [ ] Layout looks good at 1440px width
- [ ] Mobile view is readable (not broken)

---

## COMMON PITFALLS TO AVOID

### 1. Hardcoding Text
❌ BAD:
```jsx
<h1>NBA Fantasy Projections</h1>
```

✅ GOOD:
```jsx
<h1>{content?.homepage?.headline}</h1>
```

### 2. Forgetting Email Gate
❌ BAD: Direct link to projections

✅ GOOD: Check sessionStorage, redirect to email gate if needed

### 3. Missing Risk Badges
❌ BAD: Risk in separate column or not visible

✅ GOOD: Risk badge inline in projections table

### 4. Wrong API URL
❌ BAD: Hardcoded `http://localhost:8000`

✅ GOOD: Use `import.meta.env.VITE_API_BASE_URL`

---

## STOPPING POINTS (CRITICAL)

**DO NOT PROCEED WITHOUT USER APPROVAL AT THESE POINTS:**

1. ✋ After layout/setup
2. ✋ After homepage
3. ✋ After email gate
4. ✋ After projections table
5. ✋ After player detail
6. ✋ After insights page
7. ✋ Before deployment

**Why?** User needs to test locally in Docker mode and approve design before moving forward.

---

## QUESTIONS TO ASK IF UNCLEAR

**If you're unsure about:**
- Component styling → Show options, ask user to choose
- Table layout → Show mockup, get approval
- Email gate UX → Describe flow, confirm before building
- API data structure → Check API_DOCUMENTATION.md
- Mobile breakpoints → Ask for guidance

**NEVER assume. Always ask.**

---

## SUCCESS CRITERIA

Frontend is SUCCESS if:

✅ All 4 pages render correctly  
✅ API calls work in both local and production modes  
✅ All text comes from `/api/content`  
✅ Email gate blocks projections access  
✅ Risk badges visible in projections table  
✅ Search and sort work  
✅ Player detail pages load  
✅ Mobile view is readable  
✅ Deployed to Vercel with live URL  

---

## FILES TO REFERENCE

**You should have these uploaded:**

1. **FRONTEND_BUILD_SPECIFICATION.md** - Complete technical spec
2. **API_DOCUMENTATION.md** - API reference with examples
3. **BACKEND_COMPLETE_DOCUMENTATION.md** - Backend architecture
4. **BACKEND_FEATURES_CHANGELOG.md** - New features (content endpoint, etc.)
5. **This file** - Handoff instructions

---

## FINAL REMINDERS

**This is Phase 1 MVP:**
- Keep it simple
- Focus on functionality over polish
- No fancy animations
- No complex features
- Just prove the backend works

**User will test:**
- Every component locally before approving next
- Backend connection in Docker mode
- Full flow before Vercel deployment

**Your job:**
- Build incrementally
- Stop for approval
- Ask questions when unclear
- Keep scope minimal

---

## START HERE

**Step 1:** Initialize Vite project
```bash
npm create vite@latest courtdominion-frontend -- --template react
cd courtdominion-frontend
npm install
npm install react-router-dom @tanstack/react-query axios
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

**Step 2:** Configure Tailwind (follow FRONTEND_BUILD_SPECIFICATION.md)

**Step 3:** Create `.env` and `.env.production` files

**Step 4:** Build Layout components

**Step 5:** STOP - Show user, get approval, then continue

---

**END OF HANDOFF PACKAGE**

**Good luck! Build it right, build it incrementally.**
