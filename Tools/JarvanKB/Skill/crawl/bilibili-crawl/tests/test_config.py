import textwrap
from pathlib import Path

from bilibili_crawl.config import load_config


def test_load_config_reads_password_and_render(tmp_path, monkeypatch):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(textwrap.dedent(f"""
        output_root: {tmp_path}/KB
        cookie:
          base_url: http://127.0.0.1:48088
          uuid: my-uuid
          password_env: COOKIE_PW
        llm:
          profile: mimo
        render:
          include_transcript: true
          include_timestamps: true
          split_transcript: true
        classify_snippet_chars: 180
    """))
    monkeypatch.setenv("COOKIE_PW", "secret")
    mc = load_config(cfg)
    assert mc.output_root == Path(f"{tmp_path}/KB")
    assert mc.cookie.base_url == "http://127.0.0.1:48088"
    assert mc.cookie.uuid == "my-uuid"
    assert mc.cookie.password == "secret"
    assert mc.llm_profile == "mimo"
    assert mc.render.include_transcript is True
    assert mc.render.include_timestamps is True
    assert mc.render.split_transcript is True
    assert mc.classify_snippet_chars == 180


def test_defaults_when_blocks_omitted(tmp_path, monkeypatch):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(textwrap.dedent(f"""
        output_root: {tmp_path}/KB
        cookie: {{base_url: u, uuid: x, password_env: COOKIE_PW}}
    """))
    monkeypatch.setenv("COOKIE_PW", "s")
    mc = load_config(cfg)
    assert mc.llm_profile == "default"
    assert mc.render.include_transcript is True
    assert mc.render.include_timestamps is False
    assert mc.render.split_transcript is False
    assert mc.classify_snippet_chars == 240
