"""Persistent seen-id set, one JSON file per collection under state_dir.

The watcher loads the set once per collection per cycle, checks membership locally, and calls
save() after each successful fetch+save so the crash window is a single item.
"""
from __future__ import annotations

import json
import os
from pathlib import Path


class WatermarkStore:
    def __init__(self, state_dir: str):
        self._dir = Path(state_dir)

    def _path(self, collection_id: str) -> Path:
        return self._dir / f"seen-{collection_id}.json"

    def load(self, collection_id: str) -> set[str]:
        p = self._path(collection_id)
        if not p.exists():
            return set()
        return set(json.loads(p.read_text(encoding="utf-8")))

    def save(self, collection_id: str, seen: set[str]) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        final = self._path(collection_id)
        tmp = final.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(sorted(seen), ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, final)  # atomic on POSIX
