"""Shared utilities for the exchange engine."""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "exchange_engine.log", mode="a"),
    ],
)
logger = logging.getLogger("exchange_engine")

_settings_cache = None


def get_today_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def get_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: str):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    with open(p) as f:
        return json.load(f)


def write_json(path: str, data) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        json.dump(data, f, indent=2)


def write_file(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        f.write(content)


def load_settings() -> dict:
    global _settings_cache
    if _settings_cache is not None:
        return _settings_cache

    config_path = os.environ.get("CONFIG_PATH", "config/settings.json")
    _settings_cache = load_json(config_path)

    dbb2_url = os.environ.get("DBB2_API_URL")
    if dbb2_url:
        _settings_cache["dbb2_api"]["base_url"] = dbb2_url

    return _settings_cache
