#!/usr/bin/env python3
"""Generate polished static HTML pages for betting/exchange bet history + today's slate."""

from __future__ import annotations

import csv
import html
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover (py<3.9 fallback)
    ZoneInfo = None


ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "reports" / "web"


def ny_today() -> str:
    if ZoneInfo is None:
        return datetime.utcnow().strftime("%Y-%m-%d")
    return datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")


def load_betting_csv(path: Path, track: str, exclude_date: str) -> List[Dict]:
    if not path.exists():
        return []
    rows: List[Dict] = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("date") == exclude_date:
                continue
            row["track"] = track
            row["engine"] = "betting"
            rows.append(row)
    return rows


def load_exchange_slips(dir_path: Path, track: str, exclude_date: str) -> List[Dict]:
    if not dir_path.exists():
        return []
    rows: List[Dict] = []
    for fp in sorted(dir_path.glob("*.json")):
        try:
            payload = json.loads(fp.read_text())
        except Exception:
            continue
        date = str(payload.get("date", "")).strip()
        if not date or date == exclude_date:
            continue
        for bet in payload.get("bets", []):
            rows.append(
                {
                    "date": date,
                    "engine": "exchange",
                    "track": track,
                    "player_name": bet.get("player_name", ""),
                    "prop_type": bet.get("prop_type", ""),
                    "direction": bet.get("direction", ""),
                    "dbb2_projection": bet.get("projection", ""),
                    "sportsbook_line": bet.get("line", ""),
                    "edge_pct": bet.get("edge_pct", ""),
                    "confidence": bet.get("confidence", ""),
                    "units": bet.get("units", ""),
                    "source": bet.get("source", ""),
                    "execution_type": bet.get("execution_type", ""),
                    "status": "",
                    "pnl": "",
                }
            )
    return rows


