# Zhihu Engine v1.2 — Rate-Limit Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the engine robust under bulk crawling by adding (1) a process-wide **proactive rate-limiter** that smooths request bursts and (2) a **reactive backoff/retry** on 403/429 that honors `Retry-After` — so a bulk consumer (SP-5a watcher) stops tripping Zhihu's burst-sensitive throttle and transient 403s self-recover, while a single-URL consumer (SP-3) is ~unaffected.

**Architecture:** All four outbound `httpx.get` call sites (`fetcher.get_page`, `fetcher.get_api_answer`, `comments.fetch_comments`, `comments.fetch_child_comments`) route through ONE new internal `fetcher._request()` that (a) passes a module-level `_RateLimiter` singleton before each attempt and (b) retries 403/429 with backoff. One place hardened → all consumers benefit. Tunable via a new module-level `zhihu.configure(...)`; conservative safe defaults. NON-BREAKING: `fetch()` signature and `FetchResult` shape are untouched (handoff §8).

**Tech Stack:** Python 3.13, httpx (`trust_env=False`), `threading.Lock`, pytest + pytest-httpx 0.36. Injectable clock (`_now`/`_sleep`/`_rand` module hooks) for deterministic, instant tests.

> Empirical basis (why burst-sensitive, why these defaults) + the rejected mirror-ANSWER/signer paths live in
> `../../RepoMem/temp/zhihu-engine-article-fallback/probe-findings.md`. Module gotchas D1–D7 in `../../RepoMem/decisions.md`.
> Live probe 2026-06-09: 60/60 sequential nav-GETs @ ~2 req/s = zero throttle ⇒ throttle is burst/concurrency-sensitive, not cumulative.

---

## File Structure

- `src/zhihu/fetcher.py` (modify) — add `_Config` + `configure()`, `_RateLimiter` singleton, `_request()`, `_retry_after_seconds()`; rewire `get_page`/`get_api_answer` onto `_request`.
- `src/zhihu/comments.py` (modify) — route both `httpx.get` calls through `fetcher._request` (keep `raise_for_status`).
- `src/zhihu/__init__.py` (modify) — export `configure`.
- `tests/conftest.py` (modify) — autouse fixture that resets + disables pacing so the existing 58 tests stay fast/deterministic.
- `tests/test_fetcher.py` (modify) — limiter + retry + Retry-After + rewire tests.
- `docs/interface.md` (modify) — document built-in pacing + 403/429 backoff + `configure()`.

---

### Task 1: Config + `configure()` (module-level, safe defaults, exported)

**Files:**
- Modify: `src/zhihu/fetcher.py`
- Modify: `src/zhihu/__init__.py`
- Test: `tests/test_fetcher.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_fetcher.py (append)
def test_configure_updates_defaults_and_resets():
    from zhihu import fetcher
    saved = fetcher._cfg.min_interval, fetcher._cfg.max_retries, fetcher._cfg.enabled
    try:
        from zhihu import configure
        configure(min_interval=1.25, max_retries=5, enabled=False)
        assert fetcher._cfg.min_interval == 1.25
        assert fetcher._cfg.max_retries == 5
        assert fetcher._cfg.enabled is False
    finally:
        fetcher._cfg.min_interval, fetcher._cfg.max_retries, fetcher._cfg.enabled = saved

def test_default_config_is_conservative():
    from zhihu import fetcher
    c = fetcher._Config()
    assert c.min_interval == 0.5 and c.jitter == 0.3
    assert c.max_retries == 3 and c.backoff_base == 0.5
    assert c.retry_statuses == (403, 429) and c.enabled is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_fetcher.py -k "configure_updates or default_config" -v`
Expected: FAIL — `ImportError: cannot import name 'configure'` / `module 'zhihu.fetcher' has no attribute '_cfg'`.

- [ ] **Step 3: Write minimal implementation**

Add to the TOP of `src/zhihu/fetcher.py` (after `import httpx`):

