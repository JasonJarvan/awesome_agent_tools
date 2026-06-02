from __future__ import annotations
from datetime import datetime, timezone
from .models import Author


def entities(initial_data: dict) -> dict:
    return (initial_data or {}).get("initialState", {}).get("entities", {})


def epoch_to_iso(value) -> str | None:
    if not value:
        return None
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc).isoformat().replace("+00:00", "Z")
    except (ValueError, OSError, TypeError):
        return None


def parse_author(raw: dict | None) -> Author | None:
    if not raw:
        return None
    token = raw.get("url_token")
    return Author(
        name=raw.get("name", ""),
        url=f"https://www.zhihu.com/people/{token}" if token else None,
        headline=raw.get("headline") or None,
    )
