"""Orchestrate one poll cycle and wire the real components.

Collaborators are injected so the cycle is fully testable with fakes; build_watcher() supplies the real ones.
The daemon must never crash — every failure path logs and continues.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Callable, Optional

from .config import WatcherConfig
from .cookie_provider import CookieProvider
from .failure_store import FailureStore
from .favorites_client import FavoritesClient
from .fetcher import FetchedDoc
from .fetcher import fetch as default_fetch
from .resolver import TargetResolver
from .saver import save as default_save
from .watermark_store import WatermarkStore

log = logging.getLogger("zhihu_watcher.watcher")

FetcherFn = Callable[[str, dict], Optional[FetchedDoc]]
SaverFn = Callable[[str, str, str, str, str], str]


class Watcher:
    def __init__(self, config: WatcherConfig, cookie_provider, favorites_client, fetcher_fn: FetcherFn,
                 watermark_store: WatermarkStore, *, resolver, failure_store: FailureStore,
                 saver_fn: SaverFn = default_save,
                 now_fn: Callable[[], datetime] = lambda: datetime.now(timezone.utc)):
        self._cfg = config
        self._cookies = cookie_provider
        self._favorites = favorites_client
        self._fetch = fetcher_fn
        self._store = watermark_store
        self._resolver = resolver
        self._failures = failure_store
        self._save = saver_fn
        self._now = now_fn

    def run_cycle(self) -> None:
        try:
            cookies = self._cookies.get_cookies()
        except Exception as e:  # noqa: BLE001 - daemon must not crash
            log.error("cookie pull failed: %s — skipping cycle", e)
            return
        if not cookies:
            log.error("no .zhihu.com cookies available — skipping cycle")
            return
        try:
            collections = self._resolver.resolve(self._cfg.targets, cookies)
        except Exception as e:  # noqa: BLE001 - resolver already degrades per-target; belt-and-suspenders
            log.error("target resolution failed: %s — skipping cycle", e)
            return
        for coll in collections:
            self._poll_collection(coll, cookies)

    def _floor(self, collection_id: str) -> datetime | None:
        floor = self._cfg.only_after
        if not self._cfg.backfill_on_first_run:
            baseline = self._store.get_baseline(collection_id)
            if baseline is None:
                baseline = self._now()
                self._store.set_baseline(collection_id, baseline)
            floor = max(d for d in (floor, baseline) if d is not None)
        return floor

    def _poll_collection(self, coll, cookies: dict) -> None:
        try:
            items = self._favorites.list_items(coll.id, cookies)
        except Exception as e:  # noqa: BLE001
            log.error("listing collection %s failed: %s", coll.id, e)
            return
        try:
            seen = self._store.load(coll.id)
            floor = self._floor(coll.id)
        except Exception as e:  # noqa: BLE001 - corrupt state must not crash the cycle
            log.error("loading state for collection %s failed: %s — skipping", coll.id, e)
            return
        cooldown_seconds = self._cfg.failure_cooldown_hours * 3600
        new_count = 0
        for item in items:
            if floor is not None and item.favorited_at is not None and item.favorited_at <= floor:
                continue  # favorited at/before the floor (only_after / first-run baseline)
            if item.key in seen:
                continue
            if self._failures.should_skip(coll.id, item.key):
                continue  # in 403 backoff cooldown
            try:
                doc = self._fetch(item.url, cookies)
                if doc is None:
                    self._failures.record_failure(
                        coll.id, item.key,
                        max_failures=self._cfg.max_consecutive_failures, cooldown_seconds=cooldown_seconds)
                    continue
                self._save(self._cfg.output_dir, coll.name, doc.title, item.url, doc.content_markdown)
            except Exception as e:  # noqa: BLE001 - one bad item must never abort the cycle
                log.error("processing item %s failed: %s", item.key, e)
                self._failures.record_failure(
                    coll.id, item.key,
                    max_failures=self._cfg.max_consecutive_failures, cooldown_seconds=cooldown_seconds)
                continue
            seen.add(item.key)
            self._store.save(coll.id, seen)
            self._failures.clear(coll.id, item.key)
            new_count += 1
        log.info("collection %s (%s): %d new item(s)", coll.id, coll.name, new_count)


def build_watcher(config: WatcherConfig) -> Watcher:
    favorites = FavoritesClient()
    return Watcher(
        config=config,
        cookie_provider=CookieProvider(config.cookie_source),
        favorites_client=favorites,
        fetcher_fn=default_fetch,
        watermark_store=WatermarkStore(config.state_dir),
        resolver=TargetResolver(favorites),
        failure_store=FailureStore(config.state_dir),
    )
