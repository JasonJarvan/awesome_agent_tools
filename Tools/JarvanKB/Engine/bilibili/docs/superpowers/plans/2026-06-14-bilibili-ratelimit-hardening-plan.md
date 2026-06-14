# Bilibili Engine v1.x — Rate-Limit Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a process-wide **proactive rate-limiter** + **reactive throttle backoff** at the engine's bilibili.com chokepoints, so bulk consumers (SP-5b watcher) self-pace and transient throttling self-recovers, while a single `transcribe()` is ~unaffected — mirroring SP-2 Zhihu v1.2, non-breaking.

**Architecture:** A new `ratelimit.py` module exposes a process-wide `_RateLimiter` singleton + a `paced(fn)` wrapper. The **three** bilibili.com-facing calls — `metadata._get_info_raw` (`get_info`), `subtitle._get_tracks_raw` (`get_subtitle`), `subtitle._get_body_raw` (subtitle-CDN `httpx.get`) — route through `paced()` *inside their existing thin wrappers* (signatures + the tests that patch them stay untouched). Unlike SP-2's `_request()->Response`, `paced(fn)` wraps an arbitrary callable because bilibili calls **raise** on throttle (library `ResponseCodeException.code`/`NetworkException.status`; httpx `HTTPStatusError`) rather than return a Response. Backoff fires on **HTTP 429 + bilibili codes `-509`/`-799`** honoring `Retry-After`; everything else (incl. **412**, `-101`) propagates immediately → existing ASR/credential fallbacks unchanged. BN-local calls in `bilinote_client.py` are **NOT** paced (architecture memory §B站链路: 412/downloads are BN-internal yt-dlp/playurl, *below* the engine). Tunable via a new module-level `bilibili.configure(...)`; conservative defaults mirror deployed Zhihu. NON-BREAKING: the v1 frozen contract (`interface.md §3`) is byte-identical.

**Tech Stack:** Python ≥3.11, httpx, `threading.Lock`, `bilibili-api-python>=17,<18`, pytest (no pytest-httpx — tests use `unittest.mock`/monkeypatch + real `httpx.Response` objects). Injectable clock hooks (`_now`/`_sleep`/`_rand`) for deterministic, instant tests.

**Lane:** **full** (engine module change; net-new public surface `configure`; produces a §B站链路 RepoMem promotion). Spec folded into the compressed brainstorm at `../specs/2026-06-14-SP-4a-bilibili-ratelimit-design.zh.md`.

> **WORKTREE NOTE:** all pytest runs use `PYTHONPATH=src python3 -m pytest ...` from `Engine/bilibili/`, so the worktree's own `src/` overrides the editable install that points at the main checkout. Commits use explicit pathspec (`git commit -m "..." -- <paths>`); commit prefix `feat(bili-ratelimit):` / `docs(bili-ratelimit):`.

---

## File Structure

- `src/bilibili/ratelimit.py` (**create**) — `_now/_sleep/_rand` hooks, `_THROTTLE_CODES`, `_Config` + `configure()`, `_RateLimiter` singleton `_limiter`, `_retry_after_seconds()`, `_throttle_signal()`, `paced()`.
- `src/bilibili/__init__.py` (modify) — export `configure`.
- `src/bilibili/metadata.py` (modify) — route `_get_info_raw` through `ratelimit.paced`.
- `src/bilibili/subtitle.py` (modify) — route `_get_tracks_raw` + `_get_body_raw` through `ratelimit.paced`.
- `tests/conftest.py` (**create**) — autouse fixture: reset `_limiter`, disable pacing, noop `_sleep` (keep 59 baseline fast/deterministic).
- `tests/test_ratelimit.py` (**create**) — limiter, classifier, `paced()`, `configure()` unit tests.
- `tests/test_metadata.py` (modify) — wiring test: `_get_info_raw` routes through `paced`.
- `tests/test_subtitle.py` (modify) — wiring tests: `_get_tracks_raw` routes through `paced`; `_get_body_raw` retries a 429.
- `tests/test_public_api.py` (modify) — non-breaking: `configure` exported + frozen symbols intact.
- `docs/interface.md` (modify) — add §8 "内置限流与重试（v1.x，非破坏性）".

