from __future__ import annotations
from bs4 import BeautifulSoup
from ..markdown import html_to_markdown

_SELECTORS = [
    ("div", {"class": "RichContent-inner"}),
    ("div", {"class": "Post-RichText"}),
    ("div", {"class": "RichText"}),
    ("div", {"class": "Post-content"}),
]


def scrape_body(html: str) -> str | None:
    """Last-resort CSS scrape of the rendered body div. None if no known container matches."""
    soup = BeautifulSoup(html or "", "lxml")
    for name, attrs in _SELECTORS:
        node = soup.find(name, attrs=attrs)
        if node:
            return html_to_markdown(str(node))
    return None
