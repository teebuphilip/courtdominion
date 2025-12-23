COURTDOMINION — PHASE 2 AUCTION CORE (FEATURE LIST)
==================================================

OBJECTIVE:
Provide real-time auction draft decision support using
risk-adjusted values, tiers, and budget pressure.

--------------------------------------------------
CORE FEATURES (MUST BUILD)
--------------------------------------------------

1. Auction Value Engine
   - Risk-adjusted dollar values
   - Replacement-level baselines
   - One default league config (12-team, $200)

2. Tier Engine
   - Tier grouping by value drop-offs
   - Tier cliff detection
   - “Last in tier” flags

3. Manual Draft State Tracking
   - Players drafted
   - Prices paid
   - Budgets remaining
   - Slots remaining

4. Inflation Detection
   - Actual vs expected price tracking
   - Room-level inflation factor
   - Position-specific inflation

5. Should-I-Bid Decision Engine
   - YES / NO / CAUTION output
   - Suggested max bid
   - One-line rationale

6. Draft Board UI (Minimal)
   - Tiered auction board
   - Risk badges
   - Inflation indicators
   - “You’re up” view (Top 5 targets)

--------------------------------------------------
NON-GOALS (EXPLICITLY OUT OF SCOPE)
--------------------------------------------------

- No browser extensions
- No platform integrations
- No auto-bidding
- No ML opponents
- No auth or saved drafts
- No draft room scraping

--------------------------------------------------
OUTPUT CONTRACTS
--------------------------------------------------

- auction_values.json
- auction_tiers.json
- draft_state.json
- inflation_state.json
- bid_decision.json

--------------------------------------------------
SUCCESS CRITERIA
--------------------------------------------------

- Can complete a full auction draft manually
- Values feel defensible
- Tier cliffs are obvious
- Inflation reacts correctly
- Decision signals feel trustworthy

END
