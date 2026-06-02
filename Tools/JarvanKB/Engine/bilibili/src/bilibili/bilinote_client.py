"""HTTP client for a self-hosted BiliNote instance. The engine's only window into BN."""
from __future__ import annotations
import time
from typing import Optional

import httpx

from .errors import BiliNoteUnavailable, TranscriptionFailed, TranscriptionTimeout

_TERMINAL_OK = "SUCCESS"
_TERMINAL_FAIL = "FAILED"


class BiliNoteClient:
    def __init__(self, base_url: str, provider_id: str, model_name: str,
                 poll_interval_s: int = 3, poll_timeout_s: int = 600,
                 style: str = "summary", http: Optional[httpx.Client] = None):
        self.base_url = base_url.rstrip("/")
        self.provider_id = provider_id
        self.model_name = model_name
        self.poll_interval_s = poll_interval_s
        self.poll_timeout_s = poll_timeout_s
        self.style = style
        self._http = http or httpx.Client(base_url=self.base_url, timeout=30)

    def _unwrap(self, resp: httpx.Response) -> dict:
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("code") != 0:
            raise TranscriptionFailed(f"BiliNote error: {payload.get('msg')}")
        return payload.get("data") or {}

    def health_check(self) -> None:
        try:
            resp = self._http.get("/api/sys_check")
            resp.raise_for_status()
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.HTTPStatusError) as e:
            raise BiliNoteUnavailable(f"BiliNote not reachable at {self.base_url}: {e}") from e

    def push_cookie(self, cookie: str, platform: str = "bilibili") -> None:
        resp = self._http.post("/api/update_downloader_cookie",
                               json={"platform": platform, "cookie": cookie})
        self._unwrap(resp)

    def generate_note(self, video_url: str, prefetched_transcript: Optional[dict] = None) -> str:
        body = {
            "video_url": video_url,
            "platform": "bilibili",
            "quality": "fast",
            "model_name": self.model_name,
            "provider_id": self.provider_id,
            "format": [],
            "style": self.style,
            "screenshot": False,
            "link": False,
        }
        if prefetched_transcript is not None:
            body["prefetched_transcript"] = prefetched_transcript
        data = self._unwrap(self._http.post("/api/generate_note", json=body))
        return data["task_id"]

    def poll(self, task_id: str) -> dict:
        deadline = self.poll_timeout_s
        waited = 0
        while True:
            data = self._unwrap(self._http.get(f"/api/task_status/{task_id}"))
            status = data.get("status")
            if status == _TERMINAL_OK:
                return data["result"]
            if status == _TERMINAL_FAIL:
                raise TranscriptionFailed(data.get("message") or "BiliNote task FAILED")
            if waited >= deadline:
                raise TranscriptionTimeout(f"task {task_id} not done after {deadline}s (last={status})")
            time.sleep(self.poll_interval_s)
            waited += max(self.poll_interval_s, 1)

    def transcribe(self, video_url: str, prefetched_transcript: Optional[dict] = None):
        """Returns (transcript_dict_or_None, summary_markdown)."""
        self.health_check()
        task_id = self.generate_note(video_url, prefetched_transcript)
        note = self.poll(task_id)
        return note.get("transcript"), note.get("markdown")