---

### Task 1: `_Config` + `configure()` (module-level, conservative defaults, exported)

**Files:**
- Create: `src/bilibili/ratelimit.py`
- Modify: `src/bilibili/__init__.py`
- Test: `tests/test_ratelimit.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ratelimit.py (new file)
def test_default_config_is_conservative():
    from bilibili import ratelimit
    c = ratelimit._Config()
    assert c.min_interval == 0.3 and c.jitter == 0.2
    assert c.max_retries == 3 and c.backoff_base == 0.5
    assert c.throttle_codes == frozenset({-509, -799})
    assert c.retry_http_statuses == (429,)
    assert c.enabled is True


def test_configure_updates_and_restores():
    from bilibili import ratelimit
    from bilibili import configure
    saved = (ratelimit._cfg.min_interval, ratelimit._cfg.max_retries, ratelimit._cfg.enabled)
    try:
        configure(min_interval=1.25, max_retries=5, enabled=False)
        assert ratelimit._cfg.min_interval == 1.25
        assert ratelimit._cfg.max_retries == 5
        assert ratelimit._cfg.enabled is False
        configure(throttle_codes=[-509, -799, -412])
        assert ratelimit._cfg.throttle_codes == frozenset({-509, -799, -412})
    finally:
        ratelimit._cfg.min_interval, ratelimit._cfg.max_retries, ratelimit._cfg.enabled = saved
        ratelimit._cfg.throttle_codes = frozenset({-509, -799})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m pytest tests/test_ratelimit.py -k "default_config or configure_updates" -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'bilibili.ratelimit'` / `cannot import name 'configure'`.

- [ ] **Step 3: Write minimal implementation**

Create `src/bilibili/ratelimit.py`:

```python
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
```

In `src/bilibili/__init__.py` — add the import after the `.engine` import and add to `__all__`:

```python
from .engine import BilibiliEngine, transcribe
from .ratelimit import configure
```
and add `"configure",` to the `__all__` list (next to `"transcribe"`).

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m pytest tests/test_ratelimit.py -k "default_config or configure_updates" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(bili-ratelimit): module-level configure() + _Config (mirror zhihu defaults)" -- \
  src/bilibili/ratelimit.py src/bilibili/__init__.py tests/test_ratelimit.py
```

---

### Task 2: `_RateLimiter` — proactive pacing with injectable clock (copy SP-2)

**Files:**
- Modify: `src/bilibili/ratelimit.py`
- Test: `tests/test_ratelimit.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ratelimit.py (append)
def test_rate_limiter_paces_second_call(monkeypatch):
    from bilibili import ratelimit
    clock = {"t": 1000.0}
    slept = []
    monkeypatch.setattr(ratelimit, "_now", lambda: clock["t"])
    monkeypatch.setattr(ratelimit, "_sleep", lambda s: (slept.append(s), clock.__setitem__("t", clock["t"] + s)))
    monkeypatch.setattr(ratelimit, "_rand", lambda a, b: 0.0)   # zero jitter -> deterministic
    lim = ratelimit._RateLimiter()
    lim.acquire(min_interval=0.5, jitter=0.0)   # first call: last=0 -> target far in past -> no sleep
    assert slept == []
    lim.acquire(min_interval=0.5, jitter=0.0)   # immediate second call -> must wait the full interval
    assert slept == [0.5]


