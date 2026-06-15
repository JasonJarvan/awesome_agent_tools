import types

import pytest

from zhihu_watcher.classifier import ClassifyError, classify_doc
from zhihu_watcher.config import ClassifyConfig


def _doc(body):
    return types.SimpleNamespace(title="T", content_markdown=body)


class RecordingClient:
    """Returns scripted replies in order; records each prompt's snippet length proxy."""
    def __init__(self, replies):
        self.replies = list(replies)
        self.prompts = []

    def complete(self, messages, **kw):
        self.prompts.append(messages[0]["content"])
        return self.replies.pop(0)


def test_tier1_non_vague_single_call():
    client = RecordingClient(['{"category": "tech", "vague": false}'])
    cfg = ClassifyConfig(tier1_chars=200, tier2_chars=1000, allow_new_folders=False)
    folder = classify_doc(_doc("x" * 5000), ["tech", "life"], client, cfg)
    assert folder == "tech"
    assert len(client.prompts) == 1            # no escalation


def test_vague_escalates_to_tier2_with_longer_lead():
    client = RecordingClient(['{"category": "tech", "vague": true}', '{"category": "life", "vague": false}'])
    cfg = ClassifyConfig(tier1_chars=200, tier2_chars=1000, allow_new_folders=False)
    folder = classify_doc(_doc("y" * 5000), ["tech", "life"], client, cfg)
    assert folder == "life"                    # Tier-2 result wins
    assert len(client.prompts) == 2
    # the Tier-2 prompt embeds a longer snippet than Tier-1
    assert client.prompts[1].count("y") > client.prompts[0].count("y")


def test_off_list_after_tier2_raises_when_new_disallowed():
    client = RecordingClient(['{"category": "philosophy"}'])  # not in existing, not vague
    cfg = ClassifyConfig(allow_new_folders=False)
    with pytest.raises(ClassifyError):
        classify_doc(_doc("z" * 100), ["tech", "life"], client, cfg)


def test_never_passes_full_text():
    body = "w" * 100_000
    client = RecordingClient(['{"category": "tech", "vague": true}', '{"category": "tech", "vague": false}'])
    cfg = ClassifyConfig(tier1_chars=200, tier2_chars=1000, allow_new_folders=False)
    classify_doc(_doc(body), ["tech"], client, cfg)
    for p in client.prompts:
        assert p.count("w") <= 1100            # never the full 100k body (1000-char lead + ~5 template 'w's)
