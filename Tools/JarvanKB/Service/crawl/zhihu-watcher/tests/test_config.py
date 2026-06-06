import textwrap
import pytest
from zhihu_watcher.config import load_config, WatcherConfig


def _write(tmp_path, text):
    p = tmp_path / "cfg.yaml"
    p.write_text(textwrap.dedent(text), encoding="utf-8")
    return str(p)


def test_load_valid_config(tmp_path):
    path = _write(tmp_path, """
        poll_interval_minutes: 45
        output_dir: /data/output
        state_dir: /data/state
        cookie_source:
          base_url: http://127.0.0.1:48088
          uuid: box-uuid
          password: box-pass
        collections:
          - id: "630144608"
            name: AI-papers
          - id: "999"
    """)
    cfg = load_config(path)
    assert isinstance(cfg, WatcherConfig)
    assert cfg.poll_interval_minutes == 45
    assert cfg.output_dir == "/data/output"
    assert cfg.cookie_source.base_url == "http://127.0.0.1:48088"
    assert cfg.cookie_source.uuid == "box-uuid"
    assert len(cfg.collections) == 2
    assert cfg.collections[0].id == "630144608"
    assert cfg.collections[0].name == "AI-papers"
    # name defaults to id when omitted
    assert cfg.collections[1].name == "999"


def test_missing_collections_raises(tmp_path):
    path = _write(tmp_path, """
        poll_interval_minutes: 45
        output_dir: /data/output
        state_dir: /data/state
        cookie_source:
          base_url: http://x
          uuid: u
          password: p
        collections: []
    """)
    with pytest.raises(ValueError, match="at least one collection"):
        load_config(path)


def test_missing_cookie_field_raises(tmp_path):
    path = _write(tmp_path, """
        poll_interval_minutes: 45
        output_dir: /data/output
        state_dir: /data/state
        cookie_source:
          base_url: http://x
          uuid: u
        collections:
          - id: "1"
    """)
    with pytest.raises(ValueError, match="password"):
        load_config(path)
