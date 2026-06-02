# SP-5a Zhihu Watcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A standalone daemon that polls the user's Zhihu favorites/collection folder(s) on a schedule, detects newly-favorited items via a persistent seen-id set, fetches each through the frozen SP-2 engine, and saves Markdown to a configured output dir.

**Architecture:** `APScheduler.BlockingScheduler` runs one synchronous "poll all collections" cycle every N minutes (`max_instances=1`). Per collection: pull cookies from SP-1 (HTTP GET + in-memory decrypt), list items via the Zhihu collections API (offset paging, plain cookie, no signing), skip items already in the seen-set, fetch new ones via `zhihu.fetch`, save Markdown (reference-repo format), then persist the seen-id. Seven focused modules, each independently testable.

**Tech Stack:** Python ≥3.11, `httpx` (sync), `cryptography` (AES decrypt), `apscheduler`, `pyyaml`, `pytest` + `pytest-httpx`. Consumes the sibling `zhihu-engine` package (`from zhihu import fetch`). `src/` layout, mirroring `Engine/zhihu`.

**Spec:** `../specs/2026-06-02-SP-5a-zhihu-watcher-design.md` (read §2 API findings, §3 components, §4 output format, §5 error handling).

---

## File Structure

```
Service/crawl/zhihu-watcher/
├── pyproject.toml                         # package metadata, deps, console_script
├── src/zhihu_watcher/
│   ├── __init__.py
│   ├── __main__.py                        # CLI: python -m zhihu_watcher [--once] [--config PATH]
│   ├── config.py                          # load + validate YAML -> dataclasses
│   ├── cookie_provider.py                 # SP-1 GET + decrypt (legacy / aes-128-cbc-fixed) + extract
│   ├── favorites_client.py                # Zhihu collections API offset paging -> CollectionItem
│   ├── watermark_store.py                 # seen-id JSON store (load / save, atomic)
│   ├── fetcher.py                         # wrap frozen SP-2 zhihu.fetch -> FetchedDoc | None
│   ├── saver.py                           # markdown save (sanitize, collision, > url, subfolder)
│   └── watcher.py                         # Watcher.run_cycle + build_watcher wiring
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_config.py
│   ├── test_cookie_provider.py
│   ├── test_favorites_client.py
│   ├── test_watermark_store.py
│   ├── test_fetcher.py
│   ├── test_saver.py
│   └── test_watcher_integration.py
├── config/zhihu-watcher.example.yaml
├── Dockerfile
├── docker-compose.yml
└── docs/  (README / interface / architecture / runbook + RepoMem — frozen in Task 9)
```

Responsibilities are one-per-file; `watcher.py` only wires + orchestrates and holds no I/O logic of its own (all I/O lives in the injected components, which is what makes the integration test mockable).

---

## Task 0: Project scaffold & dev environment

**Files:**
- Create: `Service/crawl/zhihu-watcher/pyproject.toml`
- Create: `Service/crawl/zhihu-watcher/src/zhihu_watcher/__init__.py`
- Create: `Service/crawl/zhihu-watcher/tests/__init__.py`
- Create: `Service/crawl/zhihu-watcher/tests/conftest.py`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "zhihu-watcher"
version = "0.1.0"
description = "Polling watcher for Zhihu favorites: new items -> SP-2 fetch -> Markdown"
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
zhihu-watcher = "zhihu_watcher.__main__:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create empty package + test init files**

`src/zhihu_watcher/__init__.py`:
```python
"""SP-5a Zhihu favorites watcher."""
```

`tests/__init__.py`: (empty file)

- [ ] **Step 3: Write `tests/conftest.py`** (silence noisy logging during tests)

```python
import logging
import pytest


@pytest.fixture(autouse=True)
def _quiet_logging():
    logging.getLogger("zhihu_watcher").setLevel(logging.CRITICAL)
```

- [ ] **Step 4: Create the dev environment and install both packages editable**

Run (from repo root):
```bash
cd Service/crawl/zhihu-watcher
python3 -m venv .venv
.venv/bin/pip install -U pip
.venv/bin/pip install -e ../../../Engine/zhihu        # the frozen SP-2 engine (provides `zhihu`)
.venv/bin/pip install -e ".[dev]"                     # this package + dev deps
```
Expected: both installs succeed; `cryptography`, `apscheduler`, `pyyaml`, `httpx`, `pytest`, `pytest-httpx`, and `zhihu-engine` are present.

- [ ] **Step 5: Sanity-check imports**

Run: `.venv/bin/python -c "import zhihu, cryptography, apscheduler, yaml, httpx; print('ok')"`
Expected: prints `ok`.

- [ ] **Step 6: Commit**

```bash
git add Service/crawl/zhihu-watcher/pyproject.toml Service/crawl/zhihu-watcher/src Service/crawl/zhihu-watcher/tests
git commit -m "feat(SP-5a): scaffold zhihu-watcher package + dev env"
```

> NOTE: `.venv/` must not be committed. If there is no module-local `.gitignore` covering it, add `.venv/` to `Service/crawl/zhihu-watcher/.gitignore` in this commit.

---

## Task 1: `config.py` — load & validate YAML

**Files:**
- Create: `src/zhihu_watcher/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
import textwrap
import pytest
from zhihu_watcher.config import load_config, WatcherConfig


def _write(tmp_path, text):
    p = tmp_path / "cfg.yaml"
    p.write_text(textwrap.dedent(text), encoding="utf-8")
    return str(p)


def test_load_valid_config(tmp_path):
    path = _write(tmp_path, """
        poll_interval_minutes: 45
        output_dir: /data/output
        state_dir: /data/state
        cookie_source:
          base_url: http://127.0.0.1:48088
          uuid: box-uuid
          password: box-pass
        collections:
          - id: "630144608"
            name: AI-papers
          - id: "999"
    """)
    cfg = load_config(path)
    assert isinstance(cfg, WatcherConfig)
    assert cfg.poll_interval_minutes == 45
    assert cfg.output_dir == "/data/output"
    assert cfg.cookie_source.base_url == "http://127.0.0.1:48088"
    assert cfg.cookie_source.uuid == "box-uuid"
    assert len(cfg.collections) == 2
    assert cfg.collections[0].id == "630144608"
    assert cfg.collections[0].name == "AI-papers"
    # name defaults to id when omitted
    assert cfg.collections[1].name == "999"


def test_missing_collections_raises(tmp_path):
    path = _write(tmp_path, """
        poll_interval_minutes: 45
        output_dir: /data/output
        state_dir: /data/state
        cookie_source:
          base_url: http://x
          uuid: u
          password: p
        collections: []
    """)
    with pytest.raises(ValueError, match="at least one collection"):
        load_config(path)


def test_missing_cookie_field_raises(tmp_path):
    path = _write(tmp_path, """
        poll_interval_minutes: 45
        output_dir: /data/output
        state_dir: /data/state
        cookie_source:
          base_url: http://x
          uuid: u
        collections:
          - id: "1"
    """)
    with pytest.raises(ValueError, match="password"):
        load_config(path)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'zhihu_watcher.config'`.

