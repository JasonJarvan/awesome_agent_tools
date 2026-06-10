import json

import bilibili_crawl.cli as cli
from bilibili_crawl.api import SaveResult


def _result():
    return SaveResult(path="/KB/tech/x.md", transcript_path=None, title="X", ref="BV1xx",
                      transcript_source="asr", category="tech", was_vague=True, proposed_new=False)


def test_cli_json_output(monkeypatch, capsys):
    monkeypatch.setattr(cli, "save_bilibili", lambda *a, **k: _result())
    rc = cli.main(["BV1xx", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["path"] == "/KB/tech/x.md"
    assert out["category"] == "tech"
    assert out["transcript_source"] == "asr"


def test_cli_passes_out_and_profile(monkeypatch):
    seen = {}

    def fake(ref, save_path=None, **kw):
        seen.update(ref=ref, save_path=save_path, **kw)
        return _result()

    monkeypatch.setattr(cli, "save_bilibili", fake)
    cli.main(["BV1xx", "--out", "~/KB", "--profile", "default"])
    assert seen["ref"] == "BV1xx"
    assert seen["save_path"] == "~/KB"
    assert seen["profile"] == "default"


def test_cli_bilinote_unavailable_exit_3(monkeypatch, capsys):
    from bilibili import BiliNoteUnavailable

    def boom(*a, **k):
        raise BiliNoteUnavailable("BN down")

    monkeypatch.setattr(cli, "save_bilibili", boom)
    rc = cli.main(["BV1xx"])
    assert rc == 3
    assert "BiliNote" in capsys.readouterr().err


def test_cli_engine_error_exit_2(monkeypatch, capsys):
    from bilibili import BilibiliEngineError

    def boom(*a, **k):
        raise BilibiliEngineError("bad")

    monkeypatch.setattr(cli, "save_bilibili", boom)
    rc = cli.main(["BV1xx"])
    assert rc == 2
