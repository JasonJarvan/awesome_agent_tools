"""Token-saving classification input (2026-06-07): clean markdown noise + cap the lead snippet."""
import types

from jarvankb_common.classify import lead_text as _lead_text
from zhihu_crawl.classify import classify


def test_lead_text_strips_markdown_noise():
    md = (
        "# 标题\n\n"
        "![img](https://x/y.png) 这是正文,引用 [知乎链接](https://zhihu.com/x) 与 `code`。\n\n"
        "```python\nprint('drop me')\n```\n"
        "> 引用块\n- 列表项"
    )
    lead = _lead_text(md, 200)
    assert "https://" not in lead          # image + link URLs dropped
    assert "drop me" not in lead           # fenced code dropped
    assert "知乎链接" in lead               # link TEXT kept
    assert "这是正文" in lead
    assert "\n" not in lead                 # whitespace collapsed


def test_lead_text_caps_at_max_chars():
    assert len(_lead_text("一" * 1000, 240)) == 240
    assert _lead_text("", 240) == ""


def test_classify_respects_snippet_chars(tmp_path):
    captured = {}

    class _Client:
        def complete(self, messages, **kw):
            captured["prompt"] = messages[0]["content"]
            return '{"category": "tech", "is_new": false}'

    result = types.SimpleNamespace(title="T", type="answer", content_markdown="正" * 1000)
    classify(result, tmp_path, _Client(), snippet_chars=12)
    # the long body must have been truncated to the configured budget inside the prompt
    assert ("正" * 12) in captured["prompt"]
    assert ("正" * 13) not in captured["prompt"]