- [ ] **Step 3: Write minimal implementation**

```python
"""Load and validate the watcher YAML config into dataclasses."""
from __future__ import annotations

from dataclasses import dataclass

import yaml


@dataclass
class CollectionConfig:
    id: str
    name: str


@dataclass
class CookieSource:
    base_url: str
    uuid: str
    password: str


@dataclass
class WatcherConfig:
    poll_interval_minutes: int
    output_dir: str
    state_dir: str
    cookie_source: CookieSource
    collections: list[CollectionConfig]


def _require(d: dict, key: str, ctx: str):
    if key not in d or d[key] in (None, ""):
        raise ValueError(f"config: missing required field '{key}' in {ctx}")
    return d[key]


def load_config(path: str) -> WatcherConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    cs_raw = _require(raw, "cookie_source", "root")
    cookie_source = CookieSource(
        base_url=_require(cs_raw, "base_url", "cookie_source"),
        uuid=_require(cs_raw, "uuid", "cookie_source"),
        password=_require(cs_raw, "password", "cookie_source"),
    )

    colls_raw = raw.get("collections") or []
    if not colls_raw:
        raise ValueError("config: must define at least one collection")
    collections = []
    for c in colls_raw:
        cid = str(_require(c, "id", "collection"))
        collections.append(CollectionConfig(id=cid, name=str(c.get("name") or cid)))

    interval = int(raw.get("poll_interval_minutes", 45))
    if interval <= 0:
        raise ValueError("config: poll_interval_minutes must be > 0")

    return WatcherConfig(
        poll_interval_minutes=interval,
        output_dir=_require(raw, "output_dir", "root"),
        state_dir=_require(raw, "state_dir", "root"),
        cookie_source=cookie_source,
        collections=collections,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_config.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add src/zhihu_watcher/config.py tests/test_config.py
git commit -m "feat(SP-5a): config loader with validation"
```

---

## Task 2: `cookie_provider.py` — decrypt + extract (crypto core)

This is the fiddliest piece. Decryption is built and tested first as pure functions against **known vectors** (generated 2026-06-02, round-trip verified), then wrapped with the SP-1 HTTP GET.

**Files:**
- Create: `src/zhihu_watcher/cookie_provider.py`
- Test: `tests/test_cookie_provider.py`

- [ ] **Step 1: Write the failing test (decryption against known vectors)**

```python
import httpx
import pytest
from zhihu_watcher.cookie_provider import (
    derive_key,
    decrypt_payload,
    extract_zhihu_cookies,
    CookieProvider,
)
from zhihu_watcher.config import CookieSource

# Known vectors (generated 2026-06-02, round-trip verified with `cryptography`).
# uuid="test-box-uuid", password="test-password" -> the_key="7f0b629578cb94ce"
# inner plaintext:
# {"cookie_data":{".zhihu.com":[{"name":"z_c0","value":"ZC0TOKEN"},
#  {"name":"d_c0","value":"DC0DEVID"}]},"local_storage_data":{},
#  "update_time":"2026-06-02T00:00:00Z"}
UUID = "test-box-uuid"
PASSWORD = "test-password"
LEGACY_ENC = (
    "U2FsdGVkX18BAgMEBQYHCKJedRci3iuczFZeVrfBOKug/+Yss9Tg/xdZnSBkCzRwMkYy"
    "rexR5JZr7Olk9bIIS57PteFYfqawOj9KklEJrCukYem2RoRyhh+JKIZGCo1Ou77/yrzF"
    "2z6QaCd0hMvlXRgf14BuLo3/s8//vedmEuVgG1vyIlhzaBKo2ZCFVHa3D/itWb7iet0g"
    "e9446yKImum9etaJ5O1jbSjBAEpPFaCGEttB4mcisg3wMQNqn6Wm"
)
FIXED_ENC = (
    "kyIjmJjByCjZqPaocBuQa8u0ETzs8iT/Ws11uvwGs5BHdY1BeNDQsOWm67tx11IttqpZ"
    "Mee0uoLPf0NFC3mpXsauK5cuccJ4F8y9SbzL3Q725FSzK+gBXyZRitWMaDBOH9d+RWy2"
    "EdLCTp5SVDh33dmWUxwQjsdkRgrxqAI1eFBi+NuuM0gipUx2Ws4P0k9GXFd2Tgn3YrRz"
    "AGJ6WG3DBsOGEuiCopuX3t3BSfv87S8="
)


def test_derive_key():
    assert derive_key(UUID, PASSWORD) == "7f0b629578cb94ce"


def test_decrypt_legacy():
    payload = decrypt_payload(LEGACY_ENC, "legacy", UUID, PASSWORD)
    assert payload["cookie_data"][".zhihu.com"][0]["name"] == "z_c0"


def test_decrypt_fixed():
    payload = decrypt_payload(FIXED_ENC, "aes-128-cbc-fixed", UUID, PASSWORD)
    assert payload["cookie_data"][".zhihu.com"][1]["value"] == "DC0DEVID"


def test_unknown_crypto_type_raises():
    with pytest.raises(ValueError, match="crypto_type"):
        decrypt_payload(FIXED_ENC, "rot13", UUID, PASSWORD)


def test_extract_zhihu_cookies_merges_zhihu_domains():
    payload = {
        "cookie_data": {
            ".zhihu.com": [{"name": "z_c0", "value": "A"}],
            "www.zhihu.com": [{"name": "d_c0", "value": "B"}],
            ".other.com": [{"name": "x", "value": "C"}],
        }
    }
    out = extract_zhihu_cookies(payload)
    assert out == {"z_c0": "A", "d_c0": "B"}


def test_provider_get_cookies_end_to_end():
    src = CookieSource(base_url="http://sp1.local", uuid=UUID, password=PASSWORD)

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == f"/get/{UUID}"
        return httpx.Response(200, json={"encrypted": LEGACY_ENC, "crypto_type": "legacy"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = CookieProvider(src, http_client=client)
    cookies = provider.get_cookies()
    assert cookies == {"z_c0": "ZC0TOKEN", "d_c0": "DC0DEVID"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_cookie_provider.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'zhihu_watcher.cookie_provider'`.

