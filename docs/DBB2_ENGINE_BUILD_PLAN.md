# DBB2 ENGINE BUILD PLAN: 14 Features in 10 Weeks

## Context

CourtDominion Phase 1 is live. The new 3-layer architecture (DBB2 engine → CD platform → product modules) requires a standalone DBB2 engine. This plan covers building 14 of 15 features via Claude Code, one feature/week, with tests. Feature 2 (Death Spots Calendar) is deferred to July when the NBA schedule drops.

---

## Decision: Don't Break the Existing CD App

**Build DBB2 as a new sibling directory. Leave `courtdominion-app/` untouched.**

- Phase 1 CD stays live — zero risk
- New engine has different architecture (30yr static data vs live API cache)
- FO builds Layer 2+3 on top later, imports `dbb2-engine` as dependency
- Old CD swaps to new engine via single import change when ready

**Location:** `~/Documents/work/courtdominion/dbb2-engine/`

---

## What Already Exists

**30 years of raw data is DONE** — located at `~/Downloads/DBB2-DATA-COLLECTION/`:
- 30 CSVs (`games_1995_96.csv` through `games_2024_25.csv`) — **733K total rows**
- Collection script: `collect_nba_season.py` (654 lines, well-structured)
- Shell runners: `run_all_seasons.sh`

**CSV Schema (27 columns):**
```
player_name, player_id, game_date, team, opponent, home_or_road,
minutes_played, points, rebounds, assists, steals, blocks, turnovers,
fgm, fga, fg_pct, three_pm, three_pa, fg3_pct, ftm, fta, ft_pct,
age, position, role, opponent_def_rank_vs_position, plus_minus, wl
```

**Data notes to handle in generators:**
- **Positions** use simplified format: `G`, `F`, `C`, `C-F`, `F-C`, `G-F`, `F-G` (not PG/SG/SF/PF/C) — generators must use these as-is or create a mapping
- **Roles** classified per-game: Starter (20+ min), Rotation (10-20), Bench (<10) — spec wanted 28/15/8; generators can re-bucket from raw `minutes_played`
- **`opponent_def_rank_vs_position`** already populated — Feature 3 script update is DONE
- **`plus_minus`** and **`wl`** included as bonus fields
- Some `age` values may be null for older seasons where birthdate wasn't available

---

## Updated Dependency Graph

```
WEEK 0: Project Scaffolding (light — data already exists)
    │
WEEK 1: F1 Age Profiles ← FOUNDATION
    │
    ├── WEEK 2: F4 Usage Rate + F5 Minutes Distribution
    ├── WEEK 3: F6 B2B Decline + F9 Rest Days Boost
    ├── WEEK 4: F7 Hot Spots + F8 Altitude Effects
    ├── WEEK 5: F11 Durability + F14 Position Scarcity
    ├── WEEK 6: F10 Ceiling Games + F3 Matchup Adjustments
    │
    └── WEEK 7: F12 Z-Scores + F13 SGP (need projection base)

WEEK 8: F15 Blowout Sensitivity (optional — spec says "skip for V1")
WEEK 9: Integration Engine (chains all features)
WEEK 10: Polish + CD Bridge

JULY (one-off): F2 Death Spots Calendar (when NBA schedule drops)
```

---

## Week-by-Week Plan

### WEEK 0: Project Scaffolding
**Goal:** Set up project structure, copy existing data, establish test infrastructure.

**Deliverables:**
- Directory structure per `model-updates.txt` Section 3.3:
  ```
  ~/Documents/work/courtdominion/dbb2-engine/
    static_data/profiles/
    static_data/matchups/
    static_data/calendars/
    static_data/usage/
    static_data/pricing/
    engine/
    data_collection/       ← copy collect_nba_season.py + run_all_seasons.sh
    raw_data/              ← symlink or copy 30 CSVs from ~/Downloads/DBB2-DATA-COLLECTION/raw_data/
    tests/
  ```
- `pyproject.toml` with deps: pandas, numpy, pytest
- `conftest.py` + shared test fixtures (CSV loading, sample data)
- CSV schema validation tests (confirm all 30 files have correct columns, no critical nulls)
- Shared utility: `load_all_seasons()` function that reads all CSVs into a single DataFrame
- Shared utility: position mapping helper (G/F/C/C-F → standardized buckets)
- Git init + `.gitignore` (exclude `raw_data/*.csv`, include everything else)

**Effort:** 1-2 sessions | ~15 messages | ~$8-15

---

### WEEK 1: Feature 1 — Age-Based Performance Profiles
**Goal:** Build the foundation every other feature depends on.