```python
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


@dataclass
class _Config:
    min_interval: float = 0.5          # min seconds between request *starts* (proactive pacing)
    jitter: float = 0.3                # add U(0, jitter) to each pacing/backoff wait
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
    never waits). Pass `enabled=False` to disable both pacing and retry.
    """
    if min_interval is not None: _cfg.min_interval = min_interval
    if jitter is not None: _cfg.jitter = jitter
    if max_retries is not None: _cfg.max_retries = max_retries
    if backoff_base is not None: _cfg.backoff_base = backoff_base
    if retry_statuses is not None: _cfg.retry_statuses = tuple(retry_statuses)
    if enabled is not None: _cfg.enabled = enabled
```

In `src/zhihu/__init__.py`:

```python
from .engine import fetch
from .fetcher import configure
from .models import FetchResult, Author, EmbeddedAnswer, Comment, ZhihuType
from .errors import ZhihuFetchError

__all__ = ["fetch", "configure", "FetchResult", "Author", "EmbeddedAnswer", "Comment",
           "ZhihuType", "ZhihuFetchError"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_fetcher.py -k "configure_updates or default_config" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add Engine/zhihu/src/zhihu/fetcher.py Engine/zhihu/src/zhihu/__init__.py Engine/zhihu/tests/test_fetcher.py
git commit Engine/zhihu/src/zhihu/fetcher.py Engine/zhihu/src/zhihu/__init__.py Engine/zhihu/tests/test_fetcher.py \
  -m "feat(zhihu): module-level configure() for pacing+retry (conservative defaults)"
```

---

### Task 2: `_RateLimiter` — proactive pacing with injectable clock

**Files:**
- Modify: `src/zhihu/fetcher.py`
- Test: `tests/test_fetcher.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_fetcher.py (append)
def test_rate_limiter_paces_second_call(monkeypatch):
    from zhihu import fetcher
    clock = {"t": 1000.0}
    slept = []
    monkeypatch.setattr(fetcher, "_now", lambda: clock["t"])
    monkeypatch.setattr(fetcher, "_sleep", lambda s: (slept.append(s), clock.__setitem__("t", clock["t"] + s)))
    monkeypatch.setattr(fetcher, "_rand", lambda a, b: 0.0)   # zero jitter -> deterministic
    lim = fetcher._RateLimiter()
    lim.acquire(min_interval=0.5, jitter=0.0)   # first call: last=0 -> target far in past -> no sleep
    assert slept == []
    lim.acquire(min_interval=0.5, jitter=0.0)   # immediate second call -> must wait the full interval
    assert slept == [0.5]

def test_rate_limiter_no_wait_when_enough_time_elapsed(monkeypatch):
    from zhihu import fetcher
    clock = {"t": 1000.0}
    slept = []
    monkeypatch.setattr(fetcher, "_now", lambda: clock["t"])
    monkeypatch.setattr(fetcher, "_sleep", lambda s: slept.append(s))
    monkeypatch.setattr(fetcher, "_rand", lambda a, b: 0.0)
    lim = fetcher._RateLimiter()
    lim.acquire(0.5, 0.0)
    clock["t"] += 2.0          # 2s passes (e.g. a slow nav-GET download) -> already past interval
    lim.acquire(0.5, 0.0)
    assert slept == []         # no extra pacing when the request itself was slow enough
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_fetcher.py -k "rate_limiter" -v`
Expected: FAIL — `module 'zhihu.fetcher' has no attribute '_RateLimiter'`.

- [ ] **Step 3: Write minimal implementation**

Add to `src/zhihu/fetcher.py` (after `_cfg = _Config()`):

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_fetcher.py -k "rate_limiter" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add Engine/zhihu/src/zhihu/fetcher.py Engine/zhihu/tests/test_fetcher.py
git commit Engine/zhihu/src/zhihu/fetcher.py Engine/zhihu/tests/test_fetcher.py \
  -m "feat(zhihu): _RateLimiter proactive min-interval pacer (injectable clock)"