- [ ] **Step 3: Write minimal implementation**

```python
"""Pull the latest .zhihu.com cookies from SP-1 CookieManager and decrypt them in memory.

Cookies are NEVER written to disk; only returned as a transient dict for fetch(cookies=...).
Mirrors the CookieCloud crypto protocol documented in
Service/crawl/cookie-manager/docs/interface.md §3.
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

log = logging.getLogger("zhihu_watcher.cookie_provider")


def derive_key(uuid: str, password: str) -> str:
    """the_key = md5(uuid + '-' + password).hex[:16] (UTF-8, literal hyphen)."""
    return hashlib.md5(f"{uuid}-{password}".encode("utf-8")).hexdigest()[:16]


def _evp_bytes_to_key(pw: bytes, salt: bytes, key_len: int, iv_len: int) -> tuple[bytes, bytes]:
    """OpenSSL EVP_BytesToKey with MD5 (1 iteration), as crypto-js / OpenSSL use."""
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
    """OpenSSL 'Salted__' envelope + EVP_BytesToKey(MD5) + AES-256-CBC + PKCS7."""
    raw = base64.b64decode(encrypted)
    if raw[:8] != b"Salted__":
        raise ValueError("legacy ciphertext is not a 'Salted__' envelope")
    salt = raw[8:16]
    ct = raw[16:]
    key, iv = _evp_bytes_to_key(the_key.encode("utf-8"), salt, 32, 16)
    return json.loads(_aes_cbc_decrypt(key, iv, ct).decode("utf-8"))


def decrypt_fixed(encrypted: str, the_key: str) -> dict:
    """aes-128-cbc-fixed: 16-byte key = the_key UTF-8, zero IV, AES-128-CBC + PKCS7, bare base64."""
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


def extract_zhihu_cookies(payload: dict) -> dict[str, str]:
    """Merge cookies from every domain whose key ends with 'zhihu.com'."""
    out: dict[str, str] = {}
    for domain, cookies in (payload.get("cookie_data") or {}).items():
        if str(domain).endswith("zhihu.com"):
            for c in cookies:
                out[c["name"]] = c["value"]
    return out


class CookieProvider:
    def __init__(self, cookie_source: CookieSource, http_client: httpx.Client | None = None):
        self._src = cookie_source
        self._client = http_client or httpx.Client(timeout=30.0)

    def get_cookies(self) -> dict[str, str]:
        url = f"{self._src.base_url.rstrip('/')}/get/{self._src.uuid}"
        resp = self._client.get(url)
        resp.raise_for_status()
        body = resp.json()
        payload = decrypt_payload(
            body["encrypted"],
            body.get("crypto_type", "legacy"),
            self._src.uuid,
            self._src.password,
        )
        cookies = extract_zhihu_cookies(payload)
        log.info("pulled %d .zhihu.com cookies from SP-1", len(cookies))
        return cookies
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_cookie_provider.py -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add src/zhihu_watcher/cookie_provider.py tests/test_cookie_provider.py
git commit -m "feat(SP-5a): SP-1 cookie pull + in-memory decrypt (legacy + aes-128-cbc-fixed)"
```

---

## Task 3: `favorites_client.py` — collections API offset paging

**Files:**
- Create: `src/zhihu_watcher/favorites_client.py`
- Test: `tests/test_favorites_client.py`

- [ ] **Step 1: Write the failing test**

```python
import httpx
import pytest
from zhihu_watcher.favorites_client import (
    FavoritesClient,
    CollectionItem,
    ZhihuApiError,
    collection_id_from_url,
)


def test_collection_id_from_url():
    assert collection_id_from_url("https://www.zhihu.com/collection/630144608") == "630144608"
    assert collection_id_from_url("https://www.zhihu.com/collection/630144608?x=1") == "630144608"
    assert collection_id_from_url("630144608") == "630144608"


def _page(items, totals, is_end):
    return {"data": items, "paging": {"totals": totals, "is_end": is_end}}


def _answer_item(cid):
    return {"content": {"type": "answer", "id": cid,
                        "url": f"https://www.zhihu.com/question/1/answer/{cid}",
                        "question": {"title": f"Q{cid}"}}}


def _article_item(cid):
    return {"content": {"type": "article", "id": cid,
                        "url": f"https://zhuanlan.zhihu.com/p/{cid}", "title": f"Art{cid}"}}


def test_paging_walks_all_pages_and_parses_items():
    pages = {
        0: _page([_answer_item("11"), _article_item("12")], totals=3, is_end=False),
        20: _page([_answer_item("13")], totals=3, is_end=True),
    }

    def handler(request: httpx.Request) -> httpx.Response:
        # no signing header must be present
        assert "x-zse-96" not in {k.lower() for k in request.headers}
        offset = int(dict(request.url.params)["offset"])
        return httpx.Response(200, json=pages[offset])

    client = httpx.Client(transport=httpx.MockTransport(handler))
    fc = FavoritesClient(http_client=client)
    items = fc.list_items("630144608", {"z_c0": "x"})
    assert [i.key for i in items] == ["answer:11", "article:12", "answer:13"]
    assert items[0].title == "Q11"          # answer title comes from content.question.title
    assert items[1].title == "Art12"        # article title comes from content.title
    assert items[0].url.endswith("/answer/11")


def test_stops_on_offset_reaching_totals_without_is_end():
    pages = {
        0: _page([_answer_item("1")], totals=1, is_end=False),  # is_end stays False
    }

    def handler(request: httpx.Request) -> httpx.Response:
        offset = int(dict(request.url.params)["offset"])
        return httpx.Response(200, json=pages[offset])

    client = httpx.Client(transport=httpx.MockTransport(handler))
    fc = FavoritesClient(http_client=client)
    items = fc.list_items("c", {})
    assert [i.key for i in items] == ["answer:1"]   # stopped because offset(20) >= totals(1)


def test_non_200_raises():
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(403, json={})))
    fc = FavoritesClient(http_client=client)
    with pytest.raises(ZhihuApiError) as exc:
        fc.list_items("c", {})
    assert exc.value.status == 403


def test_skips_malformed_items():
    page = {"data": [{"content": {"type": "answer"}}, _answer_item("9")],
            "paging": {"totals": 2, "is_end": True}}
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=page)))
    fc = FavoritesClient(http_client=client)
    items = fc.list_items("c", {})
    assert [i.key for i in items] == ["answer:9"]   # item missing id/url dropped
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_favorites_client.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'zhihu_watcher.favorites_client'`.

