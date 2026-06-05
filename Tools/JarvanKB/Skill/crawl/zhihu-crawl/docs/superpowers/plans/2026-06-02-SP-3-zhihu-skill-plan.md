# SP-3 Zhihu Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Zhihu skill — a Zhihu URL is fetched through the frozen SP-2 engine and saved as Markdown to a user-chosen path; a vague path is classified by an LLM into a subfolder under a configured output root. Land the real `LLMClient` body for SP-6 reuse.

**Architecture:** Two packages. (1) `Engine/common` becomes pip-package `jarvankb-common` (`jarvankb_common`) carrying the real `litellm`-backed `LLMClient` + config loader. (2) `Skill/crawl/zhihu-crawl` is pip-package `zhihu-crawl` (`zhihu_crawl`): importable `save_zhihu()` core + thin `zhihu-crawl` CLI + one agentskills.io `SKILL.md`. SP-3 is a pure consumer of the frozen `zhihu` engine and of `jarvankb_common.LLMClient`. Cookies are pulled from SP-1 over HTTP and decrypted in memory.

**Tech Stack:** Python ≥3.11, setuptools (src-layout, editable installs), `litellm`, `httpx`, `pycryptodome` (AES-CBC), `pyyaml`, `pytest`. Authoritative spec: `docs/superpowers/specs/2026-06-02-SP-3-zhihu-skill-design.md`.

**Build order:** `jarvankb-common` first (SP-3 imports it) → `zhihu-crawl` scaffold → leaf modules (cookie, config, saver, classify) → orchestration (api, cli) → packaging artifacts (SKILL.md, sync, example config) → docs freeze → verification.

**Conventions:** TDD (test → fail → implement → pass → commit). Frequent commits, prefix `feat(SP-3):` / `docs(SP-3):`. Stage ONLY files you touched (shared branch `feat/agentcrawl-bootstrap`, sibling sessions active). Run commands from the worktree root unless a `cd` is shown.

---

## Task 0: Worktree + editable installs

**Files:** none (environment setup)

- [ ] **Step 1: Create the worktree from the LOCAL branch**

