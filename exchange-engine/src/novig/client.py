"""Novig client (minimal)."""

import os

import requests


def fetch_raw(timeout_seconds: int = 30) -> dict:
    url = os.environ.get("NOVIG_ODDS_URL")
    if not url:
        return {}
    response = requests.get(url, timeout=timeout_seconds)
    response.raise_for_status()
    return response.json()
