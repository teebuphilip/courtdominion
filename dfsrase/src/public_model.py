"""
Public Bankroll Model v1 (deterministic, read-only).

Nightly job updates bankroll history for D-1 when slate inputs are available.
No fabricated data: if required inputs are missing, the run is skipped.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "dfsrase" / "data"
HISTORY_PATH = DATA_DIR / "bankroll_history.json"
SUMMARY_PATH = DATA_DIR / "public_model_summary.json"
INPUTS_DIR = DATA_DIR / "daily_slate_inputs"

MODEL_VERSION = "v1.0"
START_DATE = date(2026, 2, 28)
STARTING_BANKROLL = 5000.00

WAGER_PCT = {
    "green": 0.05,
    "yellow": 0.02,
    "red": 0.0,
}


@dataclass
class SlateInput:
    rase: float
    confidence: str
    auction_score_actual: float
    projection_score_actual: float


def ny_today() -> date:
    if ZoneInfo is None:
        return datetime.utcnow().date()
    return datetime.now(ZoneInfo("America/New_York")).date()


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    INPUTS_DIR.mkdir(parents=True, exist_ok=True)


def load_history() -> List[Dict]:
    if not HISTORY_PATH.exists():
        return []
    return json.loads(HISTORY_PATH.read_text())


def save_history(rows: List[Dict]) -> None:
    HISTORY_PATH.write_text(json.dumps(rows, indent=2))


def initialize_if_needed(rows: List[Dict]) -> List[Dict]:
    if rows:
        return rows
    init_row = {
        "date": START_DATE.isoformat(),
        "rase": 0.0,
        "confidence": "red",
        "bankroll_start": STARTING_BANKROLL,
        "wager_amount": 0.0,
        "payout_amount": 0.0,
        "bankroll_end": STARTING_BANKROLL,
        "auction_score_actual": 0.0,
        "projection_score_actual": 0.0,
        "created_at": datetime.utcnow().isoformat(),
        "model_version": MODEL_VERSION,
        "status": "init",
    }
    return [init_row]


def load_slate_input(run_date: date) -> Optional[SlateInput]:
    path = INPUTS_DIR / f"{run_date.isoformat()}.json"
    if not path.exists():
        return None
    payload = json.loads(path.read_text())
    try:
        return SlateInput(
            rase=float(payload["rase"]),
            confidence=str(payload["confidence"]).strip().lower(),
            auction_score_actual=float(payload["auction_score_actual"]),
            projection_score_actual=float(payload["projection_score_actual"]),
        )
    except Exception:
        return None


def run_one_day(rows: List[Dict], run_date: date) -> List[Dict]:
    if run_date < START_DATE:
        return rows

    if any(str(r.get("date")) == run_date.isoformat() for r in rows):
        return rows

    slate = load_slate_input(run_date)
    if slate is None:
        # No inputs means strict skip.
        return rows

    confidence = slate.confidence if slate.confidence in WAGER_PCT else "red"
    previous_end = float(rows[-1]["bankroll_end"])
    wager = round(previous_end * WAGER_PCT[confidence], 2)
    payout = round(wager * 1.5, 2) if slate.auction_score_actual > slate.projection_score_actual else 0.0
    bankroll_end = round(previous_end - wager + payout, 2)

    rows.append(
        {
            "date": run_date.isoformat(),
            "rase": round(slate.rase, 6),
            "confidence": confidence,
            "bankroll_start": previous_end,
            "wager_amount": wager,
            "payout_amount": payout,
            "bankroll_end": bankroll_end,
            "auction_score_actual": slate.auction_score_actual,
            "projection_score_actual": slate.projection_score_actual,
            "created_at": datetime.utcnow().isoformat(),
            "model_version": MODEL_VERSION,
            "status": "processed",
        }
    )
    return rows


def build_summary(rows: List[Dict]) -> Dict:
    playable_rows = [r for r in rows if r.get("status") == "processed"]
    current_bankroll = float(rows[-1]["bankroll_end"])
    roi = ((current_bankroll - STARTING_BANKROLL) / STARTING_BANKROLL) * 100
    return {
        "model_version": MODEL_VERSION,
        "start_date": START_DATE.isoformat(),
        "starting_bankroll": STARTING_BANKROLL,
        "current_bankroll": round(current_bankroll, 2),
        "roi_percent": round(roi, 2),
        "green_days": sum(1 for r in playable_rows if r.get("confidence") == "green"),
        "yellow_days": sum(1 for r in playable_rows if r.get("confidence") == "yellow"),
        "red_days": sum(1 for r in playable_rows if r.get("confidence") == "red"),
        "days_played": len(playable_rows),
        "updated_at": datetime.utcnow().isoformat(),
    }


def main(target_date: Optional[str] = None) -> int:
    ensure_dirs()
    rows = initialize_if_needed(load_history())

    if target_date:
        run_date = datetime.strptime(target_date, "%Y-%m-%d").date()
    else:
        run_date = ny_today() - timedelta(days=1)

    rows = run_one_day(rows, run_date)
    save_history(rows)
    SUMMARY_PATH.write_text(json.dumps(build_summary(rows), indent=2))
    print(f"Public model updated through {rows[-1]['date']} | bankroll={rows[-1]['bankroll_end']}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run DFSRASE public bankroll model")
    parser.add_argument("--date", type=str, default=None, help="Override processing date YYYY-MM-DD")
    args = parser.parse_args()
    raise SystemExit(main(target_date=args.date))
