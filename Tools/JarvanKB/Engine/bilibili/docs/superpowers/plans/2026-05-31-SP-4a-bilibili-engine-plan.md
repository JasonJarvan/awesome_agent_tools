# Bilibili Engine (SP-4a) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `Engine/bilibili/` — a Python library that turns one Bilibili video reference into structured metadata + a transcript (subtitle-first, ASR-fallback via a self-hosted BiliNote/bcut instance) + BiliNote's AI summary, renderable to Markdown with progressive-disclosure switches.

**Architecture:** Engine-driven subtitle-first cascade. The engine fetches metadata + subtitles itself (`bilibili-api-python`); when a subtitle exists it feeds it to BiliNote (BN) as `prefetched_transcript` (BN runs the LLM summary only); when none exists it lets BN download audio + run bcut ASR. Network is confined to three units (`metadata`, `subtitle`, `bilinote_client`); each splits into a thin fetch wrapper + a pure parser, so all parsing/rendering logic is unit-testable without network. Rendering returns content (never writes files); the caller persists.

**Tech Stack:** Python 3.11+, `bilibili-api-python` (>=17), `httpx` (sync client + `MockTransport` for tests), `PyYAML`, `pytest`. src-layout package named `bilibili`.

**Spec:** `Engine/bilibili/docs/superpowers/specs/2026-05-31-SP-4a-bilibili-engine-design.md` (authoritative).

**Execution context:** Per the handoff, Stage 3 runs in an isolated worktree `.worktrees/sp4a-bilibili-engine/` (create via `superpowers:using-git-worktrees`). Local commits only — no push / no merge to main. Use commit prefix `feat(SP-4a):` for code, `docs(SP-4a):` for docs. Never stage the `gstack` submodule.

**Testing-shape note (read once):** For the three network units, the *pure parser* functions are TDD'd against recorded JSON fixtures (the shapes are verified from BiliNote's own `BilibiliSubtitleFetcher` + the Bilibili `view`/`player/wbi/v2` APIs). The *thin fetch* wrappers (the few lines that actually call `bilibili-api-python` / `httpx`) carry an explicit "record a real fixture and confirm the shape matches" step — that is a concrete action, not a placeholder. Live calls never run in the unit suite.

---

## File Structure

| File | Responsibility |
|---|---|
| `Engine/bilibili/pyproject.toml` | package metadata, deps, src-layout mapping `bilibili` → `src/bilibili` |
| `src/bilibili/__init__.py` | public API exports (frozen contract) |
| `src/bilibili/errors.py` | `BilibiliEngineError` + subclasses |
| `src/bilibili/models.py` | dataclasses: credential, segment, transcript, metadata, result, config, render options/output |
| `src/bilibili/url_parser.py` | `parse_video_ref(ref) → VideoRef`; pure |
| `src/bilibili/render.py` | prose-merge + full render → `RenderedOutput`; pure |
| `src/bilibili/config.py` | load `config/bilibili-engine.yaml` → `EngineConfig` |
| `src/bilibili/metadata.py` | `fetch_metadata` (thin) + `parse_info` (pure) → `BilibiliMetadata` |
| `src/bilibili/subtitle.py` | `fetch_subtitle` (thin) + `pick_track`/`parse_body` (pure) → `Transcript \| None` |
| `src/bilibili/bilinote_client.py` | `BiliNoteClient`: health/push_cookie/generate_note/poll/transcribe |
| `src/bilibili/engine.py` | `BilibiliEngine` cascade + module-level `transcribe()` |
| `src/bilibili/cli.py` | thin CLI |
| `tests/…` | pytest; fixtures under `tests/fixtures/` |
| `deploy/bilinote/{docker-compose.yml,.env.example,README.md}` | BN deployment artifacts (the Stage-3 gate) |
| `config/bilibili-engine.example.yaml` (repo root) | committed config template; real `.yaml` gitignored |
| `docs/interface.md`, `docs/architecture.md` | update from placeholders to the frozen contract |

---

## Task 1: Package scaffold

**Files:**
- Create: `Engine/bilibili/pyproject.toml`
- Create: `Engine/bilibili/src/bilibili/__init__.py`
- Test: `Engine/bilibili/tests/test_import.py`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "jarvankb-bilibili-engine"
version = "0.1.0"
description = "JarvanKB Bilibili transcription engine (SP-4a)"
requires-python = ">=3.11"
dependencies = [
    "bilibili-api-python>=17,<18",
    "httpx>=0.27",
    "PyYAML>=6",
]

[project.optional-dependencies]
dev = ["pytest>=8"]

[project.scripts]
bilibili-engine = "bilibili.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-dir]
"" = "src"
```

- [ ] **Step 2: Write a placeholder package init**

```python
# src/bilibili/__init__.py
"""JarvanKB Bilibili Engine (SP-4a). Public API populated in Task 11."""
__version__ = "0.1.0"
```

- [ ] **Step 3: Write the failing import test**

```python
# tests/test_import.py
def test_package_imports():
    import bilibili
    assert bilibili.__version__ == "0.1.0"
```

- [ ] **Step 4: Install editable + run the test**

Run: `cd Engine/bilibili && pip install -e ".[dev]" && python -m pytest tests/test_import.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add Engine/bilibili/pyproject.toml Engine/bilibili/src Engine/bilibili/tests
git commit -m "feat(SP-4a): package scaffold (src-layout, deps, editable install)"
```

---

## Task 2: Errors

**Files:**
- Create: `Engine/bilibili/src/bilibili/errors.py`
- Test: `Engine/bilibili/tests/test_errors.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_errors.py
import pytest
from bilibili.errors import (
    BilibiliEngineError, InvalidVideoRef, CredentialError,
    BiliNoteUnavailable, TranscriptionFailed, TranscriptionTimeout,
)

@pytest.mark.parametrize("cls", [
    InvalidVideoRef, CredentialError, BiliNoteUnavailable,
    TranscriptionFailed, TranscriptionTimeout,
])
def test_all_subclass_base(cls):
    assert issubclass(cls, BilibiliEngineError)
    with pytest.raises(BilibiliEngineError):
        raise cls("boom")
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tests/test_errors.py -v`
Expected: FAIL — `ModuleNotFoundError: bilibili.errors`.

- [ ] **Step 3: Implement**

```python
# src/bilibili/errors.py
"""Exception hierarchy. All engine failures subclass BilibiliEngineError."""


class BilibiliEngineError(Exception):
    """Base for all engine errors."""


class InvalidVideoRef(BilibiliEngineError):
    """The input could not be resolved to a Bilibili video id."""


class CredentialError(BilibiliEngineError):
    """Credentials missing or rejected where required (metadata/subtitle)."""


class BiliNoteUnavailable(BilibiliEngineError):
    """The BiliNote instance is unreachable (the Stage-3 gate)."""


class TranscriptionFailed(BilibiliEngineError):
    """BiliNote reported task status FAILED."""


class TranscriptionTimeout(BilibiliEngineError):
    """Polling BiliNote exceeded the configured timeout."""
```

- [ ] **Step 4: Run it to verify it passes**

Run: `python -m pytest tests/test_errors.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add Engine/bilibili/src/bilibili/errors.py Engine/bilibili/tests/test_errors.py
git commit -m "feat(SP-4a): error hierarchy"
```

---

## Task 3: Models

**Files:**
- Create: `Engine/bilibili/src/bilibili/models.py`
- Test: `Engine/bilibili/tests/test_models.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_models.py
from bilibili.models import (
    BilibiliCredential, TranscriptSegment, Transcript, BilibiliMetadata,
    BilibiliResult, EngineConfig, RenderOptions, RenderedOutput,
)


def test_credential_defaults_and_cookie_string():
    c = BilibiliCredential(sessdata="SS")
    assert c.bili_jct is None and c.buvid3 is None
    assert c.to_cookie_string() == "SESSDATA=SS"
    c2 = BilibiliCredential(sessdata="SS", bili_jct="JCT", buvid3="BV3")
    assert c2.to_cookie_string() == "SESSDATA=SS; bili_jct=JCT; buvid3=BV3"


def test_render_options_defaults():
    o = RenderOptions()
    assert o.include_transcript is True
    assert o.include_timestamps is False
    assert o.split_transcript is False
    assert o.slug is None


def test_engine_config_defaults():
    cfg = EngineConfig(bn_base_url="http://x", provider_id="p", model_name="m")
    assert cfg.poll_interval_s == 3
    assert cfg.poll_timeout_s == 600
    assert cfg.style == "summary"


