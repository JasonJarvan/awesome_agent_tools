"""Load and validate the watcher YAML config into dataclasses."""
from __future__ import annotations

from dataclasses import dataclass

import yaml


@dataclass
class CollectionConfig:
    id: str
    name: str


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
    collections: list[CollectionConfig]


def _require(d: dict, key: str, ctx: str):
    if key not in d or d[key] in (None, ""):
        raise ValueError(f"config: missing required field '{key}' in {ctx}")
    return d[key]


def load_config(path: str) -> WatcherConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    cs_raw = _require(raw, "cookie_source", "root")
    cookie_source = CookieSource(
        base_url=_require(cs_raw, "base_url", "cookie_source"),
        uuid=_require(cs_raw, "uuid", "cookie_source"),
        password=_require(cs_raw, "password", "cookie_source"),
    )

    colls_raw = raw.get("collections") or []
    if not colls_raw:
        raise ValueError("config: must define at least one collection")
    collections = []
    for c in colls_raw:
        cid = str(_require(c, "id", "collection"))
        collections.append(CollectionConfig(id=cid, name=str(c.get("name") or cid)))

    interval = int(raw.get("poll_interval_minutes", 45))
    if interval <= 0:
        raise ValueError("config: poll_interval_minutes must be > 0")

    return WatcherConfig(
        poll_interval_minutes=interval,
        output_dir=_require(raw, "output_dir", "root"),
        state_dir=_require(raw, "state_dir", "root"),
        cookie_source=cookie_source,
        collections=collections,
    )
