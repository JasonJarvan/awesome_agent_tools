"""Load and validate the watcher YAML config into dataclasses."""
from __future__ import annotations

from dataclasses import dataclass

import yaml


@dataclass
class FolderConfig:
    id: str
    name: str


@dataclass
class CookieSource:
    base_url: str
    uuid: str
    password: str
    auth_token: str | None = None


@dataclass
class EngineConfig:
    bn_base_url: str
    provider_id: str
    model_name: str


@dataclass
class RenderConfig:
    include_transcript: bool = True
    include_timestamps: bool = False
    split_transcript: bool = False


@dataclass
class WatcherConfig:
    poll_interval_minutes: int
    output_dir: str
    state_dir: str
    cookie_source: CookieSource
    engine: EngineConfig
    render: RenderConfig
    folders: list[FolderConfig]


def _require(d: dict, key: str, ctx: str):
    if key not in d or d[key] in (None, ""):
        raise ValueError(f"config: missing required field '{key}' in {ctx}")
    return d[key]


def load_config(path: str) -> WatcherConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    cs = _require(raw, "cookie_source", "root")
    cookie_source = CookieSource(
        base_url=_require(cs, "base_url", "cookie_source"),
        uuid=_require(cs, "uuid", "cookie_source"),
        password=_require(cs, "password", "cookie_source"),
        auth_token=cs.get("auth_token"),
    )

    en = _require(raw, "engine", "root")
    engine = EngineConfig(
        bn_base_url=_require(en, "bn_base_url", "engine"),
        provider_id=_require(en, "provider_id", "engine"),
        model_name=_require(en, "model_name", "engine"),
    )

    rd = raw.get("render") or {}
    render = RenderConfig(
        include_transcript=bool(rd.get("include_transcript", True)),
        include_timestamps=bool(rd.get("include_timestamps", False)),
        split_transcript=bool(rd.get("split_transcript", False)),
    )

    folders_raw = raw.get("folders") or []
    if not folders_raw:
        raise ValueError("config: must define at least one folder")
    folders = []
    for fo in folders_raw:
        fid = str(_require(fo, "id", "folder"))
        folders.append(FolderConfig(id=fid, name=str(fo.get("name") or fid)))

    interval = int(raw.get("poll_interval_minutes", 20))
    if interval <= 0:
        raise ValueError("config: poll_interval_minutes must be > 0")

    return WatcherConfig(
        poll_interval_minutes=interval,
        output_dir=_require(raw, "output_dir", "root"),
        state_dir=_require(raw, "state_dir", "root"),
        cookie_source=cookie_source,
        engine=engine,
        render=render,
        folders=folders,
    )