def test_transcript_holds_segments():
    t = Transcript(source="subtitle", language="zh", full_text="hi",
                   segments=[TranscriptSegment(0.0, 1.0, "hi")])
    assert t.source == "subtitle"
    assert t.segments[0].text == "hi"
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: bilibili.models`.

- [ ] **Step 3: Implement**

```python
# src/bilibili/models.py
"""Dataclasses for the Bilibili engine. All field names here are the frozen v1 contract."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal, Optional


@dataclass
class BilibiliCredential:
    sessdata: str
    bili_jct: Optional[str] = None
    buvid3: Optional[str] = None

    def to_cookie_string(self) -> str:
        parts = [f"SESSDATA={self.sessdata}"]
        if self.bili_jct:
            parts.append(f"bili_jct={self.bili_jct}")
        if self.buvid3:
            parts.append(f"buvid3={self.buvid3}")
        return "; ".join(parts)


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str


@dataclass
class Transcript:
    source: Literal["subtitle", "asr"]
    language: Optional[str]
    full_text: str
    segments: list[TranscriptSegment]


@dataclass
class BilibiliMetadata:
    bvid: str
    aid: int
    cid: int
    title: str
    up: str               # owner display name
    up_mid: int
    duration: int         # seconds
    pubdate: int          # unix timestamp
    cover: Optional[str]
    url: str


@dataclass
class EngineConfig:
    bn_base_url: str
    provider_id: str
    model_name: str
    poll_interval_s: int = 3
    poll_timeout_s: int = 600
    style: str = "summary"


@dataclass
class RenderOptions:
    include_transcript: bool = True
    include_timestamps: bool = False
    split_transcript: bool = False
    slug: Optional[str] = None


@dataclass
class RenderedOutput:
    main_markdown: str
    transcript_markdown: Optional[str]
    suggested_names: dict


@dataclass
class BilibiliResult:
    metadata: BilibiliMetadata
    transcript: Transcript
    summary_markdown: Optional[str]

    def render(self, options: Optional[RenderOptions] = None) -> RenderedOutput:
        from .render import render_result
        return render_result(self, options or RenderOptions())

    def to_markdown(self, options: Optional[RenderOptions] = None) -> str:
        return self.render(options).main_markdown
```

- [ ] **Step 4: Run it to verify it passes**

Run: `python -m pytest tests/test_models.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add Engine/bilibili/src/bilibili/models.py Engine/bilibili/tests/test_models.py
git commit -m "feat(SP-4a): data models + credential cookie-string helper"
```

---

## Task 4: URL parser

**Files:**
- Create: `Engine/bilibili/src/bilibili/url_parser.py`
- Test: `Engine/bilibili/tests/test_url_parser.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_url_parser.py
import pytest
from bilibili.url_parser import parse_video_ref, VideoRef
from bilibili.errors import InvalidVideoRef


def test_bare_bvid():
    assert parse_video_ref("BV1GJ411x7h7") == VideoRef(bvid="BV1GJ411x7h7", aid=None, part=None)


def test_full_url_with_part():
    assert parse_video_ref("https://www.bilibili.com/video/BV1GJ411x7h7?p=2&t=10") == \
        VideoRef(bvid="BV1GJ411x7h7", aid=None, part=2)


def test_url_without_part_defaults_none():
    assert parse_video_ref("https://www.bilibili.com/video/BV1GJ411x7h7/").part is None


def test_av_id():
    assert parse_video_ref("av170001") == VideoRef(bvid=None, aid=170001, part=None)


@pytest.mark.parametrize("bad", ["", "not a video", "https://b23.tv/abc", "https://youtube.com/x"])
def test_invalid(bad):
    with pytest.raises(InvalidVideoRef):
        parse_video_ref(bad)
```

> `b23.tv` short links need an HTTP redirect to resolve → out of v1 (raises `InvalidVideoRef`); noted as v2+ in the spec.

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tests/test_url_parser.py -v`
Expected: FAIL — `ModuleNotFoundError: bilibili.url_parser`.

- [ ] **Step 3: Implement**

```python
# src/bilibili/url_parser.py
"""Pure resolution of a video reference (BV id / bilibili.com URL / av id) to ids."""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse, parse_qs

from .errors import InvalidVideoRef

_BVID_RE = re.compile(r"(BV[0-9A-Za-z]{10})")
_AV_RE = re.compile(r"^av(\d+)$", re.IGNORECASE)


@dataclass(frozen=True)
class VideoRef:
    bvid: Optional[str]
    aid: Optional[int]
    part: Optional[int]


def parse_video_ref(ref: str) -> VideoRef:
    if not ref or not ref.strip():
        raise InvalidVideoRef("empty reference")
    ref = ref.strip()

    # av id
    m = _AV_RE.match(ref)
    if m:
        return VideoRef(bvid=None, aid=int(m.group(1)), part=None)

    # full URL: must be a bilibili.com host carrying a BV id
    if ref.startswith("http://") or ref.startswith("https://"):
        parsed = urlparse(ref)
        if "bilibili.com" not in parsed.netloc:
            raise InvalidVideoRef(f"unsupported host: {parsed.netloc}")
        bm = _BVID_RE.search(parsed.path)
        if not bm:
            raise InvalidVideoRef(f"no BV id in URL path: {parsed.path}")
        part = None
        p = parse_qs(parsed.query).get("p")
        if p and p[0].isdigit():
            part = int(p[0])
        return VideoRef(bvid=bm.group(1), aid=None, part=part)

    # bare BV id (allow it to appear with surrounding noise, but require exact-ish match)
    bm = _BVID_RE.fullmatch(ref) or _BVID_RE.fullmatch(ref.replace("/", ""))
    if bm:
        return VideoRef(bvid=bm.group(1), aid=None, part=None)

    raise InvalidVideoRef(f"unrecognized reference: {ref!r}")
```

- [ ] **Step 4: Run it to verify it passes**

Run: `python -m pytest tests/test_url_parser.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add Engine/bilibili/src/bilibili/url_parser.py Engine/bilibili/tests/test_url_parser.py
git commit -m "feat(SP-4a): pure url_parser (BV id / URL / av id)"
```

---

## Task 5: Render — prose merge

**Files:**
- Create: `Engine/bilibili/src/bilibili/render.py`
- Test: `Engine/bilibili/tests/test_render_prose.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_render_prose.py
from bilibili.models import TranscriptSegment
from bilibili.render import merge_segments_to_prose


def test_zh_segments_join_without_spaces():
    segs = [TranscriptSegment(0, 1, "你好"), TranscriptSegment(1, 2, "世界")]
    assert merge_segments_to_prose(segs) == "你好世界"


def test_en_segments_join_with_space():
    segs = [TranscriptSegment(0, 1, "hello"), TranscriptSegment(1, 2, "world")]
    assert merge_segments_to_prose(segs) == "hello world"


def test_paragraph_break_on_time_gap():
    segs = [
        TranscriptSegment(0, 1, "你好"),
        TranscriptSegment(1, 2, "世界"),
        TranscriptSegment(5, 6, "再见"),   # gap 2 -> 5 = 3s > 2s threshold
    ]
    assert merge_segments_to_prose(segs, gap_threshold_s=2.0) == "你好世界\n\n再见"


def test_paragraph_break_on_char_budget():
    segs = [TranscriptSegment(i, i + 0.1, "字" * 50) for i in range(4)]  # 200 chars, budget 120
    out = merge_segments_to_prose(segs, char_budget=120)
    assert "\n\n" in out


def test_empty_segments():
    assert merge_segments_to_prose([]) == ""
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tests/test_render_prose.py -v`
Expected: FAIL — `ImportError: cannot import name 'merge_segments_to_prose'`.

- [ ] **Step 3: Implement (prose-merge portion of render.py)**

```python
# src/bilibili/render.py
"""Pure rendering: prose-merge + full document assembly. No file I/O, no LLM."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import TranscriptSegment


def _needs_space(left: str, right: str) -> bool:
    """Insert a space only between two ASCII alphanumeric boundaries (latin words);
    Chinese/CJK fragments concatenate without spaces."""
    if not left or not right:
        return False
    a, b = left[-1], right[0]
    return a.isascii() and a.isalnum() and b.isascii() and b.isalnum()


