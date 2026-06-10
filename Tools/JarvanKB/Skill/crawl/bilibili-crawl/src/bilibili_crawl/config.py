"""Module config loader. Schema: config.example.yaml. Real config (config.yaml) is gitignored.

Engine config is NOT here: the SP-4a engine reads its own config/bilibili-engine.yaml via transcribe().
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .cookie import CookieSource


@dataclass
class RenderConfig:
    include_transcript: bool = True
    include_timestamps: bool = False
    split_transcript: bool = False


@dataclass
class ModuleConfig:
    output_root: Path
    cookie: CookieSource
    llm_profile: str
    render: RenderConfig = field(default_factory=RenderConfig)
    classify_snippet_chars: int = 240


def _default_path() -> Path:
    return Path(os.environ.get("BILIBILI_CRAWL_CONFIG", "config.yaml")).expanduser()


def load_config(config_path: str | Path | None = None) -> ModuleConfig:
    path = Path(config_path).expanduser() if config_path else _default_path()
    if not path.exists():
        raise FileNotFoundError(
            f"bilibili-crawl config not found at {path}. Copy config.example.yaml to config.yaml "
            f"or set BILIBILI_CRAWL_CONFIG."
        )
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    ck = raw["cookie"]
    rc = raw.get("render", {}) or {}
    return ModuleConfig(
        output_root=Path(raw["output_root"]).expanduser(),
        cookie=CookieSource(
            base_url=ck["base_url"],
            uuid=ck["uuid"],
            password=os.environ.get(ck["password_env"], ""),
        ),
        llm_profile=raw.get("llm", {}).get("profile", "default"),
        render=RenderConfig(
            include_transcript=bool(rc.get("include_transcript", True)),
            include_timestamps=bool(rc.get("include_timestamps", False)),
            split_transcript=bool(rc.get("split_transcript", False)),
        ),
        classify_snippet_chars=int(raw.get("classify_snippet_chars", 240)),
    )
