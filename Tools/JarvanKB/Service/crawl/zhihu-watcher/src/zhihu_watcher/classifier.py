"""Token-frugal tiered classify wrapper for the watcher.

Tier-1 feeds a short lead; if the model reports the choice as vague (>=2 plausible folders), Tier-2 feeds a
larger lead. The full text is NEVER passed. With allow_new_folders=False (the daemon default), a result that
matches no existing folder (Classification.is_new) is an error routed to the failure path.
"""
from __future__ import annotations

from jarvankb_common.classify import classify, lead_text


class ClassifyError(Exception):
    pass


def classify_doc(doc, existing_subfolders: list[str], client, cfg) -> str:
    lead1 = lead_text(doc.content_markdown, cfg.tier1_chars)
    c = classify(doc.title, lead1, existing_subfolders, client, allow_new=cfg.allow_new_folders)
    if c.vague:
        lead2 = lead_text(doc.content_markdown, cfg.tier2_chars)
        c = classify(doc.title, lead2, existing_subfolders, client, allow_new=cfg.allow_new_folders)
    if not cfg.allow_new_folders and c.is_new:
        raise ClassifyError(
            f"classifier chose off-list folder {c.folder!r} with allow_new_folders=False; "
            f"existing={existing_subfolders}")
    return c.folder
