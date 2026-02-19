#!/usr/bin/env python3
"""
Build player_stats_cache.json from NBA.com endpoints with resume/backoff.
"""

import json
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from engine.season import format_nba_season, get_current_nba_season_start_year


def _default_cache_path() -> Path:
    docker_path = Path("/data/outputs/player_stats_cache.json")
    if docker_path.parent.exists():
        return docker_path
    return Path(__file__).resolve().parent.parent / "output" / "player_stats_cache.json"


def fetch_player_stats(player_id: str, player_name: str = "") -> Optional[Dict]:
    """Fetch one player from NBA API with last-5-seasons baseline."""
    try:
        from nba_api.stats.endpoints import commonplayerinfo, playercareerstats
    except Exception:
        return None

    try:
        career_stats = playercareerstats.PlayerCareerStats(player_id=player_id)
        time.sleep(random.uniform(1.0, 2.0))
        df = career_stats.get_data_frames()[0]
        if df.empty:
            return None

        current_start = get_current_nba_season_start_year()
        valid_seasons = {
            format_nba_season(y) for y in range(current_start - 4, current_start + 1)
        }
        recent = df[df["SEASON_ID"].isin(valid_seasons)].copy()
        if recent.empty:
            recent = df.tail(5).copy()

        total_games = int(recent["GP"].sum())
        if total_games < 1:
            return None

        stats = {
            "player_id": str(player_id),
            "player_name": player_name,
            "games_played": int(round(recent["GP"].mean())),
            "minutes_per_game": round(float(recent["MIN"].sum()) / total_games, 1),
            "points_per_game": round(float(recent["PTS"].sum()) / total_games, 1),
            "rebounds_per_game": round(float(recent["REB"].sum()) / total_games, 1),
            "assists_per_game": round(float(recent["AST"].sum()) / total_games, 1),
            "steals_per_game": round(float(recent["STL"].sum()) / total_games, 1),
            "blocks_per_game": round(float(recent["BLK"].sum()) / total_games, 1),
            "turnovers_per_game": round(float(recent["TOV"].sum()) / total_games, 1),
            "field_goals_made": round(float(recent["FGM"].sum()) / total_games, 1),
            "field_goals_attempted": round(float(recent["FGA"].sum()) / total_games, 1),
            "field_goal_pct": round(float(recent["FG_PCT"].mean()), 3),
            "three_pointers_made": round(float(recent["FG3M"].sum()) / total_games, 1),
            "three_pointers_attempted": round(float(recent["FG3A"].sum()) / total_games, 1),
            "three_point_pct": round(float(recent["FG3_PCT"].mean()), 3),
            "free_throws_made": round(float(recent["FTM"].sum()) / total_games, 1),
            "free_throws_attempted": round(float(recent["FTA"].sum()) / total_games, 1),
            "free_throw_pct": round(float(recent["FT_PCT"].mean()), 3),
            "confidence": min(1.0, total_games / 400.0),
            "cached_at": datetime.utcnow().isoformat(),
        }

        try:
            info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
            time.sleep(random.uniform(1.0, 2.0))
            info_df = info.get_data_frames()[0]
            if not info_df.empty:
                birthdate = info_df["BIRTHDATE"].iloc[0]
                position = info_df["POSITION"].iloc[0] or "SF"
                if birthdate:
                    birth_year = int(str(birthdate).split("-")[0])
                    stats["age"] = datetime.utcnow().year - birth_year
                stats["position"] = position
        except Exception:
            pass

        return stats
    except Exception:
        return None


class CacheBuilder:
    def __init__(self, cache_file: Optional[Path] = None):
        self.cache_file = cache_file or _default_cache_path()
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.stats_cache: Dict[str, Dict] = {}
        self.failed_players = []
        self.save_counter = 0
        self._load_existing_cache()

    def _load_existing_cache(self) -> None:
        if not self.cache_file.exists():
            return
        try:
            with open(self.cache_file, "r") as f:
                payload = json.load(f)
            self.stats_cache = payload.get("players", {})
            if self.stats_cache:
                print(f"Found existing cache with {len(self.stats_cache)} players")
        except Exception:
            self.stats_cache = {}

    def _save_cache(self) -> bool:
        try:
            payload = {
                "version": "1.0",
                "cached_at": datetime.utcnow().isoformat(),
                "player_count": len(self.stats_cache),
                "players": self.stats_cache,
            }
            temp_file = self.cache_file.with_suffix(".tmp")
            with open(temp_file, "w") as f:
                json.dump(payload, f, indent=2)
            temp_file.replace(self.cache_file)
            return True
        except Exception as exc:
            print(f"Error saving cache: {exc}")
            return False

    def _fetch_player_stats_with_retry(self, player_id: str, player_name: str) -> Optional[Dict]:
        backoff = [5, 10, 300]
        for attempt in range(4):
            stats = fetch_player_stats(player_id, player_name)
            if stats:
                return stats
            if attempt < len(backoff):
                wait_time = backoff[attempt]
                print(f"retry in {wait_time}s", end=" ")
                time.sleep(wait_time)
        return None

    def build_cache(self) -> bool:
        try:
            from nba_api.stats.static import players
        except Exception:
            print("nba_api is not available; cannot build cache")
            return False

        all_players = players.get_active_players()
        total = len(all_players)
        success_count = len(self.stats_cache)

        for idx, player in enumerate(all_players, 1):
            player_id = str(player["id"])
            player_name = player["full_name"]

            if player_id in self.stats_cache:
                print(f"[{idx}/{total}] {player_name} ... cached")
                continue

            print(f"[{idx}/{total}] {player_name} ...", end=" ")
            stats = self._fetch_player_stats_with_retry(player_id, player_name)
            if stats:
                self.stats_cache[player_id] = stats
                success_count += 1
                self.save_counter += 1
                print("ok")
                if self.save_counter >= 10:
                    self._save_cache()
                    self.save_counter = 0
            else:
                print("failed")
                self.failed_players.append((player_id, player_name))

        self._save_cache()
        print(f"Completed: {success_count}/{total} cached")
        return True


def build_cache(cache_file: Optional[Path] = None) -> bool:
    return CacheBuilder(cache_file=cache_file).build_cache()


if __name__ == "__main__":
    ok = build_cache()
    raise SystemExit(0 if ok else 1)
