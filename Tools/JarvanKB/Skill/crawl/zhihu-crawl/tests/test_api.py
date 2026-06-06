import types
from pathlib import Path

import zhihu_crawl.api as api
from zhihu_crawl.config import ModuleConfig
from zhihu_crawl.cookie import CookieSource


def _fake_result(title="My Answer", typ="answer"):
    r = types.SimpleNamespace(title=title, type=typ, url="https://zhihu/x",
                              content_markdown="body")
    r.to_markdown = lambda with_frontmatter=True: "# My Answer\nbody"
    return r


def _patch_common(monkeypatch, tmp_path, fetch_result=None, classify_name="tech", classify_new=False):
    mc = ModuleConfig(output_root=tmp_path / "KB",
                      cookie=CookieSource("u", "id", "pw"), llm_profile="default")
    monkeypatch.setattr(api.cfgmod, "load_config", lambda p=None: mc)
    monkeypatch.setattr(api.cookie, "pull", lambda src, **kw: {"z_c0": "Z"})
    monkeypatch.setattr(api, "fetch", lambda url, **kw: fetch_result or _fake_result())
    monkeypatch.setattr(api, "LLMClient", lambda profile=None: object())
    monkeypatch.setattr(api.classify, "classify",
                        lambda result, root, client, **kw: api.classify.Category(classify_name, classify_new))
    return mc


def test_explicit_path_writes_verbatim_no_classify(tmp_path, monkeypatch):
    _patch_common(monkeypatch, tmp_path)
    called = {"classify": False}
    monkeypatch.setattr(api.classify, "classify",
                        lambda *a, **k: called.__setitem__("classify", True) or api.classify.Category("x", True))
    target = tmp_path / "out" / "note.md"
    r = api.save_zhihu("https://zhihu/x", save_path=str(target))
    assert Path(r.path) == target
    assert target.read_text().startswith("# My Answer")
    assert r.was_vague is False
    assert r.category is None
    assert called["classify"] is False


def test_vague_path_classifies_and_saves(tmp_path, monkeypatch):
    _patch_common(monkeypatch, tmp_path, classify_name="tech", classify_new=False)
    r = api.save_zhihu("https://zhihu/x", save_path=None)
    assert r.was_vague is True
    assert r.category == "tech"
    assert r.proposed_new is False
    assert Path(r.path) == tmp_path / "KB" / "tech" / "my-answer.md"
    assert Path(r.path).read_text().startswith("# My Answer")


def test_result_fields(tmp_path, monkeypatch):
    _patch_common(monkeypatch, tmp_path)
    r = api.save_zhihu("https://zhihu/x", save_path=str(tmp_path / "n.md"))
    assert r.title == "My Answer"
    assert r.type == "answer"
    assert r.url == "https://zhihu/x"
