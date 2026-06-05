import json

import zhihu_crawl.cli as cli
from zhihu_crawl.api import SaveResult


def _result():
    return SaveResult(path="/KB/tech/x.md", title="X", type="answer",
                      url="https://zhihu/x", category="tech", was_vague=True, proposed_new=False)


def test_cli_json_output(monkeypatch, capsys):
    monkeypatch.setattr(cli, "save_zhihu", lambda *a, **k: _result())
    rc = cli.main(["https://zhihu/x", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["path"] == "/KB/tech/x.md"
    assert out["category"] == "tech"


def test_cli_passes_out_and_flags(monkeypatch):
    seen = {}

    def fake(url, save_path=None, **kw):
        seen.update(url=url, save_path=save_path, **kw)
        return _result()

    monkeypatch.setattr(cli, "save_zhihu", fake)
    cli.main(["https://zhihu/x", "--out", "~/KB", "--comments", "--profile", "fallback"])
    assert seen["url"] == "https://zhihu/x"
    assert seen["save_path"] == "~/KB"
    assert seen["with_comments"] is True
    assert seen["profile"] == "fallback"


def test_cli_fetch_error_exit_code(monkeypatch, capsys):
    from zhihu import ZhihuFetchError

    def boom(*a, **k):
        raise ZhihuFetchError("bad", url="https://zhihu/x")

    monkeypatch.setattr(cli, "save_zhihu", boom)
    rc = cli.main(["https://zhihu/x"])
    assert rc == 2
    assert "fetch failed" in capsys.readouterr().err
