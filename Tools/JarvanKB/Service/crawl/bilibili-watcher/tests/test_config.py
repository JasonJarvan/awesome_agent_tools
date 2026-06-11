import pytest
from bilibili_watcher.config import load_config, WatcherConfig


def _write(tmp_path, text):
    p = tmp_path / "c.yaml"
    p.write_text(text, encoding="utf-8")
    return str(p)


def test_loads_full_config(tmp_path):
    cfg = load_config(_write(tmp_path, """
poll_interval_minutes: 20
output_dir: /data/output
state_dir: /data/state
cookie_source:
  base_url: http://127.0.0.1:48088
  uuid: u
  password: p
  auth_token: tok
engine:
  bn_base_url: http://127.0.0.1:3015
  provider_id: pid
  model_name: m
render:
  include_transcript: true
  include_timestamps: false
  split_transcript: false
folders:
  - id: "2216104467"
    name: "AI生成"
  - id: "1195057867"
"""))
    assert isinstance(cfg, WatcherConfig)
    assert cfg.poll_interval_minutes == 20
    assert cfg.cookie_source.auth_token == "tok"
    assert cfg.engine.bn_base_url == "http://127.0.0.1:3015"
    assert cfg.render.split_transcript is False
    assert [f.id for f in cfg.folders] == ["2216104467", "1195057867"]
    assert cfg.folders[0].name == "AI生成"
    assert cfg.folders[1].name == "1195057867"   # name defaults to id


def test_defaults(tmp_path):
    cfg = load_config(_write(tmp_path, """
output_dir: /o
state_dir: /s
cookie_source: {base_url: x, uuid: u, password: p}
engine: {bn_base_url: b, provider_id: pid, model_name: m}
folders: [{id: "1"}]
"""))
    assert cfg.poll_interval_minutes == 20            # default
    assert cfg.cookie_source.auth_token is None       # optional
    assert cfg.render.include_transcript is True       # default
    assert cfg.render.split_transcript is False


def test_missing_required_raises(tmp_path):
    with pytest.raises(ValueError, match="output_dir"):
        load_config(_write(tmp_path, "state_dir: /s\ncookie_source: {base_url: x, uuid: u, password: p}\nengine: {bn_base_url: b, provider_id: p, model_name: m}\nfolders: [{id: '1'}]"))


def test_no_folders_raises(tmp_path):
    with pytest.raises(ValueError, match="at least one folder"):
        load_config(_write(tmp_path, "output_dir: /o\nstate_dir: /s\ncookie_source: {base_url: x, uuid: u, password: p}\nengine: {bn_base_url: b, provider_id: p, model_name: m}\nfolders: []"))


def test_bad_interval_raises(tmp_path):
    with pytest.raises(ValueError, match="poll_interval_minutes"):
        load_config(_write(tmp_path, "poll_interval_minutes: 0\noutput_dir: /o\nstate_dir: /s\ncookie_source: {base_url: x, uuid: u, password: p}\nengine: {bn_base_url: b, provider_id: p, model_name: m}\nfolders: [{id: '1'}]"))
