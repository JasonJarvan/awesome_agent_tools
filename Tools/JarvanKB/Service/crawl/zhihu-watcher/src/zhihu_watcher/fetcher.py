"""Thin wrapper over the frozen SP-2 zhihu engine: one URL + cookies -> (title, markdown) | None."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import zhihu

log = logging.getLogger("zhihu_watcher.fetcher")


@dataclass
class FetchedDoc:
    title: str
    content_markdown: str


def fetch(url: str, cookies: dict[str, str]) -> FetchedDoc | None:
    try:
        result = zhihu.fetch(url, cookies=cookies)
    except zhihu.ZhihuFetchError as e:
        log.warning(
            "SP-2 fetch failed url=%s status=%s attempts=%s",
            url, getattr(e, "status", None), getattr(e, "attempts", None),
        )
        return None
    return FetchedDoc(title=result.title, content_markdown=result.content_markdown)