def test_rate_limiter_no_wait_when_enough_time_elapsed(monkeypatch):
    from bilibili import ratelimit
    clock = {"t": 1000.0}
    slept = []
    monkeypatch.setattr(ratelimit, "_now", lambda: clock["t"])
    monkeypatch.setattr(ratelimit, "_sleep", lambda s: slept.append(s))
    monkeypatch.setattr(ratelimit, "_rand", lambda a, b: 0.0)
    lim = ratelimit._RateLimiter()
    lim.acquire(0.5, 0.0)
    clock["t"] += 2.0          # 2s passes (e.g. a slow get_info) -> already past interval
    lim.acquire(0.5, 0.0)
    assert slept == []         # no extra pacing when the call itself was slow enough
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m pytest tests/test_ratelimit.py -k "rate_limiter" -v`
Expected: FAIL — `module 'bilibili.ratelimit' has no attribute '_RateLimiter'`.

- [ ] **Step 3: Write minimal implementation**

Add to `src/bilibili/ratelimit.py` (after `_cfg = _Config()`):

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m pytest tests/test_ratelimit.py -k "rate_limiter" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(bili-ratelimit): _RateLimiter proactive min-interval pacer (injectable clock)" -- \
  src/bilibili/ratelimit.py tests/test_ratelimit.py
```

---

### Task 3: `_retry_after_seconds` + `_throttle_signal` — the throttle classifier

**Files:**
- Modify: `src/bilibili/ratelimit.py`
- Test: `tests/test_ratelimit.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ratelimit.py (append)
import httpx


def _http_status_error(status, headers=None):
    req = httpx.Request("GET", "https://api.bilibili.com/x/web-interface/view")
    resp = httpx.Response(status, headers=headers or {}, request=req)
    return httpx.HTTPStatusError(f"{status}", request=req, response=resp)


def test_throttle_signal_http_429_with_retry_after():
    from bilibili import ratelimit
    is_t, ra = ratelimit._throttle_signal(_http_status_error(429, {"Retry-After": "12"}))
    assert is_t is True and ra == 12.0


def test_throttle_signal_http_412_is_not_throttle():
    from bilibili import ratelimit
    is_t, ra = ratelimit._throttle_signal(_http_status_error(412))
    assert is_t is False and ra is None


def test_throttle_signal_library_network_429():
    from bilibili import ratelimit
    from bilibili_api.exceptions import NetworkException
    is_t, ra = ratelimit._throttle_signal(NetworkException(429, "too many"))
    assert is_t is True and ra is None


def test_throttle_signal_response_code_509():
    from bilibili import ratelimit
    from bilibili_api.exceptions import ResponseCodeException
    is_t, _ = ratelimit._throttle_signal(ResponseCodeException(-509, "请求过于频繁"))
    assert is_t is True


def test_throttle_signal_response_code_minus_412_and_101_pass_through():
    from bilibili import ratelimit
    from bilibili_api.exceptions import ResponseCodeException
    assert ratelimit._throttle_signal(ResponseCodeException(-412, "risk"))[0] is False
    assert ratelimit._throttle_signal(ResponseCodeException(-101, "not logged in"))[0] is False


def test_throttle_signal_generic_exception_pass_through():
    from bilibili import ratelimit
    assert ratelimit._throttle_signal(ValueError("boom")) == (False, None)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m pytest tests/test_ratelimit.py -k "throttle_signal" -v`
Expected: FAIL — `module 'bilibili.ratelimit' has no attribute '_throttle_signal'`.

- [ ] **Step 3: Write minimal implementation**

Add to `src/bilibili/ratelimit.py` (after `_limiter = _RateLimiter()`):

```python
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


def _throttle_signal(exc: BaseException) -> tuple[bool, float | None]:
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m pytest tests/test_ratelimit.py -k "throttle_signal" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(bili-ratelimit): throttle classifier (429+Retry-After, codes -509/-799; 412 passes through)" -- \
  src/bilibili/ratelimit.py tests/test_ratelimit.py
```

---

### Task 4: `paced(fn)` — pace-before + reactive backoff on throttle