**Deliverables:**
- `data_collection/generate_age_profiles.py` — reads 30 CSVs, groups by (age, position, role)
- Re-bucket roles from raw `minutes_played`: Starter (28+), Rotation (15-27), Bench (8-14), Scrub (<8) — overriding the per-game role column with season-average role per player-season
- Three era output files:
  - `static_data/profiles/age_profiles_overall.py` (1995-2025)
  - `static_data/profiles/age_profiles_pre_modern.py` (1995-2017)
  - `static_data/profiles/age_profiles_modern.py` (2017-2025)
- Format: Python dict with tuple keys `(age, 'G', 'Starter')` → `{avg_points, stddev_points, variance_points, ..., sample_size}`
- Min sample: 50 games per bucket
- Null age handling: skip rows where age is null

**Tests:** Bucketing logic, known-player sanity checks, modern era has higher 3PM, sample sizes reasonable for ages 25-30, edge cases (age 19, age 39+)

**Effort:** 3-4 sessions | ~40 messages | ~$25-35

**Key files:**
- Input: `raw_data/games_*.csv` (all 30)
- Output: `static_data/profiles/age_profiles_*.py` (3 files)

---

### WEEK 2: Feature 4 (Usage Rate) + Feature 5 (Minutes Distribution)
**Goal:** Two independent features sharing same raw data iteration.

**F4 — Usage Rate Patterns:**
- Calculate usage rate: `(FGA + 0.44*FTA + TOV) / minutes_played` per game
- Simpler proxy: `FGA / minutes_played`
- Aggregate by (age, position, role): avg, stddev
- Output: `static_data/usage/usage_profiles.py`

**F5 — Minutes Distribution:**
- Per (age, position, role): 10th / 50th / 90th percentile of `minutes_played`
- Volatility: stddev < 5 = 'low', 5-10 = 'medium', >10 = 'high'
- Output: embedded in usage_profiles or standalone

**Tests:** Usage ranges 15-35%, bench < starter gap ~30%, percentile ordering, volatility classification

**Effort:** 2 sessions | ~20 messages | ~$10-18

---

### WEEK 3: Feature 6 (B2B Decline) + Feature 9 (Rest Days Boost)
**Goal:** Fatigue and rest effects — two sides of the same coin.

**F6 — B2B Decline:**
- Identify B2Bs: consecutive `game_date` entries for same player (1 calendar day apart)
- Compare 2nd-night performance vs non-B2B baseline
- Group by age bucket: Young (22-26), Prime (27-30), Veteran (31+)
- Output: `b2b_minutes_dropoff`, `b2b_scoring_dropoff` ratios

**F9 — Rest Days Boost:**
- Calculate days between games from `game_date`
- Compare 3+ day rest performance vs normal (1-2 day rest)
- Output: `rest_boost` multiplier by age bucket

**Output file:** `static_data/calendars/schedule_effects.py`
**Tests:** Veterans show 15-20% B2B decline vs young 8%. Veterans show +12% rest boost vs +5%.

**Effort:** 2 sessions | ~25 messages | ~$12-18

---

### WEEK 4: Feature 7 (Hot Spot Hangovers) + Feature 8 (Altitude Effects)
**Goal:** City-based schedule effects.

**F7 — Hot Spots:**
- Tier 1 cities: MIA, LAL, LAC, ATL, NYK, BKN, PHX
- Tier 2: GSW, HOU, TOR, DAL
- Flag games 1-2 days after playing IN a hot spot city (check `opponent` field to identify where the prior game was)
- Measure performance decline by age bucket
- Output: `hot_spot_dropoff`, `hot_spot_susceptibility`

**F8 — Altitude:**
- Altitude cities: DEN, UTA
- Flag games after playing at altitude, with recovery windows (B2B, 1 day, 2+ days)
- Output: `altitude_b2b_dropoff`, `altitude_recovery_1day`, `altitude_recovery_2day`

**Shared utility:** `TEAM_TO_CITY` mapping (team abbrev → city characteristics)
**Output file:** Added to `static_data/calendars/schedule_effects.py`
**Tests:** Young more susceptible to party cities (-12% vs -3%). Post-Denver B2B worst case (-18% to -28%).

**Effort:** 2 sessions | ~20 messages | ~$10-18

---

### WEEK 5: Feature 11 (Durability) + Feature 14 (Position Scarcity)
**Goal:** Roto-focused aggregate calculations.

**F11 — Durability & Games Played:**
- Count unique `game_date` entries per player per season
- Group by (age, position, role)
- Calculate: `avg_games_played`, `stddev_games_played`, `durability_score` (ratio to 82), `ironman_pct` (% played 70+)
- Output: added to age profiles or standalone

**F14 — Position Scarcity:**
- Count quality players per position per tier (by fantasy points thresholds)
- Calculate scarcity multipliers (C ≈ 1.15x, abundant SG ≈ 0.95x)
- Output: `static_data/pricing/position_scarcity.py`