- [ ] **Step 3: Write minimal implementation**

```python
"""List items inside a Zhihu collection via the public collections API.

Endpoint: GET https://www.zhihu.com/api/v4/collections/{id}/items?offset=&limit=20
Plain cookies + browser-like headers, NO x-zse-96 signing (verified against the reference repo,
consistent with crawl-pipeline.md §知乎链路 D5). Direct connect: trust_env=False (Zhihu is a
mainland site; the host's proxy env is for overseas sites only).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

log = logging.getLogger("zhihu_watcher.favorites_client")

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.zhihu.com/",
}


@dataclass
class CollectionItem:
    key: str           # stable dedup key: "{content_type}:{content_id}"
    url: str           # canonical content URL, fed to SP-2 fetch()
    content_type: str  # "answer" | "article" | ...
    title: str         # fallback title (SP-2 FetchResult.title is authoritative)


class ZhihuApiError(Exception):
    def __init__(self, status: int, url: str):
        super().__init__(f"Zhihu API {status} for {url}")
        self.status = status
        self.url = url


def collection_id_from_url(url_or_id: str) -> str:
    return url_or_id.split("?")[0].rstrip("/").split("/")[-1]


def _build_item(el: dict) -> CollectionItem | None:
    content = el.get("content") or {}
    ctype = content.get("type")
    cid = content.get("id")
    url = content.get("url")
    if not (ctype and cid and url):
        return None
    if ctype == "answer":
        title = (content.get("question") or {}).get("title") or content.get("title") or ""
    else:
        title = content.get("title") or ""
    return CollectionItem(key=f"{ctype}:{cid}", url=url, content_type=ctype, title=title)


class FavoritesClient:
    def __init__(self, http_client: httpx.Client | None = None, limit: int = 20):
        self._client = http_client or httpx.Client(
            trust_env=False, headers=_BROWSER_HEADERS, timeout=30.0
        )
        self._limit = limit

    def list_items(self, collection_id_or_url: str, cookies: dict[str, str]) -> list[CollectionItem]:
        collection_id = collection_id_from_url(collection_id_or_url)
        items: list[CollectionItem] = []
        offset = 0
        while True:
            url = (
                f"https://www.zhihu.com/api/v4/collections/{collection_id}"
                f"/items?offset={offset}&limit={self._limit}"
            )
            resp = self._client.get(url, cookies=cookies)
            if resp.status_code != 200:
                raise ZhihuApiError(resp.status_code, url)
            body = resp.json()
            data = body.get("data") or []
            for el in data:
                item = _build_item(el)
                if item is not None:
                    items.append(item)
            paging = body.get("paging") or {}
            if paging.get("is_end") is True:
                break
            offset += self._limit
            totals = paging.get("totals")
            if totals is not None and offset >= totals:
                break
            if not data:  # safety: empty page with no is_end / totals
                break
        log.info("collection %s: listed %d items", collection_id, len(items))
        return items
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_favorites_client.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add src/zhihu_watcher/favorites_client.py tests/test_favorites_client.py
git commit -m "feat(SP-5a): collections API client with offset paging (no signing, direct connect)"
```

---

## Task 4: `watermark_store.py` — persistent seen-id set

**Files:**
- Create: `src/zhihu_watcher/watermark_store.py`
- Test: `tests/test_watermark_store.py`

- [ ] **Step 1: Write the failing test**

```python
from zhihu_watcher.watermark_store import WatermarkStore


def test_empty_when_no_file(tmp_path):
    store = WatermarkStore(str(tmp_path))
    assert store.load("c1") == set()


def test_save_and_reload(tmp_path):
    store = WatermarkStore(str(tmp_path))
    store.save("c1", {"answer:1", "article:2"})
    # a fresh instance must read the same data (survives "restart")
    reloaded = WatermarkStore(str(tmp_path)).load("c1")
    assert reloaded == {"answer:1", "article:2"}


def test_collections_isolated(tmp_path):
    store = WatermarkStore(str(tmp_path))
    store.save("c1", {"answer:1"})
    store.save("c2", {"answer:2"})
    assert store.load("c1") == {"answer:1"}
    assert store.load("c2") == {"answer:2"}


def test_save_is_atomic_no_partial_file(tmp_path):
    store = WatermarkStore(str(tmp_path))
    store.save("c1", {"answer:1"})
    # no leftover temp files
    leftovers = [p.name for p in tmp_path.iterdir() if p.name.endswith(".tmp")]
    assert leftovers == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_watermark_store.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'zhihu_watcher.watermark_store'`.

- [ ] **Step 3: Write minimal implementation**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_watermark_store.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add src/zhihu_watcher/watermark_store.py tests/test_watermark_store.py
git commit -m "feat(SP-5a): persistent seen-id watermark store (atomic per-collection JSON)"
```

---

## Task 5: `fetcher.py` — wrap the frozen SP-2 engine

**Files:**
- Create: `src/zhihu_watcher/fetcher.py`
- Test: `tests/test_fetcher.py`

- [ ] **Step 1: Write the failing test**

```python
import types
import zhihu
from zhihu_watcher.fetcher import fetch, FetchedDoc


