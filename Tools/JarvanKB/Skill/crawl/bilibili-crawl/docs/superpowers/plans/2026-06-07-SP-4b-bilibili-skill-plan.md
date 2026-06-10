# SP-4b Bilibili Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Bilibili skill — a video ref (BV / `bilibili.com` URL / av) is transcribed through the frozen SP-4a engine and saved as Markdown to a user-chosen path; a vague path is classified by an LLM into a subfolder under a configured output root.

**Architecture:** One new package `Skill/crawl/bilibili-crawl` (dist `bilibili-crawl`, import `bilibili_crawl`): importable `save_bilibili()` core + thin `bilibili-crawl` CLI + one agentskills.io `SKILL.md`. SP-4b is a **pure consumer** of the frozen `bilibili` engine (SP-4a) and of `jarvankb_common.LLMClient` (landed + frozen by SP-3) — it edits neither. Cookies are pulled from SP-1 over HTTP and decrypted in memory (reusing SP-3's verified routine, `domain="bilibili.com"`), mapped to a `BilibiliCredential`. Render options come from config.

**Tech Stack:** Python ≥3.11, setuptools (src-layout, editable installs), `httpx`, `pycryptodome` (AES-CBC), `pyyaml`, `pytest`. Upstream deps `bilibili` (SP-4a engine) + `jarvankb-common` (LLMClient) are already installed/frozen. Authoritative spec: `docs/superpowers/specs/2026-06-07-SP-4b-bilibili-skill-design.md`.

**Build order:** scaffold → leaf modules (cookie, config, saver, classify) → orchestration (api) → CLI → packaging artifacts (SKILL.md, sync, example config) → docs freeze → verification.

**Conventions:** TDD (test → fail → implement → pass → commit). Frequent commits, prefix `feat(SP-4b):` / `docs(SP-4b):`. **Stage ONLY files you touched, with explicit pathspec** (shared branch `feat/agentcrawl-bootstrap`, sibling SP-5b session active — a bare `git commit` would swallow its concurrent changes; use `git commit -m "…" -- <paths>`). Run commands from the worktree's `Tools/JarvanKB/` unless a `cd` is shown.

**Structural mirror:** SP-3 (`Skill/crawl/zhihu-crawl/`, ⚫ done). Differences from SP-3 are flagged inline. The frozen engine surface (confirmed): `from bilibili import transcribe, BilibiliCredential, RenderOptions, BilibiliResult, BilibiliEngineError, BiliNoteUnavailable`; `transcribe(ref, credential=None) -> BilibiliResult`; `result.metadata.title`, `result.transcript.source`/`.full_text`, `result.summary_markdown`; `result.render(RenderOptions(include_transcript, include_timestamps, split_transcript, slug)) -> RenderedOutput(main_markdown, transcript_markdown, suggested_names)`.

---

## Task 0: Worktree + editable installs

**Files:** none (environment setup)

- [ ] **Step 1: Create the worktree from the LOCAL branch**

The worktree MUST branch from local `feat/agentcrawl-bootstrap` (NOT `origin/main`, which would drop sibling sessions' local commits — see memory `worktree-base-local-branch`). Using the `superpowers:using-git-worktrees` skill, create `.worktrees/sp4b-bilibili-skill/` based on the current local `feat/agentcrawl-bootstrap` HEAD. If using raw git:

Run (from repo root `/home/shenzhou/Codes/awesome_agent_tools`):
```bash
git worktree add Tools/JarvanKB/.worktrees/sp4b-bilibili-skill feat/agentcrawl-bootstrap
```
Expected: `Preparing worktree` + checkout at the current branch tip. Work happens in `Tools/JarvanKB/.worktrees/sp4b-bilibili-skill/`; all paths below are relative to `Tools/JarvanKB/` inside that worktree.

- [ ] **Step 2: Editable-install the upstream packages into the working venv**

Run (from the worktree's `Tools/JarvanKB/`):
```bash
pip install -e Engine/bilibili -e Engine/common
```
Expected: both already satisfied / reinstalled (frozen upstreams). `Skill/crawl/bilibili-crawl` is installed in Task 1 once its `pyproject.toml` exists. No commit.

---

## Task 1: `bilibili-crawl` package scaffold

**Files:**
- Create: `Skill/crawl/bilibili-crawl/pyproject.toml`
- Create: `Skill/crawl/bilibili-crawl/src/bilibili_crawl/__init__.py`
- Create: `Skill/crawl/bilibili-crawl/tests/test_smoke.py`

- [ ] **Step 1: Write a trivial import test**

Create `Skill/crawl/bilibili-crawl/tests/test_smoke.py`:
```python
def test_package_imports():
    import bilibili_crawl  # noqa: F401
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest Skill/crawl/bilibili-crawl/tests/test_smoke.py -q`
Expected: `No module named 'bilibili_crawl'`.

- [ ] **Step 3: Create pyproject + empty package init**

Create `Skill/crawl/bilibili-crawl/pyproject.toml`:
```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "bilibili-crawl"
version = "0.1.0"
description = "Bilibili skill: video ref -> frozen bilibili engine -> save Markdown (vague-path LLM classification)"
requires-python = ">=3.11"
dependencies = [
    "bilibili-engine",
    "jarvankb-common",
    "httpx>=0.27",
    "pycryptodome>=3.20",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[project.scripts]
bilibili-crawl = "bilibili_crawl.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```
> Note: dist name of the SP-4a engine is `bilibili-engine` (confirm against `Engine/bilibili/pyproject.toml` `[project].name`; adjust this dependency line if it differs). The re-exports in `__init__.py` import `api`, created in Task 6 — keep `__init__.py` EMPTY for now so the scaffold commit is self-contained; the re-exports are added in Task 6.

Create `Skill/crawl/bilibili-crawl/src/bilibili_crawl/__init__.py` as an **empty file** (re-exports added in Task 6).

- [ ] **Step 4: Reinstall + run the smoke test**

Run (from `Skill/crawl/bilibili-crawl/`):
```bash
pip install -e . -q && python -m pytest tests/test_smoke.py -q
```
Expected: 1 passed (empty package imports).

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(SP-4b): scaffold bilibili-crawl package (pyproject + src layout)" -- \
  Skill/crawl/bilibili-crawl/pyproject.toml \
  Skill/crawl/bilibili-crawl/src/bilibili_crawl/__init__.py \
  Skill/crawl/bilibili-crawl/tests/test_smoke.py
```
(Stage with `git add <those paths>` first if your git requires it; the `-- <paths>` keeps the commit scoped to your files only.)

---

## Task 2: `cookie.py` — SP-1 pull (domain=bilibili.com) + decrypt + build credential

**Files:**
- Create: `Skill/crawl/bilibili-crawl/src/bilibili_crawl/cookie.py`
- Test:   `Skill/crawl/bilibili-crawl/tests/test_cookie.py`

- [ ] **Step 1: Write the failing tests (decrypt round-trips; pull mocked; credential mapping)**

Create `Skill/crawl/bilibili-crawl/tests/test_cookie.py`:
```python
import base64
import json
import subprocess

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from bilibili_crawl.cookie import CookieSource, build_credential, decrypt, pull, _the_key


UUID = "test-uuid"
PW = "test-password"
PLAINTEXT = {
    "cookie_data": {"bilibili.com": [
        {"name": "SESSDATA", "value": "SSS"},
        {"name": "bili_jct", "value": "JJJ"},
    ]},
    "local_storage_data": {},
    "update_time": "2026-06-07T00:00:00Z",
}


def _enc_fixed(plaintext: bytes, the_key: str) -> str:
    key = the_key.encode("utf-8")[:16]
    ct = AES.new(key, AES.MODE_CBC, b"\x00" * 16).encrypt(pad(plaintext, 16))
    return base64.b64encode(ct).decode()


def _enc_legacy_via_openssl(plaintext: bytes, the_key: str) -> str:
    out = subprocess.run(
        ["openssl", "enc", "-aes-256-cbc", "-md", "md5", "-salt",
         "-pass", f"pass:{the_key}", "-base64", "-A"],
        input=plaintext, capture_output=True, check=True,
    ).stdout
    return out.decode().strip()


def test_decrypt_fixed_roundtrip():
    the_key = _the_key(UUID, PW)
    enc = _enc_fixed(json.dumps(PLAINTEXT).encode(), the_key)
    assert decrypt(enc, "aes-128-cbc-fixed", UUID, PW) == PLAINTEXT


def test_decrypt_legacy_against_openssl():
    the_key = _the_key(UUID, PW)
    enc = _enc_legacy_via_openssl(json.dumps(PLAINTEXT).encode(), the_key)
    assert decrypt(enc, "legacy", UUID, PW) == PLAINTEXT


def test_pull_picks_bilibili_dot_com_no_dot(monkeypatch):
    the_key = _the_key(UUID, PW)
    enc = _enc_fixed(json.dumps(PLAINTEXT).encode(), the_key)

    class FakeResp:
        def raise_for_status(self): pass
        def json(self): return {"encrypted": enc, "crypto_type": "aes-128-cbc-fixed"}

    class FakeClient:
        def get(self, url): assert url.endswith("/get/test-uuid"); return FakeResp()

    src = CookieSource(base_url="http://127.0.0.1:48088", uuid=UUID, password=PW)
    cookies = pull(src, client=FakeClient())   # default domain == "bilibili.com"
    assert cookies == {"SESSDATA": "SSS", "bili_jct": "JJJ"}


def test_build_credential_maps_sessdata():
    cred = build_credential({"SESSDATA": "SSS", "bili_jct": "JJJ"})
    assert cred is not None
    assert cred.sessdata == "SSS"
    assert cred.bili_jct == "JJJ"
    assert cred.buvid3 is None


def test_build_credential_none_without_sessdata():
    assert build_credential({"bili_jct": "JJJ"}) is None
    assert build_credential({}) is None
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest Skill/crawl/bilibili-crawl/tests/test_cookie.py -q`
Expected: `No module named 'bilibili_crawl.cookie'`.

- [ ] **Step 3: Implement `cookie.py`**

Create `Skill/crawl/bilibili-crawl/src/bilibili_crawl/cookie.py`:
```python
"""Active cookie pull from SP-1 cookie-manager + in-memory decrypt + BilibiliCredential build.

Pull-only (SP-1 push permanently cancelled). Plaintext cookies live only in memory; never written to disk.
Decrypt protocol: Service/crawl/cookie-manager/docs/interface.md §3 (verified routine reused from SP-3).
Bilibili box key = "bilibili.com" (NO leading dot) — verified 2026-06-02 (credentials.md §Bilibili). The
engine interface.md §5 still says ".bilibili.com"; that line is stale, credentials.md is authoritative.
"""
from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass

import httpx
from bilibili import BilibiliCredential
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


@dataclass
class CookieSource:
    base_url: str
    uuid: str
    password: str


def _the_key(uuid: str, password: str) -> str:
    return hashlib.md5(f"{uuid}-{password}".encode("utf-8")).hexdigest()[:16]


def _evp_bytes_to_key(passphrase: bytes, salt: bytes, key_len: int = 32, iv_len: int = 16):
    data = b""
    prev = b""
    while len(data) < key_len + iv_len:
        prev = hashlib.md5(prev + passphrase + salt).digest()
        data += prev
    return data[:key_len], data[key_len:key_len + iv_len]


def _decrypt_legacy(b64: str, the_key: str) -> bytes:
    raw = base64.b64decode(b64)
    if raw[:8] != b"Salted__":
        raise ValueError("legacy ciphertext missing OpenSSL Salted__ header")
    salt, ct = raw[8:16], raw[16:]
    key, iv = _evp_bytes_to_key(the_key.encode("utf-8"), salt)
    return unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(ct), AES.block_size)


def _decrypt_fixed(b64: str, the_key: str) -> bytes:
    key = the_key.encode("utf-8")[:16]
    ct = base64.b64decode(b64)
    return unpad(AES.new(key, AES.MODE_CBC, b"\x00" * 16).decrypt(ct), AES.block_size)


def decrypt(encrypted: str, crypto_type: str, uuid: str, password: str) -> dict:
    the_key = _the_key(uuid, password)
    if crypto_type == "aes-128-cbc-fixed":
        plaintext = _decrypt_fixed(encrypted, the_key)
    else:  # "legacy" (default)
        plaintext = _decrypt_legacy(encrypted, the_key)
    return json.loads(plaintext)


def pull(source: CookieSource, domain: str = "bilibili.com", *,
         client: httpx.Client | None = None) -> dict[str, str]:
    url = f"{source.base_url.rstrip('/')}/get/{source.uuid}"
    owns = client is None
    c = client or httpx.Client(timeout=15.0)
    try:
        resp = c.get(url)
        resp.raise_for_status()
        blob = resp.json()
    finally:
        if owns:
            c.close()
    data = decrypt(blob["encrypted"], blob.get("crypto_type", "legacy"), source.uuid, source.password)
    cookies = data.get("cookie_data", {}).get(domain, [])
    return {ck["name"]: ck["value"] for ck in cookies}


def build_credential(cookies: dict[str, str]) -> BilibiliCredential | None:
    """SESSDATA present -> BilibiliCredential; absent -> None (anonymous / public-video path)."""
    sessdata = cookies.get("SESSDATA")
    if not sessdata:
        return None
    return BilibiliCredential(
        sessdata=sessdata,
        bili_jct=cookies.get("bili_jct"),
        buvid3=cookies.get("buvid3"),
    )
```

- [ ] **Step 4: Run to verify it passes**

Run (from `Skill/crawl/bilibili-crawl/`): `python -m pytest tests/test_cookie.py -q`
Expected: 5 passed. (Requires `openssl` on PATH for the legacy test — standard on Linux.)

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(SP-4b): cookie pull (domain=bilibili.com) + decrypt + BilibiliCredential build" -- \
  Skill/crawl/bilibili-crawl/src/bilibili_crawl/cookie.py \
  Skill/crawl/bilibili-crawl/tests/test_cookie.py
```

---

## Task 3: `config.py` — module config loader (incl. render block)

**Files:**
- Create: `Skill/crawl/bilibili-crawl/src/bilibili_crawl/config.py`
- Test:   `Skill/crawl/bilibili-crawl/tests/test_config.py`

- [ ] **Step 1: Write the failing tests**

Create `Skill/crawl/bilibili-crawl/tests/test_config.py`:
```python
import textwrap
from pathlib import Path

from bilibili_crawl.config import load_config


def test_load_config_reads_password_and_render(tmp_path, monkeypatch):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(textwrap.dedent(f"""
        output_root: {tmp_path}/KB
        cookie:
          base_url: http://127.0.0.1:48088
          uuid: my-uuid
          password_env: COOKIE_PW
        llm:
          profile: mimo
        render:
          include_transcript: true
          include_timestamps: true
          split_transcript: true
        classify_snippet_chars: 180
    """))
    monkeypatch.setenv("COOKIE_PW", "secret")
    mc = load_config(cfg)
    assert mc.output_root == Path(f"{tmp_path}/KB")
    assert mc.cookie.base_url == "http://127.0.0.1:48088"
    assert mc.cookie.uuid == "my-uuid"
    assert mc.cookie.password == "secret"
    assert mc.llm_profile == "mimo"
    assert mc.render.include_transcript is True
    assert mc.render.include_timestamps is True
    assert mc.render.split_transcript is True
    assert mc.classify_snippet_chars == 180


def test_defaults_when_blocks_omitted(tmp_path, monkeypatch):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(textwrap.dedent(f"""
        output_root: {tmp_path}/KB
        cookie: {{base_url: u, uuid: x, password_env: COOKIE_PW}}
    """))
    monkeypatch.setenv("COOKIE_PW", "s")
    mc = load_config(cfg)
    assert mc.llm_profile == "default"
    assert mc.render.include_transcript is True
    assert mc.render.include_timestamps is False
    assert mc.render.split_transcript is False
    assert mc.classify_snippet_chars == 240
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest Skill/crawl/bilibili-crawl/tests/test_config.py -q`
Expected: `No module named 'bilibili_crawl.config'`.

- [ ] **Step 3: Implement `config.py`**

Create `Skill/crawl/bilibili-crawl/src/bilibili_crawl/config.py`:
```python
"""Module config loader. Schema: config.example.yaml. Real config (config.yaml) is gitignored.

Engine config is NOT here: the SP-4a engine reads its own config/bilibili-engine.yaml via transcribe().
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .cookie import CookieSource


@dataclass
class RenderConfig:
    include_transcript: bool = True
    include_timestamps: bool = False
    split_transcript: bool = False


@dataclass
class ModuleConfig:
    output_root: Path
    cookie: CookieSource
    llm_profile: str
    render: RenderConfig = field(default_factory=RenderConfig)
    classify_snippet_chars: int = 240


def _default_path() -> Path:
    return Path(os.environ.get("BILIBILI_CRAWL_CONFIG", "config.yaml")).expanduser()


def load_config(config_path: str | Path | None = None) -> ModuleConfig:
    path = Path(config_path).expanduser() if config_path else _default_path()
    if not path.exists():
        raise FileNotFoundError(
            f"bilibili-crawl config not found at {path}. Copy config.example.yaml to config.yaml "
            f"or set BILIBILI_CRAWL_CONFIG."
        )
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    ck = raw["cookie"]
    rc = raw.get("render", {}) or {}
    return ModuleConfig(
        output_root=Path(raw["output_root"]).expanduser(),
        cookie=CookieSource(
            base_url=ck["base_url"],
            uuid=ck["uuid"],
            password=os.environ.get(ck["password_env"], ""),
        ),
        llm_profile=raw.get("llm", {}).get("profile", "default"),
        render=RenderConfig(
            include_transcript=bool(rc.get("include_transcript", True)),
            include_timestamps=bool(rc.get("include_timestamps", False)),
            split_transcript=bool(rc.get("split_transcript", False)),
        ),
        classify_snippet_chars=int(raw.get("classify_snippet_chars", 240)),
    )
```

- [ ] **Step 4: Run to verify it passes**

Run (from `Skill/crawl/bilibili-crawl/`): `python -m pytest tests/test_config.py -q`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(SP-4b): module config loader (output_root, cookie, llm profile, render, snippet cap)" -- \
  Skill/crawl/bilibili-crawl/src/bilibili_crawl/config.py \
  Skill/crawl/bilibili-crawl/tests/test_config.py
```

---

## Task 4: `saver.py` — vagueness rule + path resolution + write (single/split)

**Files:**
- Create: `Skill/crawl/bilibili-crawl/src/bilibili_crawl/saver.py`
- Test:   `Skill/crawl/bilibili-crawl/tests/test_saver.py`

- [ ] **Step 1: Write the failing tests**

Create `Skill/crawl/bilibili-crawl/tests/test_saver.py`:
```python
from pathlib import Path

from bilibili_crawl.saver import is_vague, resolve_target, slugify, transcript_path_for, write


def test_is_vague_rules(tmp_path):
    root = tmp_path / "KB"
    assert is_vague(None, root) is True
    assert is_vague("", root) is True
    assert is_vague(str(root), root) is True               # equals output_root
    assert is_vague(str(root / "tech"), root) is True       # a directory / no .md
    assert is_vague(str(root / "tech" / "note.md"), root) is False  # explicit .md


def test_slugify_keeps_cjk_and_hyphenates():
    assert slugify("  Hello World!  ") == "hello-world"
    assert slugify("【硬核】Transformer 解析") == "硬核-transformer-解析"
    assert slugify("") == "untitled"


def test_resolve_target_explicit_md_is_verbatim(tmp_path):
    root = tmp_path / "KB"
    p = resolve_target(str(tmp_path / "x" / "note.md"), root, None, "Some Title")
    assert p == (tmp_path / "x" / "note.md")


def test_resolve_target_vague_uses_category_and_slug(tmp_path):
    root = tmp_path / "KB"
    p = resolve_target(None, root, "tech", "My Video")
    assert p == root / "tech" / "my-video.md"


def test_resolve_target_dedups_existing(tmp_path):
    root = tmp_path / "KB"
    (root / "tech").mkdir(parents=True)
    (root / "tech" / "my-video.md").write_text("x")
    p = resolve_target(None, root, "tech", "My Video")
    assert p == root / "tech" / "my-video-2.md"


def test_transcript_path_for_uses_same_stem(tmp_path):
    assert transcript_path_for(tmp_path / "a" / "my-video.md") == tmp_path / "a" / "my-video.transcript.md"


def test_write_creates_parents(tmp_path):
    out = write(tmp_path / "a" / "b" / "c.md", "# hi")
    assert out.read_text() == "# hi"
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest Skill/crawl/bilibili-crawl/tests/test_saver.py -q`
Expected: `No module named 'bilibili_crawl.saver'`.

- [ ] **Step 3: Implement `saver.py`**

Create `Skill/crawl/bilibili-crawl/src/bilibili_crawl/saver.py`:
```python
"""Path resolution + Markdown write. Vagueness rule: explicit == a path naming a .md file.

split_transcript writes a second file alongside the main note, named <stem>.transcript.md — matching the
engine's suggested_names["transcript"] when render() is called with slug=<stem>, so the in-document link
points at the file we actually write.
"""
from __future__ import annotations

import re
from pathlib import Path

_SLUG_RE = re.compile(r"[^\w一-鿿]+")


def slugify(title: str) -> str:
    s = _SLUG_RE.sub("-", title.strip()).strip("-").lower()
    return s or "untitled"


def is_vague(save_path: str | None, output_root: Path) -> bool:
    if not save_path:
        return True
    p = Path(save_path).expanduser()
    if str(p) == str(Path(output_root).expanduser()):
        return True
    return p.suffix.lower() != ".md"


def _dedup(target: Path) -> Path:
    if not target.exists():
        return target
    i = 2
    while True:
        cand = target.with_name(f"{target.stem}-{i}{target.suffix}")
        if not cand.exists():
            return cand
        i += 1


def resolve_target(save_path: str | None, output_root: Path,
                   category: str | None, title: str) -> Path:
    if save_path:
        p = Path(save_path).expanduser()
        if p.suffix.lower() == ".md":
            return p
    # slug the category too — it may originate from LLM output; idempotent for an already-slugged result.
    safe_category = slugify(category) if category else ""
    base = Path(output_root).expanduser() / safe_category
    return _dedup(base / f"{slugify(title)}.md")


def transcript_path_for(target: Path) -> Path:
    return target.with_name(f"{target.stem}.transcript.md")


def write(target: Path, markdown: str) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markdown, encoding="utf-8")
    return target
```

- [ ] **Step 4: Run to verify it passes**

Run (from `Skill/crawl/bilibili-crawl/`): `python -m pytest tests/test_saver.py -q`
Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(SP-4b): saver — vagueness rule, slug, path resolution, dedup, transcript path" -- \
  Skill/crawl/bilibili-crawl/src/bilibili_crawl/saver.py \
  Skill/crawl/bilibili-crawl/tests/test_saver.py
```

---

## Task 5: `classify.py` — vague_path LLM classification (title + summary/transcript lead)

**Files:**
- Create: `Skill/crawl/bilibili-crawl/src/bilibili_crawl/classify.py`
- Test:   `Skill/crawl/bilibili-crawl/tests/test_classify.py`

- [ ] **Step 1: Write the failing tests (LLMClient mocked)**

Create `Skill/crawl/bilibili-crawl/tests/test_classify.py`:
```python
import types
from pathlib import Path

from bilibili_crawl.classify import classify, existing_subfolders


def _result(title="Transformer 深入解析", summary="注意力机制与多头自注意力的工程实践...",
            transcript_text="大家好 今天我们来讲 transformer 的注意力机制 ..."):
    metadata = types.SimpleNamespace(title=title)
    transcript = types.SimpleNamespace(full_text=transcript_text)
    return types.SimpleNamespace(metadata=metadata, summary_markdown=summary, transcript=transcript)


class FakeClient:
    def __init__(self, reply):
        self.reply = reply
        self.prompt = None

    def complete(self, messages, **kw):
        self.prompt = messages[0]["content"]
        return self.reply


def test_existing_subfolders_lists_dirs(tmp_path):
    (tmp_path / "tech").mkdir()
    (tmp_path / "life").mkdir()
    (tmp_path / ".hidden").mkdir()
    (tmp_path / "f.md").write_text("x")
    assert existing_subfolders(tmp_path) == ["life", "tech"]


def test_classify_picks_existing_using_summary(tmp_path):
    (tmp_path / "tech").mkdir()
    client = FakeClient('{"category": "tech", "is_new": false}')
    cat = classify(_result(), tmp_path, client)
    assert cat.name == "tech"
    assert cat.is_new is False
    assert "tech" in client.prompt                 # existing folders fed to the model
    assert "注意力机制" in client.prompt            # summary used as the lead


def test_classify_proposes_new_folder(tmp_path):
    (tmp_path / "tech").mkdir()
    client = FakeClient('```json\n{"category": "Machine Learning", "is_new": true}\n```')
    cat = classify(_result(), tmp_path, client)
    assert cat.name == "machine-learning"           # slugged
    assert cat.is_new is True


def test_classify_falls_back_to_transcript_when_no_summary(tmp_path):
    (tmp_path / "tech").mkdir()
    client = FakeClient('{"category": "tech"}')
    res = _result(summary=None)
    classify(res, tmp_path, client)
    assert "transformer 的注意力机制" in client.prompt  # transcript lead used when summary missing


def test_classify_marks_new_when_not_in_existing(tmp_path):
    (tmp_path / "tech").mkdir()
    client = FakeClient('{"category": "philosophy"}')   # model omitted is_new
    cat = classify(_result(), tmp_path, client)
    assert cat.name == "philosophy"
    assert cat.is_new is True                            # not among existing -> new
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest Skill/crawl/bilibili-crawl/tests/test_classify.py -q`
Expected: `No module named 'bilibili_crawl.classify'`.

- [ ] **Step 3: Implement `classify.py`**

Create `Skill/crawl/bilibili-crawl/src/bilibili_crawl/classify.py`:
```python
"""vague_path classification: infer an existing subfolder under output_root, or propose a new one.

A video has no article body — classify on metadata.title + a lead of summary_markdown (BN's AI note, the
densest topic signal). summary_markdown is best-effort and may be None -> fall back to a lead of
transcript.full_text. Lead is markdown-noise-stripped + capped (token saving). (SP-3 stripper reused.)
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .saver import slugify

_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
_OBJ_RE = re.compile(r"\{.*?\}", re.DOTALL)   # non-greedy: each flat {...} object

# markdown-noise strippers for the classification lead (save tokens — drop what carries no topic signal)
_FENCE_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)
_IMG_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_MD_MARKS_RE = re.compile(r"[#>*`~]+")
_WS_RE = re.compile(r"\s+")


