"""Orchestrate one poll cycle and wire the real components.

Collaborators are injected so the cycle is fully testable with fakes; build_watcher() supplies the
real implementations. The daemon must never crash — every failure path logs and continues. Per folder:
list (fav_time early-stop against the stored watermark) -> for each unseen video, fetch via the engine
and save -> advance the watermark per §5 (held below any failure so failures are retried).
"""
from __future__ import annotations

import logging

from .config import WatcherConfig
from .cookie_provider import CookieProvider
from .favorites_client import FavoritesClient
from .fetcher import FetchedDoc, FetcherFn, build_credential, make_fetcher
from .saver import save as default_save
from .watermark_store import FolderState, WatermarkStore, next_watermark

log = logging.getLogger("bilibili_watcher.watcher")


class Watcher:
    def __init__(self, config, cookie_provider, favorites_client,
                 fetcher_fn: FetcherFn, watermark_store: WatermarkStore, saver_fn=default_save):
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
        if not cookies or "SESSDATA" not in cookies:
            log.error("no bilibili.com SESSDATA available — skipping cycle")
            return
        credential = build_credential(cookies)
        for folder in self._cfg.folders:
            self._poll_folder(folder, cookies, credential)

    def _poll_folder(self, folder, cookies, credential) -> None:
        try:
            state = self._store.load(folder.id)
        except Exception as e:  # noqa: BLE001 - a corrupt state file must not crash the cycle
            log.error("loading state for folder %s failed: %s — skipping", folder.id, e)
            return
        try:
            items = self._favorites.list_items(folder.id, cookies, since_fav_time=state.watermark)
        except Exception as e:  # noqa: BLE001
            log.error("listing folder %s failed: %s", folder.id, e)
            return

        listed = [it.fav_time for it in items]
        failed: list[int] = []
        new_count = 0
        for item in items:
            if item.bvid in state.seen:
                continue
            try:
                doc = self._fetch(item.bvid, credential)
                if doc is None:
                    failed.append(item.fav_time)   # transcribe failed -> retry next cycle
                    continue
                self._save(self._cfg.output_dir, folder.name, doc.title, item.bvid, doc.markdown)
            except Exception as e:  # noqa: BLE001 - one bad item must never abort the cycle
                log.error("processing bvid %s failed: %s", item.bvid, e)
                failed.append(item.fav_time)
                continue
            state.seen.add(item.bvid)
            self._store.save(folder.id, state)     # persist seen immediately (1-item crash window)
            new_count += 1

        state.watermark = next_watermark(state.watermark, listed, failed)
        self._store.save(folder.id, state)
        log.info("folder %s (%s): %d new, watermark=%d", folder.id, folder.name, new_count, state.watermark)


def build_watcher(config: WatcherConfig) -> Watcher:
    from bilibili import BilibiliEngine, EngineConfig as _EngCfg
    engine = BilibiliEngine(_EngCfg(
        bn_base_url=config.engine.bn_base_url,
        provider_id=config.engine.provider_id,
        model_name=config.engine.model_name,
    ))
    return Watcher(
        config=config,
        cookie_provider=CookieProvider(config.cookie_source),
        favorites_client=FavoritesClient(),
        fetcher_fn=make_fetcher(engine, config.render),
        watermark_store=WatermarkStore(config.state_dir),
    )
