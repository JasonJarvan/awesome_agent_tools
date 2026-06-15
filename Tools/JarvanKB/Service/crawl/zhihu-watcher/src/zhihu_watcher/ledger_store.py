"""Classification ledger — the authoritative local dedup for classify-enabled collections.

One JSON file per collection: <state_dir>/ledger-{collection_id}.json, keyed by item.key. Records SUCCESSES
only (a failed fetch/classify is never recorded -> it retries). Independent of any Zhihu API. sync_status /
sync_attempts are v1.3 forward-compat (written as local-only / 0, never read in v1.2).
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path


class LedgerStore:
    def __init__(self, state_dir: str):
        self._dir = Path(state_dir)

    def _path(self, collection_id: str) -> Path:
        return self._dir / f"ledger-{collection_id}.json"

    def _load(self, collection_id: str) -> dict:
        p = self._path(collection_id)
        if not p.exists():
            return {}
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}  # corrupt: treat as empty (never blocks the cycle)

    def _save(self, collection_id: str, data: dict) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        final = self._path(collection_id)
        tmp = final.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, final)  # atomic on POSIX

    def has(self, collection_id: str, key: str) -> bool:
        return key in self._load(collection_id)

    def record(self, collection_id: str, key: str, classified_folder: str, local_path: str,
               fav_time: datetime | None, classified_at: datetime) -> None:
        data = self._load(collection_id)
        data[key] = {
            "classified_folder": classified_folder,
            "local_path": local_path,
            "fav_time": fav_time.isoformat() if fav_time else None,
            "classified_at": classified_at.isoformat(),
            "sync_status": "local-only",
            "sync_attempts": 0,
        }
        self._save(collection_id, data)
