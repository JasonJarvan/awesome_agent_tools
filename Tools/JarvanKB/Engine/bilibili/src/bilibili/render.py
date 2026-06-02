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


import datetime as _dt
import yaml as _yaml

from .models import BilibiliResult, RenderOptions, RenderedOutput


def format_timestamp(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m:02d}:{sec:02d}"


def _frontmatter(result: BilibiliResult) -> str:
    meta = result.metadata
    pub = _dt.datetime.fromtimestamp(meta.pubdate, tz=_dt.timezone.utc).strftime("%Y-%m-%d")
    data = {
        "bvid": meta.bvid,
        "title": meta.title,
        "up": meta.up,
        "url": meta.url,
        "duration": meta.duration,
        "pubdate": pub,
        "transcript_source": result.transcript.source,
    }
    body = _yaml.safe_dump(data, allow_unicode=True, sort_keys=False).strip()
    return f"---\n{body}\n---"


def _transcript_block(result: BilibiliResult, options: RenderOptions) -> str:
    segs = result.transcript.segments
    if options.include_timestamps:
        lines = [f"[{format_timestamp(s.start)}] {s.text.strip()}" for s in segs if s.text.strip()]
        return "\n".join(lines)
    return result.transcript.full_text


def render_result(result: BilibiliResult, options: RenderOptions) -> RenderedOutput:
    slug = options.slug or result.metadata.bvid
    names = {"main": f"{slug}.md", "transcript": f"{slug}.transcript.md"}

    parts = [_frontmatter(result), f"# {result.metadata.title}"]
    if result.summary_markdown:
        parts.append(result.summary_markdown.strip())

    transcript_md = None
    if options.include_transcript:
        block = _transcript_block(result, options)
        if options.split_transcript:
            transcript_md = f"{_frontmatter(result)}\n\n# {result.metadata.title} — 全文转录\n\n{block}"
            parts.append(f"## 全文转录\n\n[全文转录](./{names['transcript']})")
        else:
            parts.append(f"## 全文转录\n\n{block}")

    return RenderedOutput(
        main_markdown="\n\n".join(parts) + "\n",
        transcript_markdown=(transcript_md + "\n") if transcript_md else None,
        suggested_names=names,
    )