```

---

### Task 3: `_request()` — unified call with 403/429 backoff that honors Retry-After

**Files:**
- Modify: `src/zhihu/fetcher.py`
- Test: `tests/test_fetcher.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_fetcher.py (append)
def test_request_retries_403_then_succeeds(httpx_mock, monkeypatch):
    from zhihu import fetcher
    monkeypatch.setattr(fetcher, "_sleep", lambda s: None)          # no real waiting
    monkeypatch.setattr(fetcher, "_rand", lambda a, b: 0.0)
    monkeypatch.setattr(fetcher._limiter, "_last", 0.0, raising=False)
    httpx_mock.add_response(url="https://www.zhihu.com/answer/9", status_code=403, text="no")
    httpx_mock.add_response(url="https://www.zhihu.com/answer/9", status_code=200, text="yes")
    fetcher.configure(min_interval=0.0, jitter=0.0, max_retries=3, enabled=True)
    r = fetcher._request("https://www.zhihu.com/answer/9", cookies={"d_c0": "x"},
                         headers=fetcher.NAV_HEADERS, timeout=5.0)
    assert r.status_code == 200 and r.text == "yes"

def test_request_honors_retry_after_header(httpx_mock, monkeypatch):
    from zhihu import fetcher
    waits = []
    monkeypatch.setattr(fetcher, "_sleep", lambda s: waits.append(s))
    monkeypatch.setattr(fetcher, "_rand", lambda a, b: 0.0)
    httpx_mock.add_response(url="https://www.zhihu.com/answer/7", status_code=429,
                            headers={"Retry-After": "12"}, text="slow down")
    httpx_mock.add_response(url="https://www.zhihu.com/answer/7", status_code=200, text="ok")
    fetcher.configure(min_interval=0.0, jitter=0.0, max_retries=3, backoff_base=0.5, enabled=True)
    r = fetcher._request("https://www.zhihu.com/answer/7", cookies={"d_c0": "x"},
                         headers=fetcher.API_HEADERS, timeout=5.0)
    assert r.status_code == 200
    assert 12 in waits            # honored Retry-After, not the 0.5 backoff

def test_request_gives_up_after_max_retries(httpx_mock, monkeypatch):
    from zhihu import fetcher
    monkeypatch.setattr(fetcher, "_sleep", lambda s: None)
    monkeypatch.setattr(fetcher, "_rand", lambda a, b: 0.0)
    for _ in range(4):            # initial + 3 retries
        httpx_mock.add_response(url="https://www.zhihu.com/answer/5", status_code=403, text="nope")
    fetcher.configure(min_interval=0.0, jitter=0.0, max_retries=3, enabled=True)
    r = fetcher._request("https://www.zhihu.com/answer/5", cookies={"d_c0": "x"},
                         headers=fetcher.NAV_HEADERS, timeout=5.0)
    assert r.status_code == 403   # returns the last response; caller decides (raise / fallback)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_fetcher.py -k "request_retries or retry_after or gives_up" -v`
Expected: FAIL — `module 'zhihu.fetcher' has no attribute '_request'`.

- [ ] **Step 3: Write minimal implementation**

Add to `src/zhihu/fetcher.py` (after `_limiter = _RateLimiter()`):

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


def _request(url: str, *, cookies: dict, headers: dict, timeout: float) -> httpx.Response:
    """The single outbound GET for the whole engine: proactive pacing before every attempt +
    reactive backoff on a retryable status (honors Retry-After). Returns the final Response WITHOUT
    raising — the caller decides what a non-2xx means (get_page tolerates 403; api/comments raise)."""
    resp = None
    for attempt in range(_cfg.max_retries + 1):
        if _cfg.enabled:
            _limiter.acquire(_cfg.min_interval, _cfg.jitter)
        resp = httpx.get(url, cookies=cookies, headers=headers, timeout=timeout,
                         follow_redirects=True, trust_env=False)
        if (not _cfg.enabled or resp.status_code not in _cfg.retry_statuses
                or attempt == _cfg.max_retries):
            return resp
        delay = _retry_after_seconds(resp)
        if delay is None:
            delay = _cfg.backoff_base * (2 ** attempt) + (_rand(0.0, _cfg.jitter) if _cfg.jitter else 0.0)
        _sleep(delay)
    return resp
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_fetcher.py -k "request_retries or retry_after or gives_up" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add Engine/zhihu/src/zhihu/fetcher.py Engine/zhihu/tests/test_fetcher.py
git commit Engine/zhihu/src/zhihu/fetcher.py Engine/zhihu/tests/test_fetcher.py \
  -m "feat(zhihu): _request unified GET with 403/429 backoff honoring Retry-After"
