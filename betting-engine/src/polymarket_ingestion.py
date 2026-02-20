"""
Polymarket Read-Only Ingestion

Fetches public NBA player prop markets for display and educational comparison.
This module is intentionally read-only and never places trades.
"""

import argparse
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import load_settings, load_json, write_json, get_today_date, get_file_age_hours, logger


def log_disclaimer(settings: dict) -> None:
    """WHY: Show legal notice on every run so output usage is unambiguous."""
    print("=" * 70)
    print(settings["legal_disclaimer"])
    print("=" * 70)


def is_player_prop(market: dict) -> bool:
    """
    WHY: Gamma returns mixed market types; only player props are relevant here.
    """
    question = str(market.get("question", "")).lower()
    prop_keywords = [
        "points",
        "rebounds",
        "assists",
        "threes",
        "three-pointers",
        "score",
        "rebound",
        "assist",
        "make",
    ]
    game_keywords = ["win", "winner", "beat", "defeat", "spread", "over/under"]
    has_prop_keyword = any(kw in question for kw in prop_keywords)
    has_game_keyword = any(kw in question for kw in game_keywords)
    return has_prop_keyword and not has_game_keyword


def fetch_nba_markets(settings: dict, force: bool = False) -> list:
    """
    WHY: Metadata discovery should happen from Gamma once and be cached.
    """
    today = get_today_date()
    output_path = Path(f"data/polymarket/markets/{today}.json")

    if not force and output_path.exists():
        age_hours = get_file_age_hours(str(output_path))
        if age_hours < 2:
            logger.info(f"Polymarket markets fetched recently ({age_hours:.1f}h), reusing cache")
            return load_json(str(output_path))

    url = f"{settings['gamma_api_url']}/markets"
    params = {"tag": "NBA", "closed": "false", "limit": 200}

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
    except requests.Timeout as e:
        if output_path.exists():
            logger.warning(f"Gamma timeout, falling back to cache: {e}")
            return load_json(str(output_path))
        raise RuntimeError(f"Polymarket Gamma API timeout and no cache available: {e}")
    except requests.RequestException as e:
        if output_path.exists():
            logger.warning(f"Gamma fetch failed, falling back to cache: {e}")
            return load_json(str(output_path))
        raise RuntimeError(f"Polymarket Gamma API fetch failed: {e}")

    markets = response.json()
    if not isinstance(markets, list):
        logger.warning("Gamma response shape unexpected; defaulting to empty list")
        markets = []

    prop_markets = [m for m in markets if is_player_prop(m)]
    logger.info(f"Polymarket: {len(markets)} NBA markets, {len(prop_markets)} player props")
    write_json(str(output_path), prop_markets)
    return prop_markets


def fetch_market_prices(settings: dict, market_id: str) -> dict:
    """
    WHY: Pricing is sourced from public CLOB snapshots; one market can fail without aborting run.
    """
    url = f"{settings['clob_api_url']}/markets/{market_id}"
    delay = float(settings.get("rate_limit_delay_seconds", 1.0))

    try:
        time.sleep(delay)
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except requests.Timeout:
        # WHY: transient timeout should not fail the entire ingest pipeline
        logger.warning(f"Timeout fetching CLOB price for market {market_id}")
        return None
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 429:
            logger.warning(f"CLOB rate limited on market {market_id}; retrying once after backoff")
            time.sleep(60)
            try:
                response = requests.get(url, timeout=15)
                response.raise_for_status()
            except requests.RequestException as retry_err:
                logger.warning(f"CLOB retry failed for market {market_id}: {retry_err}")
                return None
        else:
            logger.warning(f"CLOB HTTP error for market {market_id}: {e}")
            return None
    except requests.RequestException as e:
        logger.warning(f"CLOB fetch failed for market {market_id}: {e}")
        return None

    payload = response.json()
    yes_bid = float(payload.get("yes_bid", 0) or 0)
    yes_ask = float(payload.get("yes_ask", 0) or 0)
    no_bid = float(payload.get("no_bid", 0) or 0)
    no_ask = float(payload.get("no_ask", 0) or 0)

    yes_price = (yes_bid + yes_ask) / 2 if yes_bid and yes_ask else None
    no_price = (no_bid + no_ask) / 2 if no_bid and no_ask else None
    volume_24h = float(payload.get("volume_24h", 0) or 0)

    return {
        "yes_price": round(yes_price, 3) if yes_price is not None else None,
        "no_price": round(no_price, 3) if no_price is not None else None,
        "volume_24h": volume_24h,
        "liquidity_usd": volume_24h,
    }


