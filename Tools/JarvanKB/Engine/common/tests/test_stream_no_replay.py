"""Regression test for code-review finding #3 (2026-06-06): stream must not replay tokens
against a fallback provider after a mid-stream error on the first provider."""
import textwrap
import types

import pytest

import jarvankb_common.llm_client as mod
from jarvankb_common.llm_client import LLMClient


def _cfg(tmp_path):
    p = tmp_path / "llm.yaml"
    p.write_text(textwrap.dedent("""
        profiles:
          default: {model: claude-opus-4-7, api_key_env: ANTHROPIC_API_KEY}
          fallback: {model: dashscope/qwen-max, api_key_env: DASHSCOPE_API_KEY}
        active: [default, fallback]
    """))
    return p


def _chunk(text):
    return types.SimpleNamespace(choices=[types.SimpleNamespace(delta=types.SimpleNamespace(content=text))])


def test_stream_no_replay_after_partial_emit(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "ds")

    def fake_completion(model, messages, stream=False, **kw):
        if model == "claude-opus-4-7":
            def gen():
                yield _chunk("a")
                yield _chunk("b")
                raise RuntimeError("mid-stream failure")
            return gen()
        return iter([_chunk("x")])

    monkeypatch.setattr(mod.litellm, "completion", fake_completion)
    client = LLMClient(profile="default", config_path=_cfg(tmp_path))

    out = []
    with pytest.raises(RuntimeError):
        for piece in client.stream([{"role": "user", "content": "hi"}]):
            out.append(piece)
    # emitted the partial "ab" then propagated; did NOT fall through and replay as "abx"
    assert out == ["a", "b"]