def test_fetch_returns_title_and_markdown(monkeypatch):
    fake_result = types.SimpleNamespace(title="My Title", content_markdown="# body\nhello")

    def fake_fetch(url, cookies=None, **kw):
        assert url == "https://www.zhihu.com/question/1/answer/2"
        assert cookies == {"z_c0": "x"}
        return fake_result

    monkeypatch.setattr(zhihu, "fetch", fake_fetch)
    doc = fetch("https://www.zhihu.com/question/1/answer/2", {"z_c0": "x"})
    assert isinstance(doc, FetchedDoc)
    assert doc.title == "My Title"
    assert doc.content_markdown == "# body\nhello"


def test_fetch_returns_none_on_zhihu_error(monkeypatch):
    def boom(url, cookies=None, **kw):
        raise zhihu.ZhihuFetchError("nope")

    monkeypatch.setattr(zhihu, "fetch", boom)
    assert fetch("https://www.zhihu.com/p/1", {}) is None
```

> NOTE: `zhihu.ZhihuFetchError(...)` is constructed here with a single message arg; the real engine's
> exception also carries `url`/`attempts`/`status` attributes, but the watcher only needs the type to
> trigger graceful degradation, so a bare construction is fine for the test.

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_fetcher.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'zhihu_watcher.fetcher'`.

- [ ] **Step 3: Write minimal implementation**

```python
"""Thin wrapper over the frozen SP-2 zhihu engine: one URL + cookies -> (title, markdown) | None."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import zhihu

log = logging.getLogger("zhihu_watcher.fetcher")


@dataclass
class FetchedDoc:
    title: str
    content_markdown: str


def fetch(url: str, cookies: dict[str, str]) -> FetchedDoc | None:
    try:
        result = zhihu.fetch(url, cookies=cookies)
    except zhihu.ZhihuFetchError as e:
        log.warning(
            "SP-2 fetch failed url=%s status=%s attempts=%s",
            url, getattr(e, "status", None), getattr(e, "attempts", None),
        )
        return None
    return FetchedDoc(title=result.title, content_markdown=result.content_markdown)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_fetcher.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add src/zhihu_watcher/fetcher.py tests/test_fetcher.py
git commit -m "feat(SP-5a): SP-2 engine fetch wrapper with graceful degrade"
```

---

## Task 6: `saver.py` — Markdown output (reference-repo format)

**Files:**
- Create: `src/zhihu_watcher/saver.py`
- Test: `tests/test_saver.py`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path
from zhihu_watcher.saver import save, sanitize_title


def test_sanitize_title_rules():
    assert sanitize_title('a/b\\c"d<e>f|g') == "a b c d e f g"
    assert sanitize_title("what?") == "what？"
    assert sanitize_title("ratio 1:2") == "ratio 1：2"
    assert sanitize_title("   ") == "untitled"


def test_save_writes_url_prefixed_markdown_no_frontmatter(tmp_path):
    path = save(str(tmp_path), "AI-papers", "Hello World",
                "https://www.zhihu.com/question/1/answer/2", "# body\ntext")
    p = Path(path)
    assert p == tmp_path / "AI-papers" / "Hello World.md"
    content = p.read_text(encoding="utf-8")
    assert content.startswith("> https://www.zhihu.com/question/1/answer/2\n")
    assert "# body\ntext" in content
    assert not content.startswith("---")   # no YAML frontmatter


def test_collision_appends_url_id(tmp_path):
    save(str(tmp_path), "c", "Dup", "https://www.zhihu.com/answer/100", "first")
    second = save(str(tmp_path), "c", "Dup", "https://www.zhihu.com/answer/200", "second")
    assert Path(second).name == "Dup_200.md"
    assert (tmp_path / "c" / "Dup.md").read_text(encoding="utf-8").endswith("first\n") or \
           "first" in (tmp_path / "c" / "Dup.md").read_text(encoding="utf-8")


