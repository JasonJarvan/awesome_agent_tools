from __future__ import annotations
from bs4 import BeautifulSoup
from markdownify import MarkdownConverter


class _ZhihuConverter(MarkdownConverter):
    """Standard Markdown. Images stay as remote URLs (no download). Engine is pure-fetch."""

    def convert_img(self, el, text, parent_tags):
        src = el.get("data-original") or el.get("src") or ""
        alt = el.get("alt") or ""
        return f"![{alt}]({src})" if src else ""


def html_to_markdown(html: str) -> str:
    soup = BeautifulSoup(html or "", "lxml")
    for style in soup.find_all("style"):
        style.extract()
    return _ZhihuConverter().convert_soup(soup).strip()


def render_frontmatter(meta: dict) -> str:
    """Minimal, deterministic YAML frontmatter (flat scalar values only)."""
    lines = ["---"]
    for key, value in meta.items():
        if value is None:
            continue
        lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n"
