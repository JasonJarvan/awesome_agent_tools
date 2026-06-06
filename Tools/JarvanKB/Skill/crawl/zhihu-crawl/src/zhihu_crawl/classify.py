"""vague_path classification: infer an existing subfolder under output_root, or propose a new one."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .saver import slugify

_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
_OBJ_RE = re.compile(r"\{.*?\}", re.DOTALL)   # non-greedy: each flat {...} object


@dataclass
class Category:
    name: str
    is_new: bool


def existing_subfolders(output_root: Path) -> list[str]:
    root = Path(output_root).expanduser()
    if not root.exists():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir() and not p.name.startswith("."))


def _build_prompt(subfolders: list[str], title: str, typ: str, snippet: str) -> str:
    folder_list = ", ".join(subfolders) if subfolders else "(none yet)"
    return (
        "You classify a saved Zhihu item into ONE subfolder of a personal knowledge base.\n"
        f"Existing subfolders: {folder_list}\n"
        f"Item type: {typ}\nTitle: {title}\nContent snippet: {snippet}\n\n"
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


def classify(result, output_root: Path, client) -> Category:
    subs = existing_subfolders(output_root)
    typ = getattr(result.type, "value", str(result.type))
    snippet = (result.content_markdown or "")[:500]
    raw = client.complete([{"role": "user", "content": _build_prompt(subs, result.title, typ, snippet)}])
    data = _parse(raw)
    name = slugify(str(data["category"]))
    is_new = name not in subs   # authoritative: trust the filesystem, not the model's flag
    return Category(name=name, is_new=is_new)
