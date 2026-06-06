"""Regression tests for code-review findings (2026-06-06): robust LLM-output parsing + category sanitize."""
import types

import pytest

from zhihu_crawl.classify import classify
from zhihu_crawl.saver import resolve_target


def _result(title="T", typ="answer", body="b"):
    return types.SimpleNamespace(title=title, type=typ, content_markdown=body)


class _Client:
    def __init__(self, reply):
        self.reply = reply

    def complete(self, messages, **kw):
        return self.reply


# --- #1: _parse robustness ---

def test_parse_prose_wrapped_json(tmp_path):
    (tmp_path / "tech").mkdir()
    reply = 'Let me think {note}. Best fit: {"category": "tech", "is_new": false}'
    cat = classify(_result(), tmp_path, _Client(reply))
    assert cat.name == "tech" and cat.is_new is False


def test_parse_multiple_objects_prefers_last(tmp_path):
    reply = '{"category": "draft"} ... final answer: {"category": "philosophy", "is_new": true}'
    cat = classify(_result(), tmp_path, _Client(reply))
    assert cat.name == "philosophy"


def test_parse_unparseable_raises_valueerror(tmp_path):
    with pytest.raises(ValueError):
        classify(_result(), tmp_path, _Client("sorry, I cannot help with that"))


# --- #2: resolve_target must not let a category escape output_root ---

def test_resolve_target_sanitizes_malicious_category(tmp_path):
    root = tmp_path / "KB"
    target = resolve_target(None, root, "../../../tmp/evil", "note")
    resolved = target.resolve()
    assert str(resolved).startswith(str(root.resolve())), f"{resolved} escaped {root}"
