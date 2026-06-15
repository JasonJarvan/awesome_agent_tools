"""SP-3 classify adapter — delegates to the shared jarvankb_common classifier.

Keeps the legacy Category(name, is_new) return shape so api.py is unchanged. SP-3 always allows the model
to propose a new folder (interactive use); the watcher uses allow_new=False (unattended).
"""
from __future__ import annotations

from dataclasses import dataclass

from jarvankb_common.classify import classify as _classify
from jarvankb_common.classify import existing_subfolders, lead_text


@dataclass
class Category:
    name: str
    is_new: bool


def classify(result, output_root, client, *, snippet_chars: int = 240) -> Category:
    subs = existing_subfolders(output_root)
    lead = lead_text(result.content_markdown, snippet_chars)
    c = _classify(result.title, lead, subs, client, allow_new=True)
    return Category(name=c.folder, is_new=c.is_new)
