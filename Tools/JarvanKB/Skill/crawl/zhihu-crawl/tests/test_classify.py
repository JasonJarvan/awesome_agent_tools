import types

from zhihu_crawl.classify import classify, Category


class FakeClient:
    def __init__(self, reply):
        self.reply = reply
        self.prompt = None

    def complete(self, messages, **kw):
        self.prompt = messages[0]["content"]
        return self.reply


def _result(title="Transformer 解析", typ="answer", body="深度学习注意力机制"):
    return types.SimpleNamespace(title=title, type=typ, content_markdown=body)


def test_adapter_returns_category_picking_existing(tmp_path):
    (tmp_path / "tech").mkdir()
    cat = classify(_result(), tmp_path, FakeClient('{"category": "tech", "is_new": false}'))
    assert isinstance(cat, Category)
    assert cat.name == "tech"
    assert cat.is_new is False


def test_adapter_proposes_new_folder(tmp_path):
    (tmp_path / "tech").mkdir()
    cat = classify(_result(), tmp_path, FakeClient('{"category": "Machine Learning", "is_new": true}'))
    assert cat.name == "machine-learning"
    assert cat.is_new is True
