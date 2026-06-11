from bilibili import BilibiliCredential, BilibiliEngineError
from bilibili_watcher.fetcher import build_credential, make_fetcher, FetchedDoc
from bilibili_watcher.config import RenderConfig


class _FakeRendered:
    main_markdown = "## summary\n\nprose transcript\n"


class _FakeResult:
    class metadata:
        title = "Real Title"

    def render(self, ro):
        assert ro.include_transcript is True and ro.split_transcript is False
        return _FakeRendered()


class _FakeEngine:
    def __init__(self):
        self.calls = []

    def transcribe(self, video_ref, credential):
        self.calls.append((video_ref, credential))
        return _FakeResult()


class _BoomEngine:
    def transcribe(self, video_ref, credential):
        raise BilibiliEngineError("BN down")


def test_build_credential_from_cookies():
    cred = build_credential({"SESSDATA": "s", "bili_jct": "j", "X": "y"})
    assert isinstance(cred, BilibiliCredential)
    assert cred.sessdata == "s" and cred.bili_jct == "j"


def test_make_fetcher_success_returns_doc():
    eng = _FakeEngine()
    fetch = make_fetcher(eng, RenderConfig())
    cred = build_credential({"SESSDATA": "s"})
    doc = fetch("BV1xx", cred)
    assert isinstance(doc, FetchedDoc)
    assert doc.title == "Real Title"
    assert "prose transcript" in doc.markdown
    assert eng.calls[0][0] == "BV1xx"


def test_make_fetcher_engine_error_returns_none():
    fetch = make_fetcher(_BoomEngine(), RenderConfig())
    assert fetch("BV1xx", build_credential({"SESSDATA": "s"})) is None