def parse_market_question(question: str) -> dict:
    """
    WHY: Questions are natural language; downstream EV needs structured fields.
    """
    q = str(question).strip()
    q_lower = q.lower()

    line_match = re.search(r"(\d+(?:\.\d+)?)\+", q_lower)
    if not line_match:
        return None
    line = float(line_match.group(1))

    if "three" in q_lower or "3-point" in q_lower or "threes" in q_lower:
        prop_type = "threes"
    elif "point" in q_lower or "score" in q_lower:
        prop_type = "points"
    elif "rebound" in q_lower:
        prop_type = "rebounds"
    elif "assist" in q_lower:
        prop_type = "assists"
    else:
        return None

    prefix = re.split(r"\d+(?:\.\d+)?\+", q, maxsplit=1)[0]
    prefix = re.sub(r"\b(will|to|make|score|get|have)\b", " ", prefix, flags=re.IGNORECASE)
    prefix = re.sub(r"[^A-Za-z\-\s]", " ", prefix)
    tokens = [t for t in prefix.split() if t]

    if len(tokens) >= 3 and tokens[0].lower() == "will":
        tokens = tokens[1:]
    if len(tokens) < 2:
        return None

    # WHY: Last two/three capitalizable words are the most stable heuristic for names.
    player_name = " ".join(tokens[-3:] if len(tokens[-3:]) == 3 and len(tokens) >= 3 else tokens[-2:]).title()

    return {
        "player_name": player_name,
        "prop_type": prop_type,
        "line": line,
        "direction": "over",
    }


def normalize_polymarket_markets(settings: dict, raw_markets: list) -> dict:
    """
    WHY: Flatten to same player->prop structure used by existing adapters.
    """
    result = {}
    min_yes = float(settings["min_yes_price"])
    max_yes = float(settings["max_yes_price"])
    min_liq = float(settings["min_liquidity_usd"])

    for market in raw_markets:
        market_id = str(market.get("id", "")).strip()
        question = str(market.get("question", "")).strip()
        if not market_id or not question:
            continue

        parsed = parse_market_question(question)
        if not parsed:
            logger.warning(f"Could not parse Polymarket question: {question}")
            continue

        pricing = fetch_market_prices(settings, market_id)
        if not pricing:
            continue
        yes_price = pricing.get("yes_price")
        no_price = pricing.get("no_price")
        if yes_price is None:
            logger.warning(f"No yes_price for market {market_id}, skipping")
            continue

        if yes_price < min_yes or yes_price > max_yes:
            continue
        if pricing.get("liquidity_usd", 0) < min_liq:
            continue

        player_name = parsed["player_name"]
        prop_type = parsed["prop_type"]
        if player_name not in result:
            result[player_name] = {}
        result[player_name][prop_type] = {
            "line": parsed["line"],
            "yes_price": yes_price,
            "no_price": no_price,
            "volume_24h": pricing.get("volume_24h", 0),
            "market_id": market_id,
            "question": question,
            "source": "polymarket",
            "demo_only": True,
        }

    return result


def run(fetch_markets: bool = False, force: bool = False) -> dict:
    """
    Main read-only ingestion workflow.
    """
    settings = load_settings().get("polymarket", {})
    if not settings.get("enabled", False):
        logger.info("Polymarket adapter disabled in settings; skipping")
        return {}

    log_disclaimer(settings)
    if not fetch_markets:
        logger.info("No action selected. Use --fetch-markets")
        return {}

    raw_markets = fetch_nba_markets(settings, force=force)
    normalized = normalize_polymarket_markets(settings, raw_markets)
    today = get_today_date()
    output_path = f"data/polymarket/odds/{today}.json"
    write_json(output_path, normalized)

    player_count = len(normalized)
    prop_count = sum(len(v) for v in normalized.values())
    logger.info(f"Polymarket normalized {prop_count} props across {player_count} players -> {output_path}")
    print(settings["legal_disclaimer"])
    return normalized


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Polymarket Read-Only Ingestion")
    parser.add_argument("--fetch-markets", action="store_true")
    parser.add_argument("--force", action="store_true", help="Ignore 2h market cache")
    args = parser.parse_args()
    run(fetch_markets=args.fetch_markets, force=args.force)
