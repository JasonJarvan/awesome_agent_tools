from __future__ import annotations
import threading
import time
import random
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
import httpx

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

NAV_HEADERS = {
    "User-Agent": _UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.zhihu.com/",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Upgrade-Insecure-Requests": "1",
}

API_HEADERS = {
    "User-Agent": _UA,
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.zhihu.com/",
    "x-requested-with": "fetch",
}

# Injectable clock hooks (monkeypatched in tests for instant, deterministic runs)
_now = time.monotonic
_sleep = time.sleep
_rand = random.uniform


@dataclass
class _Config:
    min_interval: float = 0.3          # min seconds between request *starts* (proactive pacing)
    jitter: float = 0.2                # add U(0, jitter) to each pacing/backoff wait
    max_retries: int = 3               # reactive retries on a retryable status
    backoff_base: float = 0.5          # backoff = base * 2**attempt (+ jitter)
    retry_statuses: tuple = (403, 429)
    enabled: bool = True               # master switch for pacing+retry


_cfg = _Config()


def configure(*, min_interval=None, jitter=None, max_retries=None, backoff_base=None,
              retry_statuses=None, enabled=None) -> None:
    """Tune the engine's built-in proactive rate-limiter + reactive backoff (process-wide).

    Conservative defaults suit bulk crawling without tripping Zhihu's burst-sensitive throttle
    (empirically ~2 req/s sequential is safe). A single-URL caller is ~unaffected (one request
    never waits). Pass ``enabled=False`` to disable both pacing and retry.
    """
    if min_interval is not None: _cfg.min_interval = min_interval
    if jitter is not None: _cfg.jitter = jitter
    if max_retries is not None: _cfg.max_retries = max_retries
    if backoff_base is not None: _cfg.backoff_base = backoff_base
    if retry_statuses is not None: _cfg.retry_statuses = tuple(retry_statuses)
    if enabled is not None: _cfg.enabled = enabled


class _RateLimiter:
    """Process-wide min-interval pacer. Ensures consecutive request *starts* are >= min_interval
    apart (+ optional jitter). A slow request that already took longer than min_interval incurs no
    extra wait, so single-URL callers are ~unaffected while bursts get smoothed. Thread-safe."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._last = 0.0

    def acquire(self, min_interval: float, jitter: float) -> None:
        with self._lock:
            extra = _rand(0.0, jitter) if jitter else 0.0
            target = self._last + min_interval + extra
            now = _now()
            if now < target:
                _sleep(target - now)
            self._last = _now()


_limiter = _RateLimiter()


def get_page(url: str, *, cookies: dict, timeout: float = 30.0) -> tuple[int, str]:
    """GET a Zhihu page as a browser navigation. Returns (status_code, text). Does not raise on 4xx."""
    resp = httpx.get(url, cookies=cookies, headers=NAV_HEADERS, timeout=timeout,
                     follow_redirects=True, trust_env=False)
    return resp.status_code, resp.text


def get_api_answer(answer_id: str, *, cookies: dict, timeout: float = 30.0) -> dict:
    """Unsigned /api/v4 answer fallback. Raises on non-2xx."""
    url = f"https://www.zhihu.com/api/v4/answers/{answer_id}?include=content"
    resp = httpx.get(url, cookies=cookies, headers=API_HEADERS, timeout=timeout,
                     follow_redirects=True, trust_env=False)
    resp.raise_for_status()
    return resp.json()
