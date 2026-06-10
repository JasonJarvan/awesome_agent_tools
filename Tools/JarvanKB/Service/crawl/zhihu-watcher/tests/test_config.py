import textwrap
import pytest
from datetime import datetime
from zhihu_watcher.config import load_config, WatcherConfig, UserTarget, CollectionConfig


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
        targets:
          - type: collection
            id: "630144608"
            name: AI-papers
          - type: collection
            id: "999"
    """)
    cfg = load_config(path)
    assert isinstance(cfg, WatcherConfig)
    assert cfg.poll_interval_minutes == 45
    assert cfg.output_dir == "/data/output"
    assert cfg.cookie_source.base_url == "http://127.0.0.1:48088"
    assert cfg.cookie_source.uuid == "box-uuid"
    assert len(cfg.targets) == 2
    assert cfg.targets[0].id == "630144608"
    assert cfg.targets[0].name == "AI-papers"
    # name defaults to id when omitted
    assert cfg.targets[1].name == "999"


def test_missing_collections_raises(tmp_path):
    path = _write(tmp_path, """
        poll_interval_minutes: 45
        output_dir: /data/output
        state_dir: /data/state
        cookie_source:
          base_url: http://x
          uuid: u
          password: p
        targets: []
    """)
    with pytest.raises(ValueError, match="targets"):
        load_config(path)


def test_missing_cookie_field_raises(tmp_path):
    path = _write(tmp_path, """
        poll_interval_minutes: 45
        output_dir: /data/output
        state_dir: /data/state
        cookie_source:
          base_url: http://x
          uuid: u
        targets:
          - type: collection
            id: "1"
    """)
    with pytest.raises(ValueError, match="password"):
        load_config(path)


# ---------------------------------------------------------------------------
# New tests for targets schema (SP-5a v1.1)
# ---------------------------------------------------------------------------

def _write_new(tmp_path, body):
    p = tmp_path / "c.yaml"
    p.write_text(body, encoding="utf-8")
    return str(p)


_BASE = """
output_dir: /out
state_dir: /state
cookie_source: {base_url: http://x, uuid: u, password: p}
"""


def test_parses_collection_and_user_targets(tmp_path):
    cfg = load_config(_write_new(tmp_path, _BASE + """
targets:
  - type: collection
    id: "630144608"
    name: "AI-papers"
  - type: user
    url_token: me
    name_prefix: "zhao/"
"""))
    assert isinstance(cfg.targets[0], CollectionConfig)
    assert cfg.targets[0].id == "630144608" and cfg.targets[0].name == "AI-papers"
    u = cfg.targets[1]
    assert isinstance(u, UserTarget)
    assert u.url_token == "me" and u.name_prefix == "zhao/"
    assert u.skip_empty is True and u.include_default is False   # defaults


def test_collection_name_defaults_to_id(tmp_path):
    cfg = load_config(_write_new(tmp_path, _BASE + 'targets:\n  - {type: collection, id: "99"}\n'))
    assert cfg.targets[0].name == "99"


def test_missing_targets_raises(tmp_path):
    with pytest.raises(ValueError, match="targets"):
        load_config(_write_new(tmp_path, _BASE))


def test_unknown_target_type_raises(tmp_path):
    with pytest.raises(ValueError, match="type"):
        load_config(_write_new(tmp_path, _BASE + 'targets:\n  - {type: bogus}\n'))


def test_scalar_options_parsed(tmp_path):
    cfg = load_config(_write_new(tmp_path, _BASE + """
only_after: "2026-01-01T00:00:00+08:00"
backfill_on_first_run: true
max_consecutive_failures: 5
failure_cooldown_hours: 6
targets:
  - {type: collection, id: "1"}
"""))
    assert cfg.only_after == datetime.fromisoformat("2026-01-01T00:00:00+08:00")
    assert cfg.backfill_on_first_run is True
    assert cfg.max_consecutive_failures == 5
    assert cfg.failure_cooldown_hours == 6.0


def test_naive_only_after_rejected(tmp_path):
    with pytest.raises(ValueError, match="timezone offset"):
        load_config(_write(tmp_path, _BASE + """
only_after: "2026-01-01T00:00:00"
targets:
  - {type: collection, id: "1"}
"""))