def _lead_text(markdown: str, max_chars: int) -> str:
    """Plain-text lead of a markdown body for classification — strips markdown noise, caps length."""
    t = markdown or ""
    t = _FENCE_BLOCK_RE.sub(" ", t)   # drop fenced code blocks
    t = _IMG_RE.sub(" ", t)            # drop images (alt text + URL)
    t = _LINK_RE.sub(r"\1", t)         # links -> link text only
    t = _MD_MARKS_RE.sub(" ", t)       # drop heading/quote/emphasis/code marks
    t = _WS_RE.sub(" ", t).strip()     # collapse whitespace
    return t[:max_chars]


@dataclass
class Category:
    name: str
    is_new: bool


def existing_subfolders(output_root: Path) -> list[str]:
    root = Path(output_root).expanduser()
    if not root.exists():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir() and not p.name.startswith("."))


def _classification_source(result) -> str:
    """Prefer BN's AI summary; fall back to the transcript when summary is missing/empty."""
    summary = result.summary_markdown or ""
    if summary.strip():
        return summary
    return getattr(result.transcript, "full_text", "") or ""


def _build_prompt(subfolders: list[str], title: str, snippet: str) -> str:
    folder_list = ", ".join(subfolders) if subfolders else "(none yet)"
    return (
        "You classify a saved Bilibili video note into ONE subfolder of a personal knowledge base.\n"
        f"Existing subfolders: {folder_list}\n"
        f"Video title: {title}\nContent snippet: {snippet}\n\n"
        "Pick the single best existing subfolder, or propose a NEW concise subfolder name if none fit. "
        'Reply with ONLY JSON: {"category": "<name>", "is_new": <true|false>}.'
    )