The worktree MUST branch from local `feat/agentcrawl-bootstrap` (NOT `origin/main`, which would drop sibling sessions' local commits). Using the `superpowers:using-git-worktrees` skill, create `.worktrees/sp3-zhihu-skill/` based on the current local `feat/agentcrawl-bootstrap` HEAD. If using raw git:

Run (from repo root `/home/shenzhou/Codes/awesome_agent_tools`):
```bash
git worktree add Tools/JarvanKB/.worktrees/sp3-zhihu-skill feat/agentcrawl-bootstrap
```
Expected: `Preparing worktree` + checkout at the current branch tip. Work happens in `Tools/JarvanKB/.worktrees/sp3-zhihu-skill/`; all paths below are relative to `Tools/JarvanKB/` inside that worktree.

- [ ] **Step 2: Editable-install the three packages into the working venv**

Run (from the worktree's `Tools/JarvanKB/`):
```bash
pip install -e Engine/zhihu -e Engine/common -e Skill/crawl/zhihu-crawl
```
Expected: this FAILS until `Engine/common` and `Skill/crawl/zhihu-crawl` have `pyproject.toml` (created in Tasks 1 and 5). Run it now to confirm `zhihu-engine` (already packaged) installs; re-run after Task 1 and Task 5. No commit.

---

## Task 1: `jarvankb-common` package + config loader

**Files:**
- Create: `Engine/common/pyproject.toml`
- Create: `Engine/common/src/jarvankb_common/__init__.py`
- Move:   `Engine/common/src/llm_client.py` → `Engine/common/src/jarvankb_common/llm_client.py`
- Delete: `Engine/common/src/__init__.py`
- Create: `Engine/common/src/jarvankb_common/config.py`
- Test:   `Engine/common/tests/test_config.py`

- [ ] **Step 1: Write the failing test for the config loader**

Create `Engine/common/tests/test_config.py`:
```python
import os
import textwrap
from pathlib import Path

import pytest

from jarvankb_common.config import load_llm_config, resolve_candidates


def _write_cfg(tmp_path: Path) -> Path:
    p = tmp_path / "llm.yaml"
    p.write_text(textwrap.dedent("""
        profiles:
          default:
            model: claude-opus-4-7
            api_key_env: ANTHROPIC_API_KEY
          fallback:
            model: dashscope/qwen-max
            api_key_env: DASHSCOPE_API_KEY
          local:
            model: ollama/llama3
            api_key_env: ""
            api_base_env: OLLAMA_API_BASE
        active: [default, fallback]
    """))
    return p


def test_load_llm_config_resolves_key_from_env(tmp_path, monkeypatch):
    cfg_path = _write_cfg(tmp_path)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    cfg = load_llm_config("default", config_path=cfg_path)
    assert cfg.model == "claude-opus-4-7"
    assert cfg.api_key == "sk-test"
    assert cfg.api_base is None


def test_local_profile_available_without_key(tmp_path, monkeypatch):
    cfg_path = _write_cfg(tmp_path)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("OLLAMA_API_BASE", "http://localhost:11434")
    cfg = load_llm_config("local", config_path=cfg_path)
    assert cfg.model == "ollama/llama3"
    assert cfg.api_key is None
    assert cfg.api_base == "http://localhost:11434"


def test_resolve_candidates_falls_through_active_order(tmp_path, monkeypatch):
    cfg_path = _write_cfg(tmp_path)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)   # default unavailable
    monkeypatch.setenv("DASHSCOPE_API_KEY", "ds-test")        # fallback available
    cands = resolve_candidates("default", config_path=cfg_path)
    assert [c.profile for c in cands] == ["fallback"]


def test_resolve_candidates_requested_first_then_active(tmp_path, monkeypatch):
    cfg_path = _write_cfg(tmp_path)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "ds")
    cands = resolve_candidates("default", config_path=cfg_path)
    assert [c.profile for c in cands] == ["default", "fallback"]
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest Engine/common/tests/test_config.py -q`
Expected: collection/import error — `No module named 'jarvankb_common'` (package not created yet).

- [ ] **Step 3: Create the package skeleton + pyproject**

Create `Engine/common/pyproject.toml`:
```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "jarvankb-common"
version = "0.1.0"
description = "JarvanKB shared layer: LLMClient (litellm backend) + config loader"
requires-python = ">=3.11"
dependencies = [
    "litellm>=1.40",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

Run (from `Engine/common/`):
```bash
git mv src/llm_client.py src/jarvankb_common/llm_client.py 2>/dev/null || (mkdir -p src/jarvankb_common && git mv src/llm_client.py src/jarvankb_common/llm_client.py)
git rm src/__init__.py
```
Create `Engine/common/src/jarvankb_common/__init__.py`:
```python
from .llm_client import LLMClient

__all__ = ["LLMClient"]
```

- [ ] **Step 4: Implement the config loader**

Create `Engine/common/src/jarvankb_common/config.py`:
```python
"""Loader for config/llm.yaml — resolves a profile to model + credentials (from env).

Schema (see config/llm.yaml.example):
    profiles:
      <name>: {model: str, api_key_env: str, api_base_env?: str}
    active: [<name>, ...]   # fallthrough order
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class LLMConfig:
    profile: str
    model: str
    api_key: str | None
    api_base: str | None


def _default_config_path() -> Path:
    env = os.environ.get("JARVANKB_LLM_CONFIG")
    if env:
        return Path(env).expanduser()
    return Path("config/llm.yaml")


def _load_raw(config_path: str | Path | None) -> dict:
    path = Path(config_path).expanduser() if config_path else _default_config_path()
    if not path.exists():
        raise FileNotFoundError(
            f"LLM config not found at {path}. Copy config/llm.yaml.example to config/llm.yaml "
            f"or set JARVANKB_LLM_CONFIG."
        )
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _resolve_profile(name: str, raw: dict) -> LLMConfig:
    prof = raw.get("profiles", {}).get(name)
    if prof is None:
        raise KeyError(f"profile {name!r} not in config (have {list(raw.get('profiles', {}))})")
    key_env = prof.get("api_key_env", "")
    base_env = prof.get("api_base_env", "")
    return LLMConfig(
        profile=name,
        model=prof["model"],
        api_key=os.environ.get(key_env) if key_env else None,
        api_base=os.environ.get(base_env) if base_env else None,
    )


def _is_available(name: str, raw: dict) -> bool:
    prof = raw.get("profiles", {}).get(name, {})
    key_env = prof.get("api_key_env", "")
    return (not key_env) or bool(os.environ.get(key_env))


def load_llm_config(profile: str = "default", config_path: str | Path | None = None) -> LLMConfig:
    return _resolve_profile(profile, _load_raw(config_path))


def resolve_candidates(profile: str = "default", config_path: str | Path | None = None) -> list[LLMConfig]:
    """Available profiles in fallthrough order: requested first, then `active`, deduped."""
    raw = _load_raw(config_path)
    order: list[str] = [profile, *raw.get("active", [])]
    seen: set[str] = set()
    out: list[LLMConfig] = []
    for name in order:
        if name in seen or name not in raw.get("profiles", {}):
            continue
        seen.add(name)
        if _is_available(name, raw):
            out.append(_resolve_profile(name, raw))
    return out
```

- [ ] **Step 5: Reinstall and run the test to verify it passes**

Run (from `Engine/common/`):
```bash
pip install -e . -q && python -m pytest tests/test_config.py -q
```
Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add Engine/common/pyproject.toml Engine/common/src/jarvankb_common/ Engine/common/tests/test_config.py
git rm --cached Engine/common/src/__init__.py 2>/dev/null; true
git commit -m "feat(SP-3): package Engine/common as jarvankb-common + llm config loader"
```

---

## Task 2: `LLMClient` real body (litellm)

**Files:**
- Modify: `Engine/common/src/jarvankb_common/llm_client.py`
- Test:   `Engine/common/tests/test_llm_client.py`

- [ ] **Step 1: Write the failing test (litellm mocked)**

Create `Engine/common/tests/test_llm_client.py`:
```python
import textwrap
import types
from pathlib import Path

import pytest

import jarvankb_common.llm_client as mod
from jarvankb_common.llm_client import LLMClient


def _cfg(tmp_path: Path) -> Path:
    p = tmp_path / "llm.yaml"
    p.write_text(textwrap.dedent("""
        profiles:
          default: {model: claude-opus-4-7, api_key_env: ANTHROPIC_API_KEY}
          fallback: {model: dashscope/qwen-max, api_key_env: DASHSCOPE_API_KEY}
        active: [default, fallback]
    """))
    return p


def _resp(text):
    msg = types.SimpleNamespace(content=text)
    return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])


def test_complete_returns_text(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk")
    calls = {}

    def fake_completion(model, messages, **kw):
        calls["model"] = model
        return _resp("hello-world")

    monkeypatch.setattr(mod.litellm, "completion", fake_completion)
    client = LLMClient(profile="default", config_path=_cfg(tmp_path))
    out = client.complete([{"role": "user", "content": "hi"}])
    assert out == "hello-world"
    assert calls["model"] == "claude-opus-4-7"


def test_complete_falls_through_on_error(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "ds")
    seen = []

    def fake_completion(model, messages, **kw):
        seen.append(model)
        if model == "claude-opus-4-7":
            raise RuntimeError("boom")
        return _resp("from-fallback")

    monkeypatch.setattr(mod.litellm, "completion", fake_completion)
    client = LLMClient(profile="default", config_path=_cfg(tmp_path))
    assert client.complete([{"role": "user", "content": "hi"}]) == "from-fallback"
    assert seen == ["claude-opus-4-7", "dashscope/qwen-max"]


def test_complete_raises_when_all_exhausted(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "ds")
    monkeypatch.setattr(mod.litellm, "completion",
                        lambda model, messages, **kw: (_ for _ in ()).throw(RuntimeError("x")))
    client = LLMClient(profile="default", config_path=_cfg(tmp_path))
    with pytest.raises(RuntimeError):
        client.complete([{"role": "user", "content": "hi"}])


def test_stream_yields_chunks(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk")

    def chunk(text):
        delta = types.SimpleNamespace(content=text)
        return types.SimpleNamespace(choices=[types.SimpleNamespace(delta=delta)])

    monkeypatch.setattr(mod.litellm, "completion",
                        lambda model, messages, stream=False, **kw: iter([chunk("a"), chunk("b"), chunk(None)]))
    client = LLMClient(profile="default", config_path=_cfg(tmp_path))
    assert "".join(client.stream([{"role": "user", "content": "hi"}])) == "ab"


def test_to_opencode_not_implemented(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk")
    client = LLMClient(profile="default", config_path=_cfg(tmp_path))
    with pytest.raises(NotImplementedError):
        client.to_opencode()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest Engine/common/tests/test_llm_client.py -q`
Expected: FAIL — `complete` raises `NotImplementedError` (skeleton body).

- [ ] **Step 3: Implement the real body**

Replace the body of `Engine/common/src/jarvankb_common/llm_client.py` (keep the frozen signatures; add an optional `config_path` kwarg that defaults to `None` so existing `LLMClient(profile=...)` calls are unaffected):
```python
"""LLMClient — uniform LLM dispatcher with a litellm backend.

Design reference: Skill/crawl/zhihu-crawl/docs/superpowers/specs/2026-06-02-SP-3-zhihu-skill-design.md §7
(real impl landed in SP-3; first consumer = zhihu-crawl vague_path classification).

Public signatures (frozen v1 contract): __init__(profile), complete(messages, **kwargs) -> str,
stream(messages, **kwargs) -> Iterator[str], to_opencode().
"""
from __future__ import annotations

from typing import Any, Iterator

import litellm

from .config import resolve_candidates


class LLMClient:
    """Uniform LLM client. Routes to any provider via litellm; provider switches by config alone."""

    def __init__(self, profile: str = "default", config_path: str | None = None) -> None:
        self.profile = profile
        self._candidates = resolve_candidates(profile, config_path=config_path)
        if not self._candidates:
            raise RuntimeError(
                f"No available LLM profile for {profile!r}. Set the api_key_env credentials in your "
                f"environment (.env) for one of the configured profiles."
            )

    def complete(self, messages: list[dict], **kwargs: Any) -> str:
        last_err: Exception | None = None
        for cfg in self._candidates:
            try:
                resp = litellm.completion(
                    model=cfg.model, messages=messages,
                    api_key=cfg.api_key, api_base=cfg.api_base, **kwargs,
                )
                return resp.choices[0].message.content
            except Exception as e:  # noqa: BLE001 — provider-agnostic fallthrough
                last_err = e
        raise RuntimeError(f"All LLM profiles failed for {self.profile!r}") from last_err

    def stream(self, messages: list[dict], **kwargs: Any) -> Iterator[str]:
        last_err: Exception | None = None
        for cfg in self._candidates:
            try:
                stream = litellm.completion(
                    model=cfg.model, messages=messages,
                    api_key=cfg.api_key, api_base=cfg.api_base, stream=True, **kwargs,
                )
                for chunk in stream:
                    piece = chunk.choices[0].delta.content
                    if piece:
                        yield piece
                return
            except Exception as e:  # noqa: BLE001
                last_err = e
        raise RuntimeError(f"All LLM profiles failed for {self.profile!r}") from last_err

    def to_opencode(self) -> Any:
        """v1+ escape hatch: convert to opencode agent loop. Not implemented in v1."""
        raise NotImplementedError("opencode integration planned for v1.x")
```

- [ ] **Step 4: Run the test to verify it passes**

Run (from `Engine/common/`): `python -m pytest tests/ -q`
Expected: all passed (config + llm_client).

- [ ] **Step 5: Commit**

```bash
git add Engine/common/src/jarvankb_common/llm_client.py Engine/common/tests/test_llm_client.py
git commit -m "feat(SP-3): land real LLMClient body (litellm + active-order fallthrough)"
```

---

## Task 3: Update `Engine/common` interface + docs

**Files:**
- Modify: `Engine/common/docs/interface.md`
- Modify: `Engine/common/docs/RepoMem/decisions.md`

- [ ] **Step 1: Update the import + status in interface.md**

Replace the `## LLMClient` usage block and Stability/Body notes in `Engine/common/docs/interface.md`:
```markdown
## LLMClient

```python
from jarvankb_common import LLMClient          # pkg: jarvankb-common (pip install -e Engine/common)

client = LLMClient(profile="default")           # profile defined in config/llm.yaml
text   = client.complete([{"role": "user", "content": "..."}])
chunks = client.stream([{"role": "user", "content": "..."}])
```

**Stability**: signatures (`__init__` + `complete` + `stream` + `to_opencode`) are the v1 frozen contract.
`__init__` accepts an optional `config_path` kwarg (defaults to `config/llm.yaml` / `$JARVANKB_LLM_CONFIG`).
**Body**: **real impl landed in SP-3** (litellm backend, active-order fallthrough). SP-6 reuses as-is.
```

- [ ] **Step 2: Append a decision entry**

Prepend to `Engine/common/docs/RepoMem/decisions.md` (under the header):
```markdown
## 2026-06-05 — sp3-zhihu-skill — LLMClient real impl + packaged as jarvankb-common
Engine/common is now pip-package `jarvankb-common` (import `jarvankb_common`, src-layout), so LLMClient is
genuinely importable like every other module. Real litellm body landed (SP-3 is first consumer); active-order
profile fallthrough; `to_opencode()` still NotImplementedError (v1.x). Import is now
`from jarvankb_common import LLMClient` (was the non-working `from Engine.common.src.llm_client import ...`).
What changes if revisited: provider routing/config schema lives in `config/llm.yaml` + `jarvankb_common.config`.
[Promotion candidate ↗ global persist at SP-3 Step-8 merge — cross-SP reuse by SP-6/SP-4b.]
```

- [ ] **Step 3: Commit**

```bash
git add Engine/common/docs/interface.md Engine/common/docs/RepoMem/decisions.md
git commit -m "docs(SP-3): freeze LLMClient interface (jarvankb_common import, real impl landed)"
```

---

## Task 4: `zhihu-crawl` package scaffold

**Files:**
- Create: `Skill/crawl/zhihu-crawl/pyproject.toml`
- Create: `Skill/crawl/zhihu-crawl/src/zhihu_crawl/__init__.py`
- Create: `Skill/crawl/zhihu-crawl/tests/test_smoke.py`

- [ ] **Step 1: Write a trivial import test**

Create `Skill/crawl/zhihu-crawl/tests/test_smoke.py`:
```python
def test_package_imports():
    import zhihu_crawl  # noqa: F401
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest Skill/crawl/zhihu-crawl/tests/test_smoke.py -q`
Expected: `No module named 'zhihu_crawl'`.

- [ ] **Step 3: Create pyproject + package init**

Create `Skill/crawl/zhihu-crawl/pyproject.toml`:
```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "zhihu-crawl"
version = "0.1.0"
description = "Zhihu skill: URL -> frozen zhihu engine -> save Markdown (vague-path LLM classification)"
requires-python = ">=3.11"
dependencies = [
    "zhihu-engine",
    "jarvankb-common",
    "httpx>=0.27",
    "pycryptodome>=3.20",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[project.scripts]
zhihu-crawl = "zhihu_crawl.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```
Create `Skill/crawl/zhihu-crawl/src/zhihu_crawl/__init__.py`:
```python
from .api import SaveResult, save_zhihu

__all__ = ["save_zhihu", "SaveResult"]
```
> Note: `__init__` imports `api`, which is created in Task 9. Until then `test_smoke` will fail on the missing `api` import — that is expected; this task's commit lands the pyproject/scaffold, and `test_smoke` goes green at Task 9. To keep this task self-contained, temporarily make `__init__.py` empty and add the re-exports in Task 9.

Set `Skill/crawl/zhihu-crawl/src/zhihu_crawl/__init__.py` to empty for now (re-exports added in Task 9).

- [ ] **Step 4: Reinstall + run the smoke test**

Run (from `Skill/crawl/zhihu-crawl/`):
```bash
pip install -e . -q && python -m pytest tests/test_smoke.py -q
```
Expected: 1 passed (empty package imports).

- [ ] **Step 5: Commit**

```bash
git add Skill/crawl/zhihu-crawl/pyproject.toml Skill/crawl/zhihu-crawl/src/zhihu_crawl/__init__.py Skill/crawl/zhihu-crawl/tests/test_smoke.py
git commit -m "feat(SP-3): scaffold zhihu-crawl package (pyproject + src layout)"
```

---

## Task 5: `cookie.py` — SP-1 pull + decrypt

**Files:**
- Create: `Skill/crawl/zhihu-crawl/src/zhihu_crawl/cookie.py`
- Test:   `Skill/crawl/zhihu-crawl/tests/test_cookie.py`

- [ ] **Step 1: Write the failing tests (decrypt round-trips; pull mocked)**

Create `Skill/crawl/zhihu-crawl/tests/test_cookie.py`:
```python
import base64
import json
import subprocess

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from zhihu_crawl.cookie import CookieSource, decrypt, pull, _the_key


UUID = "test-uuid"
PW = "test-password"
PLAINTEXT = {
    "cookie_data": {".zhihu.com": [
        {"name": "z_c0", "value": "ZZZ"},
        {"name": "d_c0", "value": "DDD"},
    ]},
    "local_storage_data": {},
    "update_time": "2026-06-05T00:00:00Z",
}


def _enc_fixed(plaintext: bytes, the_key: str) -> str:
    key = the_key.encode("utf-8")[:16]
    ct = AES.new(key, AES.MODE_CBC, b"\x00" * 16).encrypt(pad(plaintext, 16))
    return base64.b64encode(ct).decode()


def _enc_legacy_via_openssl(plaintext: bytes, the_key: str) -> str:
    # Reference encryptor = OpenSSL, matching CryptoJS Salted__ + EVP_BytesToKey(MD5).
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


def test_pull_returns_name_value_dict(monkeypatch):
    the_key = _the_key(UUID, PW)
    enc = _enc_fixed(json.dumps(PLAINTEXT).encode(), the_key)

    class FakeResp:
        def raise_for_status(self): pass
        def json(self): return {"encrypted": enc, "crypto_type": "aes-128-cbc-fixed"}

    class FakeClient:
        def get(self, url): assert url.endswith("/get/test-uuid"); return FakeResp()

    src = CookieSource(base_url="http://127.0.0.1:48088", uuid=UUID, password=PW)
    cookies = pull(src, client=FakeClient())
    assert cookies == {"z_c0": "ZZZ", "d_c0": "DDD"}
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest Skill/crawl/zhihu-crawl/tests/test_cookie.py -q`
Expected: `No module named 'zhihu_crawl.cookie'`.

- [ ] **Step 3: Implement `cookie.py`**

Create `Skill/crawl/zhihu-crawl/src/zhihu_crawl/cookie.py`:
```python
"""Active cookie pull from SP-1 cookie-manager + in-memory client-side decrypt.

Pull-only (SP-1 push permanently cancelled). Plaintext cookies live only in memory; never written to disk.
Decrypt protocol: Service/crawl/cookie-manager/docs/interface.md §3.
"""
from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass

import httpx
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


def pull(source: CookieSource, domain: str = ".zhihu.com", *, client: httpx.Client | None = None) -> dict[str, str]:
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
```

- [ ] **Step 4: Run to verify it passes**

Run (from `Skill/crawl/zhihu-crawl/`): `python -m pytest tests/test_cookie.py -q`
Expected: 3 passed. (Requires `openssl` on PATH for the legacy test — standard on Linux.)

- [ ] **Step 5: Commit**

```bash
git add Skill/crawl/zhihu-crawl/src/zhihu_crawl/cookie.py Skill/crawl/zhihu-crawl/tests/test_cookie.py
git commit -m "feat(SP-3): cookie pull from SP-1 + client-side decrypt (legacy + fixed)"
```

---

## Task 6: `config.py` — module config loader

**Files:**
- Create: `Skill/crawl/zhihu-crawl/src/zhihu_crawl/config.py`
- Test:   `Skill/crawl/zhihu-crawl/tests/test_config.py`

- [ ] **Step 1: Write the failing test**

Create `Skill/crawl/zhihu-crawl/tests/test_config.py`:
```python
import textwrap
from pathlib import Path

from zhihu_crawl.config import load_config


def test_load_config_reads_password_from_env(tmp_path, monkeypatch):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(textwrap.dedent(f"""
        output_root: {tmp_path}/KB
        cookie:
          base_url: http://127.0.0.1:48088
          uuid: my-uuid
          password_env: COOKIE_PW
        llm:
          profile: default
    """))
    monkeypatch.setenv("COOKIE_PW", "secret")
    mc = load_config(cfg)
    assert mc.output_root == Path(f"{tmp_path}/KB")
    assert mc.cookie.base_url == "http://127.0.0.1:48088"
    assert mc.cookie.uuid == "my-uuid"
    assert mc.cookie.password == "secret"
    assert mc.llm_profile == "default"


def test_llm_profile_defaults_to_default(tmp_path, monkeypatch):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(textwrap.dedent(f"""
        output_root: {tmp_path}/KB
        cookie: {{base_url: u, uuid: x, password_env: COOKIE_PW}}
    """))
    monkeypatch.setenv("COOKIE_PW", "s")
    assert load_config(cfg).llm_profile == "default"
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest Skill/crawl/zhihu-crawl/tests/test_config.py -q`
Expected: `No module named 'zhihu_crawl.config'`.

- [ ] **Step 3: Implement `config.py`**

Create `Skill/crawl/zhihu-crawl/src/zhihu_crawl/config.py`:
```python
"""Module config loader. Schema: config.example.yaml. Real config (config.yaml) is gitignored."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

from .cookie import CookieSource


@dataclass
class ModuleConfig:
    output_root: Path
    cookie: CookieSource
    llm_profile: str


def _default_path() -> Path:
    return Path(os.environ.get("ZHIHU_CRAWL_CONFIG", "config.yaml")).expanduser()


def load_config(config_path: str | Path | None = None) -> ModuleConfig:
    path = Path(config_path).expanduser() if config_path else _default_path()
    if not path.exists():
        raise FileNotFoundError(
            f"zhihu-crawl config not found at {path}. Copy config.example.yaml to config.yaml "
            f"or set ZHIHU_CRAWL_CONFIG."
        )
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    ck = raw["cookie"]
    return ModuleConfig(
        output_root=Path(raw["output_root"]).expanduser(),
        cookie=CookieSource(
            base_url=ck["base_url"],
            uuid=ck["uuid"],
            password=os.environ.get(ck["password_env"], ""),
        ),
        llm_profile=raw.get("llm", {}).get("profile", "default"),
    )
```

- [ ] **Step 4: Run to verify it passes**

Run (from `Skill/crawl/zhihu-crawl/`): `python -m pytest tests/test_config.py -q`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add Skill/crawl/zhihu-crawl/src/zhihu_crawl/config.py Skill/crawl/zhihu-crawl/tests/test_config.py
git commit -m "feat(SP-3): module config loader (output_root, cookie source, llm profile)"
```

---

## Task 7: `saver.py` — vagueness rule + path resolution + write

**Files:**
- Create: `Skill/crawl/zhihu-crawl/src/zhihu_crawl/saver.py`
- Test:   `Skill/crawl/zhihu-crawl/tests/test_saver.py`

- [ ] **Step 1: Write the failing tests**

Create `Skill/crawl/zhihu-crawl/tests/test_saver.py`:
```python
from pathlib import Path

from zhihu_crawl.saver import is_vague, resolve_target, slugify, write


def test_is_vague_rules(tmp_path):
    root = tmp_path / "KB"
    assert is_vague(None, root) is True
    assert is_vague("", root) is True
    assert is_vague(str(root), root) is True              # equals output_root
    assert is_vague(str(root / "tech"), root) is True      # a directory / no .md
    assert is_vague(str(root / "tech" / "note.md"), root) is False  # explicit .md


def test_slugify_keeps_cjk_and_hyphenates():
    assert slugify("  Hello World!  ") == "hello-world"
    assert slugify("知乎 答案 / Test") == "知乎-答案-test"
    assert slugify("") == "untitled"


def test_resolve_target_explicit_md_is_verbatim(tmp_path):
    root = tmp_path / "KB"
    p = resolve_target(str(tmp_path / "x" / "note.md"), root, None, "Some Title")
    assert p == (tmp_path / "x" / "note.md")


def test_resolve_target_vague_uses_category_and_slug(tmp_path):
    root = tmp_path / "KB"
    p = resolve_target(None, root, "tech", "My Answer")
    assert p == root / "tech" / "my-answer.md"


def test_resolve_target_dedups_existing(tmp_path):
    root = tmp_path / "KB"
    (root / "tech").mkdir(parents=True)
    (root / "tech" / "my-answer.md").write_text("x")
    p = resolve_target(None, root, "tech", "My Answer")
    assert p == root / "tech" / "my-answer-2.md"


def test_write_creates_parents(tmp_path):
    target = tmp_path / "a" / "b" / "c.md"
    out = write(target, "# hi")
    assert out.read_text() == "# hi"
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest Skill/crawl/zhihu-crawl/tests/test_saver.py -q`
Expected: `No module named 'zhihu_crawl.saver'`.

- [ ] **Step 3: Implement `saver.py`**

Create `Skill/crawl/zhihu-crawl/src/zhihu_crawl/saver.py`:
```python
"""Path resolution + Markdown write. Vagueness rule: explicit == a path naming a .md file."""
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
    base = Path(output_root).expanduser() / (category or "")
    return _dedup(base / f"{slugify(title)}.md")


def write(target: Path, markdown: str) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markdown, encoding="utf-8")
    return target
```

- [ ] **Step 4: Run to verify it passes**

Run (from `Skill/crawl/zhihu-crawl/`): `python -m pytest tests/test_saver.py -q`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add Skill/crawl/zhihu-crawl/src/zhihu_crawl/saver.py Skill/crawl/zhihu-crawl/tests/test_saver.py
git commit -m "feat(SP-3): saver — vagueness rule, slug, path resolution, dedup write"
```

---

## Task 8: `classify.py` — vague_path LLM classification

**Files:**
- Create: `Skill/crawl/zhihu-crawl/src/zhihu_crawl/classify.py`
- Test:   `Skill/crawl/zhihu-crawl/tests/test_classify.py`

- [ ] **Step 1: Write the failing tests (LLMClient mocked)**

Create `Skill/crawl/zhihu-crawl/tests/test_classify.py`:
```python
import types
from pathlib import Path

from zhihu_crawl.classify import classify, existing_subfolders


def _result(title="Transformer 解析", typ="answer", body="深度学习注意力机制..."):
    return types.SimpleNamespace(title=title, type=typ, content_markdown=body)


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


def test_classify_picks_existing(tmp_path):
    (tmp_path / "tech").mkdir()
    client = FakeClient('{"category": "tech", "is_new": false}')
    cat = classify(_result(), tmp_path, client)
    assert cat.name == "tech"
    assert cat.is_new is False
    assert "tech" in client.prompt   # existing folders fed to the model


def test_classify_proposes_new_folder(tmp_path):
    (tmp_path / "tech").mkdir()
    client = FakeClient('```json\n{"category": "Machine Learning", "is_new": true}\n```')
    cat = classify(_result(), tmp_path, client)
    assert cat.name == "machine-learning"   # slugged
    assert cat.is_new is True


def test_classify_marks_new_when_not_in_existing(tmp_path):
    (tmp_path / "tech").mkdir()
    client = FakeClient('{"category": "philosophy"}')   # model omitted is_new
    cat = classify(_result(), tmp_path, client)
    assert cat.name == "philosophy"
    assert cat.is_new is True   # not among existing → new
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest Skill/crawl/zhihu-crawl/tests/test_classify.py -q`
Expected: `No module named 'zhihu_crawl.classify'`.

- [ ] **Step 3: Implement `classify.py`**

Create `Skill/crawl/zhihu-crawl/src/zhihu_crawl/classify.py`:
```python
"""vague_path classification: infer an existing subfolder under output_root, or propose a new one."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .saver import slugify

_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
_OBJ_RE = re.compile(r"\{.*\}", re.DOTALL)


@dataclass
class Category:
    name: str
    is_new: bool


def existing_subfolders(output_root: Path) -> list[str]:
    root = Path(output_root).expanduser()
    if not root.exists():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir() and not p.name.startswith("."))


def _build_prompt(subfolders: list[str], title: str, typ: str, snippet: str) -> str:
    folder_list = ", ".join(subfolders) if subfolders else "(none yet)"
    return (
        "You classify a saved Zhihu item into ONE subfolder of a personal knowledge base.\n"
        f"Existing subfolders: {folder_list}\n"
        f"Item type: {typ}\nTitle: {title}\nContent snippet: {snippet}\n\n"
        "Pick the single best existing subfolder, or propose a NEW concise subfolder name if none fit. "
        'Reply with ONLY JSON: {"category": "<name>", "is_new": <true|false>}.'
    )


def _parse(raw: str) -> dict:
    m = _FENCE_RE.search(raw) or _OBJ_RE.search(raw)
    return json.loads(m.group(1) if m and m.re is _FENCE_RE else (m.group(0) if m else raw))


def classify(result, output_root: Path, client) -> Category:
    subs = existing_subfolders(output_root)
    typ = getattr(result.type, "value", str(result.type))
    snippet = (result.content_markdown or "")[:500]
    raw = client.complete([{"role": "user", "content": _build_prompt(subs, result.title, typ, snippet)}])
    data = _parse(raw)
    name = slugify(str(data["category"]))
    is_new = name not in subs   # authoritative: trust the filesystem, not the model's flag
    return Category(name=name, is_new=is_new)
```

- [ ] **Step 4: Run to verify it passes**

Run (from `Skill/crawl/zhihu-crawl/`): `python -m pytest tests/test_classify.py -q`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add Skill/crawl/zhihu-crawl/src/zhihu_crawl/classify.py Skill/crawl/zhihu-crawl/tests/test_classify.py
git commit -m "feat(SP-3): vague_path classification (infer existing + propose new)"
```

---

## Task 9: `api.py` — `save_zhihu` orchestration

**Files:**
- Create: `Skill/crawl/zhihu-crawl/src/zhihu_crawl/api.py`
- Modify: `Skill/crawl/zhihu-crawl/src/zhihu_crawl/__init__.py` (add re-exports)
- Test:   `Skill/crawl/zhihu-crawl/tests/test_api.py`

- [ ] **Step 1: Write the failing tests (engine, cookie, LLMClient, config all mocked)**

Create `Skill/crawl/zhihu-crawl/tests/test_api.py`:
```python
import types
from pathlib import Path

import zhihu_crawl.api as api
from zhihu_crawl.config import ModuleConfig
from zhihu_crawl.cookie import CookieSource


def _fake_result(title="My Answer", typ="answer"):
    r = types.SimpleNamespace(title=title, type=typ, url="https://zhihu/x",
                              content_markdown="body")
    r.to_markdown = lambda with_frontmatter=True: "# My Answer\nbody"
    return r


def _patch_common(monkeypatch, tmp_path, fetch_result=None, classify_name="tech", classify_new=False):
    mc = ModuleConfig(output_root=tmp_path / "KB",
                      cookie=CookieSource("u", "id", "pw"), llm_profile="default")
    monkeypatch.setattr(api.cfgmod, "load_config", lambda p=None: mc)
    monkeypatch.setattr(api.cookie, "pull", lambda src, **kw: {"z_c0": "Z"})
    monkeypatch.setattr(api, "fetch", lambda url, **kw: fetch_result or _fake_result())
    monkeypatch.setattr(api, "LLMClient", lambda profile=None: object())
    monkeypatch.setattr(api.classify, "classify",
                        lambda result, root, client: api.classify.Category(classify_name, classify_new))
    return mc


def test_explicit_path_writes_verbatim_no_classify(tmp_path, monkeypatch):
    _patch_common(monkeypatch, tmp_path)
    called = {"classify": False}
    monkeypatch.setattr(api.classify, "classify",
                        lambda *a, **k: called.__setitem__("classify", True) or api.classify.Category("x", True))
    target = tmp_path / "out" / "note.md"
    r = api.save_zhihu("https://zhihu/x", save_path=str(target))
    assert Path(r.path) == target
    assert target.read_text().startswith("# My Answer")
    assert r.was_vague is False
    assert r.category is None
    assert called["classify"] is False


def test_vague_path_classifies_and_saves(tmp_path, monkeypatch):
    _patch_common(monkeypatch, tmp_path, classify_name="tech", classify_new=False)
    r = api.save_zhihu("https://zhihu/x", save_path=None)
    assert r.was_vague is True
    assert r.category == "tech"
    assert r.proposed_new is False
    assert Path(r.path) == tmp_path / "KB" / "tech" / "my-answer.md"
    assert Path(r.path).read_text().startswith("# My Answer")


def test_result_fields(tmp_path, monkeypatch):
    _patch_common(monkeypatch, tmp_path)
    r = api.save_zhihu("https://zhihu/x", save_path=str(tmp_path / "n.md"))
    assert r.title == "My Answer"
    assert r.type == "answer"
    assert r.url == "https://zhihu/x"
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest Skill/crawl/zhihu-crawl/tests/test_api.py -q`
Expected: `No module named 'zhihu_crawl.api'`.

- [ ] **Step 3: Implement `api.py`**

Create `Skill/crawl/zhihu-crawl/src/zhihu_crawl/api.py`:
```python
"""save_zhihu — orchestrate cookie pull -> frozen zhihu engine fetch -> markdown -> resolve path -> write.

Module-level `fetch` and `LLMClient` are imported so tests can monkeypatch them.
"""
from __future__ import annotations

from dataclasses import dataclass

from jarvankb_common import LLMClient
from zhihu import fetch

from . import classify, cookie, saver
from . import config as cfgmod


@dataclass
class SaveResult:
    path: str
    title: str
    type: str
    url: str
    category: str | None
    was_vague: bool
    proposed_new: bool


def save_zhihu(url: str, save_path: str | None = None, *,
               with_comments: bool = False, comment_limit: int | None = None,
               profile: str | None = None, config_path: str | None = None) -> SaveResult:
    cfg = cfgmod.load_config(config_path)
    cookies = cookie.pull(cfg.cookie)
    result = fetch(url, cookies=cookies, with_comments=with_comments, comment_limit=comment_limit)
    markdown = result.to_markdown()

    vague = saver.is_vague(save_path, cfg.output_root)
    category: str | None = None
    proposed_new = False
    if vague:
        client = LLMClient(profile=profile or cfg.llm_profile)
        cat = classify.classify(result, cfg.output_root, client)
        category, proposed_new = cat.name, cat.is_new

    target = saver.resolve_target(save_path, cfg.output_root, category, result.title)
    written = saver.write(target, markdown)
    return SaveResult(
        path=str(written),
        title=result.title,
        type=getattr(result.type, "value", str(result.type)),
        url=result.url,
        category=category,
        was_vague=vague,
        proposed_new=proposed_new,
    )
```
Set `Skill/crawl/zhihu-crawl/src/zhihu_crawl/__init__.py` to:
```python
from .api import SaveResult, save_zhihu

__all__ = ["save_zhihu", "SaveResult"]
```

- [ ] **Step 4: Run to verify it passes**

Run (from `Skill/crawl/zhihu-crawl/`): `python -m pytest tests/test_api.py tests/test_smoke.py -q`
Expected: all passed (api + smoke now green).

- [ ] **Step 5: Commit**

```bash
git add Skill/crawl/zhihu-crawl/src/zhihu_crawl/api.py Skill/crawl/zhihu-crawl/src/zhihu_crawl/__init__.py Skill/crawl/zhihu-crawl/tests/test_api.py
git commit -m "feat(SP-3): save_zhihu orchestration (cookie -> engine -> classify -> save)"
```

---

## Task 10: `cli.py` — thin CLI with `--json`

**Files:**
- Create: `Skill/crawl/zhihu-crawl/src/zhihu_crawl/cli.py`
- Test:   `Skill/crawl/zhihu-crawl/tests/test_cli.py`

- [ ] **Step 1: Write the failing tests (api mocked)**

Create `Skill/crawl/zhihu-crawl/tests/test_cli.py`:
```python
import json

import zhihu_crawl.cli as cli
from zhihu_crawl.api import SaveResult


def _result():
    return SaveResult(path="/KB/tech/x.md", title="X", type="answer",
                      url="https://zhihu/x", category="tech", was_vague=True, proposed_new=False)


def test_cli_json_output(monkeypatch, capsys):
    monkeypatch.setattr(cli, "save_zhihu", lambda *a, **k: _result())
    rc = cli.main(["https://zhihu/x", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["path"] == "/KB/tech/x.md"
    assert out["category"] == "tech"


def test_cli_passes_out_and_flags(monkeypatch):
    seen = {}

    def fake(url, save_path=None, **kw):
        seen.update(url=url, save_path=save_path, **kw)
        return _result()

    monkeypatch.setattr(cli, "save_zhihu", fake)
    cli.main(["https://zhihu/x", "--out", "~/KB", "--comments", "--profile", "fallback"])
    assert seen["url"] == "https://zhihu/x"
    assert seen["save_path"] == "~/KB"
    assert seen["with_comments"] is True
    assert seen["profile"] == "fallback"


def test_cli_fetch_error_exit_code(monkeypatch, capsys):
    from zhihu import ZhihuFetchError

    def boom(*a, **k):
        raise ZhihuFetchError("bad")

    monkeypatch.setattr(cli, "save_zhihu", boom)
    rc = cli.main(["https://zhihu/x"])
    assert rc == 2
    assert "fetch failed" in capsys.readouterr().err
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest Skill/crawl/zhihu-crawl/tests/test_cli.py -q`
Expected: `No module named 'zhihu_crawl.cli'`.

- [ ] **Step 3: Implement `cli.py`**

Create `Skill/crawl/zhihu-crawl/src/zhihu_crawl/cli.py`:
```python
"""Thin CLI over save_zhihu. `--json` prints a machine-readable SaveResult for any calling agent."""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys

from zhihu import ZhihuFetchError

from .api import save_zhihu


def _build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="zhihu-crawl",
                                 description="Fetch a Zhihu URL via the frozen engine and save Markdown.")
    ap.add_argument("url", help="Zhihu URL (answer / article / question)")
    ap.add_argument("--out", dest="save_path", default=None,
                    help="save path; a .md file = explicit, a dir/omitted = vague (LLM classify)")
    ap.add_argument("--comments", action="store_true", help="also fetch comments")
    ap.add_argument("--comment-limit", type=int, default=None, help="max comments (default: all)")
    ap.add_argument("--json", dest="as_json", action="store_true", help="print JSON SaveResult")
    ap.add_argument("--profile", default=None, help="LLM profile override (default: config)")
    ap.add_argument("--config", dest="config_path", default=None, help="path to config.yaml")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        result = save_zhihu(
            args.url, args.save_path,
            with_comments=args.comments, comment_limit=args.comment_limit,
            profile=args.profile, config_path=args.config_path,
        )
    except ZhihuFetchError as e:
        print(f"fetch failed: {e}", file=sys.stderr)
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
        print(f"saved: {result.path}\n  title: {result.title}  type: {result.type}{cat}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run to verify it passes**

Run (from `Skill/crawl/zhihu-crawl/`): `python -m pytest tests/test_cli.py -q`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add Skill/crawl/zhihu-crawl/src/zhihu_crawl/cli.py Skill/crawl/zhihu-crawl/tests/test_cli.py
git commit -m "feat(SP-3): thin CLI with --json structured output"
```

---

## Task 11: Packaging artifacts — SKILL.md, sync script, example config, .gitignore

**Files:**
- Create: `Skill/crawl/zhihu-crawl/SKILL.md`
- Create: `Skill/crawl/zhihu-crawl/scripts/sync-skill.sh`
- Create: `Skill/crawl/zhihu-crawl/config.example.yaml`
- Modify: `Skill/crawl/zhihu-crawl/.gitignore` (create)

- [ ] **Step 1: Create the agentskills.io SKILL.md (one file, four runtimes)**

Create `Skill/crawl/zhihu-crawl/SKILL.md`:
```markdown
---
name: zhihu-crawl
description: >
  Use when the user gives a Zhihu URL (answer / article / question) and wants it saved as a Markdown
  note. Fetches via the frozen Zhihu engine and writes Markdown to a chosen path; when the path is vague
  (a folder, the KB root, or omitted) it classifies the content into a subfolder. Do NOT use for
  non-Zhihu URLs or for video transcription.
version: 0.1.0
license: MIT
tags:
  - zhihu
  - crawl
  - markdown
  - knowledge-base
metadata:
  hermes:
    category: knowledge-capture
    required_environment_variables:
      - ANTHROPIC_API_KEY        # or DASHSCOPE_API_KEY (vague-path classification only)
      - COOKIE_MANAGER_PASSWORD  # SP-1 cookie decrypt (name per your config password_env)
  openclaw:
    requires:
      bins: [zhihu-crawl]
    install: "pip install -e Engine/common -e Engine/zhihu -e Skill/crawl/zhihu-crawl"
---

# zhihu-crawl

Save a Zhihu page as Markdown.

## When to use
A user shares a Zhihu URL and wants it in their knowledge base / notes.

## How to run
```bash
zhihu-crawl "<zhihu-url>" --out "<path>" [--comments] [--json]
```
- `--out FILE.md` → write there verbatim.
- `--out DIR` / omit `--out` → vague: classify into a subfolder under the configured `output_root`.
- `--json` → machine-readable result (`path`, `category`, `was_vague`, ...).

## Setup
1. `cp config.example.yaml config.yaml` and set `output_root` + the cookie-manager connection.
2. `cp ../../../config/llm.yaml.example ../../../config/llm.yaml` (repo root) for vague-path classification.
3. Put credentials in `.env` (never in the repo): the cookie password and one LLM `api_key_env`.

## Notes
Reads cookies from SP-1 cookie-manager (pull-only, decrypted in memory). Pure consumer of the frozen
Zhihu engine — see `docs/interface.md`.
```

- [ ] **Step 2: Create the deploy/sync script**

Create `Skill/crawl/zhihu-crawl/scripts/sync-skill.sh`:
```bash
#!/usr/bin/env bash
# Deploy this one SKILL.md to the four agent-CLI skill directories (one source, many targets).
# agentskills.io is the shared standard — no per-runtime format fork.
set -euo pipefail
SRC="$(cd "$(dirname "$0")/.." && pwd)"
NAME="zhihu-crawl"
for dir in "$HOME/.claude/skills" "$HOME/.codex/skills" "$HOME/.openclaw/skills" "$HOME/.hermes/skills"; do
  mkdir -p "$dir/$NAME"
  ln -sf "$SRC/SKILL.md" "$dir/$NAME/SKILL.md"
  echo "linked $dir/$NAME/SKILL.md -> $SRC/SKILL.md"
done
```
Run: `chmod +x Skill/crawl/zhihu-crawl/scripts/sync-skill.sh`

- [ ] **Step 3: Create the example config + gitignore**

Create `Skill/crawl/zhihu-crawl/config.example.yaml`:
```yaml
# Copy to config.yaml (gitignored). Secrets live in .env, never here.
output_root: ~/KB/zhihu          # base dir for vague-path saves; may point into an Obsidian vault subdir

cookie:
  base_url: http://127.0.0.1:48088   # SP-1 cookie-manager; or the frp HTTPS entry
  uuid: <your-cookiecloud-uuid>
  password_env: COOKIE_MANAGER_PASSWORD   # env var name holding the decrypt password

llm:
  profile: default                 # which config/llm.yaml profile to use for vague-path classification
```
Create `Skill/crawl/zhihu-crawl/.gitignore`:
```gitignore
config.yaml
*.egg-info/
__pycache__/
.env
```

- [ ] **Step 4: Verify the SKILL.md frontmatter parses**

Run:
```bash
python -c "import yaml,io,sys; t=open('Skill/crawl/zhihu-crawl/SKILL.md').read(); fm=t.split('---')[1]; yaml.safe_load(fm); print('frontmatter OK')"
```
Expected: `frontmatter OK`.

- [ ] **Step 5: Commit**

```bash
git add Skill/crawl/zhihu-crawl/SKILL.md Skill/crawl/zhihu-crawl/scripts/sync-skill.sh Skill/crawl/zhihu-crawl/config.example.yaml Skill/crawl/zhihu-crawl/.gitignore
git commit -m "feat(SP-3): agentskills.io SKILL.md + sync script + example config"
```

---

## Task 12: Freeze module docs (interface, architecture, README)

**Files:**
- Modify: `Skill/crawl/zhihu-crawl/docs/interface.md`
- Modify: `Skill/crawl/zhihu-crawl/docs/architecture.md`
- Modify: `Skill/crawl/zhihu-crawl/docs/README.md`
- Modify: `Skill/crawl/zhihu-crawl/docs/RepoMem/architecture.md`

- [ ] **Step 1: Write `docs/interface.md` (the frozen public contract)**

Replace `Skill/crawl/zhihu-crawl/docs/interface.md` with the frozen contract: the `save_zhihu` signature + `SaveResult` fields (from spec §6.1/§8) and the CLI usage (`zhihu-crawl <url> [--out] [--comments] [--comment-limit] [--json] [--profile] [--config]`). State it is a pure consumer of `Engine/zhihu/docs/interface.md` and `jarvankb_common.LLMClient`. (Mirror §8 of the design; do not invent new fields.)

- [ ] **Step 2: Write `docs/architecture.md` + `docs/RepoMem/architecture.md`**

`docs/architecture.md` (external summary): the data flow (spec §5) + the six-file module map (spec §4) + the multi-agent packaging surface (spec §3). `docs/RepoMem/architecture.md` (internal): file responsibilities + the cookie-decrypt + classification internals (spec §6), and the cross-SP promotion candidates (temp `decisions.md` D-SP3-3).

- [ ] **Step 3: Update `docs/README.md`**

Flip status from "placeholder" to implemented; point to `interface.md`, `SKILL.md`, and the design spec.

- [ ] **Step 4: Commit**

```bash
git add Skill/crawl/zhihu-crawl/docs/
git commit -m "docs(SP-3): freeze zhihu-crawl interface + architecture + README"
```

---

## Task 13: Full verification + LLM-creds gate (Step 6)

**Files:**
- Possibly modify: `docs/Dashboard/index.md` (Type-F row)
- Create: `docs/sendbox/toZhihuCrawlOrche/from-sp3impler-blocker-llm-creds.md`

- [ ] **Step 1: Reinstall all three packages cleanly**

Run (from `Tools/JarvanKB/`): `pip install -e Engine/zhihu -e Engine/common -e Skill/crawl/zhihu-crawl -q`
Expected: all three install without error.

- [ ] **Step 2: Run the full unit suite**

Run:
```bash
python -m pytest Engine/common/tests Skill/crawl/zhihu-crawl/tests -q
```
Expected: all passed (config 4, llm_client 5, cookie 3, config 2, saver 6, classify 4, api 3, smoke 1, cli 3 = 31).

- [ ] **Step 3: Lint / typecheck (if configured)**

Run (best-effort, match repo tooling if present):
```bash
python -m pyflakes Skill/crawl/zhihu-crawl/src Engine/common/src || true
```
Expected: no errors. Fix any reported.

- [ ] **Step 4: Offline smoke — explicit path (no LLM, no live creds)**

With a `config.yaml` pointing at a reachable cookie-manager (or a fixture), run the engine→save path against one Zhihu URL with an explicit `.md` out path; confirm the file is written with engine frontmatter. If no live cookie service is available, assert the same via a scripted call that monkeypatches `cookie.pull`. Document the exact command + observed output (verification-before-completion requires evidence).

- [ ] **Step 5: Raise the live-LLM gate (do NOT bake creds)**

Add a Dashboard Type-F row to `docs/Dashboard/index.md`:
> `填 config/llm.yaml + .env 的 LLM 凭据 → 解锁 SP-3 vague_path live 分类 smoke`

Create `docs/sendbox/toZhihuCrawlOrche/from-sp3impler-blocker-llm-creds.md` (English A2A) noting: non-LLM path verified offline; only the live vague_path classification awaits user creds; pointer to `config/llm.yaml.example`.

- [ ] **Step 6: Commit**

```bash
git add docs/Dashboard/index.md docs/sendbox/toZhihuCrawlOrche/from-sp3impler-blocker-llm-creds.md
git commit -m "docs(SP-3): verification evidence + LLM-creds live-smoke gate (Type-F + blocker)"
```

---

## Self-Review (run after the plan, before execution)

**Spec coverage** (design § → task):
- §3 multi-agent packaging → Task 11 (SKILL.md + sync) ✓
- §4 module structure → Tasks 4–10 ✓
- §5 data flow → Task 9 (api) ✓
- §6.1 api/SaveResult → Task 9 ✓; §6.2 cli → Task 10 ✓; §6.3 cookie → Task 5 ✓; §6.4 classify → Task 8 ✓; §6.5 config → Task 6 ✓; saver → Task 7 ✓
- §7 LLMClient + Engine/common packaging → Tasks 1–3 ✓
- §8 interface freeze → Task 12 ✓
- §9 error handling → Task 10 (CLI exit codes) + propagation in api ✓
- §10 testing → every task is test-first ✓
- §11 verification + creds gate → Task 13 ✓

**Placeholder scan:** Task 12 describes doc content rather than pasting full prose (docs, not code — acceptable; the contract fields are fully specified in spec §6/§8 which Task 12 references). No code step contains TBD/TODO.

**Type consistency:** `SaveResult` fields (path/title/type/url/category/was_vague/proposed_new) consistent across api (Task 9), cli (Task 10), tests, and spec §6.1. `Category(name, is_new)` consistent across classify (Task 8) and api (Task 9). `CookieSource(base_url, uuid, password)` consistent across cookie (Task 5), config (Task 6), api. `load_config`/`load_llm_config`/`resolve_candidates` names consistent. `is_vague`/`resolve_target`/`slugify`/`write` consistent across saver (Task 7) and api (Task 9).