```

---

### Task 4: Rewire `get_page` / `get_api_answer` onto `_request` + keep the 58-test baseline green

**Files:**
- Modify: `src/zhihu/fetcher.py`
- Modify: `tests/conftest.py`
- Test: `tests/test_fetcher.py`

- [ ] **Step 1: Write the failing test** (integration: a transient 403 nav-GET self-recovers and feeds the normal path)

```python
# tests/test_fetcher.py (append)
def test_get_page_recovers_transient_403(httpx_mock, monkeypatch):
    from zhihu import fetcher
    monkeypatch.setattr(fetcher, "_sleep", lambda s: None)
    monkeypatch.setattr(fetcher, "_rand", lambda a, b: 0.0)
    fetcher.configure(min_interval=0.0, jitter=0.0, max_retries=2, enabled=True)
    httpx_mock.add_response(url="https://www.zhihu.com/answer/3", status_code=403, text="x")
    httpx_mock.add_response(url="https://www.zhihu.com/answer/3", status_code=200, text="<html>ok</html>")
    status, text = fetcher.get_page("https://www.zhihu.com/answer/3", cookies={"d_c0": "x"})
    assert status == 200 and "ok" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_fetcher.py::test_get_page_recovers_transient_403 -v`
Expected: FAIL — current `get_page` calls `httpx.get` directly (no retry), returns 403 on the first response.

- [ ] **Step 3: Write minimal implementation** — replace the bodies of `get_page` and `get_api_answer`:

```python
def get_page(url: str, *, cookies: dict, timeout: float = 30.0) -> tuple[int, str]:
    """GET a Zhihu page as a browser navigation. Returns (status_code, text). Does not raise on 4xx.
    Goes through _request (proactive pacing + 403/429 backoff)."""
    resp = _request(url, cookies=cookies, headers=NAV_HEADERS, timeout=timeout)
    return resp.status_code, resp.text


def get_api_answer(answer_id: str, *, cookies: dict, timeout: float = 30.0) -> dict:
    """Unsigned /api/v4 answer fallback. Raises on non-2xx. Goes through _request."""
    url = f"https://www.zhihu.com/api/v4/answers/{answer_id}?include=content"
    resp = _request(url, cookies=cookies, headers=API_HEADERS, timeout=timeout)
    resp.raise_for_status()
    return resp.json()
```

Add an autouse fixture to `tests/conftest.py` so the existing suite stays instant + deterministic (no real pacing/sleep, fresh limiter per test):

```python
import pytest
from zhihu import fetcher

@pytest.fixture(autouse=True)
def _reset_engine_pacing(monkeypatch):
    # default OFF in tests: no real sleeps, no cross-test limiter state; tests that exercise
    # pacing/retry opt back in via fetcher.configure(...) + their own monkeypatch.
    monkeypatch.setattr(fetcher, "_sleep", lambda s: None)
    fetcher._limiter._last = 0.0
    saved = fetcher._cfg
    fetcher._cfg = fetcher._Config(enabled=False)
    yield
    fetcher._cfg = saved