def _parse(raw: str) -> dict:
    text = raw.strip()
    fence = _FENCE_RE.search(text)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # tolerate prose-wrapped output: prefer the LAST parseable object (models answer last)
    for candidate in reversed(_OBJ_RE.findall(text)):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise ValueError(f"LLM classification did not return parseable JSON: {raw[:200]!r}")


def classify(result, output_root: Path, client, *, snippet_chars: int = 240) -> Category:
    subs = existing_subfolders(output_root)
    title = result.metadata.title
    snippet = _lead_text(_classification_source(result), snippet_chars)
    raw = client.complete([{"role": "user", "content": _build_prompt(subs, title, snippet)}])
    data = _parse(raw)
    name = slugify(str(data["category"]))
    is_new = name not in subs   # authoritative: trust the filesystem, not the model's flag
    return Category(name=name, is_new=is_new)
```

- [ ] **Step 4: Run to verify it passes**

Run (from `Skill/crawl/bilibili-crawl/`): `python -m pytest tests/test_classify.py -q`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(SP-4b): vague_path classification (title + summary/transcript lead)" -- \
  Skill/crawl/bilibili-crawl/src/bilibili_crawl/classify.py \
  Skill/crawl/bilibili-crawl/tests/test_classify.py
```

---

## Task 6: `api.py` — `save_bilibili` orchestration + graceful cookie degrade

