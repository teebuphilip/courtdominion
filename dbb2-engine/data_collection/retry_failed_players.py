#!/usr/bin/env python3
"""
Retry failed players in player_stats_cache.json.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from build_cache import fetch_player_stats


def _default_cache_path() -> Path:
    docker_path = Path("/data/outputs/player_stats_cache.json")
    if docker_path.exists():
        return docker_path
    return Path(__file__).resolve().parent.parent / "output" / "player_stats_cache.json"


def load_cache(cache_file: Path) -> Optional[Dict]:
    if not cache_file.exists():
        return None
    try:
        with open(cache_file, "r") as f:
            return json.load(f)
    except Exception:
        return None


def find_failed_players(cache_data: Dict) -> List[str]:
    failed = []
    for player_id, stats in cache_data.get("players", {}).items():
        if stats.get("confidence", 1.0) == 0.0 or stats.get("points_per_game", -1) < 0:
            failed.append(player_id)
    return failed


def retry_player(player_id: str, max_retries: int = 5) -> Optional[Dict]:
    for attempt in range(1, max_retries + 1):
        stats = fetch_player_stats(player_id)
        if stats and stats.get("confidence", 0.0) > 0.0:
            return stats
        if attempt < max_retries:
            time.sleep(2 ** (attempt - 1))
    return None


def save_cache(cache_file: Path, cache_data: Dict) -> bool:
    try:
        cache_data["last_retry"] = datetime.utcnow().isoformat()
        with open(cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)
        return True
    except Exception:
        return False


def main() -> int:
    cache_file = _default_cache_path()
    cache_data = load_cache(cache_file)
    if not cache_data:
        print(f"Cache not found: {cache_file}")
        return 1

    failed = find_failed_players(cache_data)
    if not failed:
        print("No failed players found")
        return 0

    recovered = 0
    for player_id in failed:
        stats = retry_player(player_id)
        if stats:
            cache_data["players"][player_id] = stats
            recovered += 1

    if recovered and not save_cache(cache_file, cache_data):
        return 1

    print(f"Recovered {recovered}/{len(failed)} failed players")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
