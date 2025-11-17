CourtDominion Automation - OptionB-Final
======================================

Drop this folder into your repository as 'courtdominion-automation' and commit.
This package includes:

- config/settings.yml (adjust pause_until and times as needed)
- config/master_tasks.yaml (full master tasks for Nov18 -> Jan19)
- scripts/claude_runner.py (stub that produces projections.json and injury_feed.json)
- scripts/generator.py (generates per-platform drafts + rationale)
- scripts/quality_run.py (runs filters and writes filter_result.json)
- scripts/publish_decision.py (writes channel_status.json, per-channel logs, summary_<date>.json)
- scripts/summary_generator.py (human-readable summary)
- quality/filters.py (Option B quality gate)
- workflows/autopublish.yml (GitHub Actions workflow to run daily)
- outputs/logs/*.log (per-channel log files)
- secrets/*.placeholder (placeholders; DO NOT commit real credentials)

Testing locally:
1. python3 -m venv venv && source venv/bin/activate
2. pip install pyyaml
3. python courtdominion-automation/scripts/claude_runner.py
4. python courtdominion-automation/scripts/generator.py
5. python courtdominion-automation/scripts/quality_run.py
6. python courtdominion-automation/scripts/publish_decision.py
7. python courtdominion-automation/scripts/summary_generator.py

To enable automatic publishing, update config/settings.yml and remove or change the pause_until date. Use GitHub Secrets for live API keys and remove the secrets placeholders before pushing public repos.