**Tests:** 27yr starters avg ~74 games, 34yr starters avg ~58. Centers scarce, guards abundant in modern era.

**Effort:** 2 sessions | ~20 messages | ~$12-18

---

### WEEK 6: Feature 10 (Ceiling Games) + Feature 3 (Matchup Adjustments)
**Goal:** Ceiling tracker + full matchup system (script update NOT needed — data already has `opponent_def_rank_vs_position`).

**F10 — Ceiling Games:**
- Calculate DFS fantasy points per game: `PTS*1 + REB*1.2 + AST*1.5 + STL*3 + BLK*3 + TOV*-1`
- Per (age, position, role): 90th percentile threshold
- `ceiling_game_pct` (% of games above threshold), `avg_ceiling_game_pts`
- Output: added to profiles or standalone

**F3 — Matchup Adjustments:**
- Uses **existing** `opponent_def_rank_vs_position` column (1-30)
- Filter to 3 years (2022-2025, post-COVID)
- Bucket opponents: Elite (1-6), Above Avg (7-12), Avg (13-18), Below Avg (19-24), Poor (25-30)
- Per (age, position, role, opponent_bucket, home_or_road): calculate stat multipliers + variance increase
- Min sample: 30 games
- Output: `static_data/matchups/matchup_adjustments.py` + `opponent_defense_baseline.py`

**Tests:** Elite road defense = -18% scoring. Poor home defense = +19%. All multipliers bounded 0.5-2.0. F10: young stars 8-10% ceiling rate vs veterans 3-5%.

**Effort:** 2-3 sessions | ~30 messages | ~$15-25

---

### WEEK 7: Feature 12 (Z-Scores) + Feature 13 (SGP Weighting)
**Goal:** Auction pricing foundation.

**F12 — Z-Score Values:**
- League averages + stddevs per stat category (PPG, RPG, APG, STL, BLK, 3PM, FG%, FT%)
- Z-score = (stat - avg) / stddev
- Position-adjusted: assists from C vs from G get different context
- Output: `static_data/pricing/z_score_baselines.py`

**F13 — SGP Weighting:**
- Simulate 12-team league standings from historical data
- Calculate gaps between standings places per category
- Derive SGP weight per category
- Positional bonuses (assists from C = 1.5x, blocks from G = 1.4x)
- Output: `static_data/pricing/sgp_weights.py`

**Tests:** +2.0 z-score = elite. FT% gets higher SGP weight than rebounds. Jokic prices at $65-75. Budget sums to $2,400.

**Effort:** 2-3 sessions | ~30 messages | ~$20-30

---

### WEEK 8: Feature 15 — Blowout Sensitivity *(optional — spec says "skip for V1")*
**Goal:** Last feature. Can use `plus_minus` as a proxy for game margin, or derive from `wl` + score data.

**What gets built:**
- Identify blowout games: absolute `plus_minus` >= 15 (proxy for game margin)
- Per (age, position, role): `pct_games_blowout`, `avg_mins_when_close` vs `avg_mins_when_blowout`
- Blowout risk by team/matchup type
- Output: standalone or added to profiles

**Note:** `plus_minus` is player-level +/-, not game margin. If precision matters, may need script update to add actual game scores. For V1, player +/- as proxy is reasonable.

**Tests:** Stars lose -12% minutes in blowouts. Underdogs play full minutes.

**If deferred:** Merge Weeks 8+9 → save a week (9-week total).

**Effort:** 2 sessions | ~20 messages | ~$10-15

---

### WEEK 9: Integration Engine
**Goal:** Chain all features into a unified runtime engine with clean API.

**Deliverables:**
- `engine/projections.py` — loads all static data at startup, chains adjustments for any player + game context. All lookups O(1) dict access.
- `engine/dfs_optimizer.py` — daily slate building with cash/GPP recommendations
- `engine/auction_pricer.py` — season-long auction values ($1-$70 scale)
- `engine/__init__.py` — clean public API for FO to consume
- Backtest framework: test against 2019-2024 seasons

**Adjustment chain:**
```
base_age_profile → usage_adj → matchup_adj → b2b → rest →
hot_spot → altitude → blowout → minutes_dist → ceiling_prob → final
```

**Hard bounds:** Total compound adjustment must stay between 0.50 and 1.50 — log any cases hitting bounds.

**Tests:** End-to-end RMSE < 7.8 (vs baseline 8.5). DFS smoke test on historical date. Auction budget constraint.

**Effort:** 3-4 sessions | ~50 messages | ~$25-35

---

### WEEK 10: Polish + CD Bridge
**Goal:** Documentation, Docker, integration adapter.