**Files:**
- Create: `Skill/crawl/bilibili-crawl/src/bilibili_crawl/api.py`
- Modify: `Skill/crawl/bilibili-crawl/src/bilibili_crawl/__init__.py` (add re-exports)
- Test:   `Skill/crawl/bilibili-crawl/tests/test_api.py`

- [ ] **Step 1: Write the failing tests (engine, cookie, LLMClient, config all mocked)**

Create `Skill/crawl/bilibili-crawl/tests/test_api.py`:
```python
import types
from pathlib import Path

import bilibili_crawl.api as api
from bilibili_crawl.config import ModuleConfig, RenderConfig
from bilibili_crawl.cookie import CookieSource


def _fake_result(title="My Video", source="asr"):
    metadata = types.SimpleNamespace(title=title, url="https://b/x")
    transcript = types.SimpleNamespace(source=source, full_text="words")
    r = types.SimpleNamespace(metadata=metadata, transcript=transcript, summary_markdown="sum")

    def render(opts):
        tm = "transcript-body" if opts.split_transcript else None
        return types.SimpleNamespace(main_markdown=f"# {title}\nbody", transcript_markdown=tm,
                                     suggested_names={})
    r.render = render
    return r


def _patch(monkeypatch, tmp_path, *, split=False, classify_name="tech", classify_new=False, result=None):
    mc = ModuleConfig(output_root=tmp_path / "KB", cookie=CookieSource("u", "id", "pw"),
                      llm_profile="mimo", render=RenderConfig(split_transcript=split))
    monkeypatch.setattr(api.cfgmod, "load_config", lambda p=None: mc)
    monkeypatch.setattr(api.cookie, "pull", lambda src, **kw: {"SESSDATA": "S"})
    monkeypatch.setattr(api.cookie, "build_credential", lambda cookies: "CRED")
    monkeypatch.setattr(api, "transcribe", lambda ref, credential=None: result or _fake_result())
    monkeypatch.setattr(api, "LLMClient", lambda profile=None: object())
    monkeypatch.setattr(api.classify, "classify",
                        lambda result, root, client, **kw: api.classify.Category(classify_name, classify_new))
    return mc


def test_explicit_path_writes_verbatim_no_classify(tmp_path, monkeypatch):
    _patch(monkeypatch, tmp_path)
    called = {"classify": False}
    monkeypatch.setattr(api.classify, "classify",
                        lambda *a, **k: called.__setitem__("classify", True) or api.classify.Category("x", True))
    target = tmp_path / "out" / "note.md"
    r = api.save_bilibili("BV1xx", save_path=str(target))
    assert Path(r.path) == target
    assert target.read_text().startswith("# My Video")
    assert r.was_vague is False
    assert r.category is None
    assert r.transcript_path is None
    assert called["classify"] is False


def test_vague_path_classifies_and_saves(tmp_path, monkeypatch):
    _patch(monkeypatch, tmp_path, classify_name="tech", classify_new=False)
    r = api.save_bilibili("BV1xx", save_path=None)
    assert r.was_vague is True
    assert r.category == "tech"
    assert r.proposed_new is False
    assert Path(r.path) == tmp_path / "KB" / "tech" / "my-video.md"
    assert Path(r.path).read_text().startswith("# My Video")


def test_result_fields(tmp_path, monkeypatch):
    _patch(monkeypatch, tmp_path, result=_fake_result(title="My Video", source="subtitle"))
    r = api.save_bilibili("BV1xx", save_path=str(tmp_path / "n.md"))
    assert r.title == "My Video"
    assert r.ref == "BV1xx"
    assert r.transcript_source == "subtitle"


def test_cookie_failure_degrades_to_no_credential(tmp_path, monkeypatch):
    _patch(monkeypatch, tmp_path)
    seen = {}

    def boom(src, **kw):
        raise RuntimeError("cookie-manager down")

    monkeypatch.setattr(api.cookie, "pull", boom)
    monkeypatch.setattr(api, "transcribe",
                        lambda ref, credential=None: seen.update(cred=credential) or _fake_result())
    r = api.save_bilibili("BV1xx", save_path=str(tmp_path / "n.md"))
    assert seen["cred"] is None        # degraded gracefully
    assert Path(r.path).exists()


def test_split_transcript_writes_second_file(tmp_path, monkeypatch):
    _patch(monkeypatch, tmp_path, split=True)
    r = api.save_bilibili("BV1xx", save_path=str(tmp_path / "out" / "note.md"))
    assert r.transcript_path == str(tmp_path / "out" / "note.transcript.md")
    assert Path(r.transcript_path).read_text() == "transcript-body"
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest Skill/crawl/bilibili-crawl/tests/test_api.py -q`
Expected: `No module named 'bilibili_crawl.api'`.

