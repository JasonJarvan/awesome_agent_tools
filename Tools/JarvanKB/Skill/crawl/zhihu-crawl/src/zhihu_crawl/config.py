"""Module config loader. Schema: config.example.yaml. Real config (config.yaml) is gitignored."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

from .cookie import CookieSource


@dataclass
class ModuleConfig:
    output_root: Path
    cookie: CookieSource
    llm_profile: str
    classify_snippet_chars: int = 240


def _default_path() -> Path:
    return Path(os.environ.get("ZHIHU_CRAWL_CONFIG", "config.yaml")).expanduser()


def load_config(config_path: str | Path | None = None) -> ModuleConfig:
    path = Path(config_path).expanduser() if config_path else _default_path()
    if not path.exists():
        raise FileNotFoundError(
            f"zhihu-crawl config not found at {path}. Copy config.example.yaml to config.yaml "
            f"or set ZHIHU_CRAWL_CONFIG."
        )
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    ck = raw["cookie"]
    return ModuleConfig(
        output_root=Path(raw["output_root"]).expanduser(),
        cookie=CookieSource(
            base_url=ck["base_url"],
            uuid=ck["uuid"],
            password=os.environ.get(ck["password_env"], ""),
        ),
        llm_profile=raw.get("llm", {}).get("profile", "default"),
        classify_snippet_chars=int(raw.get("classify_snippet_chars", 240)),
    )
