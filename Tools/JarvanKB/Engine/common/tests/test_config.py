import os
import textwrap
from pathlib import Path

import pytest

from jarvankb_common.config import load_llm_config, resolve_candidates


def _write_cfg(tmp_path: Path) -> Path:
    p = tmp_path / "llm.yaml"
    p.write_text(textwrap.dedent("""
        profiles:
          default:
            model: claude-opus-4-7
            api_key_env: ANTHROPIC_API_KEY
          fallback:
            model: dashscope/qwen-max
            api_key_env: DASHSCOPE_API_KEY
          local:
            model: ollama/llama3
            api_key_env: ""
            api_base_env: OLLAMA_API_BASE
        active: [default, fallback]
    """))
    return p


def test_load_llm_config_resolves_key_from_env(tmp_path, monkeypatch):
    cfg_path = _write_cfg(tmp_path)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    cfg = load_llm_config("default", config_path=cfg_path)
    assert cfg.model == "claude-opus-4-7"
    assert cfg.api_key == "sk-test"
    assert cfg.api_base is None


def test_local_profile_available_without_key(tmp_path, monkeypatch):
    cfg_path = _write_cfg(tmp_path)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("OLLAMA_API_BASE", "http://localhost:11434")
    cfg = load_llm_config("local", config_path=cfg_path)
    assert cfg.model == "ollama/llama3"
    assert cfg.api_key is None
    assert cfg.api_base == "http://localhost:11434"


def test_resolve_candidates_falls_through_active_order(tmp_path, monkeypatch):
    cfg_path = _write_cfg(tmp_path)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)   # default unavailable
    monkeypatch.setenv("DASHSCOPE_API_KEY", "ds-test")        # fallback available
    cands = resolve_candidates("default", config_path=cfg_path)
    assert [c.profile for c in cands] == ["fallback"]


def test_resolve_candidates_requested_first_then_active(tmp_path, monkeypatch):
    cfg_path = _write_cfg(tmp_path)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "ds")
    cands = resolve_candidates("default", config_path=cfg_path)
    assert [c.profile for c in cands] == ["default", "fallback"]
