"""Pure rendering: prose-merge + full document assembly. No file I/O, no LLM."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import TranscriptSegment


def _needs_space(left: str, right: str) -> bool:
    """Insert a space only between two ASCII alphanumeric boundaries (latin words);
    Chinese/CJK fragments concatenate without spaces."""
    if not left or not right:
        return False
    a, b = left[-1], right[0]
    return a.isascii() and a.isalnum() and b.isascii() and b.isalnum()


def merge_segments_to_prose(
    segments: list["TranscriptSegment"],
    gap_threshold_s: float = 2.0,
    char_budget: int = 200,
) -> str:
    """Merge short segment fragments into readable paragraphs (deterministic; no LLM).

    A new paragraph starts when the inter-segment time gap exceeds gap_threshold_s
    OR the current paragraph reaches char_budget characters.
    """
    if not segments:
        return ""
    paragraphs: list[str] = []
    current = ""
    last_end = None
    for seg in segments:
        text = (seg.text or "").strip()
        if not text:
            continue
        gap_break = last_end is not None and (seg.start - last_end) > gap_threshold_s
        budget_break = len(current) >= char_budget
        if current and (gap_break or budget_break):
            paragraphs.append(current)
            current = ""
        if current:
            current += (" " if _needs_space(current, text) else "") + text
        else:
            current = text
        last_end = seg.end
    if current:
        paragraphs.append(current)
    return "\n\n".join(paragraphs)
