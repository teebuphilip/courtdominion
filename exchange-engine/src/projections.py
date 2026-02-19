"""Fetch projections from DBB2 API and store for today."""

import argparse
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import get_today_date, load_settings, logger, write_json


def normalize_projections(raw: dict) -> dict:
    if not isinstance(raw, dict):
        return {}

    if "players" in raw and isinstance(raw["players"], list):
        normalized = {}
        for player in raw["players"]:
            name = player.get("name")
            if not name:
                continue
            normalized[name] = {
                "team": player.get("team"),
                "is_b2b": player.get("is_b2b", False),
                "props": player.get("props", {}),
            }
        return normalized

    return raw


def run(dry_run: bool = False) -> dict:
    settings = load_settings()
    today = get_today_date()
    output_path = f"data/projections/{today}.json"

    if dry_run:
        logger.info("[DRY RUN] Skipping DBB2 API call")
        write_json(output_path, {})
        return {}

    api = settings["dbb2_api"]
    url = f"{api['base_url']}{api['projections_endpoint']}"
    timeout = api.get("timeout_seconds", 30)

    response = requests.get(url, timeout=timeout)
    response.raise_for_status()

    normalized = normalize_projections(response.json())
    write_json(output_path, normalized)
    logger.info(f"Saved projections for {len(normalized)} players to {output_path}")
    return normalized


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Exchange projections ingestion")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
