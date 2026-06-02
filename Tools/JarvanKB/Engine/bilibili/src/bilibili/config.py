"""Load config/bilibili-engine.yaml into an EngineConfig."""
from __future__ import annotations
import os
import yaml

from .models import EngineConfig

DEFAULT_CONFIG_PATH = os.path.join("config", "bilibili-engine.yaml")


def load_config(path: str = DEFAULT_CONFIG_PATH) -> EngineConfig:
    if not os.path.exists(path):
        raise FileNotFoundError(f"engine config not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    bn = raw.get("bilinote", {})
    return EngineConfig(
        bn_base_url=bn["base_url"],
        provider_id=bn["provider_id"],
        model_name=bn["model_name"],
        poll_interval_s=bn.get("poll_interval_s", 3),
        poll_timeout_s=bn.get("poll_timeout_s", 600),
        style=bn.get("style", "summary"),
    )