**Files:**
- Modify: `src/bilibili/ratelimit.py`
- Test: `tests/test_ratelimit.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ratelimit.py (append)
def test_paced_retries_429_then_succeeds(monkeypatch):
    from bilibili import ratelimit
    monkeypatch.setattr(ratelimit, "_sleep", lambda s: None)
    monkeypatch.setattr(ratelimit, "_rand", lambda a, b: 0.0)
    ratelimit._limiter._last = 0.0
    ratelimit.configure(min_interval=0.0, jitter=0.0, max_retries=3, enabled=True)
    calls = {"n": 0}
    def fn():
        calls["n"] += 1
        if calls["n"] == 1:
            raise _http_status_error(429)
        return "ok"
    assert ratelimit.paced(fn) == "ok"
    assert calls["n"] == 2


def test_paced_retries_throttle_code_then_succeeds(monkeypatch):
    from bilibili import ratelimit
    from bilibili_api.exceptions import ResponseCodeException
    monkeypatch.setattr(ratelimit, "_sleep", lambda s: None)
    monkeypatch.setattr(ratelimit, "_rand", lambda a, b: 0.0)
    ratelimit._limiter._last = 0.0
    ratelimit.configure(min_interval=0.0, jitter=0.0, max_retries=3, enabled=True)
    calls = {"n": 0}
    def fn():
        calls["n"] += 1
        if calls["n"] == 1:
            raise ResponseCodeException(-509, "请求过于频繁")
        return {"bvid": "BV1x"}
    assert ratelimit.paced(fn) == {"bvid": "BV1x"}
    assert calls["n"] == 2


def test_paced_honors_retry_after(monkeypatch):
    from bilibili import ratelimit
    waits = []
    monkeypatch.setattr(ratelimit, "_sleep", lambda s: waits.append(s))
    monkeypatch.setattr(ratelimit, "_rand", lambda a, b: 0.0)
    ratelimit._limiter._last = 0.0
    ratelimit.configure(min_interval=0.0, jitter=0.0, max_retries=3, backoff_base=0.5, enabled=True)
    calls = {"n": 0}
    def fn():
        calls["n"] += 1
        if calls["n"] == 1:
            raise _http_status_error(429, {"Retry-After": "12"})
        return "ok"
    assert ratelimit.paced(fn) == "ok"
    assert 12 in waits            # honored Retry-After, not the 0.5 backoff


def test_paced_propagates_non_throttle_immediately(monkeypatch):
    from bilibili import ratelimit
    monkeypatch.setattr(ratelimit, "_sleep", lambda s: None)
    ratelimit._limiter._last = 0.0
    ratelimit.configure(min_interval=0.0, jitter=0.0, max_retries=3, enabled=True)
    calls = {"n": 0}
    def fn():
        calls["n"] += 1
        raise _http_status_error(412)     # auth signal — must NOT retry
    import pytest
    with pytest.raises(httpx.HTTPStatusError):
        ratelimit.paced(fn)
    assert calls["n"] == 1                # called exactly once, no backoff


def test_paced_gives_up_after_max_retries(monkeypatch):
    from bilibili import ratelimit
    monkeypatch.setattr(ratelimit, "_sleep", lambda s: None)
    monkeypatch.setattr(ratelimit, "_rand", lambda a, b: 0.0)
    ratelimit._limiter._last = 0.0
    ratelimit.configure(min_interval=0.0, jitter=0.0, max_retries=3, enabled=True)
    calls = {"n": 0}
    def fn():
        calls["n"] += 1
        raise _http_status_error(429)
    import pytest
    with pytest.raises(httpx.HTTPStatusError):
        ratelimit.paced(fn)
    assert calls["n"] == 4                # initial + 3 retries
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m pytest tests/test_ratelimit.py -k "paced" -v`
Expected: FAIL — `module 'bilibili.ratelimit' has no attribute 'paced'`.

- [ ] **Step 3: Write minimal implementation**

Add to `src/bilibili/ratelimit.py` (after `_throttle_signal`):

```python
def paced(fn):
    """Run fn() under process-wide min-interval pacing + reactive backoff on a throttle signal.

    `fn` is a zero-arg callable performing ONE bilibili.com-facing request; it either returns a
    value or raises. Throttle exceptions (429 / codes -509/-799) trigger exponential backoff
    (honoring Retry-After) and a retry; NON-throttle exceptions (412, -101, ...) propagate
    immediately, unchanged. Returns fn()'s value, or re-raises the last throttle after max_retries.
    """
    last_exc: BaseException | None = None
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m pytest tests/test_ratelimit.py -k "paced" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(bili-ratelimit): paced() wrapper — pace + backoff on throttle, propagate the rest" -- \
  src/bilibili/ratelimit.py tests/test_ratelimit.py
```

