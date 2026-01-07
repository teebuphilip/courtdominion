# COURTDOMINION PHASE 1 FRONTEND - COMPLETE BUILD SPECIFICATION
## Handoff Package for Development

**Version:** 1.0  
**Date:** December 18, 2025  
**Estimated Build Time:** 17 hours  
**Target Launch:** January 19, 2026

---

## TABLE OF CONTENTS

1. [Executive Summary](#executive-summary)
2. [Project Setup](#project-setup)
3. [Architecture Overview](#architecture-overview)
4. [Backend Changes Required](#backend-changes-required)
5. [Component Specifications](#component-specifications)
6. [Page Specifications](#page-specifications)
7. [API Integration](#api-integration)
8. [Styling Guidelines](#styling-guidelines)
9. [Deployment Instructions](#deployment-instructions)
10. [Testing Checklist](#testing-checklist)
11. [Handoff Instructions](#handoff-instructions)

---

## EXECUTIVE SUMMARY

### Project Goal

Build a minimal viable frontend for CourtDominion that:
- Proves the backend works with real NBA data
- Captures email addresses for mailing list
- Shows differentiated value (risk analysis, volatility metrics)
- Positions product for January 2026 launch

### Hard Constraints

**DO NOT BUILD:**
- User accounts or authentication
- Personalization
- Saved rosters or favorites
- Draft tools
- Season-long tools
- Payments or subscriptions
- Custom scoring

**ALL USERS SEE THE SAME DATA**

### Pages (4 Total)

1. **Marketing Homepage** - Value prop + email capture
2. **Projections Table** - 398 players, sortable, paginated, risk badges
3. **Player Detail** - Read-only stats + risk analysis
4. **Insights/Waiver** - Waiver wire recommendations

### Technology Stack

- **Framework:** React 18 + Vite
- **Styling:** TailwindCSS
- **State Management:** React Query (for API calls)
- **Routing:** React Router v6
- **Email Capture:** Mailchimp embed
- **Deployment:** Vercel
- **Backend:** Existing FastAPI (minor changes needed)

### Success Criteria

- Site loads and is mobile-responsive
- All 4 pages functional
- Email capture works
- Backend APIs integrated correctly
- Risk badges visible in projections table
- Deployed to Vercel with live URL

---

## PROJECT SETUP

### Step 1: Initialize Vite Project

```bash
# Create new Vite project
npm create vite@latest courtdominion-frontend -- --template react

cd courtdominion-frontend

# Install dependencies
npm install
```

### Step 2: Install Required Packages

```bash
# Core dependencies
npm install react-router-dom @tanstack/react-query axios

# Styling
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Icons (optional but recommended)
npm install lucide-react
```

### Step 3: Configure Tailwind

**File:** `tailwind.config.js`

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // NBA-inspired dark mode friendly palette
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',  // Main blue
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        secondary: {
          500: '#f97316',  // NBA orange accent
        }
      }
    },
  },
  plugins: [],
}
```

**File:** `src/index.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-gray-900 text-gray-100;
  }
}
```

### Step 4: Project Structure

```
courtdominion-frontend/
├── public/
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Header.jsx
│   │   │   ├── Footer.jsx
│   │   │   └── Layout.jsx
│   │   ├── projections/
│   │   │   ├── ProjectionsTable.jsx
│   │   │   ├── RiskBadge.jsx
│   │   │   ├── SearchBar.jsx
│   │   │   └── Pagination.jsx
│   │   ├── player/
│   │   │   ├── PlayerCard.jsx
│   │   │   ├── StatRow.jsx
│   │   │   └── RiskIndicator.jsx
│   │   ├── insights/
│   │   │   ├── InsightCard.jsx
│   │   │   └── InsightList.jsx
│   │   └── home/
│   │       ├── Hero.jsx
│   │       ├── ValueProps.jsx
│   │       ├── EmailCapture.jsx
│   │       └── SocialProof.jsx
│   ├── pages/
│   │   ├── HomePage.jsx
│   │   ├── ProjectionsPage.jsx
│   │   ├── PlayerDetailPage.jsx
│   │   └── InsightsPage.jsx
│   ├── services/
│   │   └── api.js
│   ├── hooks/
│   │   ├── useProjections.js
│   │   ├── usePlayer.js
│   │   ├── useInsights.js
│   │   └── useContent.js
│   ├── utils/
│   │   ├── formatters.js
│   │   └── constants.js
│   ├── App.jsx
│   └── main.jsx
├── .env
├── package.json
└── vite.config.js
```

### Step 5: Environment Configuration

**File:** `.env`

```bash
VITE_API_BASE_URL=http://localhost:8000
```

**File:** `.env.production`

```bash
VITE_API_BASE_URL=https://courtdominion.up.railway.app
```

---

## ARCHITECTURE OVERVIEW

### Data Flow

```
User Opens Site
     ↓
React App Loads
     ↓
Fetch /api/content (dynamic copy)
     ↓
Render Homepage with dynamic text
     ↓
User Clicks "View Projections"
     ↓
Fetch /api/projections
     ↓
Render ProjectionsTable with risk badges
     ↓
User Clicks Player
     ↓
Fetch /api/players/{id}
     ↓
Render PlayerDetailPage
```

### React Query Setup

**File:** `src/main.jsx`

```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
)
```

### Routing Setup

**File:** `src/App.jsx`

```jsx
import { Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import HomePage from './pages/HomePage'
import ProjectionsPage from './pages/ProjectionsPage'
import PlayerDetailPage from './pages/PlayerDetailPage'
import InsightsPage from './pages/InsightsPage'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/projections" element={<ProjectionsPage />} />
        <Route path="/player/:playerId" element={<PlayerDetailPage />} />
        <Route path="/insights" element={<InsightsPage />} />
      </Routes>
    </Layout>
  )
}

export default App
```

---

## BACKEND CHANGES REQUIRED

### Change 1: Add Content Endpoint

**File:** `courtdominion-app/backend/routers/content.py` (NEW)

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
        "subtitle": "Deep sleepers and streaming candidates"
    },
    "player_detail": {
        "risk_label": "Risk Level",
        "consistency_label": "Consistency Score",
        "volatility_label": "Volatility"
    },
    "navigation": {
        "home": "Home",
        "projections": "Projections",
        "insights": "Insights"
    },
    "footer": {
        "tagline": "CourtDominion - Coach-Level Fantasy Clarity",
        "copyright": "© 2026 CourtDominion. All rights reserved."
    }
}

@router.get("/api/content")
async def get_content():
    """
    Serve dynamic content for frontend.
    Falls back to defaults if content.json doesn't exist.
    """
    content_file = Path("/data/outputs/content.json")
    
    try:
        if content_file.exists():
            with open(content_file, 'r') as f:
                return json.load(f)
        else:
            return DEFAULT_CONTENT
    except Exception as e:
        # Fallback to default on any error
        return DEFAULT_CONTENT
```

**File:** `courtdominion-app/backend/app/main.py` (MODIFY)

Add this import and include router:

```python
from routers import content  # ADD THIS

app.include_router(content.router)  # ADD THIS
```

### Change 2: Create Initial Content File

**File:** `courtdominion-app/data/outputs/content.json` (NEW)

```json
{
  "homepage": {
    "headline": "NBA Fantasy Projections with Risk Analysis",
    "subheadline": "Coach-level clarity for your lineup decisions",
    "value_props": [
      "Risk-adjusted projections based on 5-year averages",
      "Volatility indicators for every player",
      "Daily waiver wire insights and deep sleepers"
    ],
    "cta_primary": "View Today's Projections",
    "cta_secondary": "Get Daily Insights"
  },
  "projections_page": {
    "title": "Daily Projections",
    "subtitle": "398 NBA players with risk-adjusted fantasy points",
    "email_gate": {
      "headline": "Get Full Access to All Projections",
      "subheadline": "Join our mailing list for daily NBA fantasy insights",
      "cta": "Get Free Access"
    }
  },
  "insights_page": {
    "title": "Waiver Wire Insights",
    "subtitle": "Deep sleepers and streaming candidates your league is missing"
  },
  "player_detail": {
    "risk_label": "Risk Assessment",
    "consistency_label": "Consistency",
    "volatility_label": "Volatility",
    "ceiling_label": "Ceiling",
    "floor_label": "Floor"
  },
  "navigation": {
    "home": "Home",
    "projections": "Projections",
    "insights": "Insights"
  },
  "footer": {
    "tagline": "CourtDominion - Data-Driven Fantasy Basketball",
    "copyright": "© 2026 CourtDominion. All rights reserved.",
    "disclaimer": "Projections based on 5-year career averages. Use at your own risk."
  }
}
```

### Change 3: Test Backend Changes

```bash
# Rebuild backend
docker compose build --no-cache backend

# Restart backend
docker compose up -d backend

# Test content endpoint
curl http://localhost:8000/api/content
```

Expected: JSON response with content structure

---

## COMPONENT SPECIFICATIONS

### Layout Components

#### Header Component

**File:** `src/components/layout/Header.jsx`

```jsx
import { Link } from 'react-router-dom'
import { useContent } from '../../hooks/useContent'

export default function Header() {
  const { data: content } = useContent()
  
  return (
    <header className="bg-gray-800 border-b border-gray-700">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="text-xl font-bold text-primary-500">
              CourtDominion
            </Link>
          </div>
          
          <div className="flex space-x-8 items-center">
            <Link 
              to="/" 
              className="text-gray-300 hover:text-white transition"
            >
              {content?.navigation?.home || 'Home'}
            </Link>
            <Link 
              to="/projections" 
              className="text-gray-300 hover:text-white transition"
            >
              {content?.navigation?.projections || 'Projections'}
            </Link>
            <Link 
              to="/insights" 
              className="text-gray-300 hover:text-white transition"
            >
              {content?.navigation?.insights || 'Insights'}
            </Link>
          </div>
        </div>
      </nav>
    </header>
  )
}
```

#### Footer Component

**File:** `src/components/layout/Footer.jsx`

```jsx
import { useContent } from '../../hooks/useContent'

export default function Footer() {
  const { data: content } = useContent()
  
  return (
    <footer className="bg-gray-800 border-t border-gray-700 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <p className="text-gray-400 mb-2">
            {content?.footer?.tagline || 'CourtDominion'}
          </p>
          <p className="text-gray-500 text-sm">
            {content?.footer?.copyright || '© 2026 CourtDominion'}
          </p>
          {content?.footer?.disclaimer && (
            <p className="text-gray-600 text-xs mt-2">
              {content.footer.disclaimer}
            </p>
          )}
        </div>
      </div>
    </footer>
  )
}
```

#### Layout Component

**File:** `src/components/layout/Layout.jsx`

```jsx
import Header from './Header'
import Footer from './Footer'

export default function Layout({ children }) {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-grow">
        {children}
      </main>
      <Footer />
    </div>
  )
}
```

---

### Projections Components

#### Risk Badge Component

**File:** `src/components/projections/RiskBadge.jsx`

```jsx
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

#### Search Bar Component

**File:** `src/components/projections/SearchBar.jsx`

```jsx
import { Search } from 'lucide-react'

export default function SearchBar({ value, onChange, placeholder = "Search players..." }) {
  return (
    <div className="relative">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg 
                   text-gray-100 placeholder-gray-400 focus:outline-none focus:border-primary-500"
      />
    </div>
  )
}
```

#### Pagination Component

**File:** `src/components/projections/Pagination.jsx`

```jsx
export default function Pagination({ currentPage, totalPages, onPageChange }) {
  return (
    <div className="flex items-center justify-center space-x-2 mt-6">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="px-4 py-2 bg-gray-800 border border-gray-700 rounded disabled:opacity-50 
                   hover:bg-gray-700 transition"
      >
        Previous
      </button>
      
      <span className="text-gray-400">
        Page {currentPage} of {totalPages}
      </span>
      
      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="px-4 py-2 bg-gray-800 border border-gray-700 rounded disabled:opacity-50 
                   hover:bg-gray-700 transition"
      >
        Next
      </button>
    </div>
  )
}
```

#### Projections Table Component

**File:** `src/components/projections/ProjectionsTable.jsx`

```jsx
import { Link } from 'react-router-dom'
import RiskBadge from './RiskBadge'

export default function ProjectionsTable({ projections, riskData }) {
  // Create risk lookup map
  const riskMap = {}
  riskData?.risk_assessments?.forEach(r => {
    riskMap[r.player_id] = r.injury_risk
  })
  
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-700">
            <th className="text-left py-3 px-4 text-gray-400 font-semibold">Player</th>
            <th className="text-left py-3 px-4 text-gray-400 font-semibold">Team</th>
            <th className="text-left py-3 px-4 text-gray-400 font-semibold">Pos</th>
            <th className="text-right py-3 px-4 text-gray-400 font-semibold">FP</th>
            <th className="text-right py-3 px-4 text-gray-400 font-semibold">PTS</th>
            <th className="text-right py-3 px-4 text-gray-400 font-semibold">REB</th>
            <th className="text-right py-3 px-4 text-gray-400 font-semibold">AST</th>
            <th className="text-left py-3 px-4 text-gray-400 font-semibold">Risk</th>
          </tr>
        </thead>
        <tbody>
          {projections.map(player => (
            <tr 
              key={player.player_id} 
              className="border-b border-gray-800 hover:bg-gray-800/50 transition"
            >
              <td className="py-3 px-4">
                <Link 
                  to={`/player/${player.player_id}`}
                  className="text-primary-400 hover:text-primary-300 font-medium"
                >
                  {player.name}
                </Link>
              </td>
              <td className="py-3 px-4 text-gray-300">{player.team}</td>
              <td className="py-3 px-4 text-gray-300">{player.position}</td>
              <td className="py-3 px-4 text-right font-semibold text-gray-100">
                {player.fantasy_points?.toFixed(1)}
              </td>
              <td className="py-3 px-4 text-right text-gray-300">
                {player.points?.toFixed(1)}
              </td>
              <td className="py-3 px-4 text-right text-gray-300">
                {player.rebounds?.toFixed(1)}
              </td>
              <td className="py-3 px-4 text-right text-gray-300">
                {player.assists?.toFixed(1)}
              </td>
              <td className="py-3 px-4">
                <RiskBadge risk={riskMap[player.player_id]} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

---

### Home Page Components

#### Hero Component

**File:** `src/components/home/Hero.jsx`

```jsx
import { Link } from 'react-router-dom'
import { useContent } from '../../hooks/useContent'

export default function Hero() {
  const { data: content } = useContent()
  
  return (
    <div className="text-center py-20 px-4">
      <h1 className="text-5xl md:text-6xl font-bold mb-6">
        {content?.homepage?.headline || 'NBA Fantasy Projections'}
      </h1>
      
      <p className="text-xl text-gray-400 mb-8 max-w-2xl mx-auto">
        {content?.homepage?.subheadline || 'Data-driven insights'}
      </p>
      
      <div className="flex flex-col sm:flex-row gap-4 justify-center">
        <Link
          to="/projections"
          className="px-8 py-3 bg-primary-500 text-white rounded-lg font-semibold 
                     hover:bg-primary-600 transition"
        >
          {content?.homepage?.cta_primary || 'View Projections'}
        </Link>
        
        <a
          href="#email-capture"
          className="px-8 py-3 bg-gray-800 text-gray-100 rounded-lg font-semibold 
                     border border-gray-700 hover:bg-gray-700 transition"
        >
          {content?.homepage?.cta_secondary || 'Get Insights'}
        </a>
      </div>
    </div>
  )
}
```

#### Value Props Component

**File:** `src/components/home/ValueProps.jsx`

```jsx
import { Shield, TrendingUp, Target } from 'lucide-react'
import { useContent } from '../../hooks/useContent'

export default function ValueProps() {
  const { data: content } = useContent()
  
  const features = [
    {
      icon: Shield,
      title: 'Risk-Adjusted Projections',
      description: content?.homepage?.value_props?.[0] || 'Trust our data'
    },
    {
      icon: TrendingUp,
      title: 'Volatility Indicators',
      description: content?.homepage?.value_props?.[1] || 'See the variance'
    },
    {
      icon: Target,
      title: 'Waiver Wire Intelligence',
      description: content?.homepage?.value_props?.[2] || 'Find hidden gems'
    }
  ]
  
  return (
    <div className="py-16 px-4">
      <div className="max-w-6xl mx-auto grid md:grid-cols-3 gap-8">
        {features.map((feature, idx) => (
          <div key={idx} className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 
                            bg-primary-500/20 rounded-full mb-4">
              <feature.icon className="w-8 h-8 text-primary-400" />
            </div>
            <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
            <p className="text-gray-400">{feature.description}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
```

#### Email Capture Component

**File:** `src/components/home/EmailCapture.jsx`

```jsx
export default function EmailCapture() {
  return (
    <div id="email-capture" className="py-16 px-4 bg-gray-800/50">
      <div className="max-w-2xl mx-auto text-center">
        <h2 className="text-3xl font-bold mb-4">
          Get Daily Fantasy Insights
        </h2>
        <p className="text-gray-400 mb-8">
          Join our mailing list for daily projections, waiver wire tips, and more
        </p>
        
        {/* Mailchimp Embed Form */}
        <div id="mc_embed_shell">
          {/* 
            PLACEHOLDER: Replace with actual Mailchimp embed code
            
            Instructions:
            1. Go to Mailchimp → Audience → Signup forms → Embedded forms
            2. Customize styling to match dark theme
            3. Copy embed code
            4. Paste here
            
            Example structure:
            <form action="..." method="post" id="mc-embedded-subscribe-form" name="mc-embedded-subscribe-form" class="validate" target="_blank">
              <input type="email" name="EMAIL" class="required email" id="mce-EMAIL" required="">
              <input type="submit" value="Subscribe" name="subscribe" id="mc-embedded-subscribe" class="button">
            </form>
          */}
          
          <div className="text-gray-500 text-sm">
            [Mailchimp form will be embedded here]
          </div>
        </div>
      </div>
    </div>
  )
}
```

---

## API INTEGRATION

### API Service Layer

**File:** `src/services/api.js`

```javascript
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// API endpoints
export const apiService = {
  // Health check
  healthCheck: () => api.get('/health'),
  
  // Content (dynamic copy)
  getContent: () => api.get('/api/content'),
  
  // Players
  getAllPlayers: () => api.get('/api/players'),
  getPlayer: (playerId) => api.get(`/api/players/${playerId}`),
  searchPlayers: (query) => api.get(`/api/players/search`, { params: { q: query } }),
  
  // Projections
  getProjections: (params = {}) => api.get('/api/projections', { params }),
  getTopPerformers: (limit = 10, category = 'fantasy_points') => 
    api.get('/api/projections/top', { params: { limit, category } }),
  
  // Insights
  getInsights: (params = {}) => api.get('/api/insights', { params }),
  
  // Risk
  getRiskAssessments: (params = {}) => api.get('/api/risk', { params }),
  
  // Injuries
  getInjuries: () => api.get('/api/injuries'),
}

export default api
```

### Custom Hooks

**File:** `src/hooks/useContent.js`

```javascript
import { useQuery } from '@tanstack/react-query'
import { apiService } from '../services/api'

export function useContent() {
  return useQuery({
    queryKey: ['content'],
    queryFn: async () => {
      const response = await apiService.getContent()
      return response.data
    },
    staleTime: 60 * 60 * 1000, // 1 hour (content changes infrequently)
  })
}
```

**File:** `src/hooks/useProjections.js`

```javascript
import { useQuery } from '@tanstack/react-query'
import { apiService } from '../services/api'

export function useProjections(params = {}) {
  return useQuery({
    queryKey: ['projections', params],
    queryFn: async () => {
      const response = await apiService.getProjections(params)
      return response.data
    },
  })
}
```

**File:** `src/hooks/usePlayer.js`

```javascript
import { useQuery } from '@tanstack/react-query'
import { apiService } from '../services/api'

export function usePlayer(playerId) {
  return useQuery({
    queryKey: ['player', playerId],
    queryFn: async () => {
      const response = await apiService.getPlayer(playerId)
      return response.data
    },
    enabled: !!playerId, // Only run if playerId exists
  })
}
```

**File:** `src/hooks/useInsights.js`

```javascript
import { useQuery } from '@tanstack/react-query'
import { apiService } from '../services/api'

export function useInsights(params = {}) {
  return useQuery({
    queryKey: ['insights', params],
    queryFn: async () => {
      const response = await apiService.getInsights(params)
      return response.data
    },
  })
}
```

---

## PAGE SPECIFICATIONS

### HomePage

**File:** `src/pages/HomePage.jsx`

```jsx
import Hero from '../components/home/Hero'
import ValueProps from '../components/home/ValueProps'
import EmailCapture from '../components/home/EmailCapture'

export default function HomePage() {
  return (
    <div>
      <Hero />
      <ValueProps />
      <EmailCapture />
    </div>
  )
}
```

---

### ProjectionsPage

**File:** `src/pages/ProjectionsPage.jsx`

```jsx
import { useState, useMemo } from 'react'
import { useProjections } from '../hooks/useProjections'
import { useQuery } from '@tanstack/react-query'
import { apiService } from '../services/api'
import { useContent } from '../hooks/useContent'
import ProjectionsTable from '../components/projections/ProjectionsTable'
import SearchBar from '../components/projections/SearchBar'
import Pagination from '../components/projections/Pagination'

export default function ProjectionsPage() {
  const { data: content } = useContent()
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [sortBy, setSortBy] = useState('fantasy_points')
  const itemsPerPage = 50
  
  // Fetch all projections
  const { data: projectionsData, isLoading: projectionsLoading } = useProjections({
    limit: 500,
    sort_by: sortBy,
    order: 'desc'
  })
  
  // Fetch risk data
  const { data: riskData, isLoading: riskLoading } = useQuery({
    queryKey: ['risk'],
    queryFn: async () => {
      const response = await apiService.getRiskAssessments({ limit: 500 })
      return response.data
    }
  })
  
  // Filter projections by search
  const filteredProjections = useMemo(() => {
    if (!projectionsData?.projections) return []
    
    if (!searchQuery) return projectionsData.projections
    
    return projectionsData.projections.filter(p =>
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.team.toLowerCase().includes(searchQuery.toLowerCase())
    )
  }, [projectionsData, searchQuery])
  
  // Paginate
  const totalPages = Math.ceil(filteredProjections.length / itemsPerPage)
  const paginatedProjections = filteredProjections.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  )
  
  const isLoading = projectionsLoading || riskLoading
  
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">
          {content?.projections_page?.title || 'Daily Projections'}
        </h1>
        <p className="text-gray-400">
          {content?.projections_page?.subtitle || '398 players'}
        </p>
      </div>
      
      <div className="mb-6">
        <SearchBar
          value={searchQuery}
          onChange={setSearchQuery}
          placeholder="Search players or teams..."
        />
      </div>
      
      {isLoading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
          <p className="text-gray-400 mt-4">Loading projections...</p>
        </div>
      ) : (
        <>
          <div className="bg-gray-800 rounded-lg overflow-hidden">
            <ProjectionsTable 
              projections={paginatedProjections} 
              riskData={riskData}
            />
          </div>
          
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
          />
          
          <div className="text-center text-gray-500 text-sm mt-4">
            Showing {filteredProjections.length} players
          </div>
        </>
      )}
    </div>
  )
}
```

---

### PlayerDetailPage

**File:** `src/pages/PlayerDetailPage.jsx`

```jsx
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { usePlayer } from '../hooks/usePlayer'
import { useContent } from '../hooks/useContent'
import RiskBadge from '../components/projections/RiskBadge'

export default function PlayerDetailPage() {
  const { playerId } = useParams()
  const { data: player, isLoading } = usePlayer(playerId)
  const { data: content } = useContent()
  
  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
        </div>
      </div>
    )
  }
  
  if (!player) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="text-center py-12">
          <p className="text-gray-400">Player not found</p>
          <Link to="/projections" className="text-primary-400 hover:text-primary-300 mt-4 inline-block">
            ← Back to Projections
          </Link>
        </div>
      </div>
    )
  }
  
  const projection = player.projection || {}
  const risk = player.risk || {}
  
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Link 
        to="/projections" 
        className="inline-flex items-center text-primary-400 hover:text-primary-300 mb-6"
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Projections
      </Link>
      
      {/* Player Header */}
      <div className="bg-gray-800 rounded-lg p-6 mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-4xl font-bold mb-2">{player.name}</h1>
            <div className="flex items-center space-x-4 text-gray-400">
              <span>{player.team}</span>
              <span>•</span>
              <span>{player.position}</span>
              <span>•</span>
              <span>Age {player.age}</span>
            </div>
          </div>
          
          <div className="text-right">
            <div className="text-sm text-gray-400 mb-1">Fantasy Points</div>
            <div className="text-3xl font-bold text-primary-400">
              {projection.fantasy_points?.toFixed(1)}
            </div>
          </div>
        </div>
      </div>
      
      {/* Stats Grid */}
      <div className="grid md:grid-cols-2 gap-6 mb-6">
        {/* Projected Stats */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Projected Stats</h2>
          <div className="space-y-3">
            <StatRow label="Minutes" value={projection.minutes?.toFixed(1)} />
            <StatRow label="Points" value={projection.points?.toFixed(1)} />
            <StatRow label="Rebounds" value={projection.rebounds?.toFixed(1)} />
            <StatRow label="Assists" value={projection.assists?.toFixed(1)} />
            <StatRow label="Steals" value={projection.steals?.toFixed(1)} />
            <StatRow label="Blocks" value={projection.blocks?.toFixed(1)} />
            <StatRow label="Turnovers" value={projection.turnovers?.toFixed(1)} />
            <StatRow label="FG%" value={`${(projection.fg_pct * 100)?.toFixed(1)}%`} />
            <StatRow label="FT%" value={`${(projection.ft_pct * 100)?.toFixed(1)}%`} />
            <StatRow label="3PM" value={projection.three_pointers?.toFixed(1)} />
          </div>
        </div>
        
        {/* Risk Analysis */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">
            {content?.player_detail?.risk_label || 'Risk Analysis'}
          </h2>
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400">Risk Level</span>
                <RiskBadge risk={risk.injury_risk} />
              </div>
            </div>
            
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400">
                  {content?.player_detail?.consistency_label || 'Consistency'}
                </span>
                <span className="font-semibold">{risk.consistency}/100</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div 
                  className="bg-green-500 h-2 rounded-full transition-all"
                  style={{ width: `${risk.consistency}%` }}
                />
              </div>
            </div>
            
            <StatRow 
              label={content?.player_detail?.ceiling_label || 'Ceiling'} 
              value={risk.ceiling?.toFixed(1)} 
            />
            <StatRow 
              label={content?.player_detail?.floor_label || 'Floor'} 
              value={risk.floor?.toFixed(1)} 
            />
            <StatRow 
              label={content?.player_detail?.volatility_label || 'Volatility'} 
              value={(risk.volatility * 100)?.toFixed(1) + '%'} 
            />
          </div>
          
          {risk.recommendation && (
            <div className="mt-4 p-3 bg-gray-700/50 rounded">
              <p className="text-sm text-gray-300">{risk.recommendation}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function StatRow({ label, value }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-gray-400">{label}</span>
      <span className="font-semibold text-gray-100">{value || 'N/A'}</span>
    </div>
  )
}
```

---

### InsightsPage

**File:** `src/pages/InsightsPage.jsx`

```jsx
import { useInsights } from '../hooks/useInsights'
import { useContent } from '../hooks/useContent'
import { TrendingUp } from 'lucide-react'

export default function InsightsPage() {
  const { data: insightsData, isLoading } = useInsights({ 
    category: 'all',
    limit: 50 
  })
  const { data: content } = useContent()
  
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">
          {content?.insights_page?.title || 'Waiver Wire Insights'}
        </h1>
        <p className="text-gray-400">
          {content?.insights_page?.subtitle || 'Deep sleepers and value plays'}
        </p>
      </div>
      
      {isLoading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
        </div>
      ) : (
        <div className="space-y-4">
          {insightsData?.insights?.map((insight, idx) => (
            <div key={idx} className="bg-gray-800 rounded-lg p-6 hover:bg-gray-750 transition">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="text-xl font-semibold mb-1">{insight.name}</h3>
                  <div className="flex items-center space-x-3 text-sm text-gray-400">
                    <span>{insight.team}</span>
                    <span>•</span>
                    <span>{insight.position}</span>
                    {insight.ownership_estimate && (
                      <>
                        <span>•</span>
                        <span>{insight.ownership_estimate} owned</span>
                      </>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <div className="text-right">
                    <div className="text-sm text-gray-400">Value Score</div>
                    <div className="text-2xl font-bold text-primary-400">
                      {insight.value_score?.toFixed(1)}
                    </div>
                  </div>
                  {insight.trending === 'up' && (
                    <TrendingUp className="w-6 h-6 text-green-400" />
                  )}
                </div>
              </div>
              
              <div className="mb-3">
                <span className="inline-block px-3 py-1 bg-primary-500/20 text-primary-400 rounded text-sm font-medium">
                  {insight.recommendation}
                </span>
              </div>
              
              <p className="text-gray-300">{insight.reasoning}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
```

---

## STYLING GUIDELINES

### Color Palette

```
Primary Blue: #3b82f6 (primary-500)
Secondary Orange: #f97316 (for accents)
Background: #111827 (gray-900)
Surface: #1f2937 (gray-800)
Border: #374151 (gray-700)
Text Primary: #f3f4f6 (gray-100)
Text Secondary: #9ca3af (gray-400)

Risk Colors:
- Low: #22c55e (green-500)
- Medium: #eab308 (yellow-500)
- High: #ef4444 (red-500)
```

### Typography

- Headlines: Bold, 2xl-6xl
- Body: Regular, base
- Labels: Semibold, sm
- Captions: Regular, xs

### Spacing

- Page padding: px-4 sm:px-6 lg:px-8
- Section spacing: py-8 or py-16
- Component spacing: space-y-4 or gap-4

---

## DEPLOYMENT INSTRUCTIONS

### Step 1: Build for Production

```bash
# Install dependencies
npm install

# Build
npm run build

# Test build locally
npm run preview
```

### Step 2: Deploy to Vercel

**Option A: Vercel CLI**

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set production environment variable
vercel env add VITE_API_BASE_URL production
# Enter: https://courtdominion.up.railway.app

# Deploy to production
vercel --prod
```

**Option B: GitHub Integration**

1. Push code to GitHub
2. Go to vercel.com
3. Import GitHub repository
4. Configure:
   - Framework: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Environment Variables:
     - `VITE_API_BASE_URL` = `https://courtdominion.up.railway.app`
5. Deploy

### Step 3: Configure Custom Domain (Optional)

1. In Vercel dashboard → Settings → Domains
2. Add domain: `courtdominion.com`
3. Update DNS records as instructed

---

## TESTING CHECKLIST

### Functionality Tests

- [ ] Homepage loads
- [ ] Navigation works (all links)
- [ ] Projections table displays 398 players
- [ ] Search filters players correctly
- [ ] Pagination works
- [ ] Risk badges show correct colors
- [ ] Player detail page loads from table click
- [ ] Player stats display correctly
- [ ] Risk analysis shows on player page
- [ ] Insights page displays recommendations
- [ ] Email capture form loads (Mailchimp embed)
- [ ] All dynamic content loads from `/api/content`

### Responsiveness Tests

- [ ] Mobile (375px width)
- [ ] Tablet (768px width)
- [ ] Desktop (1280px width)
- [ ] Navigation collapses on mobile (if implemented)
- [ ] Tables scroll horizontally on mobile
- [ ] Text is readable on all screen sizes

### Performance Tests

- [ ] Initial page load < 3 seconds
- [ ] API calls cached appropriately
- [ ] No console errors
- [ ] Images optimized (if any)

### Cross-Browser Tests

- [ ] Chrome
- [ ] Firefox
- [ ] Safari
- [ ] Edge

---

## HANDOFF INSTRUCTIONS

### For Another Developer

**Prerequisites:**
1. Node.js 18+ installed
2. Git installed
3. Backend running at http://localhost:8000 or Railway
4. Mailchimp account for email capture

**Setup:**
```bash
git clone [repo-url]
cd courtdominion-frontend
npm install
cp .env.example .env
# Edit .env with correct API URL
npm run dev
```

**Build Order:**
1. Set up project structure (2 hours)
2. Create layout components (1 hour)
3. Build HomePage (3 hours)
4. Build ProjectionsPage (5 hours)
5. Build PlayerDetailPage (3 hours)
6. Build InsightsPage (2 hours)
7. Polish & deploy (2 hours)

**Mailchimp Integration:**
- Get embed code from Mailchimp dashboard
- Paste into `EmailCapture.jsx`
- Style to match dark theme
- Test submission

---

### For Another Claude Instance

**Context to provide:**
1. This specification document
2. Backend API documentation (API_DOCUMENTATION.md)
3. Backend complete documentation (BACKEND_COMPLETE_DOCUMENTATION.md)
4. Phase 1 requirements document

**Instructions for Claude:**
```
Build a React frontend for CourtDominion using this specification.

Follow these files in order:
1. Read this entire specification
2. Create project structure
3. Build components as specified
4. Integrate APIs using provided hooks
5. Deploy to Vercel

Do not deviate from specification.
Do not add features not listed.
Ask questions if unclear.
```

---

## MAINTENANCE & UPDATES

### Updating Content

**To change copy without redeploying frontend:**

1. SSH into backend server (or edit locally)
2. Edit `/data/outputs/content.json`
3. Restart backend: `docker compose restart backend`
4. Frontend will fetch new content on next load

### Adding New Pages (Future)

If adding pages in Phase 2+:
1. Create page component in `src/pages/`
2. Add route in `src/App.jsx`
3. Add navigation link in `Header.jsx`
4. Update content.json with new page text

### Updating Dependencies

```bash
# Check for updates
npm outdated

# Update all
npm update

# Test after update
npm run build
npm run preview
```

---

## SUPPORT & TROUBLESHOOTING

### Common Issues

**Issue:** "Cannot fetch data from API"
- Check backend is running
- Verify `VITE_API_BASE_URL` in `.env`
- Check CORS settings on backend

**Issue:** "Mailchimp form not working"
- Verify embed code is correct
- Check Mailchimp account is active
- Test form submission manually

**Issue:** "Build fails"
- Clear node_modules: `rm -rf node_modules && npm install`
- Clear build cache: `rm -rf dist`
- Rebuild: `npm run build`

**Issue:** "Content not loading"
- Check `/api/content` endpoint works: `curl http://localhost:8000/api/content`
- Verify content.json exists in backend
- Check React Query cache

---

## CONCLUSION

This specification provides everything needed to build CourtDominion Phase 1 frontend.

**Estimated Timeline:**
- Setup: 1 hour
- Development: 15 hours
- Testing & Deploy: 2 hours
- **Total: 18 hours**

**Calendar Time:**
- Full-time: 2-3 days
- Part-time: 4-5 days

**Next Steps:**
1. Set up development environment
2. Install dependencies
3. Make backend changes (content endpoint)
4. Build components in order
5. Test thoroughly
6. Deploy to Vercel

**Questions?** Reference:
- Backend API Documentation
- Phase 1 Requirements
- This specification

---

**END OF BUILD SPECIFICATION**

**Status:** Ready for development  
**Target Launch:** January 19, 2026
