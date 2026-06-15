"""Shared vague_path classifier: pick ONE subfolder under output_root (or propose a new one).

Self-contained: owns its slug + JSON-parse + prompt. Consumers supply a generic (title, lead_text):
the watcher from a fetched-content lead, SP-3 from its content_markdown lead. `vague` drives a caller-side
Tier escalation; `allow_new` only changes the prompt (is_new stays filesystem-authoritative).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
_OBJ_RE = re.compile(r"\{.*?\}", re.DOTALL)

_FENCE_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)
_IMG_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_MD_MARKS_RE = re.compile(r"[#>*`~]+")
_WS_RE = re.compile(r"\s+")
_SLUG_RE = re.compile(r"[^\w一-鿿]+")


@dataclass
class Classification:
    folder: str   # raw existing folder name on match, else slugified new name
    is_new: bool  # filesystem-authoritative: slug(model pick) matches no existing folder
    vague: bool   # model-reported: >=2 folders plausible (caller may escalate to a longer lead)


def lead_text(markdown: str, max_chars: int) -> str:
    t = markdown or ""
    t = _FENCE_BLOCK_RE.sub(" ", t)
    t = _IMG_RE.sub(" ", t)
    t = _LINK_RE.sub(r"\1", t)
    t = _MD_MARKS_RE.sub(" ", t)
    t = _WS_RE.sub(" ", t).strip()
    return t[:max_chars]


def existing_subfolders(output_root) -> list[str]:
    root = Path(output_root).expanduser()
    if not root.exists():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir() and not p.name.startswith("."))


def _slugify(name: str) -> str:
    s = _SLUG_RE.sub("-", name.strip()).strip("-").lower()
    return s or "untitled"


def _build_prompt(subfolders: list[str], title: str, snippet: str, allow_new: bool) -> str:
    folder_list = ", ".join(subfolders) if subfolders else "(none yet)"
    new_clause = (
        "Pick the single best existing subfolder, or propose a NEW concise subfolder name if none fit."
        if allow_new else
        "Pick the single best subfolder. You MUST choose ONLY from the existing list above; do NOT invent a new one."
    )
    return (
        "You classify a saved item into ONE subfolder of a personal knowledge base.\n"
        f"Existing subfolders: {folder_list}\n"
        f"Title: {title}\nContent snippet: {snippet}\n\n"
        f"{new_clause} Set \"vague\": true if two or more subfolders are plausible.\n"
        'Reply with ONLY JSON: {"category": "<name>", "is_new": <true|false>, "vague": <true|false>}.'
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
    for candidate in reversed(_OBJ_RE.findall(text)):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise ValueError(f"LLM classification did not return parseable JSON: {raw[:200]!r}")


def classify(title: str, lead_text: str, existing_subfolders: list[str], client,
             *, allow_new: bool = True) -> Classification:
    raw = client.complete([{"role": "user",
                            "content": _build_prompt(existing_subfolders, title, lead_text, allow_new)}])
    data = _parse(raw)
    chosen = _slugify(str(data["category"]))
    vague = bool(data.get("vague", False))
    match = next((s for s in existing_subfolders if _slugify(s) == chosen), None)
    if match is not None:
        return Classification(folder=match, is_new=False, vague=vague)
    return Classification(folder=chosen, is_new=True, vague=vague)
