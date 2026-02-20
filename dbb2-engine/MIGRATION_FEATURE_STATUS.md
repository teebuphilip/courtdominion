# DBB2 Migration Feature Status

Original gap list (old DBB2 feature set vs new `dbb2-engine`) with current status:

1. Dynamic current-season selection (remove hardcoded season) - **DONE**
2. Daily NBA.com refresh for current-year stats - **DONE**
3. Live team games-played ingestion (for ROS math) - **DONE**
4. Live injury ingestion from external source - **DONE**
5. Live context wiring into projection/export flow - **DONE**
6. Season-aware projection pipeline (`season` input path) - **DONE**
7. Rookie comparable fallback logic - **DONE**
8. Cache builder with resilient fetch behavior (incl. backoff/retry patterns) - **DONE**
9. Failed-player retry pass for data collection - **DONE**
10. Pipeline/workflow integration for recurring refresh + projection run - **DONE**
11. Test coverage for season/live-data migration paths - **DONE**
12. Legacy “full app” endpoint surface parity (old multi-endpoint DBB2 API) - **NOT DONE**
13. Legacy league/account DB-backed feature set parity - **NOT DONE**
14. Legacy advanced tools parity (trade/streaming/lineup suite) - **DONE**
15. Legacy internal service endpoint parity (`/api/internal/baseline-projections` style contract in DBB2 itself) - **DONE**
16. Legacy-style enhanced risk parameterization + downstream usage path - **DONE** (implemented as parallel/enhanced track, not forced as sole/default path)
