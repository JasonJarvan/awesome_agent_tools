---
Lane: full
slug: sp5b-bilibili-watcher
spec: Service/crawl/bilibili-watcher/docs/superpowers/specs/2026-06-07-SP-5b-bilibili-watcher-design.md
---

# Bilibili Watcher (SP-5b) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A standalone daemon that polls the user's Bilibili favorite folders on a schedule, transcribes newly-favorited `type==2` videos via the frozen SP-4a engine, and saves Markdown — with a `fav_time` high-watermark + `bvid` seen-set so each video is fetched exactly once.

**Architecture:** 7-component daemon mirroring the shipped SP-5a Zhihu Watcher 1:1, with two deltas: **(Δ1)** the fetcher wraps the frozen SP-4a Bilibili engine (`Engine/bilibili`); **(Δ2)** the watermark = `fav_time` early-stop (correctness via a `bvid` seen-set). `BlockingScheduler` (`max_instances=1`) drives a sync cycle; `--once` runs one cycle for smoke/CI.

**Tech Stack:** Python 3.12, `httpx` (sync), `cryptography` (cookie decrypt), `apscheduler`, `pyyaml`, the `bilibili` engine package (sibling, editable-installed), `pytest` + `pytest-httpx`.

**Reference:** This is a near-verbatim mirror of `Service/crawl/zhihu-watcher/` (SP-5a, ⚫ done). Where a file is identical-modulo-rename, the task gives the full adapted code anyway. The only genuinely new logic is `favorites_client` (fav_time/has_more/type-filter), `watermark_store.next_watermark` (the §5 advance rule), and `fetcher` (engine wiring).

**Lane:** full (new service + new deps + consumes Engine/bilibili + Step-8 promotes to `RepoMem/persist/` + net-new public contract). `grill-with-docs` auto-judged skip (spec is a 1:1 SP-5a mirror; both deltas are Stage-0-empirically-verified + user-ratified).

**Env setup (run once in the worktree before Task 1):**
```bash
cd Service/crawl/bilibili-watcher
python -m venv .venv && . .venv/bin/activate
pip install -e ../../../Engine/bilibili        # the frozen SP-4a engine (provides `bilibili` pkg)
pip install -e ".[dev]"                         # after Task 0 creates pyproject
```

---

### Task 0: Scaffold the package

