import types
from pathlib import Path

from bilibili_crawl.classify import classify, existing_subfolders


def _result(title="Transformer 深入解析", summary="注意力机制与多头自注意力的工程实践...",
            transcript_text="大家好 今天我们来讲 transformer 的注意力机制 ..."):
    metadata = types.SimpleNamespace(title=title)
    transcript = types.SimpleNamespace(full_text=transcript_text)
    return types.SimpleNamespace(metadata=metadata, summary_markdown=summary, transcript=transcript)


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


def test_classify_picks_existing_using_summary(tmp_path):
    (tmp_path / "tech").mkdir()
    client = FakeClient('{"category": "tech", "is_new": false}')
    cat = classify(_result(), tmp_path, client)
    assert cat.name == "tech"
    assert cat.is_new is False
    assert "tech" in client.prompt                 # existing folders fed to the model
    assert "注意力机制" in client.prompt            # summary used as the lead


def test_classify_proposes_new_folder(tmp_path):
    (tmp_path / "tech").mkdir()
    client = FakeClient('```json\n{"category": "Machine Learning", "is_new": true}\n```')
    cat = classify(_result(), tmp_path, client)
    assert cat.name == "machine-learning"           # slugged
    assert cat.is_new is True


def test_classify_falls_back_to_transcript_when_no_summary(tmp_path):
    (tmp_path / "tech").mkdir()
    client = FakeClient('{"category": "tech"}')
    res = _result(summary=None)
    classify(res, tmp_path, client)
    assert "transformer 的注意力机制" in client.prompt  # transcript lead used when summary missing


def test_classify_marks_new_when_not_in_existing(tmp_path):
    (tmp_path / "tech").mkdir()
    client = FakeClient('{"category": "philosophy"}')   # model omitted is_new
    cat = classify(_result(), tmp_path, client)
    assert cat.name == "philosophy"
    assert cat.is_new is True                            # not among existing -> new
