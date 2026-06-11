"""Per-folder persistent state: a fav_time high-watermark + a bvid seen-set.

One JSON file per folder under state_dir: {"watermark": int, "seen": [bvid, ...]}.
- seen-set (bvid): correctness/idempotency — a video is saved at most once.
- watermark (fav_time): early-stop optimization. Invariant: every item with fav_time > watermark
  has been saved. Advanced conservatively (next_watermark) so a failed item stays re-listable.
Saved after each successful item (1-item crash window) and again with the advanced watermark at
cycle end (mirrors SP-5a's immediate-persist posture).
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FolderState:
    watermark: int = 0
    seen: set[str] = field(default_factory=set)


def next_watermark(prev: int, listed: list[int], failed: list[int]) -> int:
    """§5 advance rule. listed = fav_times returned this cycle; failed = fav_times that failed fetch."""
    if failed:
        return min(failed) - 1          # keep every failure (and only those) re-listable next cycle
    if listed:
        return max(prev, max(listed))   # everything above is saved -> advance to newest
    return prev                         # nothing new -> hold


class WatermarkStore:
    def __init__(self, state_dir: str):
        self._dir = Path(state_dir)

    def _path(self, folder_id: str) -> Path:
        return self._dir / f"state-{folder_id}.json"

    def load(self, folder_id: str) -> FolderState:
        p = self._path(folder_id)
        if not p.exists():
            return FolderState()
        raw = json.loads(p.read_text(encoding="utf-8"))
        return FolderState(watermark=int(raw.get("watermark", 0)), seen=set(raw.get("seen", [])))

    def save(self, folder_id: str, state: FolderState) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        final = self._path(folder_id)
        tmp = final.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps({"watermark": state.watermark, "seen": sorted(state.seen)}, ensure_ascii=False),
            encoding="utf-8",
        )
        os.replace(tmp, final)  # atomic on POSIX