def test_remote_image_urls_preserved(tmp_path):
    body = "![pic](https://pic.zhimg.com/x.jpg)"
    path = save(str(tmp_path), "c", "WithImg", "https://www.zhihu.com/p/1", body)
    assert "https://pic.zhimg.com/x.jpg" in Path(path).read_text(encoding="utf-8")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_saver.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'zhihu_watcher.saver'`.

- [ ] **Step 3: Write minimal implementation**

```python
"""Save a fetched item as Markdown, matching the Zhihu-Collections-MCP reference convention.

Layout: <output_dir>/<collection_name>/<sanitized_title>.md (collision -> _<url_id>.md).
Content: first line '> <url>', then the SP-2 content_markdown body. No YAML frontmatter.
Images keep their remote URLs (SP-2 does not download images; neither do we).
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


def _url_id(url: str) -> str:
    return url.split("?")[0].rstrip("/").split("/")[-1]


def save(output_dir: str, collection_name: str, title: str, url: str, content_markdown: str) -> str:
    folder = Path(output_dir) / collection_name
    folder.mkdir(parents=True, exist_ok=True)
    base = sanitize_title(title)
    path = folder / f"{base}.md"
    if path.exists():
        path = folder / f"{base}_{_url_id(url)}.md"
    text = f"> {url}\n{content_markdown}"
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8")
    return str(path)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_saver.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add src/zhihu_watcher/saver.py tests/test_saver.py
git commit -m "feat(SP-5a): markdown saver (reference-repo format, remote images, collision suffix)"
```

---

## Task 7: `watcher.py` — orchestration + integration test

This is where the components compose. The `Watcher` takes its collaborators by injection so the
integration test can supply fakes; `build_watcher(config)` wires the real ones.

**Files:**
- Create: `src/zhihu_watcher/watcher.py`
- Test: `tests/test_watcher_integration.py`

- [ ] **Step 1: Write the failing test (full cycle + the dedup invariant)**

```python
from pathlib import Path
import types
from zhihu_watcher.config import WatcherConfig, CookieSource, CollectionConfig
from zhihu_watcher.favorites_client import CollectionItem
from zhihu_watcher.watermark_store import WatermarkStore
from zhihu_watcher.fetcher import FetchedDoc
from zhihu_watcher.watcher import Watcher


def _config(tmp_path):
    return WatcherConfig(
        poll_interval_minutes=45,
        output_dir=str(tmp_path / "out"),
        state_dir=str(tmp_path / "state"),
        cookie_source=CookieSource(base_url="http://x", uuid="u", password="p"),
        collections=[CollectionConfig(id="c1", name="Box1")],
    )


class _FakeCookies:
    def get_cookies(self):
        return {"z_c0": "x"}


class _FakeFavorites:
    def __init__(self, items):
        self._items = items
        self.calls = 0

    def list_items(self, cid, cookies):
        self.calls += 1
        return self._items


def test_full_cycle_then_second_cycle_is_noop(tmp_path):
    items = [
        CollectionItem(key="answer:11", url="https://www.zhihu.com/question/1/answer/11",
                       content_type="answer", title="Eleven"),
        CollectionItem(key="article:12", url="https://zhuanlan.zhihu.com/p/12",
                       content_type="article", title="Twelve"),
    ]
    fetch_calls = []

    def fake_fetch(url, cookies):
        fetch_calls.append(url)
        return FetchedDoc(title="T-" + url.split("/")[-1], content_markdown="body")

    cfg = _config(tmp_path)
    favorites = _FakeFavorites(items)
    watcher = Watcher(
        config=cfg,
        cookie_provider=_FakeCookies(),
        favorites_client=favorites,
        fetcher_fn=fake_fetch,
        watermark_store=WatermarkStore(cfg.state_dir),
    )

    # First cycle: both items new -> fetched + saved
    watcher.run_cycle()
    out = Path(cfg.output_dir) / "Box1"
    saved = sorted(p.name for p in out.glob("*.md"))
    assert saved == ["T-11.md", "T-12.md"]
    assert len(fetch_calls) == 2

    # Second cycle: nothing new -> no extra fetches, no extra files (THE dedup invariant)
    watcher.run_cycle()
    assert len(fetch_calls) == 2
    assert sorted(p.name for p in out.glob("*.md")) == ["T-11.md", "T-12.md"]


def test_fetch_failure_does_not_mark_seen(tmp_path):
    items = [CollectionItem(key="answer:9", url="https://www.zhihu.com/answer/9",
                            content_type="answer", title="Nine")]
    attempts = {"n": 0}

    def flaky_fetch(url, cookies):
        attempts["n"] += 1
        if attempts["n"] == 1:
            return None              # first cycle: fetch fails
        return FetchedDoc(title="Nine", content_markdown="ok")

    cfg = _config(tmp_path)
    store = WatermarkStore(cfg.state_dir)
    watcher = Watcher(cfg, _FakeCookies(), _FakeFavorites(items), flaky_fetch, store)

    watcher.run_cycle()              # fails -> not marked seen
    assert store.load("c1") == set()
    assert not (Path(cfg.output_dir) / "Box1").exists()

    watcher.run_cycle()              # retried -> succeeds
    assert store.load("c1") == {"answer:9"}
    assert (Path(cfg.output_dir) / "Box1" / "Nine.md").exists()


def test_cookie_failure_skips_cycle_without_crashing(tmp_path):
    class _BoomCookies:
        def get_cookies(self):
            raise RuntimeError("SP-1 down")

    cfg = _config(tmp_path)
    favorites = _FakeFavorites([])
    watcher = Watcher(cfg, _BoomCookies(), favorites, lambda u, c: None, WatermarkStore(cfg.state_dir))
    watcher.run_cycle()              # must not raise
    assert favorites.calls == 0      # never reached listing
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_watcher_integration.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'zhihu_watcher.watcher'`.

- [ ] **Step 3: Write minimal implementation**

```python
"""Orchestrate one poll cycle and wire the real components.

Collaborators are injected so the cycle is fully testable with fakes; build_watcher() supplies the
real implementations. The daemon must never crash — every failure path logs and continues.
"""
from __future__ import annotations

import logging
from typing import Callable, Optional

from .config import WatcherConfig
from .cookie_provider import CookieProvider
from .favorites_client import FavoritesClient
from .fetcher import FetchedDoc
from .fetcher import fetch as default_fetch
from .saver import save as default_save
from .watermark_store import WatermarkStore

log = logging.getLogger("zhihu_watcher.watcher")

FetcherFn = Callable[[str, dict], Optional[FetchedDoc]]
SaverFn = Callable[[str, str, str, str, str], str]


class Watcher:
    def __init__(
        self,
        config: WatcherConfig,
        cookie_provider,
        favorites_client,
        fetcher_fn: FetcherFn,
        watermark_store: WatermarkStore,
        saver_fn: SaverFn = default_save,
    ):
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
        if not cookies:
            log.error("no .zhihu.com cookies available — skipping cycle")
            return
        for coll in self._cfg.collections:
            self._poll_collection(coll, cookies)

    def _poll_collection(self, coll, cookies: dict) -> None:
        try:
            items = self._favorites.list_items(coll.id, cookies)
        except Exception as e:  # noqa: BLE001
            log.error("listing collection %s failed: %s", coll.id, e)
            return
        seen = self._store.load(coll.id)
        new_count = 0
        for item in items:
            if item.key in seen:
                continue
            doc = self._fetch(item.url, cookies)
            if doc is None:
                continue  # fetch failed -> NOT marked seen -> retried next cycle
            try:
                self._save(self._cfg.output_dir, coll.name, doc.title, item.url, doc.content_markdown)
            except Exception as e:  # noqa: BLE001
                log.error("save failed url=%s: %s", item.url, e)
                continue  # not marked seen -> retried
            seen.add(item.key)
            self._store.save(coll.id, seen)  # persist immediately (1-item crash window)
            new_count += 1
        log.info("collection %s (%s): %d new item(s)", coll.id, coll.name, new_count)


def build_watcher(config: WatcherConfig) -> Watcher:
    return Watcher(
        config=config,
        cookie_provider=CookieProvider(config.cookie_source),
        favorites_client=FavoritesClient(),
        fetcher_fn=default_fetch,
        watermark_store=WatermarkStore(config.state_dir),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_watcher_integration.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add src/zhihu_watcher/watcher.py tests/test_watcher_integration.py
git commit -m "feat(SP-5a): cycle orchestration + dedup invariant integration test"
```

---

## Task 8: `__main__.py` — CLI entrypoint + scheduler

**Files:**
- Create: `src/zhihu_watcher/__main__.py`
- Test: `tests/test_watcher_integration.py` (append a `--once` CLI test)

- [ ] **Step 1: Append the failing CLI test**

Add to `tests/test_watcher_integration.py`:
```python
def test_main_once_runs_single_cycle(tmp_path, monkeypatch):
    import zhihu_watcher.__main__ as m

    calls = {"n": 0}

    class _W:
        def run_cycle(self):
            calls["n"] += 1

    monkeypatch.setattr(m, "build_watcher", lambda cfg: _W())
    monkeypatch.setattr(m, "load_config", lambda path: object())

    m.main(["--once", "--config", "irrelevant.yaml"])
    assert calls["n"] == 1   # exactly one cycle, no scheduler started
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_watcher_integration.py::test_main_once_runs_single_cycle -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'zhihu_watcher.__main__'` (or attribute error).

- [ ] **Step 3: Write minimal implementation**

```python
"""CLI entrypoint: `python -m zhihu_watcher [--once] [--config PATH]`.