def merge_segments_to_prose(
    segments: list["TranscriptSegment"],
    gap_threshold_s: float = 2.0,
    char_budget: int = 200,
) -> str:
    """Merge short segment fragments into readable paragraphs (deterministic; no LLM).

    A new paragraph starts when the inter-segment time gap exceeds gap_threshold_s
    OR the current paragraph reaches char_budget characters.
    """
    if not segments:
        return ""
    paragraphs: list[str] = []
    current = ""
    last_end = None
    for seg in segments:
        text = (seg.text or "").strip()
        if not text:
            continue
        gap_break = last_end is not None and (seg.start - last_end) > gap_threshold_s
        budget_break = len(current) >= char_budget
        if current and (gap_break or budget_break):
            paragraphs.append(current)
            current = ""
        if current:
            current += (" " if _needs_space(current, text) else "") + text
        else:
            current = text
        last_end = seg.end
    if current:
        paragraphs.append(current)
    return "\n\n".join(paragraphs)
```

- [ ] **Step 4: Run it to verify it passes**

Run: `python -m pytest tests/test_render_prose.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add Engine/bilibili/src/bilibili/render.py Engine/bilibili/tests/test_render_prose.py
git commit -m "feat(SP-4a): deterministic prose-merge (no LLM)"
```

---

## Task 6: Render — full document assembly

**Files:**
- Modify: `Engine/bilibili/src/bilibili/render.py` (add `render_result`, helpers)
- Test: `Engine/bilibili/tests/test_render_document.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_render_document.py
from bilibili.models import (
    BilibiliMetadata, Transcript, TranscriptSegment, BilibiliResult, RenderOptions,
)
from bilibili.render import render_result, format_timestamp


def _result(source="subtitle", summary="## Summary\n\nhi"):
    meta = BilibiliMetadata(
        bvid="BV1x", aid=1, cid=2, title="T", up="U", up_mid=9,
        duration=125, pubdate=1610000000, cover="http://c", url="https://www.bilibili.com/video/BV1x",
    )
    tr = Transcript(source=source, language="zh", full_text="你好世界",
                    segments=[TranscriptSegment(0, 1, "你好"), TranscriptSegment(75, 76, "世界")])
    return BilibiliResult(metadata=meta, transcript=tr, summary_markdown=summary)


def test_format_timestamp():
    assert format_timestamp(75) == "01:15"
    assert format_timestamp(3725) == "1:02:05"


def test_default_inline_has_frontmatter_summary_and_prose():
    out = render_result(_result(), RenderOptions())
    assert out.transcript_markdown is None
    md = out.main_markdown
    assert md.startswith("---\n")
    assert "bvid: BV1x" in md
    assert "transcript_source: subtitle" in md
    assert "## Summary" in md
    assert "你好世界" in md           # prose-merged (gap 1->75 forces a paragraph break)
    assert "[00:00]" not in md         # timestamps off by default


def test_timestamps_mode_lists_segments():
    out = render_result(_result(), RenderOptions(include_timestamps=True))
    assert "[00:00] 你好" in out.main_markdown
    assert "[01:15] 世界" in out.main_markdown


def test_include_transcript_false_omits_body():
    out = render_result(_result(), RenderOptions(include_transcript=False))
    assert "你好世界" not in out.main_markdown
    assert "## Summary" in out.main_markdown
    assert out.transcript_markdown is None


def test_split_emits_two_documents_and_link():
    out = render_result(_result(), RenderOptions(split_transcript=True))
    assert out.transcript_markdown is not None
    assert "你好世界" in out.transcript_markdown
    assert "你好世界" not in out.main_markdown
    assert "[全文转录](./BV1x.transcript.md)" in out.main_markdown
    assert out.suggested_names == {"main": "BV1x.md", "transcript": "BV1x.transcript.md"}


def test_slug_override_drives_names_and_link():
    out = render_result(_result(), RenderOptions(split_transcript=True, slug="custom"))
    assert "[全文转录](./custom.transcript.md)" in out.main_markdown
    assert out.suggested_names["transcript"] == "custom.transcript.md"
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tests/test_render_document.py -v`
Expected: FAIL — `ImportError: cannot import name 'render_result'`.

- [ ] **Step 3: Implement (append to render.py)**

```python
# append to src/bilibili/render.py
import datetime as _dt
import yaml as _yaml

from .models import BilibiliResult, RenderOptions, RenderedOutput


def format_timestamp(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m:02d}:{sec:02d}"


def _frontmatter(result: BilibiliResult) -> str:
    meta = result.metadata
    pub = _dt.datetime.utcfromtimestamp(meta.pubdate).strftime("%Y-%m-%d")
    data = {
        "bvid": meta.bvid,
        "title": meta.title,
        "up": meta.up,
        "url": meta.url,
        "duration": meta.duration,
        "pubdate": pub,
        "transcript_source": result.transcript.source,
    }
    body = _yaml.safe_dump(data, allow_unicode=True, sort_keys=False).strip()
    return f"---\n{body}\n---"


def _transcript_block(result: BilibiliResult, options: RenderOptions) -> str:
    segs = result.transcript.segments
    if options.include_timestamps:
        lines = [f"[{format_timestamp(s.start)}] {s.text.strip()}" for s in segs if s.text.strip()]
        return "\n".join(lines)
    return merge_segments_to_prose(segs)


def render_result(result: BilibiliResult, options: RenderOptions) -> RenderedOutput:
    slug = options.slug or result.metadata.bvid
    names = {"main": f"{slug}.md", "transcript": f"{slug}.transcript.md"}

    parts = [_frontmatter(result), f"# {result.metadata.title}"]
    if result.summary_markdown:
        parts.append(result.summary_markdown.strip())

    transcript_md = None
    if options.include_transcript:
        block = _transcript_block(result, options)
        if options.split_transcript:
            transcript_md = f"{_frontmatter(result)}\n\n# {result.metadata.title} — 全文转录\n\n{block}"
            parts.append(f"## 全文转录\n\n[全文转录](./{names['transcript']})")
        else:
            parts.append(f"## 全文转录\n\n{block}")

    return RenderedOutput(
        main_markdown="\n\n".join(parts) + "\n",
        transcript_markdown=(transcript_md + "\n") if transcript_md else None,
        suggested_names=names,
    )
```

- [ ] **Step 4: Run it to verify it passes**

Run: `python -m pytest tests/test_render_document.py tests/test_render_prose.py -v`
Expected: PASS (all).

- [ ] **Step 5: Commit**

```bash
git add Engine/bilibili/src/bilibili/render.py Engine/bilibili/tests/test_render_document.py
git commit -m "feat(SP-4a): full render — frontmatter, timestamps, split/index"
```

---

## Task 7: Config loader

**Files:**
- Create: `Engine/bilibili/src/bilibili/config.py`
- Create: `config/bilibili-engine.example.yaml` (repo root)
- Modify: `.gitignore` (add `config/bilibili-engine.yaml`)
- Test: `Engine/bilibili/tests/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py
import textwrap
import pytest
from bilibili.config import load_config
from bilibili.models import EngineConfig


