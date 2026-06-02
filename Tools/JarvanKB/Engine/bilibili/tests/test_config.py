import textwrap
import pytest
from bilibili.config import load_config
from bilibili.models import EngineConfig


def test_load_minimal(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text(textwrap.dedent("""
        bilinote:
          base_url: http://127.0.0.1:3015
          provider_id: pid
          model_name: gpt-4o-mini
    """), encoding="utf-8")
    cfg = load_config(str(p))
    assert isinstance(cfg, EngineConfig)
    assert cfg.bn_base_url == "http://127.0.0.1:3015"
    assert cfg.provider_id == "pid"
    assert cfg.poll_timeout_s == 600
    assert cfg.style == "summary"


def test_load_overrides(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text(textwrap.dedent("""
        bilinote:
          base_url: http://x
          provider_id: pid
          model_name: m
          poll_interval_s: 5
          poll_timeout_s: 900
          style: detailed
    """), encoding="utf-8")
    cfg = load_config(str(p))
    assert cfg.poll_interval_s == 5
    assert cfg.poll_timeout_s == 900
    assert cfg.style == "detailed"


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(str(tmp_path / "nope.yaml"))