Default (no --once): start a BlockingScheduler interval job (max_instances=1) and run forever.
--once: run a single cycle and exit (used by the smoke test + CI).
"""
from __future__ import annotations

import argparse
import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from .config import load_config
from .watcher import build_watcher


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="zhihu_watcher")
    parser.add_argument("--config", default="config/zhihu-watcher.yaml",
                        help="path to the YAML config")
    parser.add_argument("--once", action="store_true",
                        help="run a single poll cycle and exit (smoke / CI)")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    config = load_config(args.config)
    watcher = build_watcher(config)

    if args.once:
        watcher.run_cycle()
        return

    scheduler = BlockingScheduler()
    scheduler.add_job(
        watcher.run_cycle,
        trigger="interval",
        minutes=config.poll_interval_minutes,
        max_instances=1,
        coalesce=True,
        next_run_time=None,  # also run immediately on startup via the explicit call below
    )
    logging.getLogger("zhihu_watcher").info(
        "starting scheduler: every %d min, %d collection(s)",
        config.poll_interval_minutes, len(config.collections),
    )
    watcher.run_cycle()  # run once immediately, then on the interval
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_watcher_integration.py -v`
Expected: PASS (4 tests in this file now).

- [ ] **Step 5: Run the full suite + verify it is green**

Run: `.venv/bin/python -m pytest -v`
Expected: PASS — all tests across config / cookie_provider / favorites_client / watermark_store / fetcher / saver / watcher_integration.

- [ ] **Step 6: Commit**

```bash
git add src/zhihu_watcher/__main__.py tests/test_watcher_integration.py
git commit -m "feat(SP-5a): CLI entrypoint + BlockingScheduler interval daemon"
```

---

## Task 9: Deployment artifacts

**Files:**
- Create: `config/zhihu-watcher.example.yaml`
- Create: `Dockerfile`
- Create: `docker-compose.yml`

- [ ] **Step 1: Write `config/zhihu-watcher.example.yaml`**

```yaml
# Copy to config/zhihu-watcher.yaml and fill in your values.
poll_interval_minutes: 45            # default 30-60; how often to poll
output_dir: /data/output             # where Markdown is written (may point at a vault subdir)
state_dir: /data/state               # where seen-id JSON lives (mount a volume to persist)

cookie_source:                       # SP-1 CookieManager connection
  base_url: http://127.0.0.1:48088   # or LAN/public entry from cookie-manager interface.md §8
  uuid: <your-cookiecloud-box-uuid>
  password: <your-cookiecloud-box-password>
  # crypto_type is read from GET /get/:uuid; do not set it here.

collections:                         # the user's own account; list one or more
  - id: "630144608"                  # from https://www.zhihu.com/collection/630144608 (id or full URL)
    name: "AI-papers"                # subfolder name under output_dir (optional; defaults to id)
```

- [ ] **Step 2: Write `Dockerfile`**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# The frozen SP-2 engine is a sibling package in the monorepo; copy + install both.
COPY Engine/zhihu /app/engine-zhihu
COPY Service/crawl/zhihu-watcher /app/zhihu-watcher

RUN pip install --no-cache-dir /app/engine-zhihu \
    && pip install --no-cache-dir /app/zhihu-watcher

# config + data are mounted at runtime (see docker-compose.yml)
ENTRYPOINT ["python", "-m", "zhihu_watcher", "--config", "/config/zhihu-watcher.yaml"]
```

> NOTE: this image must be built from the **repo root** so both `Engine/zhihu` and
> `Service/crawl/zhihu-watcher` are in the build context. The compose file sets `context: ../../..`
> accordingly.

- [ ] **Step 3: Write `docker-compose.yml`**

```yaml
services:
  zhihu-watcher:
    build:
      context: ../../..                      # repo root, so Engine/zhihu is in the build context
      dockerfile: Service/crawl/zhihu-watcher/Dockerfile
    container_name: jarvankb-zhihu-watcher
    restart: unless-stopped
    volumes:
      - ./config:/config:ro                  # put zhihu-watcher.yaml here
      - ./data/state:/data/state             # seen-id JSON (persisted)
      - ./data/output:/data/output           # saved Markdown
    # Zhihu is reached direct (the client sets trust_env=False); no proxy env needed.
```

- [ ] **Step 4: Validate the compose file + example config parse**

Run:
```bash
docker compose -f docker-compose.yml config >/dev/null && echo "compose ok"
.venv/bin/python -c "from zhihu_watcher.config import load_config; load_config('config/zhihu-watcher.example.yaml')" 2>&1 | head -5
```
Expected: `compose ok`. The config load will raise on the placeholder `<...>` only if validated for content — it will actually load fine (placeholders are non-empty strings), so expect no error. If `docker` is unavailable in this environment, note it and skip the compose validation (it is re-checked at the user's live smoke).

- [ ] **Step 5: Commit**

```bash
git add Service/crawl/zhihu-watcher/config Service/crawl/zhihu-watcher/Dockerfile Service/crawl/zhihu-watcher/docker-compose.yml
git commit -m "feat(SP-5a): deployment artifacts (Dockerfile, compose, example config)"
```

---

## Task 10: Freeze module docs + RepoMem

Per SP-0 §5 (mandatory module docs) and the language policy (H2A module docs = Chinese; A2A RepoMem = English).

**Files:**
- Modify: `docs/README.md`, `docs/interface.md`, `docs/architecture.md` (replace placeholders; Chinese)
- Create: `docs/runbook.md` (Chinese; service ⇒ required)
- Modify: `docs/RepoMem/architecture.md`, `docs/RepoMem/decisions.md` (English)

- [ ] **Step 1: Write `docs/README.md` (Chinese, H2A)** — 1 screen: 做什么 / 输入 / 输出 / 怎么装。Cover: polls configured collections every N min, pulls cookie from SP-1, fetches new items via SP-2, saves Markdown to `output_dir/<collection>/`. Input = YAML config. Output = `> url` + body Markdown, no frontmatter. Install = docker-compose (bring-up is a user op).

- [ ] **Step 2: Write `docs/interface.md` (Chinese, H2A)** — the stable contract: the full config schema (every key from `config/zhihu-watcher.example.yaml` with type + meaning), and the CLI: `python -m zhihu_watcher [--once] [--config PATH]` / console script `zhihu-watcher`. State that the service has no HTTP API (it is a daemon).

- [ ] **Step 3: Write `docs/architecture.md` (Chinese, H2A)** — external summary: the cycle diagram (scheduler → run_cycle → per-collection: cookie pull → list → dedup → SP-2 fetch → save), the 7 components one-liners, and the dependency on SP-1 (cookie) + SP-2 (engine). Point to the design spec for detail.

- [ ] **Step 4: Write `docs/runbook.md` (Chinese, H2A; service-required)** — deploy/config/credentials/common failures:
  - bring up: `docker compose up -d --build` from the module dir; volumes for config/state/output.
  - SP-1 connection: where to get uuid/password; HTTPS vs LAN entry.
  - common failures: cookie pull 401/decrypt error (wrong password/crypto_type), collection listing 403 (→ may need x-zse-96; surfaced as a blocker), empty cookies (no `.zhihu.com` box stored yet).
  - how to inspect state: `data/state/seen-<id>.json`.

- [ ] **Step 5: Write `docs/RepoMem/architecture.md` (English, A2A)** — internal architecture: module layering, the inject-collaborators design that makes the cycle testable, the crypto path (EVP_BytesToKey / Salted__), the offset-paging-with-is_end-fallback rationale, why seen-set not timestamp watermark.

- [ ] **Step 6: Write `docs/RepoMem/decisions.md` (English, A2A)** — append D1–D5 from the design (cookie HTTP+decrypt, seen-id set, BlockingScheduler+compose, reference-repo output format, remote images) with rationale + revisit-trigger, newest at top. Mark any global-promotion candidate (see Step 8 merge): the "collections endpoint needs no x-zse-96 (2026-06)" confirmation is a candidate to promote into `crawl-pipeline.md §知乎链路`.

- [ ] **Step 7: Commit**

```bash
git add Service/crawl/zhihu-watcher/docs
git commit -m "docs(SP-5a): freeze module docs (README/interface/architecture/runbook) + RepoMem"
```

---

## Self-Review

**1. Spec coverage:**
- §1 locked boundaries — cookie pull (Task 2), output dir (Task 6), no LLM (nothing added), frozen SP-2 (Task 5), own scheduler (Task 8). ✓
- §2 API (endpoint/offset paging/no signing/direct connect/item schema/id-from-url) — Task 3. ✓
- §3 components — Tasks 1–8 (one task per component). ✓
- §3.2 crypto (legacy + fixed, EVP_BytesToKey, key derivation) — Task 2 with known vectors. ✓
- §4 output format (subfolder, filename, sanitize, `> url`, no frontmatter, remote images) — Task 6. ✓
- §5 error handling (cookie fail skip cycle, list 403 skip collection, fetch fail no-mark, save fail no-mark, no-overlap) — Task 7 (+ max_instances/coalesce in Task 8). ✓
- §6 config + deployment — Task 1 (config), Task 9 (Dockerfile/compose/example). ✓
- §7 testing (unit per component + integration second-cycle-noop + `--once` smoke entry) — Tasks 1–8. Live smoke is the verification gate (user op), not a plan task. ✓
- §8 module docs — Task 10. ✓
- §9 future items — intentionally NOT implemented; no tasks (correct). ✓

**2. Placeholder scan:** No "TBD/TODO/handle edge cases" — every code step has complete code; every test has real assertions; the known crypto vectors are concrete. ✓

**3. Type consistency:** `WatcherConfig`/`CookieSource`/`CollectionConfig` (Task 1) used identically in Tasks 2/7/8. `CollectionItem(key,url,content_type,title)` (Task 3) used in Task 7. `FetchedDoc(title,content_markdown)` (Task 5) returned by `fetcher.fetch` and consumed in Task 7. `WatermarkStore.load/save` (Task 4) used in Task 7. `save(output_dir, collection_name, title, url, content_markdown)` (Task 6) matches the `SaverFn` signature + call in Task 7. `Watcher(config, cookie_provider, favorites_client, fetcher_fn, watermark_store, saver_fn=...)` consistent between Task 7 impl, Task 7 tests, and `build_watcher`. `main(argv)` (Task 8) matches the CLI test. ✓

---

## Execution notes (for the implementer / Step 5 of the pipeline)

- **Worktree:** create at `.worktrees/sp5a-zhihu-watcher/` branched from the **local** `feat/agentcrawl-bootstrap` (NOT `origin/main` — that would drop sibling local commits). Commit prefixes `feat(SP-5a):` / `docs(SP-5a):`. Local commits only; no push / no merge-to-main.
- **Verification gate (Step 6):** full `pytest` green + a manual `--once` smoke against a real small collection (new item saved; second `--once` = no-op; show `seen-<id>.json`). Bringing SP-1 up / storing a fresh `.zhihu.com` cookie / `docker compose up` are **USER ops** → surface as a Dashboard gate + note to SubOrche; they do NOT block code+unit+integration.
- **Residual risk:** if the live smoke gets HTTP 403 on the collections endpoint (unexpected `x-zse-96`), that is a **blocker** to SubOrche + a Dashboard row — v1 does not add a signer.
