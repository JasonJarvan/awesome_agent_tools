"""Per-collection consecutive-failure counter with a time-window cooldown.

Separate from the seen-set (failed items are never 'seen'). After `max_failures` consecutive failures an item
is skipped until `now + cooldown_seconds`; any success clears it. Time-window (not cycle-count) so it survives
restarts and interval changes. `now_fn` is injected for tests.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Callable


class FailureStore:
    def __init__(self, state_dir: str, now_fn: Callable[[], float] = time.time):
        self._dir = Path(state_dir)
        self._now = now_fn

    def _path(self, collection_id: str) -> Path:
        return self._dir / f"failures-{collection_id}.json"

    def _load(self, collection_id: str) -> dict:
        p = self._path(collection_id)
        if not p.exists():
            return {}
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}  # corrupt file: treat as empty (never blocks the cycle)

    def _save(self, collection_id: str, data: dict) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        final = self._path(collection_id)
        tmp = final.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, final)

    def should_skip(self, collection_id: str, key: str) -> bool:
        rec = self._load(collection_id).get(key)
        if not rec:
            return False
        if rec.get("circuit_broken"):
            return True
        return self._now() < rec.get("skip_until", 0)

    def record_failure(self, collection_id: str, key: str, *, max_failures: int,
                       cooldown_seconds: float, circuit_break_threshold: int | None = None,
                       url: str = "", title: str = "", excerpt: str = "") -> None:
        data = self._load(collection_id)
        rec = data.get(key) or {"failures": 0, "skip_until": 0}
        rec["failures"] = int(rec.get("failures", 0)) + 1
        if url:
            rec["url"] = url
        if title:
            rec["title"] = title
        if excerpt:
            rec["excerpt"] = excerpt
        if rec["failures"] >= max_failures:
            rec["skip_until"] = self._now() + cooldown_seconds
        if circuit_break_threshold is not None and rec["failures"] >= circuit_break_threshold:
            rec["circuit_broken"] = True
        data[key] = rec
        self._save(collection_id, data)

    def circuit_broken_items(self, collection_id: str) -> list[dict]:
        return [{"key": k, **v} for k, v in self._load(collection_id).items() if v.get("circuit_broken")]

    def clear(self, collection_id: str, key: str) -> None:
        data = self._load(collection_id)
        if key in data:
            del data[key]
            self._save(collection_id, data)
