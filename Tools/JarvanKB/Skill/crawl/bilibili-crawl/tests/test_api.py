import types
from pathlib import Path

import bilibili_crawl.api as api
from bilibili_crawl.config import ModuleConfig, RenderConfig
from bilibili_crawl.cookie import CookieSource


def _fake_result(title="My Video", source="asr"):
    metadata = types.SimpleNamespace(title=title, url="https://b/x")
    transcript = types.SimpleNamespace(source=source, full_text="words")
    r = types.SimpleNamespace(metadata=metadata, transcript=transcript, summary_markdown="sum")

    def render(opts):
        tm = "transcript-body" if opts.split_transcript else None
        return types.SimpleNamespace(main_markdown=f"# {title}\nbody", transcript_markdown=tm,
                                     suggested_names={})
    r.render = render
    return r


def _patch(monkeypatch, tmp_path, *, split=False, classify_name="tech", classify_new=False, result=None):
    mc = ModuleConfig(output_root=tmp_path / "KB", cookie=CookieSource("u", "id", "pw"),
                      llm_profile="mimo", render=RenderConfig(split_transcript=split))
    monkeypatch.setattr(api.cfgmod, "load_config", lambda p=None: mc)
    monkeypatch.setattr(api.cookie, "pull", lambda src, **kw: {"SESSDATA": "S"})
    monkeypatch.setattr(api.cookie, "build_credential", lambda cookies: "CRED")
    monkeypatch.setattr(api, "transcribe", lambda ref, credential=None: result or _fake_result())
    monkeypatch.setattr(api, "LLMClient", lambda profile=None: object())
    monkeypatch.setattr(api.classify, "classify",
                        lambda result, root, client, **kw: api.classify.Category(classify_name, classify_new))
    return mc


def test_explicit_path_writes_verbatim_no_classify(tmp_path, monkeypatch):
    _patch(monkeypatch, tmp_path)
    called = {"classify": False}
    monkeypatch.setattr(api.classify, "classify",
                        lambda *a, **k: called.__setitem__("classify", True) or api.classify.Category("x", True))
    target = tmp_path / "out" / "note.md"
    r = api.save_bilibili("BV1xx", save_path=str(target))
    assert Path(r.path) == target
    assert target.read_text().startswith("# My Video")
    assert r.was_vague is False
    assert r.category is None
    assert r.transcript_path is None
    assert called["classify"] is False


def test_vague_path_classifies_and_saves(tmp_path, monkeypatch):
    _patch(monkeypatch, tmp_path, classify_name="tech", classify_new=False)
    r = api.save_bilibili("BV1xx", save_path=None)
    assert r.was_vague is True
    assert r.category == "tech"
    assert r.proposed_new is False
    assert Path(r.path) == tmp_path / "KB" / "tech" / "my-video.md"
    assert Path(r.path).read_text().startswith("# My Video")


def test_result_fields(tmp_path, monkeypatch):
    _patch(monkeypatch, tmp_path, result=_fake_result(title="My Video", source="subtitle"))
    r = api.save_bilibili("BV1xx", save_path=str(tmp_path / "n.md"))
    assert r.title == "My Video"
    assert r.ref == "BV1xx"
    assert r.transcript_source == "subtitle"


def test_cookie_failure_degrades_to_no_credential(tmp_path, monkeypatch):
    _patch(monkeypatch, tmp_path)
    seen = {}

    def boom(src, **kw):
        raise RuntimeError("cookie-manager down")

    monkeypatch.setattr(api.cookie, "pull", boom)
    monkeypatch.setattr(api, "transcribe",
                        lambda ref, credential=None: seen.update(cred=credential) or _fake_result())
    r = api.save_bilibili("BV1xx", save_path=str(tmp_path / "n.md"))
    assert seen["cred"] is None        # degraded gracefully
    assert Path(r.path).exists()


def test_split_transcript_writes_second_file(tmp_path, monkeypatch):
    _patch(monkeypatch, tmp_path, split=True)
    r = api.save_bilibili("BV1xx", save_path=str(tmp_path / "out" / "note.md"))
    assert r.transcript_path == str(tmp_path / "out" / "note.transcript.md")
    assert Path(r.transcript_path).read_text() == "transcript-body"