```

> NOTE: this fixture sets `enabled=False` by default, so Task-3/Task-4 tests that need retry call `fetcher.configure(enabled=True, ...)` explicitly (they already do). Keep `load_fixture` and any existing conftest content intact — append, don't replace.

- [ ] **Step 4: Run test + FULL baseline**

Run: `.venv/bin/python -m pytest tests/test_fetcher.py::test_get_page_recovers_transient_403 -v && .venv/bin/python -m pytest -q`
Expected: new test PASS; **all prior 58 + new tests green**, suite still ~1–2s (no real sleeps).

- [ ] **Step 5: Commit**

```bash
git add Engine/zhihu/src/zhihu/fetcher.py Engine/zhihu/tests/conftest.py Engine/zhihu/tests/test_fetcher.py
git commit Engine/zhihu/src/zhihu/fetcher.py Engine/zhihu/tests/conftest.py Engine/zhihu/tests/test_fetcher.py \
  -m "feat(zhihu): route get_page/get_api_answer through _request; conftest disables pacing in tests"
```

---

### Task 5: Route comment pagination through `_request` too (bulk consumer hits these most)

**Files:**
- Modify: `src/zhihu/comments.py`
- Test: `tests/test_comments.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_comments.py (append)
def test_fetch_comments_retries_transient_403(httpx_mock, monkeypatch):
    from zhihu import fetcher
    from zhihu.comments import fetch_comments
    monkeypatch.setattr(fetcher, "_sleep", lambda s: None)
    monkeypatch.setattr(fetcher, "_rand", lambda a, b: 0.0)
    fetcher.configure(min_interval=0.0, jitter=0.0, max_retries=2, enabled=True)
    url = "https://www.zhihu.com/api/v4/comment_v5/answers/9/root_comment?order_by=score&limit=20"
    httpx_mock.add_response(url=url, status_code=403, text="throttled")
    httpx_mock.add_response(url=url, json={"data": [
        {"id": "k1", "content": "hi", "like_count": 0, "created_time": 1700000000,
         "author": {"name": "U", "url_token": "u"}, "child_comments": []}],
        "paging": {"is_end": True, "next": None}})
    out = fetch_comments("answer", "9", cookies={"d_c0": "x"}, limit=None)
    assert [c.id for c in out] == ["k1"]   # transient 403 retried -> recovered
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_comments.py::test_fetch_comments_retries_transient_403 -v`
Expected: FAIL — current `comments.py` calls `httpx.get` directly + `raise_for_status()`, so the first 403 raises `HTTPStatusError`.

- [ ] **Step 3: Write minimal implementation** — in `src/zhihu/comments.py`:

Add the import at the top (after `import httpx`):

```python
from . import fetcher
```

Replace the request line in `fetch_comments` (currently `resp = httpx.get(url, cookies=cookies, headers=headers or {}, timeout=30.0, follow_redirects=True, trust_env=False)`):

```python
        resp = fetcher._request(url, cookies=cookies, headers=headers or {}, timeout=30.0)
        resp.raise_for_status()
```

Replace the identical request line in `fetch_child_comments` the same way:

```python
        resp = fetcher._request(url, cookies=cookies, headers=headers or {}, timeout=30.0)
        resp.raise_for_status()
```

(Leave all pagination/guard logic unchanged. `httpx` import stays — still referenced by type/exception handling in callers; if it becomes unused, remove it.)

- [ ] **Step 4: Run test + comments suite**

Run: `.venv/bin/python -m pytest tests/test_comments.py -v`
Expected: new test PASS; all prior comment tests still green (they run with pacing disabled by the autouse fixture, so behavior is identical to before).

- [ ] **Step 5: Commit**

```bash
git add Engine/zhihu/src/zhihu/comments.py Engine/zhihu/tests/test_comments.py
git commit Engine/zhihu/src/zhihu/comments.py Engine/zhihu/tests/test_comments.py \
  -m "feat(zhihu): route comment pagination through _request (pacing+retry)"
