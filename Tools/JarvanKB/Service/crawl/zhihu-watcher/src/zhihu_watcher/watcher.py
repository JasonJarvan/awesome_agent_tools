"""Orchestrate one poll cycle and wire the real components.

Collaborators are injected so the cycle is fully testable with fakes; build_watcher() supplies the real ones.
The daemon must never crash — every failure path logs and continues.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Callable, Optional

from jarvankb_common.classify import existing_subfolders

from .attention import write_attention
from .classifier import classify_doc
from .config import WatcherConfig
from .cookie_provider import CookieProvider
from .failure_store import FailureStore
from .favorites_client import FavoritesClient
from .fetcher import FetchedDoc
from .fetcher import fetch as default_fetch
from .ledger_store import LedgerStore
from .resolver import TargetResolver
from .saver import save as default_save
from .watermark_store import WatermarkStore

log = logging.getLogger("zhihu_watcher.watcher")

FetcherFn = Callable[[str, dict], Optional[FetchedDoc]]
SaverFn = Callable[[str, str, str, str, str], str]


class Watcher:
    def __init__(self, config: WatcherConfig, cookie_provider, favorites_client, fetcher_fn: FetcherFn,
                 watermark_store: WatermarkStore, *, resolver, failure_store: FailureStore,
                 ledger_store: "LedgerStore | None" = None,
                 llm_client_factory: Callable[[str], object] | None = None,
                 saver_fn: SaverFn = default_save,
                 classify_fn=classify_doc, attention_fn=write_attention,
                 now_fn: Callable[[], datetime] = lambda: datetime.now(timezone.utc)):
        self._cfg = config
        self._cookies = cookie_provider
        self._favorites = favorites_client
        self._fetch = fetcher_fn
        self._store = watermark_store
        self._resolver = resolver
        self._failures = failure_store
        self._ledger = ledger_store
        self._llm_factory = llm_client_factory
        self._save = saver_fn
        self._classify = classify_fn
        self._attention = attention_fn
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
        except Exception as e:  # noqa: BLE001
            log.error("target resolution failed: %s — skipping cycle", e)
            return

        client = None
        subfolders: list[str] = []
        if any(getattr(c, "classify", False) for c in collections):
            try:
                # config validation guarantees cfg.classify is set when a classify target exists
                client = self._llm_factory(self._cfg.classify.llm_profile) if self._llm_factory else None
                subfolders = existing_subfolders(self._cfg.output_dir)
            except Exception as e:  # noqa: BLE001 - missing creds etc.: skip classify targets, keep others
                log.error("LLM client unavailable: %s — classify targets will be skipped this cycle", e)
                client = None
                subfolders = []

        for coll in collections:
            self._poll_collection(coll, cookies, client, subfolders)

        try:
            broken = []
            for coll in collections:
                for broken_item in self._failures.circuit_broken_items(coll.id):
                    broken.append({**broken_item, "collection": coll.name})
            self._attention(self._cfg.output_dir, broken)
        except Exception as e:  # noqa: BLE001 - attention render must never abort a cycle
            log.error("attention render failed: %s", e)

    def _floor(self, collection_id: str) -> datetime | None:
        floor = self._cfg.only_after
        if not self._cfg.backfill_on_first_run:
            baseline = self._store.get_baseline(collection_id)
            if baseline is None:
                baseline = self._now()
                self._store.set_baseline(collection_id, baseline)
            floor = max(d for d in (floor, baseline) if d is not None)
        return floor

    def _poll_collection(self, coll, cookies: dict, client, subfolders: list[str]) -> None:
        classify_on = getattr(coll, "classify", False)
        if classify_on and (client is None or self._ledger is None):
            log.warning("collection %s wants classify but no LLM/ledger available — skipping", coll.id)
            return
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
                continue
            if classify_on:
                if self._ledger.has(coll.id, item.key):
                    continue
            elif item.key in seen:
                continue
            if self._failures.should_skip(coll.id, item.key):
                continue
            try:
                doc = self._fetch(item.url, cookies)
                if doc is None:
                    self._record_fail(coll.id, item, cooldown_seconds)
                    continue
                if classify_on:
                    # ledger is the dedup store for classify collections — deliberately NO seen-set update
                    folder = self._classify(doc, subfolders, client, self._cfg.classify)
                    path = self._save(self._cfg.output_dir, folder, doc.title, item.url, doc.content_markdown)
                    self._ledger.record(coll.id, item.key, folder, path, item.favorited_at, self._now())
                else:
                    self._save(self._cfg.output_dir, coll.name, doc.title, item.url, doc.content_markdown)
                    seen.add(item.key)
                    self._store.save(coll.id, seen)
            except Exception as e:  # noqa: BLE001 - one bad item must never abort the cycle
                log.error("processing item %s failed: %s", item.key, e)
                self._record_fail(coll.id, item, cooldown_seconds)
                continue
            self._failures.clear(coll.id, item.key)
            new_count += 1
        log.info("collection %s (%s): %d new item(s)", coll.id, coll.name, new_count)

    def _record_fail(self, collection_id: str, item, cooldown_seconds: float) -> None:
        self._failures.record_failure(
            collection_id, item.key,
            max_failures=self._cfg.max_consecutive_failures, cooldown_seconds=cooldown_seconds,
            circuit_break_threshold=self._cfg.circuit_break_threshold,
            url=item.url, title=item.title, excerpt=item.excerpt)


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
