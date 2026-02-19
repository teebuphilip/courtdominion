"""Normalize ProphetX payload into exchange contract."""


def normalize(raw: dict) -> dict:
    if not isinstance(raw, dict):
        return {}
    return raw
