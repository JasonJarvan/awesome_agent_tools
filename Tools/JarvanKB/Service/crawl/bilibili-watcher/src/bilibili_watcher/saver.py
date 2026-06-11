"""Save a transcribed video as Markdown (vault-agnostic, no GBrain frontmatter).

Layout: <output_dir>/<folder_name>/<sanitized_title>.md (collision -> _<bvid>.md).
Content: first line '> https://www.bilibili.com/video/<bvid>', then the engine's main_markdown.
Sanitization rules reused verbatim from SP-5a's saver.
"""
from __future__ import annotations

import re
from pathlib import Path

_ILLEGAL = re.compile(r'[\\/"<>|]')


def sanitize_title(title: str) -> str:
    s = _ILLEGAL.sub(" ", title)
    s = s.replace("?", "？").replace(":", "：")
    s = s.strip()
    return s or "untitled"


def save(output_dir: str, folder_name: str, title: str, bvid: str, markdown: str) -> str:
    folder = Path(output_dir) / folder_name
    folder.mkdir(parents=True, exist_ok=True)
    base = sanitize_title(title)
    path = folder / f"{base}.md"
    if path.exists():
        path = folder / f"{base}_{bvid}.md"
    text = f"> https://www.bilibili.com/video/{bvid}\n{markdown}"
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8")
    return str(path)