def test_load_minimal(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text(textwrap.dedent("""
        bilinote:
          base_url: http://127.0.0.1:3015
          provider_id: pid
          model_name: gpt-4o-mini
    """), encoding="utf-8")
    cfg = load_config(str(p))
    assert isinstance(cfg, EngineConfig)
    assert cfg.bn_base_url == "http://127.0.0.1:3015"
    assert cfg.provider_id == "pid"
    assert cfg.poll_timeout_s == 600          # default
    assert cfg.style == "summary"             # default


def test_load_overrides(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text(textwrap.dedent("""
        bilinote:
          base_url: http://x
          provider_id: pid
          model_name: m
          poll_interval_s: 5
          poll_timeout_s: 900
          style: detailed
    """), encoding="utf-8")
    cfg = load_config(str(p))
    assert cfg.poll_interval_s == 5
    assert cfg.poll_timeout_s == 900
    assert cfg.style == "detailed"


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(str(tmp_path / "nope.yaml"))
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: bilibili.config`.

- [ ] **Step 3: Implement**

```python
# src/bilibili/config.py
"""Load config/bilibili-engine.yaml into an EngineConfig."""
from __future__ import annotations
import os
import yaml

from .models import EngineConfig

DEFAULT_CONFIG_PATH = os.path.join("config", "bilibili-engine.yaml")


def load_config(path: str = DEFAULT_CONFIG_PATH) -> EngineConfig:
    if not os.path.exists(path):
        raise FileNotFoundError(f"engine config not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    bn = raw.get("bilinote", {})
    return EngineConfig(
        bn_base_url=bn["base_url"],
        provider_id=bn["provider_id"],
        model_name=bn["model_name"],
        poll_interval_s=bn.get("poll_interval_s", 3),
        poll_timeout_s=bn.get("poll_timeout_s", 600),
        style=bn.get("style", "summary"),
    )
```

- [ ] **Step 4: Create the committed example config**

```yaml
# config/bilibili-engine.example.yaml
# Copy to config/bilibili-engine.yaml (gitignored) and fill provider_id.
bilinote:
  base_url: http://127.0.0.1:3015     # BiliNote nginx APP_PORT
  provider_id: ""                     # paste from BiliNote web UI after adding an LLM provider
  model_name: "gpt-4o-mini"
  poll_interval_s: 3
  poll_timeout_s: 600                  # bcut ASR can run for minutes
  style: "summary"
# credentials are NOT stored here — passed as input / sourced from SP-1 cookie-manager
```

- [ ] **Step 5: Add gitignore entry**

Append to repo-root `.gitignore`: `config/bilibili-engine.yaml`

- [ ] **Step 6: Run the test + commit**

Run: `python -m pytest tests/test_config.py -v`  → Expected: PASS.

```bash
git add Engine/bilibili/src/bilibili/config.py Engine/bilibili/tests/test_config.py config/bilibili-engine.example.yaml .gitignore
git commit -m "feat(SP-4a): config loader + example yaml"
```

---

## Task 8: Metadata unit

**Files:**
- Create: `Engine/bilibili/src/bilibili/metadata.py`
- Create: `Engine/bilibili/tests/fixtures/view_info.json` (recorded; see Step 5)
- Test: `Engine/bilibili/tests/test_metadata.py`

- [ ] **Step 1: Write the failing test (pure parser + thin wrapper boundary)**

```python
# tests/test_metadata.py
import json
import pathlib
from unittest.mock import patch
from bilibili.metadata import parse_info, fetch_metadata
from bilibili.models import BilibiliCredential, BilibiliMetadata
from bilibili.url_parser import VideoRef

FIX = pathlib.Path(__file__).parent / "fixtures" / "view_info.json"


def test_parse_info_maps_fields():
    raw = json.loads(FIX.read_text(encoding="utf-8"))
    meta = parse_info(raw)
    assert isinstance(meta, BilibiliMetadata)
    assert meta.bvid == raw["bvid"]
    assert meta.cid == raw["cid"]
    assert meta.aid == raw["aid"]
    assert meta.title == raw["title"]
    assert meta.up == raw["owner"]["name"]
    assert meta.up_mid == raw["owner"]["mid"]
    assert meta.duration == raw["duration"]
    assert meta.pubdate == raw["pubdate"]
    assert meta.cover == raw["pic"]
    assert meta.url == f"https://www.bilibili.com/video/{raw['bvid']}"


def test_fetch_metadata_uses_parser():
    raw = json.loads(FIX.read_text(encoding="utf-8"))
    ref = VideoRef(bvid=raw["bvid"], aid=None, part=None)
    with patch("bilibili.metadata._get_info_raw", return_value=raw) as m:
        meta = fetch_metadata(ref, BilibiliCredential(sessdata="SS"))
    m.assert_called_once()
    assert meta.bvid == raw["bvid"]
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tests/test_metadata.py -v`
Expected: FAIL — `ModuleNotFoundError: bilibili.metadata` (and missing fixture).

- [ ] **Step 3: Create the fixture from the documented `view` API shape**

```json
// tests/fixtures/view_info.json
{
  "bvid": "BV1GJ411x7h7",
  "aid": 170001,
  "cid": 279786,
  "title": "示例标题",
  "desc": "示例简介",
  "pubdate": 1610000000,
  "duration": 125,
  "pic": "https://i0.hdslb.com/bfs/archive/example.jpg",
  "owner": {"mid": 99999, "name": "示例UP", "face": "https://i0.hdslb.com/face.jpg"},
  "pages": [{"cid": 279786, "page": 1, "part": "P1", "duration": 125}]
}
```

- [ ] **Step 4: Implement**

```python
# src/bilibili/metadata.py
"""Fetch + parse video metadata via bilibili-api-python.

Split into a pure parser (parse_info) and a thin async-wrapping fetch (_get_info_raw),
so the field mapping is unit-tested without network.
"""
from __future__ import annotations
import asyncio
from typing import Optional

from .errors import CredentialError, InvalidVideoRef
from .models import BilibiliCredential, BilibiliMetadata
from .url_parser import VideoRef


def parse_info(raw: dict) -> BilibiliMetadata:
    """Map the Bilibili `view` API `data` dict to BilibiliMetadata (pure)."""
    owner = raw.get("owner") or {}
    bvid = raw["bvid"]
    return BilibiliMetadata(
        bvid=bvid,
        aid=int(raw.get("aid", 0)),
        cid=int(raw["cid"]),
        title=raw.get("title", ""),
        up=owner.get("name", ""),
        up_mid=int(owner.get("mid", 0)),
        duration=int(raw.get("duration", 0)),
        pubdate=int(raw.get("pubdate", 0)),
        cover=raw.get("pic"),
        url=f"https://www.bilibili.com/video/{bvid}",
    )


def _build_credential(cred: Optional[BilibiliCredential]):
    from bilibili_api import Credential
    if cred is None:
        return None
    return Credential(sessdata=cred.sessdata, bili_jct=cred.bili_jct, buvid3=cred.buvid3)


def _get_info_raw(ref: VideoRef, cred: Optional[BilibiliCredential]) -> dict:
    """Thin wrapper around bilibili-api-python's async get_info. Returns the `data` dict.

    NOTE FOR IMPLEMENTER: run this once against a real public BV id and confirm the returned
    dict contains bvid/aid/cid/title/owner/duration/pubdate/pic; if a key differs in the
    installed library version, update parse_info + the fixture together.
    """
    from bilibili_api import video

    async def _run():
        credential = _build_credential(cred)
        if ref.bvid:
            v = video.Video(bvid=ref.bvid, credential=credential)
        else:
            v = video.Video(aid=ref.aid, credential=credential)
        return await v.get_info()

    return asyncio.run(_run())


def fetch_metadata(ref: VideoRef, cred: Optional[BilibiliCredential]) -> BilibiliMetadata:
    if not ref.bvid and not ref.aid:
        raise InvalidVideoRef("VideoRef has neither bvid nor aid")
    try:
        raw = _get_info_raw(ref, cred)
    except Exception as e:  # bilibili-api raises various; surface credential issues clearly
        msg = str(e).lower()
        if "credential" in msg or "登录" in str(e) or "-101" in msg:
            raise CredentialError(f"metadata fetch rejected (check SESSDATA): {e}") from e
        raise
    return parse_info(raw)
```

- [ ] **Step 5: Run the test + record the real fixture**

Run: `python -m pytest tests/test_metadata.py -v` → Expected: PASS (against the committed fixture).
Then, once during implementation, run a real call to confirm the live shape and overwrite the fixture if any field differs:
```bash
python -c "import asyncio,json; from bilibili_api import video; print(json.dumps(asyncio.run(video.Video(bvid='BV1GJ411x7h7').get_info()), ensure_ascii=False)[:400])"
```
Adjust `parse_info` + fixture together if needed; re-run the test.

- [ ] **Step 6: Commit**

```bash
git add Engine/bilibili/src/bilibili/metadata.py Engine/bilibili/tests/test_metadata.py Engine/bilibili/tests/fixtures/view_info.json
git commit -m "feat(SP-4a): metadata unit (pure parse_info + thin fetch)"
```

---

## Task 9: Subtitle unit

**Files:**
- Create: `Engine/bilibili/src/bilibili/subtitle.py`
- Create: `Engine/bilibili/tests/fixtures/subtitle_tracks.json`, `Engine/bilibili/tests/fixtures/subtitle_body.json`
- Test: `Engine/bilibili/tests/test_subtitle.py`

> Reference shapes (verified from BiliNote's `backend/app/downloaders/bilibili_subtitle.py`):
> `player/wbi/v2` → `data.subtitle.subtitles[]`, each `{lan, lan_doc, ai_type, subtitle_url}`;
> `subtitle_url` → `{body:[{from,to,content}]}`; protocol-relative `//` URLs need `https:` prefix;
> track priority = manual zh (`ai_type` falsy) > AI zh > any non-empty.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_subtitle.py
import json
import pathlib
from unittest.mock import patch
from bilibili.subtitle import pick_track, parse_body, normalize_url, fetch_subtitle
from bilibili.models import Transcript, BilibiliCredential

FX = pathlib.Path(__file__).parent / "fixtures"


def test_pick_prefers_manual_zh():
    tracks = [
        {"lan": "en", "ai_type": 0, "subtitle_url": "//a"},
        {"lan": "ai-zh", "ai_type": 1, "subtitle_url": "//b"},
        {"lan": "zh-CN", "ai_type": 0, "subtitle_url": "//c"},
    ]
    assert pick_track(tracks)["subtitle_url"] == "//c"


def test_pick_falls_back_to_ai_zh_then_any():
    assert pick_track([{"lan": "ai-zh", "ai_type": 1, "subtitle_url": "//b"}])["lan"] == "ai-zh"
    assert pick_track([{"lan": "fr", "ai_type": 0, "subtitle_url": "//x"}])["lan"] == "fr"
    assert pick_track([]) is None


def test_normalize_url():
    assert normalize_url("//x/y.json") == "https://x/y.json"
    assert normalize_url("https://x/y.json") == "https://x/y.json"


def test_parse_body_filters_empty_and_maps_times():
    body = [{"from": 0.0, "to": 1.5, "content": "你好"}, {"from": 1.5, "to": 2.0, "content": "  "}]
    segs = parse_body(body)
    assert len(segs) == 1
    assert segs[0].start == 0.0 and segs[0].end == 1.5 and segs[0].text == "你好"


def test_fetch_subtitle_returns_transcript():
    tracks = json.loads((FX / "subtitle_tracks.json").read_text(encoding="utf-8"))
    body = json.loads((FX / "subtitle_body.json").read_text(encoding="utf-8"))
    with patch("bilibili.subtitle._get_tracks_raw", return_value=tracks), \
         patch("bilibili.subtitle._get_body_raw", return_value=body):
        tr = fetch_subtitle(bvid="BV1x", cid=2, cred=BilibiliCredential(sessdata="SS"))
    assert isinstance(tr, Transcript)
    assert tr.source == "subtitle"
    assert tr.full_text and len(tr.segments) >= 1


def test_fetch_subtitle_none_when_no_tracks():
    with patch("bilibili.subtitle._get_tracks_raw", return_value=[]):
        assert fetch_subtitle(bvid="BV1x", cid=2, cred=BilibiliCredential(sessdata="SS")) is None
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tests/test_subtitle.py -v`
Expected: FAIL — `ModuleNotFoundError: bilibili.subtitle`.

- [ ] **Step 3: Create fixtures**

```json
// tests/fixtures/subtitle_tracks.json
[
  {"lan": "ai-zh", "lan_doc": "中文（自动生成）", "ai_type": 1, "subtitle_url": "//aisubtitle.example/sub.json"}
]
```

```json
// tests/fixtures/subtitle_body.json
{"body": [
  {"from": 0.0, "to": 1.2, "content": "你好"},
  {"from": 1.2, "to": 2.4, "content": "世界"}
]}
```

- [ ] **Step 4: Implement**

```python
# src/bilibili/subtitle.py
"""Engine-side subtitle fetch (subtitle-first cascade step 1).

Pure helpers (pick_track / parse_body / normalize_url) are unit-tested; the two thin
wrappers (_get_tracks_raw via bilibili-api-python, _get_body_raw via httpx) carry the
fixture-recording note. Returns a Transcript(source="subtitle") or None when no usable track.
"""
from __future__ import annotations
import asyncio
from typing import Optional

import httpx

from .models import BilibiliCredential, Transcript, TranscriptSegment


def normalize_url(url: str) -> str:
    return "https:" + url if url.startswith("//") else url


def _is_zh(track: dict) -> bool:
    lan = (track.get("lan") or "").lower()
    return lan.startswith("zh") or lan == "ai-zh"


def pick_track(tracks: list[dict]) -> Optional[dict]:
    """manual zh (ai_type falsy) > AI zh > any non-empty."""
    if not tracks:
        return None
    for t in tracks:
        if _is_zh(t) and not t.get("ai_type"):
            return t
    for t in tracks:
        if _is_zh(t):
            return t
    return tracks[0]


def parse_body(body: list[dict]) -> list[TranscriptSegment]:
    segs: list[TranscriptSegment] = []
    for item in body or []:
        text = (item.get("content") or "").strip()
        if not text:
            continue
        segs.append(TranscriptSegment(
            start=float(item.get("from", 0)),
            end=float(item.get("to", 0)),
            text=text,
        ))
    return segs


def _build_credential(cred: Optional[BilibiliCredential]):
    from bilibili_api import Credential
    if cred is None:
        return None
    return Credential(sessdata=cred.sessdata, bili_jct=cred.bili_jct, buvid3=cred.buvid3)


def _get_tracks_raw(bvid: str, cid: int, cred: Optional[BilibiliCredential]) -> list[dict]:
    """Thin wrapper: bilibili-api-python get_subtitle(cid) → list of subtitle tracks.

    NOTE FOR IMPLEMENTER: confirm against a real video with subtitles that the returned
    structure yields the track list (the library handles wbi signing). If the library nests
    the list differently, normalize to a list of {lan, ai_type, subtitle_url} dicts here and
    update the fixture together.
    """
    from bilibili_api import video

    async def _run():
        v = video.Video(bvid=bvid, credential=_build_credential(cred))
        data = await v.get_subtitle(cid)
        # data is expected to expose the tracks under 'subtitles'
        return (data or {}).get("subtitles", []) or []

    return asyncio.run(_run())


def _get_body_raw(subtitle_url: str, cred: Optional[BilibiliCredential]) -> list[dict]:
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.bilibili.com"}
    if cred and cred.sessdata:
        headers["Cookie"] = cred.to_cookie_string()
    resp = httpx.get(normalize_url(subtitle_url), headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json().get("body") or []


def fetch_subtitle(bvid: str, cid: int, cred: Optional[BilibiliCredential]) -> Optional[Transcript]:
    tracks = _get_tracks_raw(bvid, cid, cred)
    track = pick_track(tracks)
    if not track or not track.get("subtitle_url"):
        return None
    body = _get_body_raw(track["subtitle_url"], cred)
    segs = parse_body(body)
    if not segs:
        return None
    lan = track.get("lan") or "zh"
    return Transcript(
        source="subtitle",
        language=lan,
        full_text=merge_full_text(segs),
        segments=segs,
    )


def merge_full_text(segs: list[TranscriptSegment]) -> str:
    return " ".join(s.text for s in segs)
```

- [ ] **Step 5: Run the test + commit**

Run: `python -m pytest tests/test_subtitle.py -v` → Expected: PASS.

```bash
git add Engine/bilibili/src/bilibili/subtitle.py Engine/bilibili/tests/test_subtitle.py Engine/bilibili/tests/fixtures/subtitle_tracks.json Engine/bilibili/tests/fixtures/subtitle_body.json
git commit -m "feat(SP-4a): subtitle unit (pick/parse pure + thin fetch)"
```

---

## Task 10: BiliNote client

**Files:**
- Create: `Engine/bilibili/src/bilibili/bilinote_client.py`
- Test: `Engine/bilibili/tests/test_bilinote_client.py`

> Verified BN contract: routers under `/api`; responses wrapped `{code,msg,data}` (`code==0` ok).
> `POST /api/generate_note` → `data.task_id`; `GET /api/task_status/{id}` → `data.{status,result,message}`;
> `POST /api/update_downloader_cookie`; `GET /api/sys_check`. On SUCCESS `result` = `{markdown, transcript, audio_meta}`.

- [ ] **Step 1: Write the failing test (httpx MockTransport)**

```python
# tests/test_bilinote_client.py
import json
import httpx
import pytest
from bilibili.bilinote_client import BiliNoteClient
from bilibili.errors import BiliNoteUnavailable, TranscriptionFailed, TranscriptionTimeout


def _client(handler):
    transport = httpx.MockTransport(handler)
    http = httpx.Client(transport=transport, base_url="http://bn")
    return BiliNoteClient(base_url="http://bn", provider_id="pid", model_name="m",
                          poll_interval_s=0, poll_timeout_s=5, http=http)


def test_health_ok():
    def h(req):
        assert req.url.path == "/api/sys_check"
        return httpx.Response(200, json={"code": 0, "msg": "ok", "data": None})
    _client(h).health_check()  # no raise


def test_health_unavailable_on_connect_error():
    def h(req):
        raise httpx.ConnectError("refused", request=req)
    with pytest.raises(BiliNoteUnavailable):
        _client(h).health_check()


def test_generate_note_returns_task_id():
    def h(req):
        assert req.url.path == "/api/generate_note"
        body = json.loads(req.content)
        assert body["platform"] == "bilibili"
        assert body["provider_id"] == "pid"
        assert body["quality"] == "fast"
        return httpx.Response(200, json={"code": 0, "data": {"task_id": "T1"}})
    assert _client(h).generate_note("https://www.bilibili.com/video/BV1x") == "T1"


def test_generate_note_includes_prefetched_when_given():
    seen = {}
    def h(req):
        seen["body"] = json.loads(req.content)
        return httpx.Response(200, json={"code": 0, "data": {"task_id": "T2"}})
    pf = {"language": "zh", "full_text": "hi", "segments": [{"start": 0, "end": 1, "text": "hi"}]}
    _client(h).generate_note("u", prefetched_transcript=pf)
    assert seen["body"]["prefetched_transcript"] == pf


def test_poll_success_returns_result():
    note = {"markdown": "## S", "transcript": {"language": "zh", "full_text": "hi",
            "segments": [{"start": 0, "end": 1, "text": "hi"}]}, "audio_meta": {}}
    def h(req):
        return httpx.Response(200, json={"code": 0, "data": {"status": "SUCCESS", "result": note}})
    assert _client(h).poll("T1")["markdown"] == "## S"


def test_poll_failed_raises():
    def h(req):
        return httpx.Response(200, json={"code": 0, "data": {"status": "FAILED", "message": "boom"}})
    with pytest.raises(TranscriptionFailed):
        _client(h).poll("T1")


def test_poll_timeout_raises():
    def h(req):
        return httpx.Response(200, json={"code": 0, "data": {"status": "TRANSCRIBING"}})
    with pytest.raises(TranscriptionTimeout):
        _client(h).poll("T1")


def test_transcribe_orchestrates_and_returns_transcript_and_summary():
    note = {"markdown": "## S", "transcript": {"language": "zh", "full_text": "hi",
            "segments": [{"start": 0, "end": 1, "text": "hi"}]}, "audio_meta": {}}
    def h(req):
        if req.url.path == "/api/sys_check":
            return httpx.Response(200, json={"code": 0, "data": None})
        if req.url.path == "/api/generate_note":
            return httpx.Response(200, json={"code": 0, "data": {"task_id": "T1"}})
        return httpx.Response(200, json={"code": 0, "data": {"status": "SUCCESS", "result": note}})
    transcript, summary = _client(h).transcribe("u")
    assert summary == "## S"
    assert transcript["full_text"] == "hi"
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tests/test_bilinote_client.py -v`
Expected: FAIL — `ModuleNotFoundError: bilibili.bilinote_client`.

- [ ] **Step 3: Implement**

```python
# src/bilibili/bilinote_client.py
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
```

> Note: with `poll_interval_s=0` (tests) and a non-terminal status, the loop hits the
> `waited >= deadline` branch on the second iteration because `waited += max(0,1)` advances by 1
> up to `poll_timeout_s` — keep `poll_timeout_s` small (e.g. 5) in tests so the timeout test is fast.

- [ ] **Step 4: Run it to verify it passes**

Run: `python -m pytest tests/test_bilinote_client.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add Engine/bilibili/src/bilibili/bilinote_client.py Engine/bilibili/tests/test_bilinote_client.py
git commit -m "feat(SP-4a): BiliNote HTTP client (health/cookie/generate/poll/transcribe)"
```

---

## Task 11: Engine cascade

**Files:**
- Create: `Engine/bilibili/src/bilibili/engine.py`
- Test: `Engine/bilibili/tests/test_engine.py`

- [ ] **Step 1: Write the failing test (all deps mocked)**

```python
# tests/test_engine.py
from unittest.mock import patch, MagicMock
from bilibili.engine import BilibiliEngine
from bilibili.models import (
    EngineConfig, BilibiliCredential, BilibiliMetadata, Transcript, TranscriptSegment,
)

CFG = EngineConfig(bn_base_url="http://bn", provider_id="pid", model_name="m")
META = BilibiliMetadata(bvid="BV1x", aid=1, cid=2, title="T", up="U", up_mid=9,
                        duration=10, pubdate=1610000000, cover=None,
                        url="https://www.bilibili.com/video/BV1x")
SUBT = Transcript(source="subtitle", language="zh", full_text="hi",
                  segments=[TranscriptSegment(0, 1, "hi")])


def _engine(bn):
    e = BilibiliEngine(CFG)
    e._bn = bn
    return e


def test_subtitle_path_feeds_prefetched_and_keeps_source_subtitle():
    bn = MagicMock()
    bn.transcribe.return_value = (None, "## Summary")
    with patch("bilibili.engine.fetch_metadata", return_value=META), \
         patch("bilibili.engine.fetch_subtitle", return_value=SUBT):
        res = _engine(bn).transcribe("BV1x", BilibiliCredential(sessdata="SS"))
    # prefetched_transcript passed, cookie NOT pushed
    _, kwargs = bn.transcribe.call_args
    assert kwargs["prefetched_transcript"]["full_text"] == "hi"
    bn.push_cookie.assert_not_called()
    assert res.transcript.source == "subtitle"
    assert res.summary_markdown == "## Summary"


def test_asr_path_pushes_cookie_and_sets_source_asr():
    asr = {"language": "zh", "full_text": "world", "segments": [{"start": 0, "end": 1, "text": "world"}]}
    bn = MagicMock()
    bn.transcribe.return_value = (asr, "## Summary")
    with patch("bilibili.engine.fetch_metadata", return_value=META), \
         patch("bilibili.engine.fetch_subtitle", return_value=None):
        res = _engine(bn).transcribe("BV1x", BilibiliCredential(sessdata="SS"))
    bn.push_cookie.assert_called_once()
    _, kwargs = bn.transcribe.call_args
    assert kwargs["prefetched_transcript"] is None
    assert res.transcript.source == "asr"
    assert res.transcript.full_text == "world"


def test_asr_path_cookie_push_failure_is_best_effort():
    asr = {"language": "zh", "full_text": "x", "segments": [{"start": 0, "end": 1, "text": "x"}]}
    bn = MagicMock()
    bn.push_cookie.side_effect = Exception("cookie store down")
    bn.transcribe.return_value = (asr, None)
    with patch("bilibili.engine.fetch_metadata", return_value=META), \
         patch("bilibili.engine.fetch_subtitle", return_value=None):
        res = _engine(bn).transcribe("BV1x", BilibiliCredential(sessdata="SS"))  # must not raise
    assert res.transcript.source == "asr"
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tests/test_engine.py -v`
Expected: FAIL — `ModuleNotFoundError: bilibili.engine`.

- [ ] **Step 3: Implement**

```python
# src/bilibili/engine.py
"""The cascade orchestrator: metadata → subtitle → (prefetched|ASR) BiliNote → BilibiliResult."""
from __future__ import annotations
import logging
from typing import Optional

from .bilinote_client import BiliNoteClient
from .config import load_config, DEFAULT_CONFIG_PATH
from .metadata import fetch_metadata
from .models import (
    BilibiliCredential, BilibiliResult, EngineConfig, Transcript, TranscriptSegment,
)
from .subtitle import fetch_subtitle
from .url_parser import parse_video_ref

logger = logging.getLogger(__name__)


def _transcript_to_prefetched(t: Transcript) -> dict:
    return {
        "language": t.language,
        "full_text": t.full_text,
        "segments": [{"start": s.start, "end": s.end, "text": s.text} for s in t.segments],
    }


class BilibiliEngine:
    def __init__(self, config: EngineConfig):
        self.config = config
        self._bn = BiliNoteClient(
            base_url=config.bn_base_url, provider_id=config.provider_id,
            model_name=config.model_name, poll_interval_s=config.poll_interval_s,
            poll_timeout_s=config.poll_timeout_s, style=config.style,
        )

    @classmethod
    def from_config(cls, path: str = DEFAULT_CONFIG_PATH) -> "BilibiliEngine":
        return cls(load_config(path))

    def transcribe(self, video_ref: str, credential: Optional[BilibiliCredential] = None) -> BilibiliResult:
        ref = parse_video_ref(video_ref)
        meta = fetch_metadata(ref, credential)
        subtitle = fetch_subtitle(meta.bvid, meta.cid, credential)

        if subtitle is not None:
            _, summary = self._bn.transcribe(
                meta.url, prefetched_transcript=_transcript_to_prefetched(subtitle))
            transcript = subtitle
        else:
            if credential and credential.sessdata:
                try:
                    self._bn.push_cookie(credential.to_cookie_string())
                except Exception as e:  # best-effort (decision (a))
                    logger.warning("cookie push to BiliNote failed (best-effort): %s", e)
            asr, summary = self._bn.transcribe(meta.url, prefetched_transcript=None)
            transcript = Transcript(
                source="asr",
                language=asr.get("language"),
                full_text=asr["full_text"],
                segments=[TranscriptSegment(s["start"], s["end"], s["text"]) for s in asr["segments"]],
            )

        return BilibiliResult(metadata=meta, transcript=transcript, summary_markdown=summary)


def transcribe(video_ref: str, credential: Optional[BilibiliCredential] = None,
               config: Optional[EngineConfig] = None) -> BilibiliResult:
    """Convenience: build a default engine (from EngineConfig or config file) and transcribe."""
    engine = BilibiliEngine(config) if config else BilibiliEngine.from_config()
    return engine.transcribe(video_ref, credential)
```

- [ ] **Step 4: Run it to verify it passes**

Run: `python -m pytest tests/test_engine.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add Engine/bilibili/src/bilibili/engine.py Engine/bilibili/tests/test_engine.py
git commit -m "feat(SP-4a): engine cascade (subtitle→prefetched / no-subtitle→cookie+ASR)"
```

---

## Task 12: Public API exports

**Files:**
- Modify: `Engine/bilibili/src/bilibili/__init__.py`
- Test: `Engine/bilibili/tests/test_public_api.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_public_api.py
def test_public_surface():
    import bilibili
    for name in [
        "BilibiliEngine", "BilibiliCredential", "EngineConfig", "RenderOptions",
        "BilibiliResult", "transcribe", "BilibiliEngineError",
    ]:
        assert hasattr(bilibili, name), f"missing public export: {name}"
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tests/test_public_api.py -v`
Expected: FAIL — `AssertionError: missing public export: BilibiliEngine`.

- [ ] **Step 3: Implement**

```python
# src/bilibili/__init__.py
"""JarvanKB Bilibili Engine (SP-4a). Frozen public API — see docs/interface.md."""
from .engine import BilibiliEngine, transcribe
from .models import (
    BilibiliCredential, EngineConfig, RenderOptions, RenderedOutput,
    BilibiliResult, BilibiliMetadata, Transcript, TranscriptSegment,
)
from .errors import (
    BilibiliEngineError, InvalidVideoRef, CredentialError,
    BiliNoteUnavailable, TranscriptionFailed, TranscriptionTimeout,
)

__version__ = "0.1.0"

__all__ = [
    "BilibiliEngine", "transcribe",
    "BilibiliCredential", "EngineConfig", "RenderOptions", "RenderedOutput",
    "BilibiliResult", "BilibiliMetadata", "Transcript", "TranscriptSegment",
    "BilibiliEngineError", "InvalidVideoRef", "CredentialError",
    "BiliNoteUnavailable", "TranscriptionFailed", "TranscriptionTimeout",
]
```

- [ ] **Step 4: Run the full suite + commit**

Run: `python -m pytest -v` → Expected: ALL PASS.

```bash
git add Engine/bilibili/src/bilibili/__init__.py Engine/bilibili/tests/test_public_api.py
git commit -m "feat(SP-4a): freeze public API exports"
```

---

## Task 13: Thin CLI

**Files:**
- Create: `Engine/bilibili/src/bilibili/cli.py`
- Test: `Engine/bilibili/tests/test_cli.py`

- [ ] **Step 1: Write the failing test (arg parsing + render wiring, engine mocked)**

```python
# tests/test_cli.py
from unittest.mock import patch
from bilibili.cli import build_parser, run
from bilibili.models import (
    BilibiliMetadata, Transcript, TranscriptSegment, BilibiliResult,
)

META = BilibiliMetadata(bvid="BV1x", aid=1, cid=2, title="T", up="U", up_mid=9,
                        duration=10, pubdate=1610000000, cover=None,
                        url="https://www.bilibili.com/video/BV1x")
RES = BilibiliResult(metadata=META,
                     transcript=Transcript("subtitle", "zh", "hi", [TranscriptSegment(0, 1, "hi")]),
                     summary_markdown="## S")


def test_parser_defaults():
    args = build_parser().parse_args(["BV1x"])
    assert args.video == "BV1x"
    assert args.split is False
    assert args.timestamps is False
    assert args.no_transcript is False


def test_run_prints_markdown(capsys):
    with patch("bilibili.cli.transcribe", return_value=RES), \
         patch("bilibili.cli._credential_from_args", return_value=None):
        rc = run(["BV1x", "--sessdata", "SS"])
    assert rc == 0
    assert "## S" in capsys.readouterr().out


def test_run_split_writes_files(tmp_path):
    out = tmp_path / "out"
    with patch("bilibili.cli.transcribe", return_value=RES), \
         patch("bilibili.cli._credential_from_args", return_value=None):
        rc = run(["BV1x", "--split", "--out", str(out)])
    assert rc == 0
    assert (out / "BV1x.md").exists()
    assert (out / "BV1x.transcript.md").exists()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tests/test_cli.py -v`
Expected: FAIL — `ModuleNotFoundError: bilibili.cli`.

- [ ] **Step 3: Implement**

```python
# src/bilibili/cli.py
"""Thin CLI for manual testing: resolve a video → transcribe → print or write Markdown."""
from __future__ import annotations
import argparse
import os
import sys
from typing import Optional

from .engine import transcribe
from .models import BilibiliCredential, RenderOptions


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="bilibili-engine", description="Transcribe a Bilibili video.")
    p.add_argument("video", help="BV id / bilibili.com URL / av id")
    p.add_argument("--out", default=None, help="output directory (default: print to stdout)")
    p.add_argument("--no-transcript", action="store_true", help="omit the transcript body")
    p.add_argument("--timestamps", action="store_true", help="render [mm:ss] timestamped lines")
    p.add_argument("--split", action="store_true", help="write transcript to a separate file")
    p.add_argument("--slug", default=None, help="override output basename (default: bvid)")
    p.add_argument("--sessdata", default=None, help="SESSDATA cookie (or set BILI_SESSDATA)")
    p.add_argument("--bili-jct", default=None)
    p.add_argument("--buvid3", default=None)
    return p


def _credential_from_args(args) -> Optional[BilibiliCredential]:
    sessdata = args.sessdata or os.getenv("BILI_SESSDATA")
    if not sessdata:
        return None
    return BilibiliCredential(sessdata=sessdata, bili_jct=args.bili_jct, buvid3=args.buvid3)


def run(argv: Optional[list] = None) -> int:
    args = build_parser().parse_args(argv)
    cred = _credential_from_args(args)
    result = transcribe(args.video, cred)
    opts = RenderOptions(
        include_transcript=not args.no_transcript,
        include_timestamps=args.timestamps,
        split_transcript=args.split,
        slug=args.slug,
    )
    rendered = result.render(opts)
    if not args.out:
        sys.stdout.write(rendered.main_markdown)
        return 0
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, rendered.suggested_names["main"]), "w", encoding="utf-8") as f:
        f.write(rendered.main_markdown)
    if rendered.transcript_markdown:
        with open(os.path.join(args.out, rendered.suggested_names["transcript"]), "w", encoding="utf-8") as f:
            f.write(rendered.transcript_markdown)
    return 0


def main() -> None:  # console_scripts entry point
    raise SystemExit(run())
```

- [ ] **Step 4: Run the test + commit**

Run: `python -m pytest tests/test_cli.py -v` → Expected: PASS.

```bash
git add Engine/bilibili/src/bilibili/cli.py Engine/bilibili/tests/test_cli.py
git commit -m "feat(SP-4a): thin CLI (stdout or --out, render switches)"
```

---

## Task 14: BiliNote deployment artifacts (the Stage-3 gate)

**Files:**
- Create: `Engine/bilibili/deploy/bilinote/docker-compose.yml`
- Create: `Engine/bilibili/deploy/bilinote/.env.example`
- Create: `Engine/bilibili/deploy/bilinote/README.md`

> No automated test — these are deployment artifacts. They are the deliverable that unblocks the
> Stage-3 gate (Dashboard UN-018): the user runs BN, then the manual smoke (Task 15) can proceed.

- [ ] **Step 1: Write `.env.example`**

```bash
# Engine/bilibili/deploy/bilinote/.env.example  → copy to .env, then `docker compose up -d`
APP_PORT=3015                 # browser-facing port (engine config base_url uses this)
BACKEND_PORT=8483
BACKEND_HOST=0.0.0.0
TRANSCRIBER_TYPE=bcut         # B站必剪 free cloud ASR — no SESSDATA needed for ASR itself
ENV=production
# LLM API keys are NOT set here — add a provider in BiliNote's web UI after first boot,
# then copy its provider_id into config/bilibili-engine.yaml.
```

- [ ] **Step 2: Write `docker-compose.yml`** (pulls the published image; does not vendor BN source)

```yaml
# Engine/bilibili/deploy/bilinote/docker-compose.yml
# Minimal BiliNote deployment for SP-4a. Upstream: https://github.com/JefferyHcool/BiliNote
# Running this is a USER action (Dashboard UN-018). After boot, open http://localhost:${APP_PORT},
# add an LLM provider, and read back its provider_id for config/bilibili-engine.yaml.
services:
  bilinote:
    image: ghcr.io/jefferyhcool/bilinote:latest
    container_name: jarvankb-bilinote
    env_file: [.env]
    environment:
      - TRANSCRIBER_TYPE=${TRANSCRIBER_TYPE:-bcut}
    ports:
      - "${APP_PORT:-3015}:80"
    volumes:
      - bilinote-data:/app/backend/data
      - bilinote-config:/app/backend/config
      - bilinote-static:/app/backend/static
    restart: unless-stopped
volumes:
  bilinote-data:
  bilinote-config:
  bilinote-static:
```

> NOTE FOR IMPLEMENTER: confirm the published image tag/name against upstream at deploy time
> (`ghcr.io/jefferyhcool/bilinote:latest` per the README quick-start). If upstream only ships a
> build-from-source compose, fall back to documenting `git clone … && docker-compose up -d` in the
> README and keep `TRANSCRIBER_TYPE=bcut` in `.env`.

- [ ] **Step 3: Write `README.md` (runbook)**

```markdown
# BiliNote deployment for SP-4a (Bilibili Engine)

SP-4a is a *client* of a self-hosted BiliNote (BN) instance. BN does audio extraction + bcut ASR +
the LLM summary; the engine submits jobs and parses results.

## Bring BN up (USER action — Dashboard UN-018)
1. `cp .env.example .env` (adjust `APP_PORT` if 3015 is taken).
2. `docker compose up -d` (this directory).
3. Open `http://localhost:<APP_PORT>` → **模型供应商** → add your LLM provider (key stored in BN's
   SQLite, not in git). Note the provider's id.
4. Put `base_url: http://127.0.0.1:<APP_PORT>` and that `provider_id` into
   `config/bilibili-engine.yaml` (copy from `config/bilibili-engine.example.yaml`).
5. Tell the engine session the endpoint is live so Stage-3 smoke can run.

## Why bcut
`TRANSCRIBER_TYPE=bcut` uses B站必剪's free cloud ASR — no local Whisper model download, no GPU,
no extra API key. The subtitle-first cascade means ASR only runs for videos without subtitles.
```

- [ ] **Step 4: Commit**

```bash
git add Engine/bilibili/deploy/bilinote/
git commit -m "feat(SP-4a): BiliNote deployment artifacts (compose + .env + runbook)"
```

---

## Task 15: docs/interface.md + architecture.md + Stage-3 gate

**Files:**
- Modify: `Engine/bilibili/docs/interface.md`
- Modify: `Engine/bilibili/docs/architecture.md`
- Sendbox: `docs/sendbox/toOrchestrator/from-sp4aimpler-blocker-bn-docker.md`

- [ ] **Step 1: Replace `docs/interface.md` placeholder with the frozen contract**

Mirror §4 of the design (public API: `BilibiliEngine`, `transcribe`, `BilibiliCredential`,
`EngineConfig`, `RenderOptions`, `BilibiliResult`/`render`/`to_markdown`, dataclass fields, the
`from bilibili import …` import + `pip install -e .` note). Copy the §4 code block verbatim so
downstream SP-4b/SP-5b integrate against a single source.

- [ ] **Step 2: Replace `docs/architecture.md` placeholder**

Summarize the unit table + data flow from design §2–§3 (engine-driven cascade, network-only-in-three-units,
BN hard-required, render returns content). Keep it short; point to the spec for detail.

- [ ] **Step 3: Run the full suite once more**

Run: `cd Engine/bilibili && python -m pytest -v`
Expected: ALL PASS.

- [ ] **Step 4: Commit docs**

```bash
git add Engine/bilibili/docs/interface.md Engine/bilibili/docs/architecture.md
git commit -m "docs(SP-4a): freeze interface.md + architecture.md from design"
```

- [ ] **Step 5: Write the Stage-3 gate blocker letter + track Dashboard UN-018**

Write `docs/sendbox/toOrchestrator/from-sp4aimpler-blocker-bn-docker.md` (sendbox-protocol blocker
letter, English/A2A): state that code + tests are green offline, and Stage-3 execute (the mandatory
manual smoke) is gated on a reachable BN — point to `Engine/bilibili/deploy/bilinote/` and ask the
user to bring BN up + confirm the endpoint. Ensure Dashboard `UN-018` reflects the ask. Then pause
for the user (this is a real gate — do not fake the smoke).

---

## Task 16: Mandatory manual smoke (after BN is reachable) + verification gate

**Files:** none (verification activity); may add `docs/RepoMem/temp/sp4a-bilibili-engine/smoke.md` evidence.

- [ ] **Step 1: Fill `config/bilibili-engine.yaml`** with the live BN `base_url` + `provider_id`.

- [ ] **Step 2: Subtitle-path smoke** — pick a BV known to have subtitles (official or AI CC):

Run: `bilibili-engine <BV_with_subtitle> --sessdata "$BILI_SESSDATA"`
Expected: prints Markdown; `transcript_source: subtitle` in frontmatter; transcript body present as prose.

- [ ] **Step 3: ASR-path smoke** — pick a BV without subtitles:

Run: `bilibili-engine <BV_without_subtitle> --sessdata "$BILI_SESSDATA" --out /tmp/sp4a`
Expected: `transcript_source: asr`; `/tmp/sp4a/<bvid>.md` written with a summary + prose transcript.

- [ ] **Step 4: Split-mode smoke**

Run: `bilibili-engine <BV_with_subtitle> --split --out /tmp/sp4a`
Expected: two files; main has `[全文转录](./<bvid>.transcript.md)`; transcript file holds the body.

- [ ] **Step 5: Run `superpowers:verification-before-completion`** — full `pytest` green + the three
smoke captures recorded as evidence. Only then is SP-4a done.

- [ ] **Step 6: Commit smoke evidence (optional) + proceed to finishing-a-development-branch**

```bash
git add Engine/bilibili/docs/RepoMem/temp/sp4a-bilibili-engine/smoke.md
git commit -m "test(SP-4a): manual smoke evidence (subtitle + asr + split paths)"
```

---

## Post-plan steps (not tasks)

- `superpowers:requesting-code-review` + `superpowers:finishing-a-development-branch` — both ask-first.
- `RepoMem.merge` (Step 8) — **the implementer owns closure** (CLAUDE.md §3/§4): promote any global-scope
  lesson (e.g. a reusable BiliNote-client / subtitle-cascade pattern) to `docs/RepoMem/persist/`; keep
  module specifics in `Engine/bilibili/docs/RepoMem/decisions.md`. May delegate *execution* to orche but
  track to completion before reporting done — never fire-and-forget.
- Write `docs/sendbox/toOrchestrator/from-sp4aimpler-sp4a-done.md`, then burn the handoff.

---

## Self-Review (run by the plan author)

**1. Spec coverage:**
- §1 scope (metadata / subtitle-first / ASR-fallback / summary / output) → Tasks 8, 9, 10, 11, 6. ✓
- §2 decisions (BN client / engine-driven cascade / manual provider / cookie push / BN hard-required) → Tasks 10, 11, 7. ✓
- §3 units (url_parser/models/metadata/subtitle/bilinote_client/engine/render/config/cli) → Tasks 2–13. ✓
- §4 frozen interface → Tasks 3, 11, 12, 15. ✓
- §5 render switches + prose-merge + split + purity → Tasks 5, 6, 13. ✓
- §6 credentials/BN deploy/config → Tasks 7, 11, 14. ✓
- §7 errors → Task 2 (+ raised across 8/10/11). ✓
- §8 testing (pure units, mocked network, cascade, manual smoke) → every task + Task 16. ✓
- §9 v2+ futures → explicitly out of scope; no tasks (correct). ✓

**2. Placeholder scan:** No "TBD/TODO/handle edge cases" steps. The two "record a real fixture" notes
(Tasks 8, 9) and the image-tag confirmation (Task 14) are concrete verification actions, not placeholders.

**3. Type consistency:** `BilibiliCredential.to_cookie_string`, `parse_info`/`_get_info_raw`,
`pick_track`/`parse_body`/`_get_tracks_raw`/`_get_body_raw`, `BiliNoteClient.{health_check,push_cookie,
generate_note,poll,transcribe}`, `render_result`/`merge_segments_to_prose`/`format_timestamp`,
`RenderedOutput.{main_markdown,transcript_markdown,suggested_names}`, `EngineConfig` fields,
`BilibiliEngine.{from_config,transcribe}` + module `transcribe` — names are consistent across tasks and
match the design §4 contract. ✓
