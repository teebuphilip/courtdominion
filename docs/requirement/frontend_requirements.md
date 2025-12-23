============================================================
COURTDOMINION — PHASE 1 FRONTEND REQUIREMENTS (REDUCED SCOPE)
============================================================

STATUS
------
Authoritative Phase 1 frontend requirements for CourtDominion.
This document reflects reduced scope due to founder workload
and is optimized for the fastest path to a credible Jan 2026 launch.

This is NOT a full product spec.
This is NOT Phase 2+.
This is the MINIMUM VIABLE COURTDOMINION FRONTEND.

------------------------------------------------------------
CORE PRINCIPLES
------------------------------------------------------------

1. Phase 1 is CONTENT-FIRST, not PRODUCT-FIRST
2. No user accounts, no auth, no personalization
3. Email capture is REQUIRED before showing projections
4. Backend is READ-ONLY (except email capture)
5. Frontend copy MUST be editable without redeploy
6. Everything must be simple enough to code quickly
7. Must position CD as DIFFERENT from ESPN / Yahoo / Swish

------------------------------------------------------------
BACKEND ASSUMPTIONS (ALREADY TRUE)
------------------------------------------------------------

The following backend APIs already exist and are sufficient:

- GET /health
- GET /api/projections
- GET /api/players/{id}
- GET /api/insights
- GET /api/risk
- GET /api/injuries
- GET /api/content

Backend reads JSON from /data/outputs
Backend does NOT compute on request
Backend does NOT manage users

------------------------------------------------------------
NEW PHASE 1 BACKEND ADDITION (MINIMAL)
------------------------------------------------------------

EMAIL CAPTURE ENDPOINT (REQUIRED)

- POST /api/subscribe
- Accepts: email, source, timestamp
- Stores emails in a flat file or external provider
- NO authentication
- NO user model
- NO sessions

This endpoint exists ONLY to:
- Gate projections
- Build a mailing list
- Enable Draft 2026 monetization

------------------------------------------------------------
FRONTEND PAGES (PHASE 1 ONLY)
------------------------------------------------------------

PAGE 1: LANDING / HOME
----------------------
Purpose:
- Explain what CourtDominion is
- Capture email BEFORE access
- Establish differentiation

Required Elements:
- Headline (dynamic)
- Subheadline (dynamic)
- 3–4 value props (dynamic)
- Email input + submit
- CTA: "Unlock Today’s Projections"

Behavior:
- User MUST submit email to continue
- After submit → access granted (cookie or localStorage OK)

------------------------------------------------------------

PAGE 2: PROJECTIONS TABLE (PRIMARY PAGE)
----------------------------------------
Purpose:
- Core product value
- Daily projections + risk clarity

Access Rule:
- BLOCKED until email submitted

Table Requirements:
- Show top 100 players
- Sortable columns
- Key columns:
  - Player
  - Team
  - Fantasy Points
  - Minutes
  - Key Stats (PTS / REB / AST)
  - Risk (color badge)
  - Injury Indicator (icon)

Risk Display:
- Simple color badge (green / yellow / red)
- Tooltip on hover (optional, cheap)

------------------------------------------------------------

PAGE 3: PLAYER DETAIL PAGE (OPTIONAL BUT RECOMMENDED)
-----------------------------------------------------
Purpose:
- Demonstrate depth & seriousness

Elements:
- Player name, team, position
- Projection stats
- Risk summary
- Insight text (if exists)
- Injury status

------------------------------------------------------------

PAGE 4: INSIGHTS / WAIVER PAGE (OPTIONAL)
-----------------------------------------
Purpose:
- Differentiation vs ESPN / Yahoo

Elements:
- Top waiver targets
- Short explanation text
- Value score
- Trend indicator

------------------------------------------------------------
DYNAMIC CONTENT REQUIREMENTS (CRITICAL)
------------------------------------------------------------

ALL TEXT CONTENT MUST BE CONTROLLABLE
WITHOUT FRONTEND REDEPLOY.

Content includes:
- Homepage headline
- Subheadline
- Value props
- CTA text
- Page titles
- Explanatory copy
- Email gate copy
- Footer copy

------------------------------------------------------------
CONTENT DELIVERY MECHANISM (PHASE 1)
------------------------------------------------------------

Chosen Approach: STATIC JSON FILE

- Content stored in:
  /data/outputs/content.json

- Backend exposes:
  GET /api/content

- Frontend loads content on page load
- Editing JSON updates site copy instantly

NO:
- CMS
- Admin UI
- POST content endpoints
- Auth

------------------------------------------------------------
CONTENT.JSON STRUCTURE (APPROVED)
------------------------------------------------------------

{
  "homepage": {
    "headline": "Coach-level fantasy clarity.",
    "subheadline": "Daily projections with real risk, not hype.",
    "value_props": [
      "Risk-aware, injury-adjusted projections",
      "Auction-first fantasy intelligence",
      "Built for serious players"
    ],
    "cta_primary": "Unlock Today’s Projections"
  },
  "projections_page": {
    "title": "Today’s Fantasy Projections",
    "subtitle": "Risk-aware. Injury-adjusted. No fluff.",
    "email_gate": {
      "headline": "Get full access to today’s projections",
      "subheadline": "Enter your email to unlock CourtDominion’s daily fantasy edge.",
      "cta": "Unlock Projections"
    }
  },
  "insights_page": {
    "title": "Waiver Wire Intelligence",
    "subtitle": "Who to add before your league notices."
  },
  "footer": {
    "disclaimer": "For informational purposes only. Not affiliated with Yahoo, ESPN, or Sleeper."
  }
}

------------------------------------------------------------
EMAIL GATING LOGIC
------------------------------------------------------------

- On first visit:
  - User sees landing page
  - Projections are hidden

- On email submit:
  - Call POST /api/subscribe
  - Store local flag (cookie or localStorage)
  - Unlock projections + insights

- NO login
- NO password
- NO account recovery
- Email is the ONLY identity

------------------------------------------------------------
WHAT IS EXPLICITLY OUT OF SCOPE (PHASE 1)
------------------------------------------------------------

- User accounts
- Authentication
- Saved players
- Custom scoring
- Draft kits
- Auction tools
- Season-long management
- Notifications
- Payments
- Tiered access

These belong to Phase 2+.

------------------------------------------------------------
WHY THIS WORKS FOR JAN 2026
------------------------------------------------------------

- Extremely fast to build
- Minimal cognitive load on founder
- Builds email list immediately
- Establishes differentiation early
- Backend already supports this
- Sets foundation for Draft 2026 monetization
- Fully compatible with FO-driven expansion

------------------------------------------------------------
END OF REQUIREMENTS
------------------------------------------------------------