```

---

### Task 6: Docs + full suite + gentle live smoke (the verification gate)

**Files:**
- Modify: `docs/interface.md`
- Smoke: throwaway under `Engine/zhihu/` using gitignored `tests/fixtures/cookies.local.json` (NOT committed)

- [ ] **Step 1: Update `docs/interface.md`** — add to §9 (the "纯抓取" boundary) a non-breaking behavior note:

```markdown
## 11. 内置限流与重试（v1.2，非破坏性）

引擎对所有出站请求内置 **主动限流（请求间最小间隔 + 抖动，进程内共享）** 与 **被动重试**（对 403/429
按指数退避重试，若响应含 `Retry-After` 则遵从）。目的：批量消费者（SP-5a Watcher）不再因突发请求触发
知乎的「突发敏感」风控（实测顺序 ~2 req/s 安全），瞬时 403 自动恢复；单 URL 消费者（SP-3）几乎无感
（单请求不等待）。

默认值保守，可经模块级 `configure()` 调整或关闭，**不改变 `fetch()` 签名与 `FetchResult`**：

​```python
from zhihu import configure
configure(min_interval=0.5, jitter=0.3, max_retries=3, backoff_base=0.5, enabled=True)
configure(enabled=False)   # 完全关闭限流+重试
​```

> 注意：文章接口 `/api/v4/articles/{id}` 需 `x-zse-96` 签名（403 code 10003），引擎**不**实现签名器（D1）；
> 专栏正文经导航页（200）正常抓取，此限流/重试正是为降低批量场景下导航页被风控 403 的概率而加。
```

- [ ] **Step 2: Full unit suite**

Run: `.venv/bin/python -m pytest -q` (from `Engine/zhihu/`)
Expected: all green (58 baseline + the new pacing/retry tests), suite still fast (<3s, no real sleeps).

- [ ] **Step 3: Pull cookies into gitignored fixture** (already present from probing; re-pull if stale)

```bash
# from Service/crawl/cookie-manager (service on 127.0.0.1:48088); NEVER commit (matches *.local* gitignore)
COOKIE_MANAGER_CONFIG=config/cookie-manager.yaml node_modules/.bin/tsx src/cli.ts show domain=zhihu.com \
  > ../../../Tools/JarvanKB/Engine/zhihu/tests/fixtures/cookies.local.json
```

- [ ] **Step 4: GENTLE live smoke (no forced throttle)** — throwaway script: with default `configure()` pacing ON, bulk-`fetch()` ~15 real 专栏 URLs from the default collection sequentially. CONFIRM:
- all return 200 / parse to non-empty `content_markdown` (no 403s under paced cadence)
- observed inter-request start gap >= `min_interval` (pacing is actually engaging) — log timestamps
- a single-URL `fetch()` of one article shows ~no added latency (the first request never waits)
- do NOT force a 403; if one occurs naturally, confirm it self-recovers via the backoff (log `attempts`)

- [ ] **Step 5: Commit docs**

```bash
git add Engine/zhihu/docs/interface.md
git commit Engine/zhihu/docs/interface.md \
  -m "docs(zhihu): document built-in pacing + 403/429 backoff (v1.2, non-breaking)"
```

---

## Self-Review notes

- **Spec coverage:** proactive limiter (Task 2), reactive backoff honoring Retry-After (Task 3), all 4 call sites routed (Tasks 4–5), non-breaking `fetch()`/`FetchResult` (no signature change anywhere), configurable (Task 1), docs (Task 6). ✓
- **No signer / no article API fallback** — honored (D1, handoff §8); the gap is addressed by pacing, not a mirror endpoint. ✓
- **Type consistency:** `_request(url, *, cookies, headers, timeout) -> httpx.Response` used identically in `get_page`, `get_api_answer`, `fetch_comments`, `fetch_child_comments`. `_cfg`/`_limiter`/`_now`/`_sleep`/`_rand` names consistent across tasks. ✓
- **Baseline safety:** the autouse conftest fixture (Task 4) disables pacing + nukes real sleeps so the 58 existing tests stay fast/deterministic; pacing/retry tests opt in explicitly. ✓
