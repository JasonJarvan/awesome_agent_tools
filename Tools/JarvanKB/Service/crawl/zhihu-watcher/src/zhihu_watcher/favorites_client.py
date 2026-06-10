"""List items inside a Zhihu collection via the public collections API.

Endpoint: GET https://www.zhihu.com/api/v4/collections/{id}/items?offset=&limit=20
Plain cookies + browser-like headers, NO x-zse-96 signing (verified against the reference repo,
consistent with crawl-pipeline.md §知乎链路 D5). Direct connect: trust_env=False (Zhihu is a
mainland site; the host's proxy env is for overseas sites only).
"""
from __future__ import annotations

import html
import logging
from dataclasses import dataclass
from datetime import datetime

import httpx

log = logging.getLogger("zhihu_watcher.favorites_client")

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.zhihu.com/",
}


@dataclass
class CollectionItem:
    key: str           # stable dedup key: "{content_type}:{content_id}"
    url: str           # canonical content URL, fed to SP-2 fetch()
    content_type: str  # "answer" | "article" | ...
    title: str         # fallback title (SP-2 FetchResult.title is authoritative)
    favorited_at: datetime | None = None  # top-level `created` = the time it was added to the collection
    excerpt: str = ""  # per-type body lead (article: excerpt_title; answer: excerpt), html-unescaped


class ZhihuApiError(Exception):
    def __init__(self, status: int, url: str):
        super().__init__(f"Zhihu API {status} for {url}")
        self.status = status
        self.url = url


def collection_id_from_url(url_or_id: str) -> str:
    return url_or_id.split("?")[0].rstrip("/").split("/")[-1]


def _parse_favorited_at(el: dict) -> datetime | None:
    raw = el.get("created")
    if not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def _build_item(el: dict) -> CollectionItem | None:
    content = el.get("content") or {}
    ctype = content.get("type")
    cid = content.get("id")
    url = content.get("url")
    if not (ctype and cid and url):
        return None
    if ctype == "answer":
        title = (content.get("question") or {}).get("title") or content.get("title") or ""
        excerpt_raw = content.get("excerpt") or ""
    else:
        title = content.get("title") or ""
        excerpt_raw = content.get("excerpt_title") or content.get("excerpt") or ""
    return CollectionItem(
        key=f"{ctype}:{cid}", url=url, content_type=ctype, title=title,
        favorited_at=_parse_favorited_at(el),
        excerpt=html.unescape(excerpt_raw),
    )


class FavoritesClient:
    def __init__(self, http_client: httpx.Client | None = None, limit: int = 20):
        self._client = http_client or httpx.Client(
            trust_env=False, headers=_BROWSER_HEADERS, timeout=30.0
        )
        self._limit = limit

    def list_items(self, collection_id_or_url: str, cookies: dict[str, str]) -> list[CollectionItem]:
        collection_id = collection_id_from_url(collection_id_or_url)
        items: list[CollectionItem] = []
        offset = 0
        while True:
            url = (
                f"https://www.zhihu.com/api/v4/collections/{collection_id}"
                f"/items?offset={offset}&limit={self._limit}"
            )
            resp = self._client.get(url, cookies=cookies)
            if resp.status_code != 200:
                raise ZhihuApiError(resp.status_code, url)
            body = resp.json()
            data = body.get("data") or []
            for el in data:
                item = _build_item(el)
                if item is not None:
                    items.append(item)
            paging = body.get("paging") or {}
            if paging.get("is_end") is True:
                break
            offset += self._limit
            totals = paging.get("totals")
            if totals is not None and len(items) >= totals:
                break
            if not data:  # safety: empty page with no is_end / totals
                break
        log.info("collection %s: listed %d items", collection_id, len(items))
        return items
