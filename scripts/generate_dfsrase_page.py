#!/usr/bin/env python3
"""Generate a static public page for DFSRASE model and write to reports/web."""

from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "dfsrase" / "data"
SUMMARY_PATH = DATA_DIR / "public_model_summary.json"
HISTORY_PATH = DATA_DIR / "bankroll_history.json"
OUTPUT_DIR = ROOT / "reports" / "web"


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def render(summary: dict, history: list) -> str:
    chart_points = []
    for row in history:
        date = str(row.get("date", ""))
        bankroll = float(row.get("bankroll_end", 0.0) or 0.0)
        conf = str(row.get("confidence", "")).lower()
        color = "#22c55e" if conf == "green" else "#eab308" if conf == "yellow" else "#ef4444"
        chart_points.append((date, bankroll, color))

    # Build lightweight sparkline polyline points with fixed 800x220 space.
    width = 800
    height = 220
    pad = 24
    y_vals = [p[1] for p in chart_points] or [5000.0]
    ymin = min(y_vals)
    ymax = max(y_vals)
    yrange = max(1.0, ymax - ymin)

    poly_points = []
    markers = []
    for i, (d, y, c) in enumerate(chart_points):
        x = pad + (i / max(1, len(chart_points) - 1)) * (width - 2 * pad)
        yy = height - pad - ((y - ymin) / yrange) * (height - 2 * pad)
        poly_points.append(f"{x:.1f},{yy:.1f}")
        markers.append(f"<circle cx='{x:.1f}' cy='{yy:.1f}' r='3' fill='{c}'><title>{html.escape(d)}: ${y:.2f}</title></circle>")

    summary = summary or {
        "start_date": "2026-02-28",
        "starting_bankroll": 5000.0,
        "current_bankroll": 5000.0,
        "roi_percent": 0.0,
        "green_days": 0,
        "yellow_days": 0,
        "red_days": 0,
        "days_played": 0,
    }

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>CourtDominion - Public DFS Bankroll Model</title>
  <style>
    :root {{
      --bg:#0f172a;
      --bg2:#111827;
      --panel:#1f2937;
      --line:#374151;
      --ink:#f3f4f6;
      --muted:#9ca3af;
      --green:#22c55e;
      --yellow:#eab308;
      --red:#ef4444;
      --blue:#3b82f6;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Avenir Next","Segoe UI",system-ui,sans-serif;
      color: var(--ink);
      background:
        radial-gradient(1200px 450px at 95% -10%, rgba(59,130,246,.18), transparent 55%),
        linear-gradient(180deg, var(--bg), var(--bg2));
      min-height: 100vh;
    }}
    .wrap {{ max-width: 1100px; margin: 22px auto 36px; padding: 0 14px; }}
    .hero {{ background: linear-gradient(180deg, rgba(31,41,55,.96), rgba(17,24,39,.96)); border:1px solid var(--line); border-radius:16px; padding:18px; }}
    h1 {{ margin:0 0 8px; font-size:30px; }}
    .sub {{ color: var(--muted); font-size:14px; }}
    .grid {{ display:grid; grid-template-columns: repeat(4,minmax(140px,1fr)); gap:10px; margin-top:14px; }}
    .kpi {{ background:rgba(17,24,39,.7); border:1px solid var(--line); border-radius:12px; padding:10px; }}
    .kpi .label {{ font-size:11px; color:var(--muted); text-transform:uppercase; letter-spacing:.08em; }}
    .kpi .val {{ font-size:24px; font-weight:700; margin-top:4px; }}
    .section {{ margin-top:14px; background:rgba(31,41,55,.92); border:1px solid var(--line); border-radius:14px; padding:14px; }}
    .rule {{ color:#cbd5e1; font-size:14px; margin:4px 0; }}
    table {{ width:100%; border-collapse: collapse; font-size:13px; }}
    th,td {{ padding:8px 9px; border-bottom:1px solid rgba(55,65,81,.45); text-align:left; white-space:nowrap; }}
    thead th {{ background:#111827; position:sticky; top:0; }}
    .chart {{ width:100%; overflow:auto; border:1px solid var(--line); border-radius:12px; background:#0b1220; }}
    .foot {{ margin-top:10px; color:var(--muted); font-size:12px; }}
    @media (max-width: 900px) {{ .grid {{ grid-template-columns:repeat(2,minmax(140px,1fr)); }} }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <h1>Public Bankroll Model (v1)</h1>
      <div class="sub">Read-only deterministic simulation. No real-money execution. Updated nightly.</div>
      <div class="grid">
        <div class="kpi"><div class="label">Start</div><div class="val">${float(summary.get('starting_bankroll', 5000.0)):,.2f}</div></div>
        <div class="kpi"><div class="label">Current</div><div class="val">${float(summary.get('current_bankroll', 5000.0)):,.2f}</div></div>
        <div class="kpi"><div class="label">ROI</div><div class="val">{float(summary.get('roi_percent', 0.0)):+.2f}%</div></div>
        <div class="kpi"><div class="label">Days Played</div><div class="val">{int(summary.get('days_played', 0))}</div></div>
        <div class="kpi"><div class="label">Green Days</div><div class="val">{int(summary.get('green_days', 0))}</div></div>
        <div class="kpi"><div class="label">Yellow Days</div><div class="val">{int(summary.get('yellow_days', 0))}</div></div>
        <div class="kpi"><div class="label">Red Days</div><div class="val">{int(summary.get('red_days', 0))}</div></div>
        <div class="kpi"><div class="label">Start Date</div><div class="val" style="font-size:17px">{html.escape(str(summary.get('start_date', '2026-02-28')))}</div></div>
      </div>
    </section>

    <section class="section">
      <h2 style="margin:0 0 8px">Locked Rules</h2>
      <div class="rule">Green day wager: 5% of bankroll</div>
      <div class="rule">Yellow day wager: 2% of bankroll</div>
      <div class="rule">Red day wager: 0% (skip)</div>
      <div class="rule">Payout model: if auction_actual &gt; projection_actual =&gt; 1.5x wager, else 0</div>
    </section>

    <section class="section">
      <h2 style="margin:0 0 10px">Bankroll Curve</h2>
      <div class="chart">
        <svg viewBox="0 0 {width} {height}" width="100%" height="240" preserveAspectRatio="xMidYMid meet">
          <polyline fill="none" stroke="var(--blue)" stroke-width="2" points="{' '.join(poly_points)}" />
          {''.join(markers)}
        </svg>
      </div>
    </section>

    <section class="section">
      <h2 style="margin:0 0 10px">History</h2>
      <div style="overflow:auto; border:1px solid var(--line); border-radius:12px;">
        <table>
          <thead><tr><th>Date</th><th>Conf</th><th>Start</th><th>Wager</th><th>Payout</th><th>End</th><th>Auction</th><th>Projection</th></tr></thead>
          <tbody>
            {''.join(f"<tr><td>{html.escape(str(r.get('date','')))}</td><td>{html.escape(str(r.get('confidence','')))}</td><td>${float(r.get('bankroll_start',0)):,.2f}</td><td>${float(r.get('wager_amount',0)):,.2f}</td><td>${float(r.get('payout_amount',0)):,.2f}</td><td>${float(r.get('bankroll_end',0)):,.2f}</td><td>{float(r.get('auction_score_actual',0)):.2f}</td><td>{float(r.get('projection_score_actual',0)):.2f}</td></tr>" for r in reversed(history))}
          </tbody>
        </table>
      </div>
      <div class="foot">Generated at {html.escape(datetime.utcnow().isoformat())} UTC.</div>
    </section>
  </div>
</body>
</html>
"""


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = load_json(SUMMARY_PATH, {})
    history = load_json(HISTORY_PATH, [])
    page = render(summary, history)
    out = OUTPUT_DIR / "dfsrase_public_model.html"
    out.write_text(page)
    (OUTPUT_DIR / "dfsrase_public_model_data.json").write_text(json.dumps({"summary": summary, "history": history}, indent=2))
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
