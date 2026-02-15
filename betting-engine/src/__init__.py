"""
Shared utilities for the DBB2 Betting Engine.

Central utilities prevent duplicated file I/O logic across modules.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Configure logging once at import
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/betting_engine.log", mode="a"),
    ],
)
logger = logging.getLogger("betting_engine")

# Cached settings (loaded once)
_settings_cache = None


def get_today_date() -> str:
    """Returns YYYY-MM-DD string for today."""
    return datetime.now().strftime("%Y-%m-%d")


def get_timestamp() -> str:
    """Returns ISO 8601 timestamp."""
    return datetime.now(timezone.utc).isoformat()


def load_json(path: str) -> dict:
    """Load JSON file. Raises FileNotFoundError with clear message if missing."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    with open(p) as f:
        return json.load(f)


def write_json(path: str, data) -> None:
    """Write JSON with indent=2, create dirs if needed."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        json.dump(data, f, indent=2)


def write_file(path: str, content: str) -> None:
    """Write plaintext file, create dirs if needed."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        f.write(content)


def get_file_age_hours(path: str) -> float:
    """Return hours since file was last modified."""
    p = Path(path)
    if not p.exists():
        return float("inf")
    mtime = p.stat().st_mtime
    now = datetime.now().timestamp()
    return (now - mtime) / 3600


def load_settings() -> dict:
    """Load config/settings.json once, cache in memory."""
    global _settings_cache
    if _settings_cache is not None:
        return _settings_cache

    # WHY: Check env var first, fallback to relative path
    config_path = os.environ.get("CONFIG_PATH", "config/settings.json")
    _settings_cache = load_json(config_path)

    # WHY: Override API key from env var so it's never in the JSON file
    api_key = os.environ.get("ODDS_API_KEY")
    if api_key:
        _settings_cache["odds_api"]["api_key"] = api_key

    dbb2_url = os.environ.get("DBB2_API_URL")
    if dbb2_url:
        _settings_cache["dbb2_api"]["base_url"] = dbb2_url

    return _settings_cache