- [ ] **Step 3: Implement `api.py`**

Create `Skill/crawl/bilibili-crawl/src/bilibili_crawl/api.py`:
```python
"""save_bilibili — orchestrate cookie pull -> frozen bilibili engine transcribe -> render -> resolve -> write.

Module-level `transcribe` and `LLMClient` are imported so tests can monkeypatch them. Cookie failure is
NON-FATAL: the engine is cookie-less-capable on public videos, so a missing/expired cookie degrades to
credential=None with a warning rather than crashing.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass

from bilibili import RenderOptions, transcribe
from jarvankb_common import LLMClient

from . import classify, cookie, saver
from . import config as cfgmod


@dataclass
class SaveResult:
    path: str
    transcript_path: str | None
    title: str
    ref: str
    transcript_source: str
    category: str | None
    was_vague: bool
    proposed_new: bool


def save_bilibili(ref: str, save_path: str | None = None, *,
                  profile: str | None = None, config_path: str | None = None) -> SaveResult:
    cfg = cfgmod.load_config(config_path)

    # Cookie is best-effort: engine works cookie-less on public videos (subtitle path needs SESSDATA only).
    try:
        cookies = cookie.pull(cfg.cookie, domain="bilibili.com")
        cred = cookie.build_credential(cookies)
    except Exception as e:  # noqa: BLE001 — never let cookie issues abort a transcribe
        warnings.warn(f"bilibili-crawl: cookie unavailable ({e}); proceeding without credential")
        cred = None

    result = transcribe(ref, credential=cred)

    vague = saver.is_vague(save_path, cfg.output_root)
    category: str | None = None
    proposed_new = False
    if vague:
        client = LLMClient(profile=profile or cfg.llm_profile)
        cat = classify.classify(result, cfg.output_root, client, snippet_chars=cfg.classify_snippet_chars)
        category, proposed_new = cat.name, cat.is_new

    target = saver.resolve_target(save_path, cfg.output_root, category, result.metadata.title)
    rendered = result.render(RenderOptions(
        include_transcript=cfg.render.include_transcript,
        include_timestamps=cfg.render.include_timestamps,
        split_transcript=cfg.render.split_transcript,
        slug=target.stem,
    ))
    main_path = saver.write(target, rendered.main_markdown)
    transcript_path = None
    if cfg.render.split_transcript and rendered.transcript_markdown is not None:
        transcript_path = saver.write(saver.transcript_path_for(target), rendered.transcript_markdown)

    return SaveResult(
        path=str(main_path),
        transcript_path=str(transcript_path) if transcript_path else None,
        title=result.metadata.title,
        ref=ref,
        transcript_source=result.transcript.source,
        category=category,
        was_vague=vague,
        proposed_new=proposed_new,
    )
```
Set `Skill/crawl/bilibili-crawl/src/bilibili_crawl/__init__.py` to:
```python
from .api import SaveResult, save_bilibili

__all__ = ["save_bilibili", "SaveResult"]
```

- [ ] **Step 4: Run to verify it passes**

Run (from `Skill/crawl/bilibili-crawl/`): `python -m pytest tests/test_api.py tests/test_smoke.py -q`
Expected: all passed (api + smoke now green).

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(SP-4b): save_bilibili orchestration (cookie degrade -> engine -> classify -> render -> save)" -- \
  Skill/crawl/bilibili-crawl/src/bilibili_crawl/api.py \
  Skill/crawl/bilibili-crawl/src/bilibili_crawl/__init__.py \
  Skill/crawl/bilibili-crawl/tests/test_api.py
```

---

## Task 7: `cli.py` — thin CLI with `--json`

**Files:**
- Create: `Skill/crawl/bilibili-crawl/src/bilibili_crawl/cli.py`
- Test:   `Skill/crawl/bilibili-crawl/tests/test_cli.py`

- [ ] **Step 1: Write the failing tests (api mocked)**

Create `Skill/crawl/bilibili-crawl/tests/test_cli.py`:
```python
import json

import bilibili_crawl.cli as cli
from bilibili_crawl.api import SaveResult


def _result():
    return SaveResult(path="/KB/tech/x.md", transcript_path=None, title="X", ref="BV1xx",
                      transcript_source="asr", category="tech", was_vague=True, proposed_new=False)