**Deliverables:**
- Fill test coverage gaps, full regression suite
- `README.md` — project overview, setup, architecture
- `ANNUAL_MAINTENANCE.md` — 5-week summer rebuild workflow (from spec Section 3.5)
- `Dockerfile` for standalone engine
- CD integration bridge: thin adapter so `courtdominion-app/automation/projection_generator.py` can import new engine via single line change
- Data validation suite per spec Section 3.6

**Effort:** 2-3 sessions | ~25 messages | ~$15-25

---

### JULY (One-Off): Feature 2 — Death Spots Calendar
**Goal:** Generate the composite death spots calendar when NBA schedule is released.

**What gets built:**
- `data_collection/generate_death_spots.py`
- Takes released 2026-27 NBA schedule as input
- Uses measured effect sizes from F6, F7, F8 (already built) as severity calibrations
- Compound patterns: LA→Utah B2B (-31%), post-Denver B2B (-23%), post-Miami B2B (-18%)
- Age amplification: veterans 20-30% worse
- Output: `static_data/calendars/death_spots_2026_27.py` keyed by `(team, date)`
- O(1) lookup at runtime

**Tests:** Compound effects worse than single effects. Home teams exempt from altitude. Known death spot patterns validated.

**Effort:** 2 sessions | ~20 messages | ~$12-20

---

## Totals

| | Sessions | Messages | Est. Cost |
|---|---------|----------|-----------|
| **All 11 weeks (Feb-Apr)** | 24-32 | ~300 | **$162-252** |
| **If skip F15 (10 weeks)** | 22-30 | ~280 | **$150-235** |
| **+ July Death Spots** | +2 | +20 | **+$12-20** |

---

## Key Files

| File | Purpose |
|------|---------|
| `~/Downloads/DBB2-DATA-COLLECTION/raw_data/*.csv` | 30 years raw data (733K rows) |
| `~/Downloads/DBB2-DATA-COLLECTION/collect_nba_season.py` | Collection script (copy to new project) |
| `~/Downloads/FUTURE-CD-BASKETBALL-WORK/model-updates.txt` | Primary spec (15 features, schemas, architecture) |
| `~/Downloads/FUTURE-CD-BASKETBALL-WORK/DBB2_COMPLETE_ENHANCEMENT_ROADMAP.md` | Roadmap (auction code, RMSE targets) |
| `~/Downloads/FUTURE-CD-BASKETBALL-WORK/dfs-feature-3.txt` | DFS Risk Optimizer product spec |
| `courtdominion-app/automation/dbb2_projections.py` | Current baseline engine (to be replaced) |
| `courtdominion-app/automation/projection_generator.py` | CD integration point (single import swap) |

---

## Full Product Timeline (All 3 Layers)

Layer 2 starts immediately (FO has auth/billing template). Product modules stagger based on DBB2 feature availability.

| Work | Builder | Start | Ship | Depends On |
|------|---------|-------|------|------------|
| **Layer 1: DBB2 Engine** | You + Claude Code | **Feb** | **Apr** | — |
| **Layer 2: CD Platform** (auth/billing/entitlements) | FO (template clone) | **Feb/Mar** | **Mar/Apr** | — |
| **Module 3: DFS Risk Optimizer** ($5.99/mo, "Play or Not") | FO | **Late Mar** | **May** | DBB2 Wk3-4 (age profiles + variance + schedule effects) |
| **Module 2: Auction Product** (draft tool, cheat sheets) | FO | **Early Apr** | **Jun** | DBB2 Wk7 (Z-scores + SGP + scarcity + durability) |
| **Module 1: DFS Optimizer** (salary cap, slate builder) | FO | **Apr** | **Jun/Jul** | DBB2 Wk10 (all features) + Death Spots (Jul) |
| **Death Spots Calendar** | You + Claude Code | **Jul** | **Jul** | NBA schedule release |
| **Soft Launch** (beta users) | — | — | **Aug** | All above |
| **Full Launch** (2026-27 season) | — | — | **Oct** | Soft launch feedback |

**Key:** All 3 paying features start by April, ship May-June, soft launch August — 2 months before season.

---

## Risks & Mitigations

1. **Rare age/position/role buckets have <50 samples** — Fall back to nearest age or collapsed role bucket
2. **Compound multipliers produce unreasonable projections** — Hard bounds: 0.50-1.50, log violations
3. **Position format (G/F/C-F vs PG/SG)** — Use CSV format as-is in tuple keys; mapping only needed for user-facing display
4. **Null ages in older seasons** — Skip rows with null age; validate sample sizes aren't materially affected
5. **Feature 15 `plus_minus` is player-level, not game margin** — Acceptable proxy for V1; exact game margin can be added in summer data refresh
6. **Feature 2 blocked until July** — Historical validation of effect sizes (F6/F7/F8) happens in Weeks 3-4; only the calendar generation waits for schedule