**Files:**
- Create: `Service/crawl/bilibili-watcher/pyproject.toml`
- Create: `Service/crawl/bilibili-watcher/.gitignore`
- Create: `Service/crawl/bilibili-watcher/src/bilibili_watcher/__init__.py`
- Create: `Service/crawl/bilibili-watcher/tests/__init__.py`
- Create: `Service/crawl/bilibili-watcher/tests/conftest.py`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "bilibili-watcher"
version = "0.1.0"
description = "Polling watcher for Bilibili favorites: new videos -> SP-4a engine -> Markdown"
requires-python = ">=3.11"
dependencies = [
    "httpx>=0.27",
    "cryptography>=42",
    "apscheduler>=3.10",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-httpx>=0.30"]

[project.scripts]
bilibili-watcher = "bilibili_watcher.__main__:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create `.gitignore`**

```
.venv/
*.egg-info/
```

- [ ] **Step 3: Create the package + test `__init__.py` files**

`src/bilibili_watcher/__init__.py`:
```python
"""SP-5b Bilibili favorites watcher."""
```

`tests/__init__.py`: (empty file)

- [ ] **Step 4: Create `tests/conftest.py`**

```python
import logging
import pytest


@pytest.fixture(autouse=True)
def _quiet_logging():
    logging.getLogger("bilibili_watcher").setLevel(logging.CRITICAL)
```

- [ ] **Step 5: Install + verify empty test run**

Run:
```bash
pip install -e ../../../Engine/bilibili && pip install -e ".[dev]" && pytest -q
```
Expected: `no tests ran` (exit 5) or `collected 0 items` — install succeeds, `import bilibili` works.

- [ ] **Step 6: Commit**

```bash
git add Service/crawl/bilibili-watcher/pyproject.toml Service/crawl/bilibili-watcher/.gitignore Service/crawl/bilibili-watcher/src Service/crawl/bilibili-watcher/tests
git commit -m "feat(SP-5b): scaffold bilibili-watcher package"
```

---

### Task 1: `config` — load + validate YAML

**Files:**
- Create: `src/bilibili_watcher/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write the failing tests**

```python
import pytest
from bilibili_watcher.config import load_config, WatcherConfig


def _write(tmp_path, text):
    p = tmp_path / "c.yaml"
    p.write_text(text, encoding="utf-8")
    return str(p)


def test_loads_full_config(tmp_path):
    cfg = load_config(_write(tmp_path, """
poll_interval_minutes: 20
output_dir: /data/output
state_dir: /data/state
cookie_source:
  base_url: http://127.0.0.1:48088
  uuid: u
  password: p
  auth_token: tok
engine:
  bn_base_url: http://127.0.0.1:3015
  provider_id: pid
  model_name: m
render:
  include_transcript: true
  include_timestamps: false
  split_transcript: false
folders:
  - id: "2216104467"
    name: "AI生成"
  - id: "1195057867"
"""))
    assert isinstance(cfg, WatcherConfig)
    assert cfg.poll_interval_minutes == 20
    assert cfg.cookie_source.auth_token == "tok"
    assert cfg.engine.bn_base_url == "http://127.0.0.1:3015"
    assert cfg.render.split_transcript is False
    assert [f.id for f in cfg.folders] == ["2216104467", "1195057867"]
    assert cfg.folders[0].name == "AI生成"
    assert cfg.folders[1].name == "1195057867"   # name defaults to id


def test_defaults(tmp_path):
    cfg = load_config(_write(tmp_path, """
output_dir: /o
state_dir: /s
cookie_source: {base_url: x, uuid: u, password: p}
engine: {bn_base_url: b, provider_id: pid, model_name: m}
folders: [{id: "1"}]
"""))
    assert cfg.poll_interval_minutes == 20            # default
    assert cfg.cookie_source.auth_token is None       # optional
    assert cfg.render.include_transcript is True       # default
    assert cfg.render.split_transcript is False


def test_missing_required_raises(tmp_path):
    with pytest.raises(ValueError, match="output_dir"):
        load_config(_write(tmp_path, "state_dir: /s\ncookie_source: {base_url: x, uuid: u, password: p}\nengine: {bn_base_url: b, provider_id: p, model_name: m}\nfolders: [{id: '1'}]"))


def test_no_folders_raises(tmp_path):
    with pytest.raises(ValueError, match="at least one folder"):
        load_config(_write(tmp_path, "output_dir: /o\nstate_dir: /s\ncookie_source: {base_url: x, uuid: u, password: p}\nengine: {bn_base_url: b, provider_id: p, model_name: m}\nfolders: []"))


def test_bad_interval_raises(tmp_path):
    with pytest.raises(ValueError, match="poll_interval_minutes"):
        load_config(_write(tmp_path, "poll_interval_minutes: 0\noutput_dir: /o\nstate_dir: /s\ncookie_source: {base_url: x, uuid: u, password: p}\nengine: {bn_base_url: b, provider_id: p, model_name: m}\nfolders: [{id: '1'}]"))
```

- [ ] **Step 2: Run to verify they fail**

Run: `pytest tests/test_config.py -v`
Expected: FAIL (`ModuleNotFoundError: bilibili_watcher.config`)

- [ ] **Step 3: Write `config.py`**

```python
"""Load and validate the watcher YAML config into dataclasses."""
from __future__ import annotations

from dataclasses import dataclass

import yaml


@dataclass
class FolderConfig:
    id: str
    name: str


@dataclass
class CookieSource:
    base_url: str
    uuid: str
    password: str
    auth_token: str | None = None


@dataclass
class EngineConfig:
    bn_base_url: str
    provider_id: str
    model_name: str


@dataclass
class RenderConfig:
    include_transcript: bool = True
    include_timestamps: bool = False
    split_transcript: bool = False


@dataclass
class WatcherConfig:
    poll_interval_minutes: int
    output_dir: str
    state_dir: str
    cookie_source: CookieSource
    engine: EngineConfig
    render: RenderConfig
    folders: list[FolderConfig]


def _require(d: dict, key: str, ctx: str):
    if key not in d or d[key] in (None, ""):
        raise ValueError(f"config: missing required field '{key}' in {ctx}")
    return d[key]


def load_config(path: str) -> WatcherConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    cs = _require(raw, "cookie_source", "root")
    cookie_source = CookieSource(
        base_url=_require(cs, "base_url", "cookie_source"),
        uuid=_require(cs, "uuid", "cookie_source"),
        password=_require(cs, "password", "cookie_source"),
        auth_token=cs.get("auth_token"),
    )

    en = _require(raw, "engine", "root")
    engine = EngineConfig(
        bn_base_url=_require(en, "bn_base_url", "engine"),
        provider_id=_require(en, "provider_id", "engine"),
        model_name=_require(en, "model_name", "engine"),
    )

    rd = raw.get("render") or {}
    render = RenderConfig(
        include_transcript=bool(rd.get("include_transcript", True)),
        include_timestamps=bool(rd.get("include_timestamps", False)),
        split_transcript=bool(rd.get("split_transcript", False)),
    )

    folders_raw = raw.get("folders") or []
    if not folders_raw:
        raise ValueError("config: must define at least one folder")
    folders = []
    for fo in folders_raw:
        fid = str(_require(fo, "id", "folder"))
        folders.append(FolderConfig(id=fid, name=str(fo.get("name") or fid)))

    interval = int(raw.get("poll_interval_minutes", 20))
    if interval <= 0:
        raise ValueError("config: poll_interval_minutes must be > 0")

    return WatcherConfig(
        poll_interval_minutes=interval,
        output_dir=_require(raw, "output_dir", "root"),
        state_dir=_require(raw, "state_dir", "root"),
        cookie_source=cookie_source,
        engine=engine,
        render=render,
        folders=folders,
    )
```

- [ ] **Step 4: Run to verify pass**

Run: `pytest tests/test_config.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add src/bilibili_watcher/config.py tests/test_config.py
git commit -m "feat(SP-5b): config loader (folders/engine/render/cookie_source)"
```

---

### Task 2: `cookie_provider` — pull + decrypt `bilibili.com` cookies

**Files:**
- Create: `src/bilibili_watcher/cookie_provider.py`
- Test: `tests/test_cookie_provider.py`

This reuses SP-5a's verified CookieCloud decrypt verbatim; the only delta is extracting domain **`bilibili.com`** (no dot) and sending the optional `X-CookieCloud-Token`.

- [ ] **Step 1: Write the failing tests**

```python
import base64, hashlib, json
import httpx
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

from bilibili_watcher.cookie_provider import (
    derive_key, decrypt_payload, extract_bilibili_cookies, CookieProvider,
)
from bilibili_watcher.config import CookieSource


def _evp(pw, salt, klen, ivlen):
    d = b""; prev = b""
    while len(d) < klen + ivlen:
        prev = hashlib.md5(prev + pw + salt).digest(); d += prev
    return d[:klen], d[klen:klen + ivlen]


def _enc_legacy(plaintext: dict, the_key: str) -> str:
    salt = b"12345678"
    key, iv = _evp(the_key.encode(), salt, 32, 16)
    enc = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    pad = PKCS7(128).padder()
    body = pad.update(json.dumps(plaintext).encode()) + pad.finalize()
    ct = enc.update(body) + enc.finalize()
    return base64.b64encode(b"Salted__" + salt + ct).decode()


def test_derive_key():
    assert derive_key("u", "p") == hashlib.md5(b"u-p").hexdigest()[:16]


def test_decrypt_legacy_roundtrip():
    payload = {"cookie_data": {"bilibili.com": [{"name": "SESSDATA", "value": "abc"}]}}
    the_key = derive_key("u", "p")
    enc = _enc_legacy(payload, the_key)
    assert decrypt_payload(enc, "legacy", "u", "p") == payload


def test_extract_bilibili_cookies_no_dot():
    payload = {"cookie_data": {
        "bilibili.com": [{"name": "SESSDATA", "value": "s"}, {"name": "bili_jct", "value": "j"}],
        ".bilibili.com": [{"name": "OTHER", "value": "x"}],   # leading-dot domain must be IGNORED
        "zhihu.com": [{"name": "z_c0", "value": "z"}],
    }}
    out = extract_bilibili_cookies(payload)
    assert out == {"SESSDATA": "s", "bili_jct": "j"}


def test_provider_pulls_and_sends_auth_token():
    payload = {"cookie_data": {"bilibili.com": [{"name": "SESSDATA", "value": "s"}]}}
    enc = _enc_legacy(payload, derive_key("u", "p"))
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["token"] = request.headers.get("X-CookieCloud-Token")
        seen["path"] = request.url.path
        return httpx.Response(200, json={"encrypted": enc, "crypto_type": "legacy"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    src = CookieSource(base_url="http://box", uuid="u", password="p", auth_token="tok")
    cp = CookieProvider(src, http_client=client)
    assert cp.get_cookies() == {"SESSDATA": "s"}
    assert seen["token"] == "tok"
    assert seen["path"] == "/get/u"
```

- [ ] **Step 2: Run to verify they fail**

Run: `pytest tests/test_cookie_provider.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: Write `cookie_provider.py`**

```python
"""Pull the latest bilibili.com cookies from SP-1 CookieManager and decrypt them in memory.

Cookies are NEVER written to disk; only returned as a transient dict. Mirrors the CookieCloud
crypto protocol documented in Service/crawl/cookie-manager/docs/interface.md §3 (verified Python
reference: Skill/crawl/zhihu-crawl/src/zhihu_crawl/cookie.py, credentials.md §Consumer-side decrypt).
Delta vs SP-5a: domain 'bilibili.com' (NO leading dot — credentials.md §Bilibili authoritative) +
optional X-CookieCloud-Token header.
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging

import httpx
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

from .config import CookieSource

log = logging.getLogger("bilibili_watcher.cookie_provider")


def derive_key(uuid: str, password: str) -> str:
    return hashlib.md5(f"{uuid}-{password}".encode("utf-8")).hexdigest()[:16]


def _evp_bytes_to_key(pw: bytes, salt: bytes, key_len: int, iv_len: int) -> tuple[bytes, bytes]:
    d = b""
    prev = b""
    while len(d) < key_len + iv_len:
        prev = hashlib.md5(prev + pw + salt).digest()
        d += prev
    return d[:key_len], d[key_len:key_len + iv_len]


def _aes_cbc_decrypt(key: bytes, iv: bytes, ct: bytes) -> bytes:
    decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    padded = decryptor.update(ct) + decryptor.finalize()
    unpadder = PKCS7(128).unpadder()
    return unpadder.update(padded) + unpadder.finalize()


def decrypt_legacy(encrypted: str, the_key: str) -> dict:
    raw = base64.b64decode(encrypted)
    if raw[:8] != b"Salted__":
        raise ValueError("legacy ciphertext is not a 'Salted__' envelope")
    salt = raw[8:16]
    ct = raw[16:]
    key, iv = _evp_bytes_to_key(the_key.encode("utf-8"), salt, 32, 16)
    return json.loads(_aes_cbc_decrypt(key, iv, ct).decode("utf-8"))


def decrypt_fixed(encrypted: str, the_key: str) -> dict:
    ct = base64.b64decode(encrypted)
    key = the_key.encode("utf-8")
    iv = b"\x00" * 16
    return json.loads(_aes_cbc_decrypt(key, iv, ct).decode("utf-8"))


def decrypt_payload(encrypted: str, crypto_type: str, uuid: str, password: str) -> dict:
    the_key = derive_key(uuid, password)
    if crypto_type == "legacy":
        return decrypt_legacy(encrypted, the_key)
    if crypto_type == "aes-128-cbc-fixed":
        return decrypt_fixed(encrypted, the_key)
    raise ValueError(f"unknown crypto_type: {crypto_type!r}")


def extract_bilibili_cookies(payload: dict) -> dict[str, str]:
    """Cookies from domain EXACTLY 'bilibili.com' (no leading dot — credentials.md authoritative)."""
    out: dict[str, str] = {}
    for domain, cookies in (payload.get("cookie_data") or {}).items():
        if str(domain) == "bilibili.com":
            for c in cookies:
                out[c["name"]] = c["value"]
    return out


class CookieProvider:
    def __init__(self, cookie_source: CookieSource, http_client: httpx.Client | None = None):
        self._src = cookie_source
        # trust_env=False: SP-1 is local/mainland, reached direct — ignore overseas proxy env.
        self._client = http_client or httpx.Client(timeout=30.0, trust_env=False)

    def get_cookies(self) -> dict[str, str]:
        url = f"{self._src.base_url.rstrip('/')}/get/{self._src.uuid}"
        headers = {}
        if self._src.auth_token:
            headers["X-CookieCloud-Token"] = self._src.auth_token
        resp = self._client.get(url, headers=headers)
        resp.raise_for_status()
        body = resp.json()
        payload = decrypt_payload(
            body["encrypted"], body.get("crypto_type", "legacy"),
            self._src.uuid, self._src.password,
        )
        cookies = extract_bilibili_cookies(payload)
        log.info("pulled %d bilibili.com cookies from SP-1", len(cookies))
        return cookies
```

- [ ] **Step 4: Run to verify pass**

Run: `pytest tests/test_cookie_provider.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/bilibili_watcher/cookie_provider.py tests/test_cookie_provider.py
git commit -m "feat(SP-5b): cookie_provider (bilibili.com extraction + optional auth token)"
```

---

### Task 3: `favorites_client` — list one folder (order=mtime, fav_time early-stop, has_more paging, type==2)

**Files:**
- Create: `src/bilibili_watcher/favorites_client.py`
- Test: `tests/test_favorites_client.py`

- [ ] **Step 1: Write the failing tests**

```python
import httpx
import pytest
from bilibili_watcher.favorites_client import (
    FavoritesClient, BiliFavItem, BilibiliFavApiError,
)


def _media(bvid, fav_time, type_=2, title=None):
    return {"bvid": bvid, "fav_time": fav_time, "type": type_, "title": title or bvid}


def _page(medias, has_more, code=0):
    return {"code": code, "message": "0", "data": {"medias": medias, "has_more": has_more,
                                                    "info": {"media_count": len(medias)}}}


def test_pages_until_has_more_false_and_parses():
    pages = {
        1: _page([_media("BV1", 300), _media("BV2", 200)], has_more=True),
        2: _page([_media("BV3", 100)], has_more=False),
    }

    def handler(request: httpx.Request) -> httpx.Response:
        pn = int(dict(request.url.params)["pn"])
        assert dict(request.url.params)["order"] == "mtime"
        return httpx.Response(200, json=pages[pn])

    fc = FavoritesClient(http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    items = fc.list_items("121", {"SESSDATA": "s"})
    assert [(i.bvid, i.fav_time) for i in items] == [("BV1", 300), ("BV2", 200), ("BV3", 100)]


def test_filters_non_type_2():
    page = _page([_media("BV1", 300), _media("AU9", 250, type_=12), _media("BV2", 200)], has_more=False)
    fc = FavoritesClient(http_client=httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=page))))
    items = fc.list_items("121", {"SESSDATA": "s"})
    assert [i.bvid for i in items] == ["BV1", "BV2"]   # type=12 audio dropped


def test_early_stops_on_fav_time_at_or_below_watermark():
    # order=mtime DESC; watermark=200 -> BV1(300) kept, BV2(200) triggers stop (<=200)
    pages = {1: _page([_media("BV1", 300), _media("BV2", 200), _media("BV3", 100)], has_more=True)}
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        pn = int(dict(request.url.params)["pn"])
        return httpx.Response(200, json=pages[pn])

    fc = FavoritesClient(http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    items = fc.list_items("121", {"SESSDATA": "s"}, since_fav_time=200)
    assert [i.bvid for i in items] == ["BV1"]          # stopped at BV2 (fav_time<=200)
    assert calls["n"] == 1                             # did NOT page to page 2 (early-stop)


def test_early_stop_evaluated_before_type_filter():
    # a non-video item at the boundary still triggers stop (ordering is across all types)
    page = _page([_media("BV1", 300), _media("AU0", 200, type_=12), _media("BV9", 150)], has_more=True)
    fc = FavoritesClient(http_client=httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=page))))
    items = fc.list_items("121", {"SESSDATA": "s"}, since_fav_time=200)
    assert [i.bvid for i in items] == ["BV1"]          # AU0 (type 12, fav<=200) stops before BV9


def test_does_not_stop_from_media_count():
    # media_count says 4 but only 3 returned + has_more False (deleted item gotcha) -> must not loop
    page = {"code": 0, "data": {"medias": [_media("BV1", 30), _media("BV2", 20), _media("BV3", 10)],
                                "has_more": False, "info": {"media_count": 4}}}
    fc = FavoritesClient(http_client=httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=page))))
    items = fc.list_items("121", {"SESSDATA": "s"})
    assert [i.bvid for i in items] == ["BV1", "BV2", "BV3"]


def test_non_200_raises():
    fc = FavoritesClient(http_client=httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(412, json={}))))
    with pytest.raises(BilibiliFavApiError) as exc:
        fc.list_items("121", {"SESSDATA": "s"})
    assert exc.value.status == 412


def test_nonzero_code_raises():
    # e.g. -101 not logged in (expired cookie)
    page = {"code": -101, "message": "账号未登录", "data": None}
    fc = FavoritesClient(http_client=httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=page))))
    with pytest.raises(BilibiliFavApiError) as exc:
        fc.list_items("121", {"SESSDATA": "s"})
    assert exc.value.code == -101


def test_skips_malformed_items():
    page = _page([{"type": 2}, _media("BV9", 100)], has_more=False)   # first lacks bvid/fav_time
    fc = FavoritesClient(http_client=httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=page))))
    items = fc.list_items("121", {"SESSDATA": "s"})
    assert [i.bvid for i in items] == ["BV9"]
```

- [ ] **Step 2: Run to verify they fail**

Run: `pytest tests/test_favorites_client.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: Write `favorites_client.py`**

```python
"""List items in one Bilibili favorite folder via the public resource/list API.

Endpoint: GET https://api.bilibili.com/x/v3/fav/resource/list?media_id=&pn=&ps=20&order=mtime
Plain cookie (SESSDATA) + browser headers, NO signing (Stage-0 verified 2026-06-10). Direct connect
(trust_env=False; bilibili is a mainland site). order=mtime => medias sorted by fav_time DESC, so we
early-stop once an item's fav_time <= since_fav_time. Paging stops on data.has_more==False (NEVER on
media_count — it counts deleted/invalid items not returned; Stage-0 gotcha). Only type==2 (UGC video).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

log = logging.getLogger("bilibili_watcher.favorites_client")

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.bilibili.com/",
}


@dataclass
class BiliFavItem:
    bvid: str       # fed to engine.transcribe(bvid, ...)
    fav_time: int   # the collected-time (Stage-0: distinct from pubtime); watermark axis
    title: str      # fallback title (engine's metadata.title is authoritative)


class BilibiliFavApiError(Exception):
    def __init__(self, status: int, code, url: str):
        super().__init__(f"Bilibili fav API status={status} code={code} for {url}")
        self.status = status
        self.code = code
        self.url = url


def folder_id_from_url(url_or_id: str) -> str:
    # accepts a raw media_id or a .../fid<id> / ?fid= URL; config normally gives the bare id
    s = url_or_id.split("?")[0].rstrip("/").split("/")[-1]
    return s.replace("fid", "") if s.startswith("fid") else s


class FavoritesClient:
    def __init__(self, http_client: httpx.Client | None = None, page_size: int = 20):
        self._client = http_client or httpx.Client(
            trust_env=False, headers=_BROWSER_HEADERS, timeout=30.0
        )
        self._ps = page_size

    def list_items(
        self, folder_id_or_url: str, cookies: dict[str, str], since_fav_time: int = 0
    ) -> list[BiliFavItem]:
        folder_id = folder_id_from_url(folder_id_or_url)
        items: list[BiliFavItem] = []
        pn = 1
        while True:
            url = "https://api.bilibili.com/x/v3/fav/resource/list"
            params = {"media_id": folder_id, "pn": pn, "ps": self._ps,
                      "order": "mtime", "type": 0, "platform": "web"}
            resp = self._client.get(url, params=params, cookies=cookies)
            if resp.status_code != 200:
                raise BilibiliFavApiError(resp.status_code, None, str(resp.url))
            body = resp.json()
            if body.get("code") != 0:
                raise BilibiliFavApiError(resp.status_code, body.get("code"), str(resp.url))
            data = body.get("data") or {}
            medias = data.get("medias") or []
            for m in medias:
                ft = m.get("fav_time")
                bvid = m.get("bvid") or m.get("bv_id")
                if ft is None or not bvid:
                    continue                                  # malformed -> skip (don't stop)
                if ft <= since_fav_time:
                    log.info("folder %s: early-stop at fav_time=%s <= watermark=%s",
                             folder_id, ft, since_fav_time)
                    return items                              # all further items are older
                if m.get("type") != 2:
                    continue                                  # only UGC video
                items.append(BiliFavItem(bvid=bvid, fav_time=ft, title=str(m.get("title") or bvid)))
            if not data.get("has_more"):
                break
            pn += 1
        log.info("folder %s: listed %d new video item(s)", folder_id, len(items))
        return items
```

- [ ] **Step 4: Run to verify pass**

Run: `pytest tests/test_favorites_client.py -v`
Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git add src/bilibili_watcher/favorites_client.py tests/test_favorites_client.py
git commit -m "feat(SP-5b): favorites_client (order=mtime, fav_time early-stop, has_more paging, type==2)"
```

---

### Task 4: `watermark_store` — per-folder {watermark, seen} + the §5 advance rule

**Files:**
- Create: `src/bilibili_watcher/watermark_store.py`
- Test: `tests/test_watermark_store.py`

- [ ] **Step 1: Write the failing tests**

```python
from bilibili_watcher.watermark_store import WatermarkStore, FolderState, next_watermark


def test_load_empty(tmp_path):
    st = WatermarkStore(str(tmp_path)).load("f1")
    assert st.watermark == 0 and st.seen == set()


def test_save_and_reload(tmp_path):
    store = WatermarkStore(str(tmp_path))
    store.save("f1", FolderState(watermark=300, seen={"BV1", "BV2"}))
    reloaded = WatermarkStore(str(tmp_path)).load("f1")
    assert reloaded.watermark == 300
    assert reloaded.seen == {"BV1", "BV2"}


def test_folders_isolated(tmp_path):
    store = WatermarkStore(str(tmp_path))
    store.save("f1", FolderState(10, {"BV1"}))
    store.save("f2", FolderState(20, {"BV2"}))
    assert WatermarkStore(str(tmp_path)).load("f1").seen == {"BV1"}
    assert WatermarkStore(str(tmp_path)).load("f2").watermark == 20


def test_atomic_no_leftover_tmp(tmp_path):
    WatermarkStore(str(tmp_path)).save("f1", FolderState(1, {"BV1"}))
    assert [p.name for p in tmp_path.iterdir() if p.name.endswith(".tmp")] == []


def test_next_watermark_no_failures_advances_to_newest():
    # listed fav_times newest-first; no failures -> advance to max
    assert next_watermark(prev=100, listed=[300, 250, 110], failed=[]) == 300


def test_next_watermark_no_new_items_keeps_prev():
    assert next_watermark(prev=100, listed=[], failed=[]) == 100


def test_next_watermark_failure_holds_below_oldest_failure():
    # BV at 250 failed; 300 saved. Must keep failed item listable next cycle => 250-1
    assert next_watermark(prev=100, listed=[300, 250], failed=[250]) == 249


def test_next_watermark_multiple_failures_uses_min():
    assert next_watermark(prev=100, listed=[300, 250, 180], failed=[250, 180]) == 179
```

- [ ] **Step 2: Run to verify they fail**

Run: `pytest tests/test_watermark_store.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: Write `watermark_store.py`**

```python
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
```

- [ ] **Step 4: Run to verify pass**

Run: `pytest tests/test_watermark_store.py -v`
Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git add src/bilibili_watcher/watermark_store.py tests/test_watermark_store.py
git commit -m "feat(SP-5b): watermark_store (fav_time watermark + bvid seen-set, §5 advance rule)"
```

---

### Task 5: `fetcher` — wrap the frozen SP-4a engine

**Files:**
- Create: `src/bilibili_watcher/fetcher.py`
- Test: `tests/test_fetcher.py`

- [ ] **Step 1: Write the failing tests**

```python
from bilibili import BilibiliCredential, BilibiliEngineError
from bilibili_watcher.fetcher import build_credential, make_fetcher, FetchedDoc
from bilibili_watcher.config import RenderConfig


class _FakeRendered:
    main_markdown = "## summary\n\nprose transcript\n"


class _FakeResult:
    class metadata:
        title = "Real Title"

    def render(self, ro):
        assert ro.include_transcript is True and ro.split_transcript is False
        return _FakeRendered()


class _FakeEngine:
    def __init__(self):
        self.calls = []

    def transcribe(self, video_ref, credential):
        self.calls.append((video_ref, credential))
        return _FakeResult()


class _BoomEngine:
    def transcribe(self, video_ref, credential):
        raise BilibiliEngineError("BN down")


def test_build_credential_from_cookies():
    cred = build_credential({"SESSDATA": "s", "bili_jct": "j", "X": "y"})
    assert isinstance(cred, BilibiliCredential)
    assert cred.sessdata == "s" and cred.bili_jct == "j"


def test_make_fetcher_success_returns_doc():
    eng = _FakeEngine()
    fetch = make_fetcher(eng, RenderConfig())
    cred = build_credential({"SESSDATA": "s"})
    doc = fetch("BV1xx", cred)
    assert isinstance(doc, FetchedDoc)
    assert doc.title == "Real Title"
    assert "prose transcript" in doc.markdown
    assert eng.calls[0][0] == "BV1xx"


def test_make_fetcher_engine_error_returns_none():
    fetch = make_fetcher(_BoomEngine(), RenderConfig())
    assert fetch("BV1xx", build_credential({"SESSDATA": "s"})) is None
```

- [ ] **Step 2: Run to verify they fail**

Run: `pytest tests/test_fetcher.py -v`
Expected: FAIL (`ModuleNotFoundError: bilibili_watcher.fetcher`)

- [ ] **Step 3: Write `fetcher.py`**

```python
"""Wrap the frozen SP-4a Bilibili engine: (bvid, credential) -> FetchedDoc | None.

build_credential turns the pulled bilibili.com cookies into a BilibiliCredential. make_fetcher binds
an engine instance + render options into a (bvid, cred) closure the watcher calls per item. On any
BilibiliEngineError (BN down / transcription failed / timeout / bad ref) we log + return None so the
daemon degrades gracefully and the item is retried next cycle (not marked seen / not watermarked).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Optional

from bilibili import BilibiliCredential, RenderOptions, BilibiliEngineError

log = logging.getLogger("bilibili_watcher.fetcher")

from .config import RenderConfig

FetcherFn = Callable[[str, BilibiliCredential], Optional["FetchedDoc"]]


@dataclass
class FetchedDoc:
    title: str
    markdown: str


def build_credential(cookies: dict[str, str]) -> BilibiliCredential:
    return BilibiliCredential(sessdata=cookies.get("SESSDATA", ""), bili_jct=cookies.get("bili_jct"))


def make_fetcher(engine, render: RenderConfig) -> FetcherFn:
    ro = RenderOptions(
        include_transcript=render.include_transcript,
        include_timestamps=render.include_timestamps,
        split_transcript=render.split_transcript,
    )

    def fetch(bvid: str, credential: BilibiliCredential) -> Optional[FetchedDoc]:
        try:
            result = engine.transcribe(bvid, credential=credential)
            markdown = result.render(ro).main_markdown
        except BilibiliEngineError as e:
            log.warning("SP-4a engine failed bvid=%s: %s", bvid, e)
            return None
        return FetchedDoc(title=result.metadata.title, markdown=markdown)

    return fetch
```

- [ ] **Step 4: Run to verify pass**

Run: `pytest tests/test_fetcher.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/bilibili_watcher/fetcher.py tests/test_fetcher.py
git commit -m "feat(SP-5b): fetcher wraps frozen SP-4a engine (graceful degrade -> None)"
```

---

### Task 6: `saver` — write Markdown (subfolder/title, `_<bvid>` collision, `> url` first line)

**Files:**
- Create: `src/bilibili_watcher/saver.py`
- Test: `tests/test_saver.py`

- [ ] **Step 1: Write the failing tests**

```python
from pathlib import Path
from bilibili_watcher.saver import save, sanitize_title


def test_sanitize_title():
    assert sanitize_title('a/b\\c"d<e>f|g') == "a b c d e f g"
    assert sanitize_title("what? yes: no") == "what？ yes： no"
    assert sanitize_title("   ") == "untitled"


def test_save_layout_and_content(tmp_path):
    path = save(str(tmp_path), "AI生成", "Hello World", "BV1xx", "## body\n")
    p = Path(path)
    assert p.parent.name == "AI生成"
    assert p.name == "Hello World.md"
    assert p.read_text(encoding="utf-8") == "> https://www.bilibili.com/video/BV1xx\n## body\n"


def test_collision_appends_bvid(tmp_path):
    save(str(tmp_path), "f", "Same", "BV1", "a\n")
    second = save(str(tmp_path), "f", "Same", "BV2", "b\n")
    assert Path(second).name == "Same_BV2.md"
```

- [ ] **Step 2: Run to verify they fail**

Run: `pytest tests/test_saver.py -v`
Expected: FAIL (`ModuleNotFoundError`)

- [ ] **Step 3: Write `saver.py`**

```python
"""Save a transcribed video as Markdown (vault-agnostic, no GBrain frontmatter).

Layout: <output_dir>/<folder_name>/<sanitized_title>.md (collision -> _<bvid>.md).
Content: first line '> https://www.bilibili.com/video/<bvid>', then the engine's main_markdown.
Sanitization rules reused verbatim from SP-5a's saver.
"""
from __future__ import annotations

import re
from pathlib import Path

_ILLEGAL = re.compile(r'[\\/"<>|]')


def sanitize_title(title: str) -> str:
    s = _ILLEGAL.sub(" ", title)
    s = s.replace("?", "？").replace(":", "：")
    s = s.strip()
    return s or "untitled"


def save(output_dir: str, folder_name: str, title: str, bvid: str, markdown: str) -> str:
    folder = Path(output_dir) / folder_name
    folder.mkdir(parents=True, exist_ok=True)
    base = sanitize_title(title)
    path = folder / f"{base}.md"
    if path.exists():
        path = folder / f"{base}_{bvid}.md"
    text = f"> https://www.bilibili.com/video/{bvid}\n{markdown}"
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8")
    return str(path)
```

- [ ] **Step 4: Run to verify pass**

Run: `pytest tests/test_saver.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/bilibili_watcher/saver.py tests/test_saver.py
git commit -m "feat(SP-5b): saver (subfolder/title, _<bvid> collision, > url first line)"
```

---

### Task 7: `watcher` — orchestrate a cycle (seen-skip → fetch → save → advance)

**Files:**
- Create: `src/bilibili_watcher/watcher.py`
- Test: `tests/test_watcher_integration.py` (unit-level cycle tests with fakes)

- [ ] **Step 1: Write the failing tests**

```python
from pathlib import Path
from bilibili_watcher.config import (
    WatcherConfig, CookieSource, EngineConfig, RenderConfig, FolderConfig,
)
from bilibili_watcher.favorites_client import BiliFavItem
from bilibili_watcher.watermark_store import WatermarkStore
from bilibili_watcher.fetcher import FetchedDoc
from bilibili_watcher.watcher import Watcher


def _config(tmp_path):
    return WatcherConfig(
        poll_interval_minutes=20,
        output_dir=str(tmp_path / "out"),
        state_dir=str(tmp_path / "state"),
        cookie_source=CookieSource("http://x", "u", "p"),
        engine=EngineConfig("b", "pid", "m"),
        render=RenderConfig(),
        folders=[FolderConfig(id="f1", name="Box1")],
    )


class _FakeCookies:
    def get_cookies(self):
        return {"SESSDATA": "s", "bili_jct": "j"}


class _FakeFavorites:
    def __init__(self, items):
        self._items = items
        self.calls = []

    def list_items(self, fid, cookies, since_fav_time=0):
        self.calls.append(since_fav_time)
        # emulate fav_time early-stop against the watermark passed in
        return [i for i in self._items if i.fav_time > since_fav_time]


def _item(bvid, ft):
    return BiliFavItem(bvid=bvid, fav_time=ft, title="T-" + bvid)


def test_full_cycle_then_second_is_noop_and_passes_watermark(tmp_path):
    items = [_item("BV1", 300), _item("BV2", 200)]
    fetch_calls = []

    def fake_fetch(bvid, cred):
        fetch_calls.append(bvid)
        return FetchedDoc(title="T-" + bvid, markdown="body\n")

    cfg = _config(tmp_path)
    fav = _FakeFavorites(items)
    store = WatermarkStore(cfg.state_dir)
    w = Watcher(cfg, _FakeCookies(), fav, fake_fetch, store)

    w.run_cycle()
    out = Path(cfg.output_dir) / "Box1"
    assert sorted(p.name for p in out.glob("*.md")) == ["T-BV1.md", "T-BV2.md"]
    assert fetch_calls == ["BV1", "BV2"]
    st = store.load("f1")
    assert st.watermark == 300 and st.seen == {"BV1", "BV2"}

    # second cycle: watermark 300 passed in -> fake returns nothing new -> no fetch, no file
    w.run_cycle()
    assert fav.calls == [0, 300]
    assert fetch_calls == ["BV1", "BV2"]


def test_fetch_failure_holds_watermark_below_failure_and_retries(tmp_path):
    items = [_item("BV1", 300), _item("BV2", 200)]
    attempts = {"BV2": 0}

    def flaky_fetch(bvid, cred):
        if bvid == "BV2":
            attempts["BV2"] += 1
            if attempts["BV2"] == 1:
                return None                       # BV2 fails first cycle
        return FetchedDoc(title="T-" + bvid, markdown="ok\n")

    cfg = _config(tmp_path)
    store = WatermarkStore(cfg.state_dir)
    w = Watcher(cfg, _FakeCookies(), _FakeFavorites(items), flaky_fetch, store)

    w.run_cycle()
    st = store.load("f1")
    assert st.seen == {"BV1"}                      # BV2 not saved
    assert st.watermark == 199                     # held below the failure (200-1) per §5
    assert (Path(cfg.output_dir) / "Box1" / "T-BV1.md").exists()

    w.run_cycle()                                  # re-lists fav_time>199 -> BV1(seen,skip)+BV2(retry)
    st = store.load("f1")
    assert st.seen == {"BV1", "BV2"}
    assert st.watermark == 300


def test_no_sessdata_skips_cycle(tmp_path):
    class _NoSess:
        def get_cookies(self):
            return {"bili_jct": "j"}              # no SESSDATA

    cfg = _config(tmp_path)
    fav = _FakeFavorites([_item("BV1", 1)])
    Watcher(cfg, _NoSess(), fav, lambda b, c: None, WatermarkStore(cfg.state_dir)).run_cycle()
    assert fav.calls == []                          # never listed


def test_cookie_failure_skips_without_crashing(tmp_path):
    class _Boom:
        def get_cookies(self):
            raise RuntimeError("SP-1 down")

    cfg = _config(tmp_path)
    fav = _FakeFavorites([_item("BV1", 1)])
    Watcher(cfg, _Boom(), fav, lambda b, c: None, WatermarkStore(cfg.state_dir)).run_cycle()
    assert fav.calls == []


def test_listing_error_skips_folder_without_crashing(tmp_path):
    class _BoomFav:
        calls = []

        def list_items(self, fid, cookies, since_fav_time=0):
            raise RuntimeError("403")

    cfg = _config(tmp_path)
    Watcher(cfg, _FakeCookies(), _BoomFav(), lambda b, c: None, WatermarkStore(cfg.state_dir)).run_cycle()
    # must not raise; nothing saved
    assert not (Path(cfg.output_dir) / "Box1").exists()


def test_unexpected_fetch_exception_does_not_crash_cycle(tmp_path):
    items = [_item("BV1", 300), _item("BV2", 200)]

    def fetch_fn(bvid, cred):
        if bvid == "BV1":
            raise RuntimeError("engine leaked a non-BilibiliEngineError")
        return FetchedDoc(title="T-BV2", markdown="ok\n")

    cfg = _config(tmp_path)
    store = WatermarkStore(cfg.state_dir)
    Watcher(cfg, _FakeCookies(), _FakeFavorites(items), fetch_fn, store).run_cycle()
    st = store.load("f1")
    assert st.seen == {"BV2"}                       # BV1 (raised) not seen
    assert st.watermark == 199                      # treated as a failure at 300 -> wait, see note
    assert (Path(cfg.output_dir) / "Box1" / "T-BV2.md").exists()
    assert not (Path(cfg.output_dir) / "Box1" / "T-BV1.md").exists()


def test_corrupt_state_file_skips_folder(tmp_path):
    cfg = _config(tmp_path)
    state = Path(cfg.state_dir)
    state.mkdir(parents=True, exist_ok=True)
    (state / "state-f1.json").write_text("{bad json", encoding="utf-8")
    fetch_calls = []
    Watcher(cfg, _FakeCookies(), _FakeFavorites([_item("BV1", 1)]),
            lambda b, c: fetch_calls.append(b), WatermarkStore(cfg.state_dir)).run_cycle()
    assert fetch_calls == []                          # folder skipped
```

> Note for the implementer: in `test_unexpected_fetch_exception...`, BV1 raises *before* BV2; the
> watcher treats any item exception as a failure (records its `fav_time` in `failed`). With BV1=300
> failing, `next_watermark(0, listed=[300,200], failed=[300]) = 299`... but BV2=200 succeeded and is
> seen. Re-check the assertion when you implement: the correct expected watermark is
> `min(failed)-1`. Adjust the asserted value to match the rule you implemented (the rule, §5, is the
> source of truth; this test documents intent — fix the literal to the computed value and keep the
> behavioral asserts on `seen`/files).

- [ ] **Step 2: Run to verify they fail**

Run: `pytest tests/test_watcher_integration.py -v`
Expected: FAIL (`ModuleNotFoundError: bilibili_watcher.watcher`)

- [ ] **Step 3: Write `watcher.py`**

```python
"""Orchestrate one poll cycle and wire the real components.

Collaborators are injected so the cycle is fully testable with fakes; build_watcher() supplies the
real implementations. The daemon must never crash — every failure path logs and continues. Per folder:
list (fav_time early-stop against the stored watermark) -> for each unseen video, fetch via the engine
and save -> advance the watermark per §5 (held below any failure so failures are retried).
"""
from __future__ import annotations

import logging

from .config import WatcherConfig
from .cookie_provider import CookieProvider
from .favorites_client import FavoritesClient
from .fetcher import FetchedDoc, FetcherFn, build_credential, make_fetcher
from .saver import save as default_save
from .watermark_store import FolderState, WatermarkStore, next_watermark

log = logging.getLogger("bilibili_watcher.watcher")


class Watcher:
    def __init__(self, config, cookie_provider, favorites_client,
                 fetcher_fn: FetcherFn, watermark_store: WatermarkStore, saver_fn=default_save):
        self._cfg = config
        self._cookies = cookie_provider
        self._favorites = favorites_client
        self._fetch = fetcher_fn
        self._store = watermark_store
        self._save = saver_fn

    def run_cycle(self) -> None:
        try:
            cookies = self._cookies.get_cookies()
        except Exception as e:  # noqa: BLE001 - daemon must not crash
            log.error("cookie pull failed: %s — skipping cycle", e)
            return
        if not cookies or "SESSDATA" not in cookies:
            log.error("no bilibili.com SESSDATA available — skipping cycle")
            return
        credential = build_credential(cookies)
        for folder in self._cfg.folders:
            self._poll_folder(folder, cookies, credential)

    def _poll_folder(self, folder, cookies, credential) -> None:
        try:
            state = self._store.load(folder.id)
        except Exception as e:  # noqa: BLE001 - a corrupt state file must not crash the cycle
            log.error("loading state for folder %s failed: %s — skipping", folder.id, e)
            return
        try:
            items = self._favorites.list_items(folder.id, cookies, since_fav_time=state.watermark)
        except Exception as e:  # noqa: BLE001
            log.error("listing folder %s failed: %s", folder.id, e)
            return

        listed = [it.fav_time for it in items]
        failed: list[int] = []
        new_count = 0
        for item in items:
            if item.bvid in state.seen:
                continue
            try:
                doc = self._fetch(item.bvid, credential)
                if doc is None:
                    failed.append(item.fav_time)   # transcribe failed -> retry next cycle
                    continue
                self._save(self._cfg.output_dir, folder.name, doc.title, item.bvid, doc.markdown)
            except Exception as e:  # noqa: BLE001 - one bad item must never abort the cycle
                log.error("processing bvid %s failed: %s", item.bvid, e)
                failed.append(item.fav_time)
                continue
            state.seen.add(item.bvid)
            self._store.save(folder.id, state)     # persist seen immediately (1-item crash window)
            new_count += 1

        state.watermark = next_watermark(state.watermark, listed, failed)
        self._store.save(folder.id, state)
        log.info("folder %s (%s): %d new, watermark=%d", folder.id, folder.name, new_count, state.watermark)


def build_watcher(config: WatcherConfig) -> Watcher:
    from bilibili import BilibiliEngine, EngineConfig as _EngCfg
    engine = BilibiliEngine(_EngCfg(
        bn_base_url=config.engine.bn_base_url,
        provider_id=config.engine.provider_id,
        model_name=config.engine.model_name,
    ))
    return Watcher(
        config=config,
        cookie_provider=CookieProvider(config.cookie_source),
        favorites_client=FavoritesClient(),
        fetcher_fn=make_fetcher(engine, config.render),
        watermark_store=WatermarkStore(config.state_dir),
    )
```

> Implementer note on `build_watcher`'s `EngineConfig`: confirm the exact `EngineConfig` field names
> against `Engine/bilibili/docs/interface.md §3` (`BilibiliEngine(EngineConfig(bn_base_url=...,
> provider_id=..., model_name=...))`). If the frozen engine's `EngineConfig` differs, adapt the kwargs
> — this is the one place that touches the engine's constructor.

- [ ] **Step 4: Run to verify pass**

Run: `pytest tests/test_watcher_integration.py -v`
Expected: PASS (fix the one documented literal in `test_unexpected_fetch_exception...` to the value the §5 rule computes, then green)

- [ ] **Step 5: Commit**

```bash
git add src/bilibili_watcher/watcher.py tests/test_watcher_integration.py
git commit -m "feat(SP-5b): watcher cycle (seen-skip -> fetch -> save -> §5 watermark advance)"
```

---

### Task 8: `__main__` — CLI (`--once` / scheduler)

**Files:**
- Create: `src/bilibili_watcher/__main__.py`
- Test: append to `tests/test_watcher_integration.py`

- [ ] **Step 1: Write the failing tests** (append)

```python
def test_main_once_runs_single_cycle(monkeypatch):
    import bilibili_watcher.__main__ as m
    calls = {"n": 0}

    class _W:
        def run_cycle(self):
            calls["n"] += 1

    monkeypatch.setattr(m, "build_watcher", lambda cfg: _W())
    monkeypatch.setattr(m, "load_config", lambda path: object())
    m.main(["--once", "--config", "irrelevant.yaml"])
    assert calls["n"] == 1


def test_main_default_schedules_interval_job(monkeypatch):
    import types as _t
    import bilibili_watcher.__main__ as m
    cycles = {"n": 0}

    class _W:
        def run_cycle(self):
            cycles["n"] += 1

    captured = {}

    class _FakeScheduler:
        def add_job(self, func, **kwargs):
            captured["kwargs"] = kwargs

        def start(self):
            captured["started"] = True

        def shutdown(self):
            pass

    fake_cfg = _t.SimpleNamespace(poll_interval_minutes=20, folders=[1, 2])
    monkeypatch.setattr(m, "load_config", lambda path: fake_cfg)
    monkeypatch.setattr(m, "build_watcher", lambda cfg: _W())
    monkeypatch.setattr(m, "BlockingScheduler", lambda: _FakeScheduler())
    m.main([])
    assert cycles["n"] == 1
    assert captured.get("started") is True
    assert captured["kwargs"]["trigger"] == "interval"
    assert captured["kwargs"]["minutes"] == 20
    assert captured["kwargs"]["max_instances"] == 1
```

- [ ] **Step 2: Run to verify they fail**

Run: `pytest tests/test_watcher_integration.py -k main -v`
Expected: FAIL (`ModuleNotFoundError: bilibili_watcher.__main__`)

- [ ] **Step 3: Write `__main__.py`**

```python
"""CLI entrypoint: `python -m bilibili_watcher [--once] [--config PATH]`.

Default: start a BlockingScheduler interval job (max_instances=1) and run forever.
--once: run a single cycle and exit (smoke / CI).
"""
from __future__ import annotations

import argparse
import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from .config import load_config
from .watcher import build_watcher


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="bilibili_watcher")
    parser.add_argument("--config", default="config/bilibili-watcher.yaml", help="path to the YAML config")
    parser.add_argument("--once", action="store_true", help="run a single poll cycle and exit (smoke / CI)")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    config = load_config(args.config)
    watcher = build_watcher(config)

    if args.once:
        watcher.run_cycle()
        return

    scheduler = BlockingScheduler()
    scheduler.add_job(
        watcher.run_cycle, trigger="interval",
        minutes=config.poll_interval_minutes, max_instances=1, coalesce=True,
    )
    logging.getLogger("bilibili_watcher").info(
        "starting scheduler: every %d min, %d folder(s)", config.poll_interval_minutes, len(config.folders),
    )
    watcher.run_cycle()   # run once immediately, then APScheduler fires every interval
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run full suite**

Run: `pytest -q`
Expected: PASS (all tasks green; ~30 tests)

- [ ] **Step 5: Commit**

```bash
git add src/bilibili_watcher/__main__.py tests/test_watcher_integration.py
git commit -m "feat(SP-5b): __main__ CLI (--once + BlockingScheduler interval job)"
```

---

### Task 9: Deployment artifacts

**Files:**
- Create: `Service/crawl/bilibili-watcher/Dockerfile`
- Create: `Service/crawl/bilibili-watcher/docker-compose.yml`
- Create: `Service/crawl/bilibili-watcher/config/bilibili-watcher.example.yaml`

- [ ] **Step 1: Create `Dockerfile`**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# The frozen SP-4a engine is a sibling package in the monorepo; copy + install both.
COPY Engine/bilibili /app/engine-bilibili
COPY Service/crawl/bilibili-watcher /app/bilibili-watcher

RUN pip install --no-cache-dir /app/engine-bilibili \
    && pip install --no-cache-dir /app/bilibili-watcher

# config + data are mounted at runtime (see docker-compose.yml)
ENTRYPOINT ["python", "-m", "bilibili_watcher", "--config", "/config/bilibili-watcher.yaml"]
```

- [ ] **Step 2: Create `docker-compose.yml`**

```yaml
services:
  bilibili-watcher:
    build:
      context: ../../..                      # repo root, so Engine/bilibili is in the build context
      dockerfile: Service/crawl/bilibili-watcher/Dockerfile
    container_name: jarvankb-bilibili-watcher
    restart: unless-stopped
    network_mode: host                       # must reach BN at 127.0.0.1:3015 + SP-1 at :48088
    volumes:
      - ./config:/config:ro                  # put bilibili-watcher.yaml here
      - ./data/state:/data/state             # per-folder state JSON (persisted)
      - ./data/output:/data/output           # saved Markdown
    # bilibili + SP-1 are reached direct (clients set trust_env=False); no proxy env needed.
```

- [ ] **Step 3: Create `config/bilibili-watcher.example.yaml`**

```yaml
# Copy to config/bilibili-watcher.yaml and fill in your values.
poll_interval_minutes: 20            # SP-0: 15-30; how often to poll
output_dir: /data/output             # where Markdown is written (may point at a vault subdir)
state_dir: /data/state               # per-folder state-<id>.json (mount a volume to persist)

cookie_source:                       # SP-1 CookieManager connection
  base_url: http://127.0.0.1:48088   # or LAN/public entry from cookie-manager interface.md §8
  uuid: <your-cookiecloud-box-uuid>
  password: <your-cookiecloud-box-password>
  auth_token: <optional; set only if the box has server.auth_token>

engine:                              # SP-4a Bilibili engine (BiliNote backend)
  bn_base_url: http://127.0.0.1:3015 # BN backend (host maps :8483; see crawl-pipeline.md §B站链路)
  provider_id: <BN provider id from GET /api/get_all_providers>
  model_name: <model name registered in BN>

render:
  include_transcript: true
  include_timestamps: false
  split_transcript: false

folders:                             # the user's own account; list one or more (id = media_id)
  - id: "2216104467"                 # AI生成
    name: "AI生成"
  - id: "1195057867"                 # 编程折腾
    name: "编程折腾"
```

- [ ] **Step 4: Verify compose config parses**

Run: `cd Service/crawl/bilibili-watcher && docker compose config -q && echo OK`
Expected: `OK` (no schema error). If docker is unavailable, skip + note it.

- [ ] **Step 5: Commit**

```bash
git add Service/crawl/bilibili-watcher/Dockerfile Service/crawl/bilibili-watcher/docker-compose.yml Service/crawl/bilibili-watcher/config/bilibili-watcher.example.yaml
git commit -m "feat(SP-5b): deployment artifacts (Dockerfile, compose, example config)"
```

---

### Task 10: Freeze module `docs/`

**Files:**
- Modify: `Service/crawl/bilibili-watcher/docs/README.md`
- Modify: `Service/crawl/bilibili-watcher/docs/interface.md`
- Modify: `Service/crawl/bilibili-watcher/docs/architecture.md`
- Create: `Service/crawl/bilibili-watcher/docs/runbook.md`
- Modify: `Service/crawl/bilibili-watcher/docs/RepoMem/architecture.md`
- Modify: `Service/crawl/bilibili-watcher/docs/RepoMem/decisions.md`

- [ ] **Step 1: Write the H2A docs (中文)** — `README.md` (what/input/output/install), `interface.md`
  (config schema table + CLI `python -m bilibili_watcher [--once] [--config PATH]`), `architecture.md`
  (external summary: 7 components, BlockingScheduler, fav_time+seen watermark, engine dependency),
  `runbook.md` (deploy/config/credentials/**BN dependency at 127.0.0.1:3015**/common failures incl.
  expired-cookie -101 + BN-down). Model them on `Service/crawl/zhihu-watcher/docs/*` (same sections).

- [ ] **Step 2: Write the A2A docs (English)** — `RepoMem/architecture.md` (internal layering, the §5
  watermark advance rule, cookie→credential path), `RepoMem/decisions.md` (decision log **D1–D8** from
  the design's §3, append-only newest-first).

- [ ] **Step 3: Commit**

```bash
git add Service/crawl/bilibili-watcher/docs
git commit -m "docs(SP-5b): freeze module docs (README/interface/architecture/runbook + RepoMem)"
```

---

### Task 11: Live smoke (verification-before-completion gate)

> This is the single mandatory verification gate. It needs USER ops: BN up at `127.0.0.1:3015`
> (already up), a fresh `bilibili.com` cookie in SP-1, and a real config. Surface those as a Dashboard
> row + note to SubOrche; the gate does NOT block Tasks 0–10. Do NOT claim "done" without this evidence.

- [ ] **Step 1: Prepare a real `config/bilibili-watcher.yaml`** (gitignored secrets) with the real SP-1
  box uuid/password (+auth_token), the real BN `provider_id`/`model_name` (from `GET /api/get_all_providers`),
  `output_dir`/`state_dir` pointing at temp dirs, and the 2 folders `2216104467` + `1195057867`.

- [ ] **Step 2: First `--once`**

Run: `python -m bilibili_watcher --once --config config/bilibili-watcher.yaml`
Expected: logs show cookies pulled, folder listed, ≥1 new video transcribed via the engine (BN), Markdown
written under `<output_dir>/AI生成/` (or 编程折腾). Capture the log + `ls` of the output + the saved file head.

- [ ] **Step 3: Show the state JSON**

Run: `cat <state_dir>/state-2216104467.json`
Expected: `{"watermark": <fav_time>, "seen": ["BV...", ...]}`.

- [ ] **Step 4: Second `--once` (dedup invariant)**

Run: `python -m bilibili_watcher --once --config config/bilibili-watcher.yaml`
Expected: logs show early-stop / 0 new; **no new files**; state unchanged. This is the core daemon invariant.

- [ ] **Step 5: Record evidence** in `docs/RepoMem/temp/sp5b-bilibili-watcher/smoke-evidence.md` (logs +
  file listing + state JSON). If BN is down / cookie expired → write a blocker letter to SubOrche +
  Dashboard row instead of claiming done.

---

## Self-Review

**Spec coverage:**
- §3 D1 cookie-pull → Task 2. D2 watermark → Tasks 3 (early-stop) + 4 (advance rule) + 7 (wiring). D3 scheduler → Task 8. D4 engine output/RenderOptions → Task 5 + 1 (render config). D5 filename → Task 6. D6 type==2 → Task 3. D7 folders → Task 1/9 config. D8 interval → Task 1/8.
- §4 components: config(1) cookie_provider(2) favorites_client(3) watermark_store(4) fetcher(5) saver(6) watcher(7) + __main__(8). ✓ all 7 + CLI.
- §5 watermark advance rule → Task 4 `next_watermark` + Task 7 wiring + dedicated tests.
- §7 error handling → Task 7 tests (cookie fail, no SESSDATA, listing error, unexpected exception, corrupt state) + Task 3 (non-200/code).
- §8 deployment → Task 9. §9 testing → unit tasks + Task 11 smoke. §10 module docs → Task 10.
- §11 out-of-v1 → not implemented (correct).

**Placeholder scan:** No TBD/TODO. Two explicit implementer notes (the `test_unexpected...` watermark literal; the engine `EngineConfig` field-name confirmation) are flagged with the rule to follow, not hand-waves.

**Type consistency:** `FolderState(watermark, seen)`, `BiliFavItem(bvid, fav_time, title)`, `FetchedDoc(title, markdown)`, `next_watermark(prev, listed, failed)`, `make_fetcher(engine, render)`, `build_credential(cookies)`, `save(output_dir, folder_name, title, bvid, markdown)`, `FavoritesClient.list_items(folder_id, cookies, since_fav_time=0)`, `WatermarkStore.{load,save}` — all names consistent across tasks 1–8 and the watcher wiring.
