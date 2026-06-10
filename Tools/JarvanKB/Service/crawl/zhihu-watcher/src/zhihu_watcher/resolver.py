"""Resolve config.targets into the list[CollectionConfig] the v1 poll loop consumes.

Collection targets pass through; user targets are expanded via favorites_client (per cycle, so newly-created
collections are picked up and a single user-target failure degrades without crashing the daemon).
"""
from __future__ import annotations

import logging

from .config import CollectionConfig, UserTarget

log = logging.getLogger("zhihu_watcher.resolver")


class TargetResolver:
    def __init__(self, favorites_client):
        self._fc = favorites_client

    def resolve(self, targets: list, cookies: dict) -> list[CollectionConfig]:
        # collections first so an explicit name wins over a discovered title on id collision
        ordered = sorted(targets, key=lambda t: isinstance(t, UserTarget))
        out: list[CollectionConfig] = []
        seen_ids: set[str] = set()
        for t in ordered:
            try:
                resolved = self._resolve_one(t, cookies)
            except Exception as e:  # noqa: BLE001 - one bad target must not kill resolution
                log.error("resolving target %r failed: %s — skipping", t, e)
                continue
            for cc in resolved:
                if cc.id in seen_ids:
                    continue
                seen_ids.add(cc.id)
                out.append(cc)
        log.info("resolved %d target(s) -> %d collection(s)", len(targets), len(out))
        return out

    def _resolve_one(self, t, cookies: dict) -> list[CollectionConfig]:
        if isinstance(t, UserTarget):
            token = self._fc.get_current_url_token(cookies) if t.url_token == "me" else t.url_token
            res: list[CollectionConfig] = []
            for c in self._fc.list_user_collections(token, cookies):
                if c.is_default and not t.include_default:
                    continue
                if t.skip_empty and c.item_count == 0:
                    continue
                name = f"{t.name_prefix}{c.title}" if t.name_prefix else c.title
                res.append(CollectionConfig(id=str(c.id), name=name))
            return res
        return [t]  # already a CollectionConfig
