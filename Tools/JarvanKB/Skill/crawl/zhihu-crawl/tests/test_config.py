import textwrap
from pathlib import Path

from zhihu_crawl.config import load_config


def test_load_config_reads_password_from_env(tmp_path, monkeypatch):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(textwrap.dedent(f"""
        output_root: {tmp_path}/KB
        cookie:
          base_url: http://127.0.0.1:48088
          uuid: my-uuid
          password_env: COOKIE_PW
        llm:
          profile: default
    """))
    monkeypatch.setenv("COOKIE_PW", "secret")
    mc = load_config(cfg)
    assert mc.output_root == Path(f"{tmp_path}/KB")
    assert mc.cookie.base_url == "http://127.0.0.1:48088"
    assert mc.cookie.uuid == "my-uuid"
    assert mc.cookie.password == "secret"
    assert mc.llm_profile == "default"


def test_llm_profile_defaults_to_default(tmp_path, monkeypatch):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(textwrap.dedent(f"""
        output_root: {tmp_path}/KB
        cookie: {{base_url: u, uuid: x, password_env: COOKIE_PW}}
    """))
    monkeypatch.setenv("COOKIE_PW", "s")
    assert load_config(cfg).llm_profile == "default"
