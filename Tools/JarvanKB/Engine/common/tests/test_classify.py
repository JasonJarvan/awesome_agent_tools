from pathlib import Path

from jarvankb_common.classify import classify, existing_subfolders, lead_text, Classification


class FakeClient:
    def __init__(self, reply):
        self.reply = reply
        self.prompt = None

    def complete(self, messages, **kw):
        self.prompt = messages[0]["content"]
        return self.reply


def test_lead_text_strips_markdown_and_caps():
    md = "# Title\n\n![img](http://x/y.png) see [link](http://z) `code`\n\n```\nblock\n```\n\nbody text here"
    out = lead_text(md, 40)
    assert "![img]" not in out and "http://" not in out and "```" not in out
    assert "link" in out                      # link text kept
    assert len(out) <= 40


def test_existing_subfolders_lists_dirs(tmp_path):
    (tmp_path / "tech").mkdir()
    (tmp_path / "life").mkdir()
    (tmp_path / ".hidden").mkdir()
    (tmp_path / "f.md").write_text("x")
    assert existing_subfolders(tmp_path) == ["life", "tech"]


def test_classify_picks_existing():
    client = FakeClient('{"category": "tech", "is_new": false}')
    c = classify("Transformer 解析", "深度学习注意力机制", ["tech", "life"], client)
    assert c.folder == "tech"
    assert c.is_new is False
    assert c.vague is False
    assert "tech" in client.prompt              # existing folders fed to the model


def test_classify_proposes_new_when_allowed():
    client = FakeClient('```json\n{"category": "Machine Learning", "is_new": true}\n```')
    c = classify("t", "body", ["tech"], client, allow_new=True)
    assert c.folder == "machine-learning"       # slugged new name
    assert c.is_new is True


def test_classify_marks_new_when_not_in_existing():
    client = FakeClient('{"category": "philosophy"}')   # model omitted is_new
    c = classify("t", "body", ["tech"], client)
    assert c.folder == "philosophy"
    assert c.is_new is True                     # filesystem-authoritative, not the model flag


def test_classify_returns_raw_existing_name_on_slug_match():
    # existing folder has uppercase + CJK; model answers a slug-equivalent -> we keep the REAL folder name
    client = FakeClient('{"category": "技术-ai生成"}')
    c = classify("t", "body", ["技术-AI生成", "生涯-育儿"], client)
    assert c.folder == "技术-AI生成"            # raw matched name (so the watcher writes the real dir)
    assert c.is_new is False


def test_classify_reports_vague():
    client = FakeClient('{"category": "tech", "vague": true}')
    c = classify("t", "body", ["tech", "ai"], client)
    assert c.vague is True


def test_allow_new_false_changes_prompt_only():
    client = FakeClient('{"category": "tech"}')
    classify("t", "body", ["tech"], client, allow_new=False)
    assert "ONLY" in client.prompt or "only" in client.prompt   # instructed to pick from existing
