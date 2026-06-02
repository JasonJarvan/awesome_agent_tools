from __future__ import annotations
import json
from bs4 import BeautifulSoup


def extract_initial_data(html: str) -> dict | None:
    """Extract and parse the <script id="js-initialData"> JSON blob. None if absent/unparseable."""
    soup = BeautifulSoup(html, "lxml")
    tag = soup.find("script", id="js-initialData")
    if not tag or not tag.string:
        return None
    try:
        return json.loads(tag.string)
    except (ValueError, TypeError):
        return None
