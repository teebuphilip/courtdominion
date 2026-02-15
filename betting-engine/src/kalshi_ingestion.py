"""
Kalshi Ingestion — authenticate with Kalshi API, fetch NBA player prop markets.

Kalshi uses probability pricing (0.0-1.0), not American odds.
Authentication is RSA-PSS signed headers per request.
"""

import argparse
import base64
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

from src import load_settings, load_json, write_json, get_today_date, get_file_age_hours, logger

# WHY: Kalshi only offers 4 NBA prop types (no steals or blocks)
KALSHI_PROP_TYPES = {"points", "rebounds", "assists", "threes"}

# WHY: Kalshi uses natural language titles — regex patterns to parse them
TITLE_PATTERNS = [
    (re.compile(r"^(.+?):\s*(\d+(?:\.\d+)?)\+\s*(?:points?)\s*", re.IGNORECASE), "points"),
    (re.compile(r"^(.+?):\s*(\d+(?:\.\d+)?)\+\s*(?:rebounds?)\s*", re.IGNORECASE), "rebounds"),
    (re.compile(r"^(.+?):\s*(\d+(?:\.\d+)?)\+\s*(?:assists?)\s*", re.IGNORECASE), "assists"),
    (re.compile(r"^(.+?):\s*(\d+(?:\.\d+)?)\+\s*(?:three[- ]?pointers?|threes?|3s?)\s*", re.IGNORECASE), "threes"),
]

# WHY: Map various stat keyword forms to canonical prop names
STAT_NORMALIZE = {
    "point": "points", "points": "points",
    "rebound": "rebounds", "rebounds": "rebounds",
    "assist": "assists", "assists": "assists",
    "three-pointer": "threes", "three-pointers": "threes",
    "threes": "threes", "3s": "threes",
}


def authenticate():
    """
    Load Kalshi API credentials.

    WHY: Kalshi uses RSA-PSS signing, not simple Bearer tokens.
    In CI, read private key from KALSHI_PRIVATE_KEY env var (PEM string).
    Locally, read from PEM file at config path.
    """
    settings = load_settings()
    kalshi_cfg = settings["kalshi"]

    api_key_id = os.environ.get("KALSHI_API_KEY_ID", kalshi_cfg["api_key_id"])

    # WHY: GitHub Actions can't have PEM files on disk — use env var in CI
    private_key_pem = os.environ.get("KALSHI_PRIVATE_KEY")

    if private_key_pem:
        from cryptography.hazmat.primitives.serialization import load_pem_private_key
        private_key = load_pem_private_key(private_key_pem.encode(), password=None)
        logger.info("Kalshi auth: loaded private key from env var")
    else:
        key_path = kalshi_cfg["private_key_path"]
        if not Path(key_path).exists():
            raise FileNotFoundError(
                f"Kalshi private key not found at {key_path}. "
                "Set KALSHI_PRIVATE_KEY env var or place PEM file."
            )
        from cryptography.hazmat.primitives.serialization import load_pem_private_key
        with open(key_path, "rb") as f:
            private_key = load_pem_private_key(f.read(), password=None)
        logger.info(f"Kalshi auth: loaded private key from {key_path}")

    return {"api_key_id": api_key_id, "private_key": private_key}


def build_auth_headers(method: str, path: str, auth: dict) -> dict:
    """
    Build signed headers for a Kalshi API request.

    WHY: Every request needs a timestamped RSA-PSS signature to prevent replay attacks.
    """
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives import hashes

    timestamp_ms = int(time.time() * 1000)
    message = f"{timestamp_ms}{method}{path}"

    signature = auth["private_key"].sign(
        message.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )

    return {
        "KALSHI-ACCESS-KEY": auth["api_key_id"],
        "KALSHI-ACCESS-TIMESTAMP": str(timestamp_ms),
        "KALSHI-ACCESS-SIGNATURE": base64.b64encode(signature).decode(),
        "Content-Type": "application/json",
    }


