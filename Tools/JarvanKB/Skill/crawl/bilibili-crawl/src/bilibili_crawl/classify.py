"""vague_path classification: infer an existing subfolder under output_root, or propose a new one.

A video has no article body — classify on metadata.title + a lead of summary_markdown (BN's AI note, the
densest topic signal). summary_markdown is best-effort and may be None -> fall back to a lead of
transcript.full_text. Lead is markdown-noise-stripped + capped (token saving). (SP-3 stripper reused.)
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .saver import slugify

_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
_OBJ_RE = re.compile(r"\{.*?\}", re.DOTALL)   # non-greedy: each flat {...} object

# markdown-noise strippers for the classification lead (save tokens — drop what carries no topic signal)
_FENCE_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)
_IMG_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_MD_MARKS_RE = re.compile(r"[#>*`~]+")
_WS_RE = re.compile(r"\s+")


def _lead_text(markdown: str, max_chars: int) -> str:
    """Plain-text lead of a markdown body for classification — strips markdown noise, caps length."""
    t = markdown or ""
    t = _FENCE_BLOCK_RE.sub(" ", t)   # drop fenced code blocks
    t = _IMG_RE.sub(" ", t)            # drop images (alt text + URL)
    t = _LINK_RE.sub(r"\1", t)         # links -> link text only
    t = _MD_MARKS_RE.sub(" ", t)       # drop heading/quote/emphasis/code marks
    t = _WS_RE.sub(" ", t).strip()     # collapse whitespace
    return t[:max_chars]


@dataclass
class Category:
    name: str
    is_new: bool


def existing_subfolders(output_root: Path) -> list[str]:
    root = Path(output_root).expanduser()
    if not root.exists():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir() and not p.name.startswith("."))


def _classification_source(result) -> str:
    """Prefer BN's AI summary; fall back to the transcript when summary is missing/empty."""
    summary = result.summary_markdown or ""
    if summary.strip():
        return summary
    return getattr(result.transcript, "full_text", "") or ""


def _build_prompt(subfolders: list[str], title: str, snippet: str) -> str:
    folder_list = ", ".join(subfolders) if subfolders else "(none yet)"
    return (
        "You classify a saved Bilibili video note into ONE subfolder of a personal knowledge base.\n"
        f"Existing subfolders: {folder_list}\n"
        f"Video title: {title}\nContent snippet: {snippet}\n\n"
        "Pick the single best existing subfolder, or propose a NEW concise subfolder name if none fit. "
        'Reply with ONLY JSON: {"category": "<name>", "is_new": <true|false>}.'
    )


def _parse(raw: str) -> dict:
    text = raw.strip()
    fence = _FENCE_RE.search(text)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # tolerate prose-wrapped output: prefer the LAST parseable object (models answer last)
    for candidate in reversed(_OBJ_RE.findall(text)):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise ValueError(f"LLM classification did not return parseable JSON: {raw[:200]!r}")


def classify(result, output_root: Path, client, *, snippet_chars: int = 240) -> Category:
    subs = existing_subfolders(output_root)
    title = result.metadata.title
    snippet = _lead_text(_classification_source(result), snippet_chars)
    raw = client.complete([{"role": "user", "content": _build_prompt(subs, title, snippet)}])
    data = _parse(raw)
    name = slugify(str(data["category"]))
    is_new = name not in subs   # authoritative: trust the filesystem, not the model's flag
    return Category(name=name, is_new=is_new)