---

### Task 5: Wire the 3 bilibili-facing calls + autouse conftest (keep 59 baseline green)

**Files:**
- Modify: `src/bilibili/metadata.py`
- Modify: `src/bilibili/subtitle.py`
- Create: `tests/conftest.py`
- Test: `tests/test_metadata.py`, `tests/test_subtitle.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_metadata.py (append)
def test_get_info_raw_routes_through_paced(monkeypatch):
    from bilibili import metadata, ratelimit
    from bilibili.url_parser import VideoRef
    seen = {}
    def fake_paced(fn):
        seen["ok"] = True                    # routed through paced; fn() never run -> no network
        return {"bvid": "BV1x", "aid": 1, "cid": 1, "owner": {}}
    monkeypatch.setattr(ratelimit, "paced", fake_paced)
    out = metadata._get_info_raw(VideoRef(bvid="BV1x", aid=None, part=None), None)
    assert seen.get("ok") is True and out["bvid"] == "BV1x"
```

```python
# tests/test_subtitle.py (append)
import httpx as _httpx


def test_get_tracks_raw_routes_through_paced(monkeypatch):
    from bilibili import subtitle, ratelimit
    seen = {}
    def fake_paced(fn):
        seen["ok"] = True
        return [{"lan": "ai-zh", "subtitle_url": "//x"}]
    monkeypatch.setattr(ratelimit, "paced", fake_paced)
    out = subtitle._get_tracks_raw("BV1x", 2, None)
    assert seen.get("ok") is True and out[0]["lan"] == "ai-zh"


def test_get_body_raw_retries_transient_429(monkeypatch):
    from bilibili import subtitle, ratelimit
    ratelimit._limiter._last = 0.0
    monkeypatch.setattr(ratelimit, "_sleep", lambda s: None)
    monkeypatch.setattr(ratelimit, "_rand", lambda a, b: 0.0)
    ratelimit.configure(min_interval=0.0, jitter=0.0, max_retries=2, enabled=True)
    req = _httpx.Request("GET", "https://x/sub.json")
    responses = [
        _httpx.Response(429, request=req),
        _httpx.Response(200, json={"body": [{"from": 0.0, "to": 1.0, "content": "你好"}]}, request=req),
    ]
    monkeypatch.setattr(subtitle.httpx, "get", lambda *a, **k: responses.pop(0))
    body = subtitle._get_body_raw("//x/sub.json", None)
    assert body == [{"from": 0.0, "to": 1.0, "content": "你好"}]   # 429 retried -> recovered
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=src python3 -m pytest tests/test_metadata.py::test_get_info_raw_routes_through_paced tests/test_subtitle.py -k "routes_through_paced or retries_transient_429" -v`
Expected: FAIL — `metadata`/`subtitle` have no `ratelimit` attribute; `_get_body_raw` calls `httpx.get` directly (no retry) so the first 429 raises.

- [ ] **Step 3: Write minimal implementation**

In `src/bilibili/metadata.py` — add import after the existing `.url_parser` import:

```python
from . import ratelimit
```

Replace the `return` line of `_get_info_raw` (currently `return asyncio.run(_run())`):

```python
    return ratelimit.paced(lambda: asyncio.run(_run()))
```

In `src/bilibili/subtitle.py` — add import after the `from .models import ...` line:

```python
from . import ratelimit
```

Replace the `return` line of `_get_tracks_raw` (currently `return asyncio.run(_run())`):

```python
    return ratelimit.paced(lambda: asyncio.run(_run()))
```

Replace the body of `_get_body_raw` (the three lines after building `headers`) — wrap the existing GET + raise + json in a local callable routed through `paced`:

