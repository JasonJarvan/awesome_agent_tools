"""Load and validate the watcher YAML config into dataclasses."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import yaml


@dataclass
class CollectionConfig:
    id: str
    name: str


@dataclass
class UserTarget:
    url_token: str
    name_prefix: str = ""
    skip_empty: bool = True
    include_default: bool = False


@dataclass
class CookieSource:
    base_url: str
    uuid: str
    password: str


@dataclass
class WatcherConfig:
    poll_interval_minutes: int
    output_dir: str
    state_dir: str
    cookie_source: CookieSource
    targets: list                      # list[CollectionConfig | UserTarget]
    only_after: datetime | None = None
    backfill_on_first_run: bool = False
    max_consecutive_failures: int = 3
    failure_cooldown_hours: float = 24.0


def _require(d: dict, key: str, ctx: str):
    if key not in d or d[key] in (None, ""):
        raise ValueError(f"config: missing required field '{key}' in {ctx}")
    return d[key]


def _parse_target(t: dict):
    typ = _require(t, "type", "target")
    if typ == "collection":
        cid = str(_require(t, "id", "collection target"))
        return CollectionConfig(id=cid, name=str(t.get("name") or cid))
    if typ == "user":
        return UserTarget(
            url_token=str(_require(t, "url_token", "user target")),
            name_prefix=str(t.get("name_prefix") or ""),
            skip_empty=bool(t.get("skip_empty", True)),
            include_default=bool(t.get("include_default", False)),
        )
    raise ValueError(f"config: unknown target type {typ!r}")


def load_config(path: str) -> WatcherConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    cs_raw = _require(raw, "cookie_source", "root")
    cookie_source = CookieSource(
        base_url=_require(cs_raw, "base_url", "cookie_source"),
        uuid=_require(cs_raw, "uuid", "cookie_source"),
        password=_require(cs_raw, "password", "cookie_source"),
    )

    targets_raw = raw.get("targets") or []
    if not targets_raw:
        raise ValueError("config: must define at least one entry under 'targets'")
    targets = [_parse_target(t) for t in targets_raw]

    interval = int(raw.get("poll_interval_minutes", 45))
    if interval <= 0:
        raise ValueError("config: poll_interval_minutes must be > 0")

    only_after_raw = raw.get("only_after")
    only_after = datetime.fromisoformat(only_after_raw) if only_after_raw else None
    if only_after is not None and only_after.tzinfo is None:
        raise ValueError(
            "config: only_after must include a timezone offset, e.g. '2026-01-01T00:00:00+08:00'")

    return WatcherConfig(
        poll_interval_minutes=interval,
        output_dir=_require(raw, "output_dir", "root"),
        state_dir=_require(raw, "state_dir", "root"),
        cookie_source=cookie_source,
        targets=targets,
        only_after=only_after,
        backfill_on_first_run=bool(raw.get("backfill_on_first_run", False)),
        max_consecutive_failures=int(raw.get("max_consecutive_failures", 3)),
        failure_cooldown_hours=float(raw.get("failure_cooldown_hours", 24)),
    )