def parse_num(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return default


def summarize(rows: List[Dict]) -> Dict[str, float]:
    return {
        "count": len(rows),
        "units": round(sum(parse_num(r.get("units")) for r in rows), 2),
        "pnl": round(sum(parse_num(r.get("pnl")) for r in rows), 2),
    }


def render_table_rows(rows: List[Dict]) -> str:
    out = []
    for r in sorted(rows, key=lambda x: (x.get("date", ""), x.get("engine", ""), x.get("player_name", "")), reverse=True):
        track = str(r.get("track", ""))
        track_cell = (
            f"<span class='track {'enhanced' if track == 'enhanced' else 'baseline'}'>{html.escape(track)}</span>"
            if track
            else ""
        )
        cells = [
            r.get("date", ""),
            r.get("engine", ""),
            track_cell,
            r.get("player_name", ""),
            r.get("prop_type", ""),
            r.get("direction", ""),
            r.get("dbb2_projection", ""),
            r.get("sportsbook_line", ""),
            r.get("edge_pct", ""),
            r.get("confidence", ""),
            r.get("units", ""),
            r.get("source", ""),
            r.get("execution_type", ""),
            r.get("status", ""),
            r.get("pnl", ""),
        ]
        row_cells = []
        for i, c in enumerate(cells):
            if i == 2:
                row_cells.append(f"<td>{c}</td>")
            else:
                row_cells.append(f"<td>{html.escape(str(c))}</td>")
        out.append("<tr>" + "".join(row_cells) + "</tr>")
    return "\n".join(out)


def _shell_style() -> str:
    return """
    :root {
      --bg:#111827;           /* gray-900 */
      --bg2:#0b1220;
      --panel:#1f2937;        /* gray-800 */
      --line:#374151;         /* gray-700 */
      --ink:#f3f4f6;          /* gray-100 */
      --muted:#9ca3af;        /* gray-400 */
      --primary:#3b82f6;      /* blue-500 */
      --secondary:#f97316;    /* orange-500 */
      --good:#22c55e;
      --bad:#ef4444;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0; padding: 0;
      font-family: "Avenir Next","Segoe UI",system-ui,sans-serif;
      color: var(--ink);
      background:
        radial-gradient(1000px 420px at 95% -10%, rgba(59,130,246,.16), transparent 60%),
        radial-gradient(900px 380px at -8% 0%, rgba(249,115,22,.11), transparent 58%),
        linear-gradient(180deg, var(--bg), var(--bg2));
      min-height: 100vh;
    }
    .wrap { max-width: 1320px; margin: 24px auto 42px; padding: 0 16px; }
    .hero { background: linear-gradient(180deg, rgba(31,41,55,.96), rgba(17,24,39,.96)); border:1px solid var(--line); border-radius:18px; padding:20px; }
    h1 { margin:0 0 8px; font-size:30px; letter-spacing:.2px; }
    h2 { margin:0 0 8px; font-size:22px; }
    .sub { color:var(--muted); font-size:14px; }
    .links { display:flex; gap:10px; margin-top:12px; flex-wrap:wrap; }
    .links a {
      color:var(--ink); text-decoration:none; font-size:13px; padding:7px 12px;
      border:1px solid var(--line); border-radius:999px; background:rgba(55,65,81,.35);
    }
    .links a:hover { border-color:var(--primary); box-shadow:0 0 0 1px rgba(59,130,246,.25) inset; }
    .grid { display:grid; grid-template-columns: repeat(4,minmax(170px,1fr)); gap:12px; margin-top:14px; }
    .kpi { background:rgba(17,24,39,.72); border:1px solid var(--line); border-radius:13px; padding:11px 12px; }
    .kpi .label { font-size:11px; color:var(--muted); text-transform:uppercase; letter-spacing:.08em; }
    .kpi .val { font-size:24px; font-weight:700; margin-top:4px; }
    .section { margin-top:16px; background: rgba(31,41,55,.92); border:1px solid var(--line); border-radius:14px; padding:14px; }
    .row { display:flex; justify-content:space-between; gap:10px; align-items:center; margin-bottom:10px; }
    .pill { font-size:12px; border:1px solid var(--line); border-radius:999px; padding:4px 9px; color:var(--muted); }
    .pill.blue { color:#bfdbfe; border-color:rgba(59,130,246,.45); }
    .pill.orange { color:#fed7aa; border-color:rgba(249,115,22,.45); }
    .table-wrap { overflow:auto; border:1px solid var(--line); border-radius:12px; }
    table { width:100%; border-collapse: collapse; font-size:13px; }
    th,td { white-space:nowrap; text-align:left; padding:9px 10px; border-bottom:1px solid rgba(55,65,81,.5); }
    thead th { background:#111827; position:sticky; top:0; z-index:1; }
    tbody tr:hover { background: rgba(59,130,246,.08); }
    .track { font-size:11px; padding:2px 8px; border-radius:999px; border:1px solid; display:inline-block; }
    .track.baseline { border-color:rgba(59,130,246,.5); color:#bfdbfe; }
    .track.enhanced { border-color:rgba(249,115,22,.5); color:#fed7aa; }
    .foot { margin-top:12px; color:var(--muted); font-size:12px; }
    @media (max-width: 900px) { .grid { grid-template-columns:repeat(2,minmax(140px,1fr)); } }
    """


def _table_header() -> str:
    return (
        "<thead><tr>"
        "<th>Date</th><th>Engine</th><th>Track</th><th>Player</th><th>Prop</th><th>Dir</th>"
        "<th>Proj</th><th>Line</th><th>Edge%</th><th>Conf</th><th>Units</th><th>Source</th>"
        "<th>Exec</th><th>Status</th><th>P/L</th>"
        "</tr></thead>"
    )


def render_history_page(all_rows: List[Dict], exclude_date: str) -> str:
    baseline_rows = [r for r in all_rows if r.get("track") == "baseline"]
    enhanced_rows = [r for r in all_rows if r.get("track") == "enhanced"]

    s_all = summarize(all_rows)
    s_base = summarize(baseline_rows)
    s_enh = summarize(enhanced_rows)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>CourtDominion - Historical Bet Runs</title>
  <style>{_shell_style()}</style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <h1>Historical Bet Runs</h1>
      <div class="sub">Built from betting + exchange history. Today's date ({html.escape(exclude_date)}) is excluded.</div>
      <div class="links">
        <a href="./index.html">Historical</a>
        <a href="./today.html">Today's Bets</a>
      </div>
      <div class="grid">
        <div class="kpi"><div class="label">All Bets</div><div class="val">{s_all['count']}</div></div>
        <div class="kpi"><div class="label">Baseline Bets</div><div class="val">{s_base['count']}</div></div>
        <div class="kpi"><div class="label">Enhanced Bets</div><div class="val">{s_enh['count']}</div></div>
        <div class="kpi"><div class="label">All Units</div><div class="val">{s_all['units']}</div></div>
        <div class="kpi"><div class="label">Baseline P/L</div><div class="val">{s_base['pnl']:+.2f}</div></div>
        <div class="kpi"><div class="label">Enhanced P/L</div><div class="val">{s_enh['pnl']:+.2f}</div></div>
        <div class="kpi"><div class="label">Baseline Units</div><div class="val">{s_base['units']}</div></div>
        <div class="kpi"><div class="label">Enhanced Units</div><div class="val">{s_enh['units']}</div></div>
      </div>
    </section>

    <section class="section">
      <div class="row">
        <h2>All Historical Bets</h2>
        <div>
          <span class="pill blue">Baseline</span>
          <span class="pill orange">Enhanced</span>
        </div>
      </div>
      <div class="table-wrap">
        <table>
          {_table_header()}
          <tbody>
            {render_table_rows(all_rows)}
          </tbody>
        </table>
      </div>
      <div class="foot">Generated at {html.escape(datetime.utcnow().isoformat())} UTC.</div>
    </section>
  </div>
</body>
</html>
"""


def render_today_sections(rows: List[Dict], today: str) -> str:
    def section(engine: str, title: str) -> str:
        erows = [r for r in rows if r.get("engine") == engine]
        summary = summarize(erows)
        if not erows:
            body = "<div class='sub'>No bets for this section today.</div>"
        else:
            body = (
                "<div class='table-wrap'><table>"
                + _table_header()
                + "<tbody>"
                + render_table_rows(erows)
                + "</tbody></table></div>"
            )
        return (
            "<section class='section'>"
            f"<div class='row'><h2>{html.escape(title)}</h2>"
            f"<span class='pill'>{summary['count']} bets • {summary['units']} units • P/L {summary['pnl']:+.2f}</span></div>"
            + body
            + "</section>"
        )

    return "\n".join(
        [
            section("betting_sportsbook", "Sportsbook"),
            section("betting_kalshi", "Kalshi"),
            section("exchange", "Exchange"),
        ]
    )


def render_today_page(today_rows: List[Dict], today: str) -> str:
    s = summarize(today_rows)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>CourtDominion - Today's Bets</title>
  <style>{_shell_style()}</style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <h1>Today's Bets</h1>
      <div class="sub">Date: {html.escape(today)} • Broken out by sportsbook, kalshi, and exchange.</div>
      <div class="links">
        <a href="./index.html">Historical</a>
        <a href="./today.html">Today's Bets</a>
      </div>
      <div class="grid">
        <div class="kpi"><div class="label">Total Bets</div><div class="val">{s['count']}</div></div>
        <div class="kpi"><div class="label">Total Units</div><div class="val">{s['units']}</div></div>
        <div class="kpi"><div class="label">Total P/L</div><div class="val">{s['pnl']:+.2f}</div></div>
        <div class="kpi"><div class="label">Generated</div><div class="val" style="font-size:16px">{html.escape(datetime.utcnow().strftime('%H:%M UTC'))}</div></div>
      </div>
    </section>
    {render_today_sections(today_rows, today)}
  </div>
</body>
</html>
"""


def main() -> int:
    today = ny_today()
    exclude_date = today
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    history_rows = []
    history_rows += load_betting_csv(ROOT / "betting-engine" / "data" / "bets" / "master_bets.csv", "baseline", exclude_date)
    history_rows += load_betting_csv(ROOT / "betting-engine" / "data" / "bets" / "master_bets_enhanced.csv", "enhanced", exclude_date)
    history_rows += load_exchange_slips(ROOT / "exchange-engine" / "data" / "bet_slips", "baseline", exclude_date)
    history_rows += load_exchange_slips(ROOT / "exchange-engine" / "data" / "bet_slips_enhanced", "enhanced", exclude_date)

    # Today's rows by requested categories.
    today_rows: List[Dict] = []
    for track, csv_path in [
        ("baseline", ROOT / "betting-engine" / "data" / "bets" / "master_bets.csv"),
        ("enhanced", ROOT / "betting-engine" / "data" / "bets" / "master_bets_enhanced.csv"),
    ]:
        if csv_path.exists():
            with open(csv_path, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("date") != today:
                        continue
                    src = str(row.get("source", "")).lower()
                    engine = "betting_kalshi" if src == "kalshi" else "betting_sportsbook"
                    row["engine"] = engine
                    row["track"] = track
                    today_rows.append(row)

    for track, dir_path in [
        ("baseline", ROOT / "exchange-engine" / "data" / "bet_slips"),
        ("enhanced", ROOT / "exchange-engine" / "data" / "bet_slips_enhanced"),
    ]:
        if dir_path.exists():
            for fp in sorted(dir_path.glob("*.json")):
                try:
                    payload = json.loads(fp.read_text())
                except Exception:
                    continue
                if str(payload.get("date", "")).strip() != today:
                    continue
                for bet in payload.get("bets", []):
                    today_rows.append(
                        {
                            "date": today,
                            "engine": "exchange",
                            "track": track,
                            "player_name": bet.get("player_name", ""),
                            "prop_type": bet.get("prop_type", ""),
                            "direction": bet.get("direction", ""),
                            "dbb2_projection": bet.get("projection", ""),
                            "sportsbook_line": bet.get("line", ""),
                            "edge_pct": bet.get("edge_pct", ""),
                            "confidence": bet.get("confidence", ""),
                            "units": bet.get("units", ""),
                            "source": bet.get("source", ""),
                            "execution_type": bet.get("execution_type", ""),
                            "status": "",
                            "pnl": "",
                        }
                    )

    history_page = render_history_page(history_rows, exclude_date)
    today_page = render_today_page(today_rows, today)
    (OUTPUT_DIR / "index.html").write_text(history_page)
    (OUTPUT_DIR / "today.html").write_text(today_page)
    (OUTPUT_DIR / "data.json").write_text(json.dumps(history_rows, indent=2))
    (OUTPUT_DIR / "history_data.json").write_text(json.dumps(history_rows, indent=2))
    (OUTPUT_DIR / "today_data.json").write_text(json.dumps(today_rows, indent=2))

    print(
        f"Wrote {OUTPUT_DIR / 'index.html'} ({len(history_rows)} historical rows, excluding {exclude_date}) "
        f"and {OUTPUT_DIR / 'today.html'} ({len(today_rows)} today rows)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