```python
def _get_body_raw(subtitle_url: str, cred: Optional[BilibiliCredential]) -> list[dict]:
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.bilibili.com"}
    if cred and cred.sessdata:
        headers["Cookie"] = cred.to_cookie_string()

    def _do() -> list[dict]:
        resp = httpx.get(normalize_url(subtitle_url), headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.json().get("body") or []

    return ratelimit.paced(_do)
```

Create `tests/conftest.py`:

```python
import pytest
from bilibili import ratelimit


@pytest.fixture(autouse=True)
def _reset_engine_pacing(monkeypatch):
    # default OFF in tests: no real sleeps, no cross-test limiter state; tests that exercise
    # pacing/retry opt back in via ratelimit.configure(enabled=True, ...) + their own monkeypatch.
    monkeypatch.setattr(ratelimit, "_sleep", lambda s: None)
    ratelimit._limiter._last = 0.0
    saved = ratelimit._cfg
    ratelimit._cfg = ratelimit._Config(enabled=False)
    yield
    ratelimit._cfg = saved
```

- [ ] **Step 4: Run the new tests + FULL baseline**

Run: `PYTHONPATH=src python3 -m pytest tests/test_metadata.py tests/test_subtitle.py -v && PYTHONPATH=src python3 -m pytest -q`
Expected: new tests PASS; **all prior 59 + new tests green** (existing tests patch the wrappers or run with pacing disabled, so behavior is identical), suite still ~1s.

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(bili-ratelimit): route get_info/get_subtitle/subtitle-body through paced(); conftest disables pacing in tests" -- \
  src/bilibili/metadata.py src/bilibili/subtitle.py tests/conftest.py tests/test_metadata.py tests/test_subtitle.py
```

---

### Task 6: Non-breaking contract test + docs + full suite + live smoke (verification gate)

**Files:**
- Modify: `tests/test_public_api.py`
- Modify: `docs/interface.md`
- Smoke: throwaway under `Engine/bilibili/` (BN reachable at `127.0.0.1:3015`); cookies via gitignored fixture if a subtitle path is exercised — NOT committed.

- [ ] **Step 1: Write the non-breaking contract test**

```python
# tests/test_public_api.py (append)
def test_configure_is_exported_and_contract_intact():
    import bilibili
    assert hasattr(bilibili, "configure") and callable(bilibili.configure)
    assert "configure" in bilibili.__all__
    # additive: the v1 frozen contract symbols are all still exported
    for name in ("BilibiliEngine", "transcribe", "BilibiliCredential", "EngineConfig",
                 "RenderOptions", "RenderedOutput", "BilibiliResult", "BilibiliMetadata",
                 "Transcript", "TranscriptSegment"):
        assert hasattr(bilibili, name), f"frozen contract symbol missing: {name}"
```

- [ ] **Step 2: Run it**

Run: `PYTHONPATH=src python3 -m pytest tests/test_public_api.py::test_configure_is_exported_and_contract_intact -v`
Expected: PASS (Task 1 already exported `configure`).

- [ ] **Step 3: Update `docs/interface.md`** — insert a new section after §7 (before any later sections), numbered to fit:

```markdown
## 8. 内置限流与重试（v1.x，非破坏性）

引擎对**自身面向 bilibili.com 的出站调用**（`get_info` 元数据 / `get_subtitle` 字幕轨 / 字幕正文 CDN
下载）内置 **主动限流（请求间最小间隔 + 抖动，进程内共享）** 与 **被动重试**：对 **HTTP 429** 及 bilibili
业务码 **`-509`/`-799`**（「请求过于频繁」类）按指数退避重试，若响应含 `Retry-After` 则遵从。目的：批量
消费者（SP-5b Watcher）不再因突发触发 B站风控，瞬时节流自动恢复；单次 `transcribe()` 几乎无感（新进程
首个调用不等待，字幕命中路径至多多等 ~2×min_interval，被 BN 总结耗时淹没）。