def fetch_nba_markets(dry_run: bool = False, force: bool = False) -> list:
    """
    Fetch today's NBA player prop markets from Kalshi.

    WHY: Kalshi organizes by events → markets. One NBA game event has
    many player prop markets within it.
    """
    settings = load_settings()
    kalshi_cfg = settings["kalshi"]
    today = get_today_date()
    output_path = f"data/kalshi/markets/{today}.json"

    if not force and Path(output_path).exists():
        file_age = get_file_age_hours(output_path)
        if file_age < 2:
            logger.info("Kalshi markets fetched recently, skipping")
            return load_json(output_path)

    if dry_run:
        logger.info("[DRY RUN] Would fetch Kalshi NBA markets")
        _create_dry_run_markets(output_path)
        return load_json(output_path) if Path(output_path).exists() else []

    auth = authenticate()
    base_url = kalshi_cfg["demo_url"] if kalshi_cfg["use_demo"] else kalshi_cfg["base_url"]

    # Step 1: Get all events tagged NBA
    path = "/events"
    params = {
        "series_ticker": kalshi_cfg["nba_series_tag"],
        "status": "open",
        "limit": 200,
    }

    headers = build_auth_headers("GET", path, auth)
    try:
        response = requests.get(base_url + path, headers=headers, params=params, timeout=30)
    except requests.RequestException as e:
        logger.error(f"Kalshi events fetch failed: {e}")
        raise

    if response.status_code == 401:
        raise RuntimeError("Kalshi auth failed — check API key and private key")
    if response.status_code != 200:
        raise RuntimeError(f"Kalshi events fetch failed: {response.status_code}")

    data = response.json()
    events = data.get("events", [])
    logger.info(f"Found {len(events)} open NBA events")

    # Step 2: For each event, get its markets
    all_markets = []

    for event in events:
        event_ticker = event.get("event_ticker", "")
        time.sleep(kalshi_cfg["rate_limit_delay_seconds"])

        mkt_path = f"/events/{event_ticker}/markets"
        mkt_headers = build_auth_headers("GET", mkt_path, auth)

        try:
            mkt_response = requests.get(
                base_url + mkt_path, headers=mkt_headers, timeout=30
            )
        except requests.RequestException as e:
            logger.warning(f"Failed to get markets for {event_ticker}: {e}")
            continue

        if mkt_response.status_code != 200:
            logger.warning(f"Markets fetch failed for {event_ticker}: {mkt_response.status_code}")
            continue

        markets = mkt_response.json().get("markets", [])

        # WHY: Filter to only player prop markets (not game spreads/totals)
        for m in markets:
            if is_player_prop(m):
                all_markets.append(m)

    logger.info(f"Found {len(all_markets)} NBA player prop markets")
    write_json(output_path, all_markets)
    return all_markets


def is_player_prop(market: dict) -> bool:
    """
    WHY: Kalshi events contain both game-level and player-level markets.
    Player props have specific patterns in their titles.
    """
    title = market.get("title", "").lower()
    prop_keywords = ["points", "rebounds", "assists", "three-pointers", "threes", "3s"]
    return any(kw in title for kw in prop_keywords)


def parse_market_title(title: str) -> dict:
    """
    Parse Kalshi natural language market title into structured data.

    WHY: Kalshi uses titles like "LeBron James: 25+ points scored tonight"
    Must extract player name, line, and prop type.
    """
    for pattern, prop_type in TITLE_PATTERNS:
        match = pattern.match(title)
        if match:
            player_name = match.group(1).strip().title()
            line = float(match.group(2))
            return {
                "player_name": player_name,
                "line": line,
                "prop_type": prop_type,
            }
    return None


def normalize_kalshi_markets(raw_markets: list) -> dict:
    """
    Normalize raw Kalshi market data to flat file structure matching sportsbook odds.

    WHY: Downstream EV calculator expects consistent structure regardless of source.

    Output: {player_name: {prop_type: {line, yes_price, no_price, ticker, volume, open_interest}}}
    """
    settings = load_settings()
    kalshi_cfg = settings["kalshi"]
    result = {}

    for market in raw_markets:
        title = market.get("title", "")
        parsed = parse_market_title(title)

        if parsed is None:
            logger.warning(f"Could not parse market title: {title}")
            continue

        player_name = parsed["player_name"]
        prop_type = parsed["prop_type"]
        line = parsed["line"]

        # WHY: Kalshi returns prices in cents (55 = $0.55)
        yes_price = (market.get("yes_ask", 0) or 0) / 100
        no_price = (market.get("no_ask", 0) or 0) / 100

        # WHY: Filter extreme prices — unreliable signal zones
        if yes_price < kalshi_cfg["min_yes_price"]:
            continue
        if yes_price > kalshi_cfg["max_yes_price"]:
            continue

        volume = market.get("volume", 0) or 0

        # WHY: Skip thin markets — price is unreliable
        if volume < kalshi_cfg["min_volume"]:
            continue

        if player_name not in result:
            result[player_name] = {}

        result[player_name][prop_type] = {
            "line": line,
            "yes_price": round(yes_price, 3),
            "no_price": round(no_price, 3),
            "ticker": market.get("ticker", ""),
            "volume": volume,
            "open_interest": market.get("open_interest", 0) or 0,
        }

    logger.info(f"Normalized {len(result)} players with Kalshi props")

    today = get_today_date()
    write_json(f"data/kalshi/odds/{today}.json", result)
    return result


def _create_dry_run_markets(output_path: str) -> None:
    """Load fixture data for dry-run mode."""
    fixture = "tests/fixtures/sample_kalshi_markets.json"
    if Path(fixture).exists():
        data = load_json(fixture)
        write_json(output_path, data)
        logger.info(f"[DRY RUN] Wrote fixture Kalshi markets to {output_path}")
    else:
        write_json(output_path, {})
        logger.warning("[DRY RUN] No fixture found, wrote empty markets")


def run(dry_run: bool = False, force: bool = False) -> dict:
    """Main Kalshi ingestion pipeline."""
    raw_markets = fetch_nba_markets(dry_run=dry_run, force=force)

    if isinstance(raw_markets, dict):
        # WHY: Dry-run fixture is already normalized
        today = get_today_date()
        write_json(f"data/kalshi/odds/{today}.json", raw_markets)
        logger.info(f"Loaded {len(raw_markets)} players from fixture")
        return raw_markets

    normalized = normalize_kalshi_markets(raw_markets)
    return normalized


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kalshi NBA Market Ingestion")
    parser.add_argument("--fetch-markets", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = run(dry_run=args.dry_run)
    logger.info(f"Kalshi: {len(result)} players with active props")
