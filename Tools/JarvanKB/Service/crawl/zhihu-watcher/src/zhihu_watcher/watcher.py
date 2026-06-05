"""Orchestrate one poll cycle and wire the real components.

Collaborators are injected so the cycle is fully testable with fakes; build_watcher() supplies the
real implementations. The daemon must never crash — every failure path logs and continues.
"""
from __future__ import annotations

import logging
from typing import Callable, Optional

from .config import WatcherConfig
from .cookie_provider import CookieProvider
from .favorites_client import FavoritesClient
from .fetcher import FetchedDoc
from .fetcher import fetch as default_fetch
from .saver import save as default_save
from .watermark_store import WatermarkStore

log = logging.getLogger("zhihu_watcher.watcher")

FetcherFn = Callable[[str, dict], Optional[FetchedDoc]]
SaverFn = Callable[[str, str, str, str, str], str]


class Watcher:
    def __init__(
        self,
        config: WatcherConfig,
        cookie_provider,
        favorites_client,
        fetcher_fn: FetcherFn,
        watermark_store: WatermarkStore,
        saver_fn: SaverFn = default_save,
    ):
        self._cfg = config
        self._cookies = cookie_provider
        self._favorites = favorites_client
        self._fetch = fetcher_fn
        self._store = watermark_store
        self._save = saver_fn

    def run_cycle(self) -> None:
        try:
            cookies = self._cookies.get_cookies()
        except Exception as e:  # noqa: BLE001 - daemon must not crash
            log.error("cookie pull failed: %s — skipping cycle", e)
            return
        if not cookies:
            log.error("no .zhihu.com cookies available — skipping cycle")
            return
        for coll in self._cfg.collections:
            self._poll_collection(coll, cookies)

    def _poll_collection(self, coll, cookies: dict) -> None:
        try:
            items = self._favorites.list_items(coll.id, cookies)
        except Exception as e:  # noqa: BLE001
            log.error("listing collection %s failed: %s", coll.id, e)
            return
        seen = self._store.load(coll.id)
        new_count = 0
        for item in items:
            if item.key in seen:
                continue
            try:
                doc = self._fetch(item.url, cookies)
                if doc is None:
                    continue  # fetch failed (expected ZhihuFetchError path) -> NOT seen -> retried
                self._save(self._cfg.output_dir, coll.name, doc.title, item.url, doc.content_markdown)
            except Exception as e:  # noqa: BLE001 - one bad item must never abort the cycle
                log.error("processing item %s failed: %s", item.key, e)
                continue  # not marked seen -> retried next cycle
            seen.add(item.key)
            self._store.save(coll.id, seen)  # persist immediately (1-item crash window)
            new_count += 1
        log.info("collection %s (%s): %d new item(s)", coll.id, coll.name, new_count)


def build_watcher(config: WatcherConfig) -> Watcher:
    return Watcher(
        config=config,
        cookie_provider=CookieProvider(config.cookie_source),
        favorites_client=FavoritesClient(),
        fetcher_fn=default_fetch,
        watermark_store=WatermarkStore(config.state_dir),
    )
