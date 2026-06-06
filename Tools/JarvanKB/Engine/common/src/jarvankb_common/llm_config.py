"""Loader for config/llm.yaml — resolves a profile to model + credentials (from env).

Schema (see config/llm.yaml.example):
    profiles:
      <name>: {model: str, api_key_env: str, api_base_env?: str}
    active: [<name>, ...]   # fallthrough order
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class LLMConfig:
    profile: str
    model: str
    api_key: str | None
    api_base: str | None


def _default_config_path() -> Path:
    env = os.environ.get("JARVANKB_LLM_CONFIG")
    if env:
        return Path(env).expanduser()
    return Path("config/llm.yaml")


def _load_raw(config_path: str | Path | None) -> dict:
    path = Path(config_path).expanduser() if config_path else _default_config_path()
    if not path.exists():
        raise FileNotFoundError(
            f"LLM config not found at {path}. Copy config/llm.yaml.example to config/llm.yaml "
            f"or set JARVANKB_LLM_CONFIG."
        )
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _resolve_profile(name: str, raw: dict) -> LLMConfig:
    prof = raw.get("profiles", {}).get(name)
    if prof is None:
        raise KeyError(f"profile {name!r} not in config (have {list(raw.get('profiles', {}))})")
    key_env = prof.get("api_key_env", "")
    base_env = prof.get("api_base_env", "")
    return LLMConfig(
        profile=name,
        model=prof["model"],
        api_key=os.environ.get(key_env) if key_env else None,
        # literal `api_base` (non-secret, for custom OpenAI-compatible endpoints) wins; else `api_base_env`
        api_base=prof.get("api_base") or (os.environ.get(base_env) if base_env else None),
    )


def _is_available(name: str, raw: dict) -> bool:
    prof = raw.get("profiles", {}).get(name, {})
    key_env = prof.get("api_key_env", "")
    return (not key_env) or bool(os.environ.get(key_env))


def load_llm_config(profile: str = "default", config_path: str | Path | None = None) -> LLMConfig:
    return _resolve_profile(profile, _load_raw(config_path))


def resolve_candidates(profile: str = "default", config_path: str | Path | None = None) -> list[LLMConfig]:
    """Available profiles in fallthrough order: requested first, then `active`, deduped."""
    raw = _load_raw(config_path)
    order: list[str] = [profile, *raw.get("active", [])]
    seen: set[str] = set()
    out: list[LLMConfig] = []
    for name in order:
        if name in seen or name not in raw.get("profiles", {}):
            continue
        seen.add(name)
        if _is_available(name, raw):
            out.append(_resolve_profile(name, raw))
    return out