**不限流的:** `bilinote_client.py` 的 BN 本地调用（`127.0.0.1`，非 bilibili 调用）；BN 内部 yt-dlp/playurl
下载位于引擎请求路径之下，归 BN/ops 侧。**`412` 不视作节流**（匿名 playurl 鉴权信号，BN-412，引擎照旧穿透
降级到 ASR）；`-101`（未登录）同理穿透 → `CredentialError` 路径不变。

默认值保守，可经模块级 `configure()` 调整或关闭，**不改变 `transcribe()` 签名与 `BilibiliResult`/冻结契约**：

​```python
from bilibili import configure
configure(min_interval=0.3, jitter=0.2, max_retries=3, backoff_base=0.5,
          throttle_codes=[-509, -799], retry_http_statuses=[429], enabled=True)
configure(enabled=False)   # 完全关闭限流+重试
​```

> 机制镜像知乎引擎（SP-2 v1.2 `Engine/zhihu/docs/interface.md §11`），但因 bilibili 调用「抛异常」而非
> 「返回 Response」，收口形状是包装 callable 的 `ratelimit.paced(fn)`。
```

- [ ] **Step 4: Full unit suite**

Run: `PYTHONPATH=src python3 -m pytest -q` (from `Engine/bilibili/`)
Expected: all green (59 baseline + new ratelimit/wiring/contract tests), suite fast (<3s, no real sleeps).

- [ ] **Step 5: GENTLE live smoke** — throwaway script (BN up at `127.0.0.1:3015`, `NO_PROXY=127.0.0.1,localhost`, `.env` loaded if a real LLM provider is exercised). CONFIRM:
  - With default `configure()` pacing ON, instrument `ratelimit._limiter` (or wrap `_now`/`_sleep` with logging): fire N≥4 rapid bilibili-facing calls (e.g. `metadata.fetch_metadata` on a few public BVs, or `ratelimit.paced` around a trivial timed call) and confirm observed inter-call start gaps ≥ `min_interval` (pacing observably engages) — log timestamps.
  - The **first** call of a fresh process never waits; a single `transcribe()` of one public BV completes end-to-end (metadata + transcript + summary) with added latency ≤ ~1s vs pacing disabled — log both wall-times.
  - Do NOT force a 429; if one occurs naturally, confirm it self-recovers via backoff (log attempts). 412 (if BN download hits it) is unrelated and out of scope.

- [ ] **Step 6: Commit docs + contract test**

```bash
git commit -m "docs(bili-ratelimit): document built-in pacing + 429/-509/-799 backoff (v1.x, non-breaking)" -- \
  docs/interface.md tests/test_public_api.py
```

---

## Self-Review notes

- **Spec coverage:** proactive limiter (Task 2), throttle classifier + Retry-After (Task 3), `paced()` backoff (Task 4), all 3 bilibili-facing call sites routed (Task 5), BN-local excluded (Task 5 — no change to `bilinote_client.py`), non-breaking `transcribe()`/contract (Task 6 test, no signature change anywhere), configurable + exported (Task 1), conftest keeps baseline (Task 5), docs (Task 6), live smoke (Task 6). ✓
- **412 left alone** — `_throttle_signal` returns `(False, None)` for HTTP 412 and code `-412`/`-101`; `paced()` re-raises non-throttle immediately (Task 4 `test_paced_propagates_non_throttle_immediately`). ✓
- **Type consistency:** `paced(fn) -> Any`, `_throttle_signal(exc) -> (bool, float|None)`, `_retry_after_seconds(resp) -> float|None`, `_RateLimiter.acquire(min_interval, jitter)`, `_cfg`/`_limiter`/`_now`/`_sleep`/`_rand` names consistent across Tasks 1–5 and the wiring in metadata/subtitle. ✓
- **Baseline safety:** autouse conftest (Task 5) disables pacing + nukes real sleeps so the 59 existing tests stay fast/deterministic; pacing/retry tests opt in via `ratelimit.configure(enabled=True, ...)`. ✓
- **Worktree/editable-install trap:** every pytest run uses `PYTHONPATH=src` (documented in the header). ✓
