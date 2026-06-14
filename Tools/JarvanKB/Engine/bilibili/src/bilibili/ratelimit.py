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
