import textwrap
import types
from pathlib import Path

import pytest

import jarvankb_common.llm_client as mod
from jarvankb_common.llm_client import LLMClient


def _cfg(tmp_path: Path) -> Path:
    p = tmp_path / "llm.yaml"
    p.write_text(textwrap.dedent("""
        profiles:
          default: {model: claude-opus-4-7, api_key_env: ANTHROPIC_API_KEY}
          fallback: {model: dashscope/qwen-max, api_key_env: DASHSCOPE_API_KEY}
        active: [default, fallback]
    """))
    return p


def _resp(text):
    msg = types.SimpleNamespace(content=text)
    return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])


def test_complete_returns_text(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk")
    calls = {}

    def fake_completion(model, messages, **kw):
        calls["model"] = model
        return _resp("hello-world")

    monkeypatch.setattr(mod.litellm, "completion", fake_completion)
    client = LLMClient(profile="default", config_path=_cfg(tmp_path))
    out = client.complete([{"role": "user", "content": "hi"}])
    assert out == "hello-world"
    assert calls["model"] == "claude-opus-4-7"


def test_complete_falls_through_on_error(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "ds")
    seen = []

    def fake_completion(model, messages, **kw):
        seen.append(model)
        if model == "claude-opus-4-7":
            raise RuntimeError("boom")
        return _resp("from-fallback")

    monkeypatch.setattr(mod.litellm, "completion", fake_completion)
    client = LLMClient(profile="default", config_path=_cfg(tmp_path))
    assert client.complete([{"role": "user", "content": "hi"}]) == "from-fallback"
    assert seen == ["claude-opus-4-7", "dashscope/qwen-max"]


def test_complete_raises_when_all_exhausted(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "ds")
    monkeypatch.setattr(mod.litellm, "completion",
                        lambda model, messages, **kw: (_ for _ in ()).throw(RuntimeError("x")))
    client = LLMClient(profile="default", config_path=_cfg(tmp_path))
    with pytest.raises(RuntimeError):
        client.complete([{"role": "user", "content": "hi"}])


def test_stream_yields_chunks(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk")

    def chunk(text):
        delta = types.SimpleNamespace(content=text)
        return types.SimpleNamespace(choices=[types.SimpleNamespace(delta=delta)])

    monkeypatch.setattr(mod.litellm, "completion",
                        lambda model, messages, stream=False, **kw: iter([chunk("a"), chunk("b"), chunk(None)]))
    client = LLMClient(profile="default", config_path=_cfg(tmp_path))
    assert "".join(client.stream([{"role": "user", "content": "hi"}])) == "ab"


def test_to_opencode_not_implemented(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk")
    client = LLMClient(profile="default", config_path=_cfg(tmp_path))
    with pytest.raises(NotImplementedError):
        client.to_opencode()
