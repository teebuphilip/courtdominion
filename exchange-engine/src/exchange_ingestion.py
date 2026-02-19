"""Fetch and normalize exchange odds for Novig and ProphetX."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import get_today_date, load_settings, logger, write_json
from src.novig.client import fetch_raw as fetch_novig_raw
from src.novig.normalize import normalize as normalize_novig
from src.prophetx.client import fetch_raw as fetch_prophetx_raw
from src.prophetx.normalize import normalize as normalize_prophetx


def _fetch_source(source: str, timeout_seconds: int) -> dict:
    if source == "novig":
        return normalize_novig(fetch_novig_raw(timeout_seconds=timeout_seconds))
    if source == "prophetx":
        return normalize_prophetx(fetch_prophetx_raw(timeout_seconds=timeout_seconds))
    return {}


def run(dry_run: bool = False) -> dict:
    settings = load_settings()
    today = get_today_date()
    include_sources = settings["exchange"].get("include_sources", [])
    timeout = settings["dbb2_api"].get("timeout_seconds", 30)

    all_sources = {}
    for source in include_sources:
        output_path = f"data/exchange_odds/{source}/{today}.json"
        if dry_run:
            normalized = {}
        else:
            normalized = _fetch_source(source, timeout_seconds=timeout)
        write_json(output_path, normalized)
        logger.info(f"Saved {source} odds for {len(normalized)} players to {output_path}")
        all_sources[source] = normalized

    return all_sources


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Exchange odds ingestion")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
