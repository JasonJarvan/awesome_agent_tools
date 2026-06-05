import types
from pathlib import Path

from zhihu_crawl.classify import classify, existing_subfolders


def _result(title="Transformer 解析", typ="answer", body="深度学习注意力机制..."):
    return types.SimpleNamespace(title=title, type=typ, content_markdown=body)


class FakeClient:
    def __init__(self, reply):
        self.reply = reply
        self.prompt = None

    def complete(self, messages, **kw):
        self.prompt = messages[0]["content"]
        return self.reply


def test_existing_subfolders_lists_dirs(tmp_path):
    (tmp_path / "tech").mkdir()
    (tmp_path / "life").mkdir()
    (tmp_path / ".hidden").mkdir()
    (tmp_path / "f.md").write_text("x")
    assert existing_subfolders(tmp_path) == ["life", "tech"]


def test_classify_picks_existing(tmp_path):
    (tmp_path / "tech").mkdir()
    client = FakeClient('{"category": "tech", "is_new": false}')
    cat = classify(_result(), tmp_path, client)
    assert cat.name == "tech"
    assert cat.is_new is False
    assert "tech" in client.prompt   # existing folders fed to the model


def test_classify_proposes_new_folder(tmp_path):
    (tmp_path / "tech").mkdir()
    client = FakeClient('```json\n{"category": "Machine Learning", "is_new": true}\n```')
    cat = classify(_result(), tmp_path, client)
    assert cat.name == "machine-learning"   # slugged
    assert cat.is_new is True


def test_classify_marks_new_when_not_in_existing(tmp_path):
    (tmp_path / "tech").mkdir()
    client = FakeClient('{"category": "philosophy"}')   # model omitted is_new
    cat = classify(_result(), tmp_path, client)
    assert cat.name == "philosophy"
    assert cat.is_new is True   # not among existing → new
