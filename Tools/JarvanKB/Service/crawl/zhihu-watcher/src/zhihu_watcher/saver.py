"""Save a fetched item as Markdown, matching the Zhihu-Collections-MCP reference convention.

Layout: <output_dir>/<collection_name>/<sanitized_title>.md (collision -> _<url_id>.md).
Content: first line '> <url>', then the SP-2 content_markdown body. No YAML frontmatter.
Images keep their remote URLs (SP-2 does not download images; neither do we).
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


def _url_id(url: str) -> str:
    return url.split("?")[0].rstrip("/").split("/")[-1]


def save(output_dir: str, collection_name: str, title: str, url: str, content_markdown: str) -> str:
    folder = Path(output_dir) / collection_name
    folder.mkdir(parents=True, exist_ok=True)
    base = sanitize_title(title)
    path = folder / f"{base}.md"
    if path.exists():
        path = folder / f"{base}_{_url_id(url)}.md"
    text = f"> {url}\n{content_markdown}"
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8")
    return str(path)
