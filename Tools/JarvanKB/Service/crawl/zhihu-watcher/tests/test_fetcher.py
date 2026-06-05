import types
import zhihu
from zhihu_watcher.fetcher import fetch, FetchedDoc


def test_fetch_returns_title_and_markdown(monkeypatch):
    fake_result = types.SimpleNamespace(title="My Title", content_markdown="# body\nhello")

    def fake_fetch(url, cookies=None, **kw):
        assert url == "https://www.zhihu.com/question/1/answer/2"
        assert cookies == {"z_c0": "x"}
        return fake_result

    monkeypatch.setattr(zhihu, "fetch", fake_fetch)
    doc = fetch("https://www.zhihu.com/question/1/answer/2", {"z_c0": "x"})
    assert isinstance(doc, FetchedDoc)
    assert doc.title == "My Title"
    assert doc.content_markdown == "# body\nhello"


def test_fetch_returns_none_on_zhihu_error(monkeypatch):
    def boom(url, cookies=None, **kw):
        raise zhihu.ZhihuFetchError("nope", url=url)

    monkeypatch.setattr(zhihu, "fetch", boom)
    assert fetch("https://www.zhihu.com/p/1", {}) is None
