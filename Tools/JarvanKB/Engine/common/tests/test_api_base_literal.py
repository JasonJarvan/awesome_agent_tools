"""A literal `api_base` in config/llm.yaml must be honored (custom OpenAI-compatible endpoints),
taking precedence over api_base_env. Added 2026-06-07 for third-party provider config."""
import textwrap

from jarvankb_common.llm_config import load_llm_config


def test_literal_api_base_in_yaml(tmp_path, monkeypatch):
    p = tmp_path / "llm.yaml"
    p.write_text(textwrap.dedent("""
        profiles:
          custom:
            model: openai/some-model
            api_key_env: CUSTOM_KEY
            api_base: https://example.com/v1
        active: [custom]
    """))
    monkeypatch.setenv("CUSTOM_KEY", "k")
    cfg = load_llm_config("custom", config_path=p)
    assert cfg.model == "openai/some-model"
    assert cfg.api_key == "k"
    assert cfg.api_base == "https://example.com/v1"