def test_cli_json_output(monkeypatch, capsys):
    monkeypatch.setattr(cli, "save_bilibili", lambda *a, **k: _result())
    rc = cli.main(["BV1xx", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["path"] == "/KB/tech/x.md"
    assert out["category"] == "tech"
    assert out["transcript_source"] == "asr"


def test_cli_passes_out_and_profile(monkeypatch):
    seen = {}

    def fake(ref, save_path=None, **kw):
        seen.update(ref=ref, save_path=save_path, **kw)
        return _result()

    monkeypatch.setattr(cli, "save_bilibili", fake)
    cli.main(["BV1xx", "--out", "~/KB", "--profile", "default"])
    assert seen["ref"] == "BV1xx"
    assert seen["save_path"] == "~/KB"
    assert seen["profile"] == "default"


def test_cli_bilinote_unavailable_exit_3(monkeypatch, capsys):
    from bilibili import BiliNoteUnavailable

    def boom(*a, **k):
        raise BiliNoteUnavailable("BN down")

    monkeypatch.setattr(cli, "save_bilibili", boom)
    rc = cli.main(["BV1xx"])
    assert rc == 3
    assert "BiliNote" in capsys.readouterr().err


def test_cli_engine_error_exit_2(monkeypatch, capsys):
    from bilibili import BilibiliEngineError

    def boom(*a, **k):
        raise BilibiliEngineError("bad")

    monkeypatch.setattr(cli, "save_bilibili", boom)
    rc = cli.main(["BV1xx"])
    assert rc == 2
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest Skill/crawl/bilibili-crawl/tests/test_cli.py -q`
Expected: `No module named 'bilibili_crawl.cli'`.

- [ ] **Step 3: Implement `cli.py`**

Create `Skill/crawl/bilibili-crawl/src/bilibili_crawl/cli.py`:
```python
"""Thin CLI over save_bilibili. `--json` prints a machine-readable SaveResult for any calling agent."""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys

from bilibili import BilibiliEngineError, BiliNoteUnavailable

from .api import save_bilibili


def _build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="bilibili-crawl",
                                 description="Transcribe a Bilibili video via the frozen engine and save Markdown.")
    ap.add_argument("ref", help="video ref: BV id / bilibili.com URL / av id")
    ap.add_argument("--out", dest="save_path", default=None,
                    help="save path; a .md file = explicit, a dir/omitted = vague (LLM classify)")
    ap.add_argument("--json", dest="as_json", action="store_true", help="print JSON SaveResult")
    ap.add_argument("--profile", default=None, help="LLM profile override (default: config)")
    ap.add_argument("--config", dest="config_path", default=None, help="path to config.yaml")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        result = save_bilibili(
            args.ref, args.save_path,
            profile=args.profile, config_path=args.config_path,
        )
    except BiliNoteUnavailable as e:   # subclass of BilibiliEngineError — catch first
        print(f"BiliNote unavailable (is the container up?): {e}", file=sys.stderr)
        return 3
    except BilibiliEngineError as e:
        print(f"transcription failed: {e}", file=sys.stderr)
        return 2
    except Exception as e:  # noqa: BLE001
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.as_json:
        print(json.dumps(dataclasses.asdict(result), ensure_ascii=False))
    else:
        cat = ""
        if result.category:
            cat = f"  category: {result.category}" + (" (new)" if result.proposed_new else "")
        extra = f"\n  transcript: {result.transcript_path}" if result.transcript_path else ""
        print(f"saved: {result.path}\n  title: {result.title}  source: {result.transcript_source}{cat}{extra}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run to verify it passes**

Run (from `Skill/crawl/bilibili-crawl/`): `python -m pytest tests/test_cli.py -q`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(SP-4b): thin CLI with --json + BN-unavailable/engine exit codes" -- \
  Skill/crawl/bilibili-crawl/src/bilibili_crawl/cli.py \
  Skill/crawl/bilibili-crawl/tests/test_cli.py
```

---

## Task 8: Packaging artifacts — SKILL.md, config.example.yaml, sync script

**Files:**
- Create: `Skill/crawl/bilibili-crawl/SKILL.md`
- Create: `Skill/crawl/bilibili-crawl/config.example.yaml`
- Create: `Skill/crawl/bilibili-crawl/scripts/sync-skill.sh`
- Create: `Skill/crawl/bilibili-crawl/.gitignore`

- [ ] **Step 1: Create `config.example.yaml`**

Create `Skill/crawl/bilibili-crawl/config.example.yaml`:
```yaml
# Copy to config.yaml (gitignored). Secrets live in .env, never here.
output_root: ~/KB/bilibili        # base dir for vague-path saves; may point into an Obsidian vault subdir

cookie:
  base_url: http://127.0.0.1:48088   # SP-1 cookie-manager; or the frp HTTPS entry
  uuid: <your-cookiecloud-uuid>
  password_env: COOKIE_MANAGER_PASSWORD   # env var name holding the decrypt password

llm:
  profile: mimo                    # which config/llm.yaml profile to use for vague-path classification

# default saved-note shape (all overridable). single-file: AI summary + readable transcript inline.
render:
  include_transcript: true
  include_timestamps: false        # false -> readable merged paragraphs; true -> [mm:ss] lines
  split_transcript: false          # true -> main note links to a separate <name>.transcript.md

# vague-path classification reads only this many chars of the (markdown-cleaned) summary/transcript lead
classify_snippet_chars: 240
```
> The engine reads its OWN `config/bilibili-engine.yaml` (repo root) — not configured here. The skill depends
> on that file existing + BiliNote reachable for a real transcribe.

- [ ] **Step 2: Create `SKILL.md`** (one agentskills.io descriptor — Claude Code / Codex / OpenClaw / Hermes)

Create `Skill/crawl/bilibili-crawl/SKILL.md`:
```markdown
---
name: bilibili-crawl
description: >
  Use when the user gives a Bilibili video reference (BV id, a bilibili.com URL, or an av id) and wants it
  transcribed and saved as a Markdown note. Transcribes via the frozen Bilibili engine (subtitle-first, ASR
  fallback) and writes Markdown to a chosen path; when the path is vague (a folder, the KB root, or omitted)
  it classifies the note into a subfolder. Do NOT use for non-Bilibili URLs or for article/text crawling.
version: 0.1.0
license: MIT
tags:
  - bilibili
  - video
  - transcription
  - markdown
  - knowledge-base
metadata:
  hermes:
    category: knowledge-capture
    required_environment_variables:
      - MIMO_API_KEY            # or another config/llm.yaml profile key (vague-path classification only)
      - COOKIE_MANAGER_PASSWORD # SP-1 cookie decrypt (name per your config password_env)
  openclaw:
    requires:
      bins: [bilibili-crawl]
    install: "pip install -e Engine/common -e Engine/bilibili -e Skill/crawl/bilibili-crawl"
---

# bilibili-crawl

Transcribe a Bilibili video and save it as Markdown.

## When to use
A user shares a Bilibili video (BV / URL / av) and wants the transcript + AI summary in their knowledge base.

## How to run
```bash
bilibili-crawl "<BV-id-or-url>" --out "<path>" [--json]
```
- `--out FILE.md` → write there verbatim.
- `--out DIR` / omit `--out` → vague: classify into a subfolder under the configured `output_root`.
- `--json` → machine-readable result (`path`, `transcript_path`, `category`, `transcript_source`, ...).

## Setup
1. `cp config.example.yaml config.yaml` and set `output_root` + the cookie-manager connection.
2. Ensure the repo-root `config/llm.yaml` has the `mimo` profile (vague-path classification) and
   `config/bilibili-engine.yaml` points at a reachable BiliNote.
3. Put credentials in `.env` (never in the repo): the cookie password and one LLM `api_key_env`.

## Notes
Reads cookies from SP-1 cookie-manager (pull-only, decrypted in memory; a missing cookie degrades to the
public-video ASR path, never fatal). Pure consumer of the frozen Bilibili engine — see `docs/interface.md`.
```

- [ ] **Step 3: Create `scripts/sync-skill.sh`**

Create `Skill/crawl/bilibili-crawl/scripts/sync-skill.sh`:
```bash
#!/usr/bin/env bash
# Deploy this one SKILL.md to the four agent-CLI skill directories (one source, many targets).
# agentskills.io is the shared standard — no per-runtime format fork.
set -euo pipefail
SRC="$(cd "$(dirname "$0")/.." && pwd)"
NAME="bilibili-crawl"
for dir in "$HOME/.claude/skills" "$HOME/.codex/skills" "$HOME/.openclaw/skills" "$HOME/.hermes/skills"; do
  mkdir -p "$dir/$NAME"
  ln -sf "$SRC/SKILL.md" "$dir/$NAME/SKILL.md"
  echo "linked $dir/$NAME/SKILL.md -> $SRC/SKILL.md"
done
```
Then: `chmod +x Skill/crawl/bilibili-crawl/scripts/sync-skill.sh`

- [ ] **Step 4: Create `.gitignore`**

Create `Skill/crawl/bilibili-crawl/.gitignore`:
```gitignore
config.yaml
.env
*.egg-info/
__pycache__/
```

- [ ] **Step 5: Sanity-check the CLI is wired (no new test)**

Run (from `Skill/crawl/bilibili-crawl/`):
```bash
pip install -e . -q && bilibili-crawl --help
```
Expected: argparse help text with `ref`, `--out`, `--json`, `--profile`, `--config`.

- [ ] **Step 6: Commit**

```bash
git add Skill/crawl/bilibili-crawl/scripts/sync-skill.sh && chmod +x Skill/crawl/bilibili-crawl/scripts/sync-skill.sh
git commit -m "feat(SP-4b): packaging — SKILL.md (agentskills.io), config.example, sync script, gitignore" -- \
  Skill/crawl/bilibili-crawl/SKILL.md \
  Skill/crawl/bilibili-crawl/config.example.yaml \
  Skill/crawl/bilibili-crawl/scripts/sync-skill.sh \
  Skill/crawl/bilibili-crawl/.gitignore
```

---

## Task 9: Docs freeze — interface.md, architecture.md, RepoMem

**Files:**
- Modify: `Skill/crawl/bilibili-crawl/docs/interface.md`
- Modify: `Skill/crawl/bilibili-crawl/docs/architecture.md`
- Modify: `Skill/crawl/bilibili-crawl/docs/RepoMem/architecture.md`
- Modify: `Skill/crawl/bilibili-crawl/docs/RepoMem/decisions.md`

- [ ] **Step 1: Freeze `docs/interface.md`**

Replace `Skill/crawl/bilibili-crawl/docs/interface.md` with the v1 frozen contract:
```markdown
# bilibili-crawl — 公开接口合约（v1，冻结）

> 已实现并冻结的 v1 公开 API。所有调用方（LLM agent、脚本、CI）针对本文件编程，不依赖内部实现。
> SP-4b 是 `Engine/bilibili`（SP-4a 冻结引擎）与 `jarvankb_common.LLMClient` 的纯消费者——不修改引擎，
> 亦不持有自己的 LLM 连接配置。

## 1. Python API

### 安装与导入
```bash
pip install -e Engine/common -e Engine/bilibili -e Skill/crawl/bilibili-crawl
```
```python
from bilibili_crawl import save_bilibili, SaveResult
```

### `save_bilibili()` — 主入口
```python
def save_bilibili(
    ref: str,
    save_path: str | None = None,
    *,
    profile: str | None = None,
    config_path: str | None = None,
) -> SaveResult:
```

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `ref` | `str` | （必填）| 视频引用：BV id / `bilibili.com` URL / av id |
| `save_path` | `str \| None` | `None` | `.md` 结尾 = 明确路径直接写入；目录 / `output_root` / `None` / 空 = 模糊路径触发 LLM 分类 |
| `profile` | `str \| None` | `None` | LLM 配置文件名覆盖；`None` 取 `config.yaml` 的 `llm.profile`（默认 `default`，示例配置用 `mimo`） |
| `config_path` | `str \| None` | `None` | `config.yaml` 路径；`None` 取 `BILIBILI_CRAWL_CONFIG` 环境变量，否则当前目录 `config.yaml` |

**异常：** 引擎失败抛 `BilibiliEngineError` 子类（`InvalidVideoRef` / `TranscriptionFailed` /
`TranscriptionTimeout` / `BiliNoteUnavailable`）；配置缺失抛 `FileNotFoundError`。**Cookie 失败不致命**——
降级为无凭据（公开视频 ASR 路径）。

### `SaveResult` — 返回字段
```python
@dataclass
class SaveResult:
    path: str                   # 主文件绝对路径
    transcript_path: str | None # split_transcript=True 时的转录文件绝对路径，否则 None
    title: str                  # 视频标题
    ref: str                    # 原始请求 ref
    transcript_source: str      # "subtitle" | "asr"
    category: str | None        # LLM 分类子文件夹名；明确路径写入时为 None
    was_vague: bool             # True 表示发生了 LLM 路径分类
    proposed_new: bool          # True 表示 LLM 建议了一个新子文件夹
```

## 2. CLI
```bash
bilibili-crawl <ref> [--out PATH] [--json] [--profile NAME] [--config PATH]
```
退出码：`0` 成功 / `1` 通用错误（配置 / cookie / LLM）/ `2` `BilibiliEngineError`（转录失败）/
`3` `BiliNoteUnavailable`（BN 不可达）。

## 3. 支持的 ref 形式
与 `Engine/bilibili` 一致：BV id / `bilibili.com` URL / av id（见 `Engine/bilibili/docs/interface.md`）。

## 4. 依赖的上游接口
- **`Engine/bilibili`（SP-4a，冻结）：** `transcribe(ref, credential=None) -> BilibiliResult`，
  `result.render(RenderOptions(...))`；完整合约见 `Engine/bilibili/docs/interface.md`。
- **`jarvankb_common.LLMClient`（Engine/common，SP-3 冻结）：** `LLMClient(profile).complete(messages) -> str`。

## 5. 配置文件（`config.yaml`）
见 `config.example.yaml`：`output_root` / `cookie{base_url,uuid,password_env}` / `llm{profile}` /
`render{include_transcript,include_timestamps,split_transcript}` / `classify_snippet_chars`。引擎自身配置
（`config/bilibili-engine.yaml`）不在此处。真实 `config.yaml` 被 `.gitignore` 排除，密钥存 `.env`。
```

- [ ] **Step 2: Update `docs/architecture.md`** (external summary — replace the placeholder)

Replace `Skill/crawl/bilibili-crawl/docs/architecture.md`:
```markdown
# bilibili-crawl — architecture (external summary)

Pure consumer skill: `ref → cookie pull (SP-1, domain=bilibili.com) → BilibiliCredential → frozen SP-4a
engine transcribe → render → save Markdown`. Vague save paths are classified by `jarvankb_common.LLMClient`
into a subfolder under `output_root`. Cookie failure degrades to the public-video ASR path (non-fatal).

Modules: `cookie` (pull+decrypt+credential), `config` (load), `classify` (vague + LLM categorize),
`saver` (path + write, single/split), `api` (orchestrate `save_bilibili`), `cli` (thin adapter). Frozen
upstreams (`bilibili` engine, `jarvankb_common.LLMClient`) are consumed verbatim. Internal detail:
`docs/RepoMem/architecture.md`. Frozen contract: `docs/interface.md`.
```

- [ ] **Step 3: Populate `docs/RepoMem/architecture.md`** (internal)

Replace `Skill/crawl/bilibili-crawl/docs/RepoMem/architecture.md`:
```markdown
# Module internal architecture

Layering (leaf → orchestration): `cookie` / `config` / `saver` / `classify` are independent leaves;
`api.save_bilibili` orchestrates them + the frozen engine; `cli` is a thin argparse adapter over `api`.

Key paths:
- Cookie: `cookie.pull(source, domain="bilibili.com")` reuses SP-3's verified decrypt (legacy +
  aes-128-cbc-fixed); `build_credential` maps `SESSDATA`(+`bili_jct`,`buvid3`) → `BilibiliCredential`, or
  `None` when SESSDATA absent. In-memory only.
- Render: options come from `config.render`; `api` passes `slug=target.stem` so a split transcript file
  (`<stem>.transcript.md`) matches the engine's in-document link.
- Classify input: `metadata.title` + a markdown-stripped lead of `summary_markdown` (fallback
  `transcript.full_text`), capped at `classify_snippet_chars`.
- Graceful degrade: cookie pull/decrypt failure is caught in `api` → `credential=None` + warning.

Test seams: `api.transcribe` / `api.LLMClient` / `api.cookie.*` / `api.cfgmod.load_config` are
module-level so unit tests monkeypatch them — no live engine / LLM / cookie service needed.
```

- [ ] **Step 4: Append the module decision log** (prepend under the header)

Prepend to `Skill/crawl/bilibili-crawl/docs/RepoMem/decisions.md` (below the existing header lines):
```markdown
## 2026-06-07 — sp4b-bilibili-skill — Bilibili Skill v1 (mirror SP-3)
Decisions: packaging mirrors SP-3 (importable `save_bilibili` + thin CLI + one agentskills.io SKILL.md);
cookie via SP-3 pull+decrypt reuse with `domain="bilibili.com"` (no dot) → `BilibiliCredential`; vague_path
= rule-based (`.md`=explicit) + infer-existing/propose-new; classify input = title + summary lead (fallback
transcript lead, cap `classify_snippet_chars` default 240); render default = single file (summary + readable
transcript), config-overridable to split.
Divergence from SP-3 worth noting: **cookie failure is NON-FATAL here** (engine is cookie-less-capable on
public videos) — contrast SP-3's fail-loud. What changes if revisited: if the engine ever requires SESSDATA
for all videos, restore fail-loud.
[Step-8 merge promotion candidates ↗ global persist: "credential-fatality depends on the engine's anonymous
capability (decide per-vertical)"; confirm `domain=bilibili.com` already in credentials.md.]
```

- [ ] **Step 5: Commit**

```bash
git commit -m "docs(SP-4b): freeze interface + architecture + module decisions" -- \
  Skill/crawl/bilibili-crawl/docs/interface.md \
  Skill/crawl/bilibili-crawl/docs/architecture.md \
  Skill/crawl/bilibili-crawl/docs/RepoMem/architecture.md \
  Skill/crawl/bilibili-crawl/docs/RepoMem/decisions.md
```

---

## Task 10: Verification — full suite + offline smoke + live smoke (BN-gated)

**Files:**
- Create: `Skill/crawl/bilibili-crawl/scripts/live_smoke.py`

- [ ] **Step 1: Run the full unit suite**

Run (from `Skill/crawl/bilibili-crawl/`):
```bash
python -m pytest tests/ -q
```
Expected: all pass — `test_smoke`, `test_cookie` (5), `test_config` (2), `test_saver` (7), `test_classify` (5), `test_api` (5), `test_cli` (4).

- [ ] **Step 2: Offline smoke — explicit path through a mocked engine seam**

This proves the api→render→save wiring end-to-end without BiliNote/LLM. It is already covered by
`test_api.py::test_explicit_path_writes_verbatim_no_classify` (engine + cookie mocked, real saver writes a
real file). Confirm that test passes in Step 1; no extra code needed.

- [ ] **Step 3: Create the live-smoke script (gated; run manually)**

Create `Skill/crawl/bilibili-crawl/scripts/live_smoke.py`:
```python
"""Manual live smoke: real Bilibili video -> engine transcribe -> save, both explicit and vague paths.

Requires: BiliNote up (container jarvankb-bilinote @ 127.0.0.1:3015), config/bilibili-engine.yaml present,
config/llm.yaml `mimo` profile + MIMO_API_KEY set, and a bilibili-crawl config.yaml. Run from a dir where
those configs resolve. NOT part of the unit suite (needs live services).

Usage: python scripts/live_smoke.py "BV1xx..." [output_dir]
"""
import sys

from bilibili_crawl import save_bilibili


def main() -> int:
    ref = sys.argv[1] if len(sys.argv) > 1 else "BV1GJ411x7h7"  # replace with a known-public ref
    out_dir = sys.argv[2] if len(sys.argv) > 2 else None

    print("== explicit-path save ==")
    r1 = save_bilibili(ref, save_path=f"{out_dir or '.'}/_smoke_explicit.md")
    print(f"  path={r1.path} source={r1.transcript_source} title={r1.title!r}")

    print("== vague-path save (LLM classify via mimo) ==")
    r2 = save_bilibili(ref, save_path=out_dir)  # None -> classify under config output_root
    print(f"  path={r2.path} category={r2.category} new={r2.proposed_new} was_vague={r2.was_vague}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the live smoke (BN-gated)**

Prereqs check, then run (from `Skill/crawl/bilibili-crawl/` with a real `config.yaml`):
```bash
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3015/ || echo "BN DOWN"
python scripts/live_smoke.py "<a-known-public-BV>"
```
Expected: two saved files; `transcript_source` is `subtitle` (if SESSDATA valid + the video has subtitles)
or `asr`; the vague run prints a chosen `category`.

**GATE:** If BiliNote is down / `config/bilibili-engine.yaml` missing, do NOT block the unit-verified work.
Emit a Dashboard row + `from-sp4bimpler-blocker-bn-down.md` to `toBilibiliCrawlOrche/`, and proceed to
`requesting-code-review` on the offline-verified deliverable. (No LLM-creds gate — `mimo` is configured.)

- [ ] **Step 5: Commit the live-smoke script**

```bash
git commit -m "test(SP-4b): manual live-smoke script (BN-gated)" -- \
  Skill/crawl/bilibili-crawl/scripts/live_smoke.py
```

- [ ] **Step 6: `verification-before-completion`**

Invoke `superpowers:verification-before-completion`. Paste the actual `pytest tests/ -q` summary line and
the live-smoke output (or the BN-down gate note) as evidence before claiming done. Only then proceed to
`requesting-code-review` + `finishing-a-development-branch` (both ask-first), then Step-8 `RepoMem.merge`.

---

## Self-Review (run after writing — checklist)

**1. Spec coverage:**
- design §1 scope (ref→cookie→engine→render→save; vague classify) → Tasks 2,5,6,4. ✓
- §2 decision 1 packaging → Tasks 1,7,8. ✓  decision 2 cookie → Task 2. ✓  decision 3 vague+path → Tasks 4,5. ✓
  decision 4 classify input → Task 5. ✓  decision 5 render default + config override → Tasks 3,6. ✓
- §3 multi-agent packaging (SKILL.md, sync) → Task 8. ✓
- §6 components (cookie/config/classify/saver/api/cli) → Tasks 2–7. ✓
- §7 interface freeze → Task 9. ✓
- §8 error handling (engine errors, BN gate, cookie non-fatal, collision, output_root unset) → Tasks 2,6,7 tests + cli exit codes. ✓
- §9 testing strategy (all bullets) → Tasks 2–7 tests. ✓
- §10 verification (offline + live BN-gated, no LLM gate) → Task 10. ✓

**2. Placeholder scan:** No TBD/TODO; every code step is complete. The only `<...>` are user-supplied config
values (uuid, BV ref) and the engine dist-name confirm-note in Task 1 — both intentional, not plan gaps.

**3. Type consistency:** `SaveResult` fields identical across Tasks 6,7,9 (path, transcript_path, title, ref,
transcript_source, category, was_vague, proposed_new). `classify(result, output_root, client, *, snippet_chars)`
signature consistent (Tasks 5,6). `RenderConfig`/`ModuleConfig` fields consistent (Tasks 3,6). `transcribe`,
`RenderOptions`, `BilibiliCredential` names match the frozen engine surface.
```
