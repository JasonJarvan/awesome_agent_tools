"""Process-wide proactive rate-limiter + reactive throttle backoff for the engine's
bilibili.com-facing calls. Mirrors SP-2 Zhihu v1.2, generalized to wrap a callable because
bilibili calls RAISE on throttle (library ResponseCodeException/NetworkException; httpx
HTTPStatusError) rather than return a Response. See docs/superpowers/specs/2026-06-14-*.
"""
from __future__ import annotations
import threading
import time
import random
from dataclasses import dataclass, field
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

import httpx

# Injectable clock hooks (monkeypatched in tests for instant, deterministic runs)
_now = time.monotonic
_sleep = time.sleep
_rand = random.uniform

# Bilibili business codes meaning "throttled / slow down" (NOT 412 auth, NOT -101 credential).
_THROTTLE_CODES = frozenset({-509, -799})


@dataclass
class _Config:
    min_interval: float = 0.3                 # min seconds between request *starts* (proactive pacing)
    jitter: float = 0.2                       # add U(0, jitter) to each pacing/backoff wait
    max_retries: int = 3                      # reactive retries on a throttle signal
    backoff_base: float = 0.5                 # backoff = base * 2**attempt (+ jitter)
    throttle_codes: frozenset = field(default_factory=lambda: _THROTTLE_CODES)
    retry_http_statuses: tuple = (429,)       # HTTP statuses treated as throttle (honors Retry-After)
    enabled: bool = True                      # master switch for pacing+retry


_cfg = _Config()


def configure(*, min_interval=None, jitter=None, max_retries=None, backoff_base=None,
              throttle_codes=None, retry_http_statuses=None, enabled=None) -> None:
    """Tune the engine's built-in proactive rate-limiter + reactive throttle backoff (process-wide).

    Conservative defaults suit bulk crawling without tripping bilibili's burst-sensitive risk
    control. A single transcribe() is ~unaffected (the first call of a fresh process never waits).
    Pass ``enabled=False`` to disable both pacing and retry. Mirrors ``zhihu.configure(...)``.
    """
    if min_interval is not None: _cfg.min_interval = min_interval
    if jitter is not None: _cfg.jitter = jitter
    if max_retries is not None: _cfg.max_retries = max_retries
    if backoff_base is not None: _cfg.backoff_base = backoff_base
    if throttle_codes is not None: _cfg.throttle_codes = frozenset(throttle_codes)
    if retry_http_statuses is not None: _cfg.retry_http_statuses = tuple(retry_http_statuses)
    if enabled is not None: _cfg.enabled = enabled


class _RateLimiter:
    """Process-wide min-interval pacer. Ensures consecutive request *starts* are >= min_interval
    apart (+ optional jitter). A slow call that already took longer than min_interval incurs no
    extra wait, so a single transcribe()'s first call is ~unaffected while bursts get smoothed.
    Thread-safe."""

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


def _retry_after_seconds(resp: httpx.Response) -> float | None:
    """Parse a Retry-After header (delta-seconds or HTTP-date) into seconds, or None."""
    raw = resp.headers.get("retry-after")
    if not raw:
        return None
    raw = raw.strip()
    if raw.isdigit():
        return float(raw)
    try:
        when = parsedate_to_datetime(raw)
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        return max(0.0, (when - datetime.now(tz=timezone.utc)).total_seconds())
    except (TypeError, ValueError):
        return None


def _throttle_signal(exc: Exception) -> tuple[bool, float | None]:
    """Classify an exception raised by a bilibili.com-facing call as throttle-or-not.

    Returns (is_throttle, retry_after_seconds_or_None). Throttle == HTTP 429 (honors Retry-After)
    or a bilibili business code in `_cfg.throttle_codes`. Duck-types `.status`/`.code` so this
    module needs no hard `bilibili_api` import. 412 / -101 / anything else -> (False, None).
    """
    if isinstance(exc, httpx.HTTPStatusError):
        resp = exc.response
        if resp is not None and resp.status_code in _cfg.retry_http_statuses:
            return True, _retry_after_seconds(resp)
        return False, None
    status = getattr(exc, "status", None)              # bilibili_api NetworkException
    if isinstance(status, int) and status in _cfg.retry_http_statuses:
        return True, None
    code = getattr(exc, "code", None)                  # bilibili_api ResponseCodeException
    if isinstance(code, int) and code in _cfg.throttle_codes:
        return True, None
    return False, None


def paced(fn):
    """Run fn() under process-wide min-interval pacing + reactive backoff on a throttle signal.

    `fn` is a zero-arg callable performing ONE bilibili.com-facing request; it either returns a
    value or raises. Throttle exceptions (429 / codes -509/-799) trigger exponential backoff
    (honoring Retry-After) and a retry; NON-throttle exceptions (412, -101, ...) propagate
    immediately, unchanged. Returns fn()'s value, or re-raises the last throttle after max_retries.
    """
    last_exc: Exception | None = None
    for attempt in range(_cfg.max_retries + 1):
        if _cfg.enabled:
            _limiter.acquire(_cfg.min_interval, _cfg.jitter)
        try:
            return fn()
        except Exception as e:
            is_throttle, retry_after = _throttle_signal(e)
            if not _cfg.enabled or not is_throttle or attempt == _cfg.max_retries:
                raise
            delay = retry_after
            if delay is None:
                delay = _cfg.backoff_base * (2 ** attempt) + (_rand(0.0, _cfg.jitter) if _cfg.jitter else 0.0)
            _sleep(delay)
            last_exc = e
    raise last_exc  # pragma: no cover (unreachable: max_retries>=0 => loop always returns/raises)
