# Zhihu Engine (SP-2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `Engine/zhihu/` — a pure-fetch Python library that turns one Zhihu URL (answer / article / question) into clean Markdown + structured metadata, consuming injected cookies, with optional flat two-layer comments.

**Architecture:** Pure functions for parsing (`url_router`, `initialdata`, `parsers/*`, `markdown`, comment-flattening) + a thin networked `fetcher`/`comments` layer + an `engine.fetch()` orchestrator. Bodies come from the page's embedded `js-initialData` JSON (primary) → CSS-selector scrape (fallback) → unsigned `/api/v4` (fallback on 403). **No browser, no zse-96 signer** (see design.md §2). Cookies are injected input; the engine never touches cookie-manager.

**Tech Stack:** Python 3.11+, `httpx`, `beautifulsoup4` + `lxml`, `markdownify`; `pytest` + `pytest-httpx` for tests; `src/`-layout package `zhihu` with its own `pyproject.toml`.

**Design doc:** `Engine/zhihu/docs/superpowers/specs/2026-05-31-SP-2-zhihu-engine-design.md`
**Working notes / open empirical items:** `Engine/zhihu/docs/RepoMem/temp/sp2-zhihu-engine/requirements.md`

---

## File Structure

```
Engine/zhihu/
├── pyproject.toml                     # package "zhihu", src-layout, deps
├── src/zhihu/
│   ├── __init__.py                    # public exports: fetch, FetchResult, models, ZhihuFetchError
│   ├── errors.py                      # ZhihuFetchError
│   ├── models.py                      # ZhihuType, Author, EmbeddedAnswer, Comment, FetchResult(+to_markdown)
│   ├── url_router.py                  # classify(url) -> (ZhihuType, ids)
│   ├── initialdata.py                 # extract_initial_data(html) -> dict
│   ├── markdown.py                    # html_to_markdown(html) ; render_frontmatter(meta)
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── answer.py                  # parse_answer(initial_data, ids) -> FetchResult
│   │   ├── article.py                 # parse_article(initial_data, ids) -> FetchResult
│   │   └── question.py                # parse_question(initial_data, ids) -> FetchResult
│   ├── comments.py                    # flatten_comments(root_pages) ; fetch_comments(...)
│   ├── fetcher.py                     # HTTP: headers, get_page, get_api_answer
│   ├── engine.py                      # fetch() orchestration + fallback chain
│   └── cli.py                         # python -m zhihu
└── tests/
    ├── conftest.py
    ├── fixtures/                      # captured/synthetic html + json
    ├── test_url_router.py
    ├── test_initialdata.py
    ├── test_markdown.py
    ├── test_parsers_answer.py
    ├── test_parsers_article.py
    ├── test_parsers_question.py
    ├── test_models.py                 # to_markdown / frontmatter
    ├── test_comments.py
    ├── test_fetcher.py
    └── test_engine.py
```

> **Note on Zhihu JSON shapes:** the parser tasks below use Zhihu's known `js-initialData` structure (`initialState.entities.{answers,articles,questions}`). The exact field paths are validated and corrected against **real captured fixtures** in Task 15 (smoke). Build the pure units against the synthetic fixtures here; adjust paths in Task 15 if live data differs.

---

## Task 0: Package scaffold

**Files:**
- Create: `Engine/zhihu/pyproject.toml`
- Create: `Engine/zhihu/src/zhihu/__init__.py`
- Create: `Engine/zhihu/tests/conftest.py`
- Create: `Engine/zhihu/tests/__init__.py`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "zhihu-engine"
version = "0.1.0"
description = "Pure-fetch Zhihu engine: one URL -> Markdown + metadata"
requires-python = ">=3.11"
dependencies = [
    "httpx>=0.27",
    "beautifulsoup4>=4.12",
    "lxml>=5.0",
    "markdownify>=0.13",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-httpx>=0.30"]

[project.scripts]
zhihu = "zhihu.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create empty package + test init files**

`Engine/zhihu/src/zhihu/__init__.py`:
```python
"""Zhihu engine — one URL -> Markdown + metadata. Public API exported below."""
```
`Engine/zhihu/tests/__init__.py`: (empty file)

- [ ] **Step 3: Write `conftest.py` with a fixtures-dir helper**

```python
from pathlib import Path
import pytest

FIXTURES = Path(__file__).parent / "fixtures"

@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES

def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")
```
Also create the dir: `mkdir -p Engine/zhihu/tests/fixtures`.

- [ ] **Step 4: Install dev env and verify pytest runs**

Run (from `Engine/zhihu/`): `python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"`
Then: `pytest -q`
Expected: `no tests ran` (exit 5) — scaffold imports cleanly.

- [ ] **Step 5: Add `.gitignore` and commit**

`Engine/zhihu/.gitignore`:
```
.venv/
__pycache__/
*.egg-info/
.pytest_cache/
tests/fixtures/*.local.*
```
```bash
git add Engine/zhihu/pyproject.toml Engine/zhihu/src Engine/zhihu/tests Engine/zhihu/.gitignore
git commit -m "feat(SP-2): scaffold zhihu engine package (src-layout, pytest)"
```

---

## Task 1: Errors

**Files:**
- Create: `Engine/zhihu/src/zhihu/errors.py`
- Test: `Engine/zhihu/tests/test_engine.py` (later); covered indirectly. Add a focused test here.

- [ ] **Step 1: Write the failing test** — append to a new `tests/test_errors.py`:

```python
from zhihu.errors import ZhihuFetchError

def test_error_carries_diagnostics():
    err = ZhihuFetchError("boom", url="https://www.zhihu.com/x", attempts=["html", "api"], status=403)
    assert err.url == "https://www.zhihu.com/x"
    assert err.attempts == ["html", "api"]
    assert err.status == 403
    assert "boom" in str(err)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_errors.py -v`
Expected: FAIL — `ModuleNotFoundError: zhihu.errors`.

- [ ] **Step 3: Write minimal implementation** — `src/zhihu/errors.py`:

```python
from __future__ import annotations


class ZhihuFetchError(Exception):
    """Raised when all body-fetch fallbacks fail. Carries diagnostics, never a silent sentinel."""

    def __init__(self, message: str, *, url: str, attempts: list[str] | None = None,
                 status: int | None = None) -> None:
        super().__init__(message)
        self.url = url
        self.attempts = attempts or []
        self.status = status
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_errors.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/zhihu/errors.py tests/test_errors.py
git commit -m "feat(SP-2): ZhihuFetchError with diagnostics"
```

---

## Task 2: Models

**Files:**
- Create: `Engine/zhihu/src/zhihu/models.py`
- Test: `Engine/zhihu/tests/test_models.py`

- [ ] **Step 1: Write the failing test** — `tests/test_models.py`:

```python
from zhihu.models import Author, EmbeddedAnswer, Comment, FetchResult, ZhihuType

def test_fetchresult_defaults():
    r = FetchResult(
        url="u", type=ZhihuType.ANSWER, title="t",
        author=Author(name="a"), content_markdown="body",
        metadata={"vote_count": 5}, fetched_at="2026-06-01T00:00:00Z",
    )
    assert r.answers == []
    assert r.comments == []
    assert r.raw is None
    assert r.type is ZhihuType.ANSWER

def test_comment_is_flat():
    c = Comment(id="1", parent_id=None, author=Author(name="x"),
                content="hi", like_count=2, created_at="2026-06-01T00:00:00Z")
    child = Comment(id="2", parent_id="1", author=Author(name="y"),
                    content="re", like_count=0, created_at="2026-06-01T00:00:00Z",
                    reply_to_author="x")
    assert child.parent_id == "1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: zhihu.models`.

- [ ] **Step 3: Write minimal implementation** — `src/zhihu/models.py`:

```python
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class ZhihuType(str, Enum):
    ANSWER = "answer"
    ARTICLE = "article"
    QUESTION = "question"


@dataclass
class Author:
    name: str
    url: str | None = None
    headline: str | None = None


@dataclass
class EmbeddedAnswer:
    answer_id: str
    author: Author | None
    vote_count: int
    comment_count: int
    created_at: str | None
    updated_at: str | None
    url: str
    content_markdown: str  # FULL content when initialData carries it; "" otherwise


@dataclass
class Comment:
    id: str
    parent_id: str | None          # None = top-level
    author: Author | None
    content: str
    like_count: int
    created_at: str | None
    reply_to_author: str | None = None


@dataclass
class FetchResult:
    url: str
    type: ZhihuType
    title: str
    author: Author | None
    content_markdown: str
    metadata: dict
    fetched_at: str
    answers: list[EmbeddedAnswer] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)
    raw: dict | None = None

    def to_markdown(self, with_frontmatter: bool = True) -> str:
        # Implemented in Task 8b once render_frontmatter exists; placeholder raises until then.
        raise NotImplementedError
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py -v`
Expected: PASS (the two tests; `to_markdown` not exercised yet).

- [ ] **Step 5: Commit**

```bash
git add src/zhihu/models.py tests/test_models.py
git commit -m "feat(SP-2): data models (FetchResult, EmbeddedAnswer, Comment, Author)"
```

---

## Task 3: URL router

**Files:**
- Create: `Engine/zhihu/src/zhihu/url_router.py`
- Test: `Engine/zhihu/tests/test_url_router.py`

- [ ] **Step 1: Write the failing test** — `tests/test_url_router.py`:

```python
import pytest
from zhihu.url_router import classify
from zhihu.models import ZhihuType
from zhihu.errors import ZhihuFetchError

@pytest.mark.parametrize("url,expected_type,expected_ids", [
    ("https://www.zhihu.com/question/123/answer/456", ZhihuType.ANSWER, {"answer_id": "456", "question_id": "123"}),
    ("https://www.zhihu.com/answer/456", ZhihuType.ANSWER, {"answer_id": "456"}),
    ("https://zhuanlan.zhihu.com/p/789", ZhihuType.ARTICLE, {"article_id": "789"}),
    ("https://www.zhihu.com/p/789", ZhihuType.ARTICLE, {"article_id": "789"}),
    ("https://www.zhihu.com/question/123", ZhihuType.QUESTION, {"question_id": "123"}),
])
def test_classify(url, expected_type, expected_ids):
    t, ids = classify(url)
    assert t is expected_type
    for k, v in expected_ids.items():
        assert ids[k] == v

def test_classify_rejects_unknown():
    with pytest.raises(ZhihuFetchError):
        classify("https://www.zhihu.com/people/someone")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_url_router.py -v`
Expected: FAIL — `ModuleNotFoundError: zhihu.url_router`.

- [ ] **Step 3: Write minimal implementation** — `src/zhihu/url_router.py`:

```python
from __future__ import annotations
import re
from .models import ZhihuType
from .errors import ZhihuFetchError

_ANSWER_WITH_Q = re.compile(r"/question/(?P<q>\d+)/answer/(?P<a>\d+)")
_ANSWER_BARE = re.compile(r"/answer/(?P<a>\d+)")
_ARTICLE = re.compile(r"/p/(?P<p>\d+)")
_QUESTION = re.compile(r"/question/(?P<q>\d+)/?$")


def classify(url: str) -> tuple[ZhihuType, dict]:
    """Classify a Zhihu URL into (type, ids). Raises ZhihuFetchError on unsupported URLs."""
    m = _ANSWER_WITH_Q.search(url)
    if m:
        return ZhihuType.ANSWER, {"answer_id": m.group("a"), "question_id": m.group("q")}
    m = _ANSWER_BARE.search(url)
    if m:
        return ZhihuType.ANSWER, {"answer_id": m.group("a")}
    m = _ARTICLE.search(url)
    if m:
        return ZhihuType.ARTICLE, {"article_id": m.group("p")}
    m = _QUESTION.search(url)
    if m:
        return ZhihuType.QUESTION, {"question_id": m.group("q")}
    raise ZhihuFetchError(f"Unsupported Zhihu URL: {url}", url=url)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_url_router.py -v`
Expected: PASS (6 cases).

- [ ] **Step 5: Commit**

```bash
git add src/zhihu/url_router.py tests/test_url_router.py
git commit -m "feat(SP-2): URL router (answer/article/question classification)"
```

---

## Task 4: initialData extraction

**Files:**
- Create: `Engine/zhihu/src/zhihu/initialdata.py`
- Test: `Engine/zhihu/tests/test_initialdata.py`
- Fixture: `Engine/zhihu/tests/fixtures/initialdata_min.html`

- [ ] **Step 1: Create the synthetic fixture** — `tests/fixtures/initialdata_min.html`:

```html
<!doctype html><html><head><title>x</title></head><body>
<div id="root">hi</div>
<script id="js-initialData" type="text/json">{"initialState":{"entities":{"answers":{"456":{"id":456,"content":"<p>hello</p>"}}}}}</script>
</body></html>
```

- [ ] **Step 2: Write the failing test** — `tests/test_initialdata.py`:

```python
from conftest import load_fixture
from zhihu.initialdata import extract_initial_data

def test_extract_parses_blob():
    data = extract_initial_data(load_fixture("initialdata_min.html"))
    assert data["initialState"]["entities"]["answers"]["456"]["content"] == "<p>hello</p>"

def test_extract_returns_none_when_absent():
    assert extract_initial_data("<html><body>no script</body></html>") is None
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_initialdata.py -v`
Expected: FAIL — `ModuleNotFoundError: zhihu.initialdata`.

- [ ] **Step 4: Write minimal implementation** — `src/zhihu/initialdata.py`:

```python
from __future__ import annotations
import json
from bs4 import BeautifulSoup


def extract_initial_data(html: str) -> dict | None:
    """Extract and parse the <script id="js-initialData"> JSON blob. None if absent/unparseable."""
    soup = BeautifulSoup(html, "lxml")
    tag = soup.find("script", id="js-initialData")
    if not tag or not tag.string:
        return None
    try:
        return json.loads(tag.string)
    except (ValueError, TypeError):
        return None
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_initialdata.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/zhihu/initialdata.py tests/test_initialdata.py tests/fixtures/initialdata_min.html
git commit -m "feat(SP-2): initialData blob extraction"
```

---

## Task 5: Markdown conversion

**Files:**
- Create: `Engine/zhihu/src/zhihu/markdown.py`
- Test: `Engine/zhihu/tests/test_markdown.py`

- [ ] **Step 1: Write the failing test** — `tests/test_markdown.py`:

```python
from zhihu.markdown import html_to_markdown, render_frontmatter

def test_basic_conversion():
    md = html_to_markdown("<p>Hello <strong>world</strong></p>")
    assert "Hello **world**" in md

def test_image_keeps_remote_url_no_download():
    md = html_to_markdown('<img src="https://pic.zhimg.com/x.jpg" alt="cap">')
    assert "https://pic.zhimg.com/x.jpg" in md
    assert "![" in md  # standard markdown image, not Obsidian embed
    assert "![[" not in md

def test_style_tags_stripped():
    md = html_to_markdown("<style>.x{}</style><p>kept</p>")
    assert ".x{}" not in md
    assert "kept" in md

def test_render_frontmatter():
    fm = render_frontmatter({"title": "T", "type": "answer", "source": "zhihu"})
    assert fm.startswith("---\n")
    assert "title: T" in fm
    assert fm.rstrip().endswith("---")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_markdown.py -v`
Expected: FAIL — `ModuleNotFoundError: zhihu.markdown`.

- [ ] **Step 3: Write minimal implementation** — `src/zhihu/markdown.py`:

```python
from __future__ import annotations
from bs4 import BeautifulSoup
from markdownify import MarkdownConverter


class _ZhihuConverter(MarkdownConverter):
    """Standard Markdown. Images stay as remote URLs (no download). Engine is pure-fetch."""

    def convert_img(self, el, text, parent_tags):
        src = el.get("data-original") or el.get("src") or ""
        alt = el.get("alt") or ""
        return f"![{alt}]({src})" if src else ""


def html_to_markdown(html: str) -> str:
    soup = BeautifulSoup(html or "", "lxml")
    for style in soup.find_all("style"):
        style.extract()
    return _ZhihuConverter().convert_soup(soup).strip()


def render_frontmatter(meta: dict) -> str:
    """Minimal, deterministic YAML frontmatter (flat scalar values only)."""
    lines = ["---"]
    for key, value in meta.items():
        if value is None:
            continue
        lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_markdown.py -v`
Expected: PASS (4 cases).

- [ ] **Step 5: Commit**

```bash
git add src/zhihu/markdown.py tests/test_markdown.py
git commit -m "feat(SP-2): HTML->Markdown (remote images, style strip, frontmatter)"
```

---

## Task 6: Answer parser

**Files:**
- Create: `Engine/zhihu/src/zhihu/parsers/__init__.py` (empty)
- Create: `Engine/zhihu/src/zhihu/parsers/answer.py`
- Create: `Engine/zhihu/src/zhihu/_entities.py` (shared entity helpers)
- Test: `Engine/zhihu/tests/test_parsers_answer.py`

- [ ] **Step 1: Write the failing test** — `tests/test_parsers_answer.py`:

```python
from zhihu.parsers.answer import parse_answer
from zhihu.models import ZhihuType

INITIAL = {
    "initialState": {"entities": {"answers": {"456": {
        "id": 456,
        "content": "<p>Answer body</p>",
        "voteup_count": 12,
        "comment_count": 3,
        "created_time": 1700000000,
        "updated_time": 1700000100,
        "author": {"name": "Alice", "url_token": "alice", "headline": "dev"},
        "question": {"id": 123, "title": "Why?"},
    }}}}
}

def test_parse_answer():
    r = parse_answer(INITIAL, {"answer_id": "456", "question_id": "123"},
                     url="https://www.zhihu.com/question/123/answer/456")
    assert r.type is ZhihuType.ANSWER
    assert r.title == "Why?"
    assert r.author.name == "Alice"
    assert "Answer body" in r.content_markdown
    assert r.metadata["vote_count"] == 12
    assert r.metadata["comment_count"] == 3
    assert r.metadata["created_at"].startswith("20")

def test_parse_answer_missing_entity_returns_none():
    assert parse_answer({"initialState": {"entities": {"answers": {}}}},
                        {"answer_id": "999"}, url="u") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_parsers_answer.py -v`
Expected: FAIL — `ModuleNotFoundError: zhihu.parsers.answer`.

- [ ] **Step 3: Write shared helpers** — `src/zhihu/_entities.py`:

```python
from __future__ import annotations
from datetime import datetime, timezone
from .models import Author


def entities(initial_data: dict) -> dict:
    return (initial_data or {}).get("initialState", {}).get("entities", {})


def epoch_to_iso(value) -> str | None:
    if not value:
        return None
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc).isoformat().replace("+00:00", "Z")
    except (ValueError, OSError, TypeError):
        return None


def parse_author(raw: dict | None) -> Author | None:
    if not raw:
        return None
    token = raw.get("url_token")
    return Author(
        name=raw.get("name", ""),
        url=f"https://www.zhihu.com/people/{token}" if token else None,
        headline=raw.get("headline") or None,
    )
```

- [ ] **Step 4: Write the parser** — `src/zhihu/parsers/__init__.py` (empty) and `src/zhihu/parsers/answer.py`:

```python
from __future__ import annotations
from ..models import FetchResult, ZhihuType
from ..markdown import html_to_markdown
from .._entities import entities, epoch_to_iso, parse_author


def parse_answer(initial_data: dict, ids: dict, *, url: str) -> FetchResult | None:
    ent = entities(initial_data).get("answers", {})
    raw = ent.get(str(ids.get("answer_id")))
    if not raw:
        return None
    question = raw.get("question") or {}
    return FetchResult(
        url=url,
        type=ZhihuType.ANSWER,
        title=question.get("title", ""),
        author=parse_author(raw.get("author")),
        content_markdown=html_to_markdown(raw.get("content", "")),
        metadata={
            "vote_count": raw.get("voteup_count", 0),
            "comment_count": raw.get("comment_count", 0),
            "created_at": epoch_to_iso(raw.get("created_time")),
            "updated_at": epoch_to_iso(raw.get("updated_time")),
        },
        fetched_at="",  # set by engine
        raw=raw,
    )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_parsers_answer.py -v`
Expected: PASS (2 cases).

- [ ] **Step 6: Commit**

```bash
git add src/zhihu/parsers tests/test_parsers_answer.py src/zhihu/_entities.py
git commit -m "feat(SP-2): answer parser + shared entity helpers"
```

---

## Task 7: Article parser

**Files:**
- Create: `Engine/zhihu/src/zhihu/parsers/article.py`
- Test: `Engine/zhihu/tests/test_parsers_article.py`

- [ ] **Step 1: Write the failing test** — `tests/test_parsers_article.py`:

```python
from zhihu.parsers.article import parse_article
from zhihu.models import ZhihuType

INITIAL = {
    "initialState": {"entities": {"articles": {"789": {
        "id": 789,
        "title": "My Article",
        "content": "<p>Article body</p>",
        "voteup_count": 7,
        "comment_count": 1,
        "created": 1700000000,
        "updated": 1700000100,
        "author": {"name": "Bob", "url_token": "bob"},
    }}}}
}

def test_parse_article():
    r = parse_article(INITIAL, {"article_id": "789"}, url="https://zhuanlan.zhihu.com/p/789")
    assert r.type is ZhihuType.ARTICLE
    assert r.title == "My Article"
    assert r.author.name == "Bob"
    assert "Article body" in r.content_markdown
    assert r.metadata["vote_count"] == 7

def test_parse_article_missing_returns_none():
    assert parse_article({"initialState": {"entities": {"articles": {}}}},
                         {"article_id": "0"}, url="u") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_parsers_article.py -v`
Expected: FAIL — `ModuleNotFoundError: zhihu.parsers.article`.

- [ ] **Step 3: Write the parser** — `src/zhihu/parsers/article.py`:

```python
from __future__ import annotations
from ..models import FetchResult, ZhihuType
from ..markdown import html_to_markdown
from .._entities import entities, epoch_to_iso, parse_author


def parse_article(initial_data: dict, ids: dict, *, url: str) -> FetchResult | None:
    ent = entities(initial_data).get("articles", {})
    raw = ent.get(str(ids.get("article_id")))
    if not raw:
        return None
    return FetchResult(
        url=url,
        type=ZhihuType.ARTICLE,
        title=raw.get("title", ""),
        author=parse_author(raw.get("author")),
        content_markdown=html_to_markdown(raw.get("content", "")),
        metadata={
            "vote_count": raw.get("voteup_count", 0),
            "comment_count": raw.get("comment_count", 0),
            "created_at": epoch_to_iso(raw.get("created")),
            "updated_at": epoch_to_iso(raw.get("updated")),
        },
        fetched_at="",
        raw=raw,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_parsers_article.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/zhihu/parsers/article.py tests/test_parsers_article.py
git commit -m "feat(SP-2): article parser"
```

---

## Task 8: Question parser (embedded answers, full fidelity)

**Files:**
- Create: `Engine/zhihu/src/zhihu/parsers/question.py`
- Test: `Engine/zhihu/tests/test_parsers_question.py`

- [ ] **Step 1: Write the failing test** — `tests/test_parsers_question.py`:

```python
from zhihu.parsers.question import parse_question
from zhihu.models import ZhihuType

INITIAL = {
    "initialState": {"entities": {
        "questions": {"123": {
            "id": 123, "title": "Why sky blue?",
            "detail": "<p>Question detail</p>",
            "answerCount": 2, "followerCount": 50, "visitCount": 999,
        }},
        "answers": {
            "456": {"id": 456, "content": "<p>Rayleigh</p>", "voteup_count": 9,
                    "comment_count": 1, "created_time": 1700000000, "updated_time": 1700000000,
                    "author": {"name": "Alice", "url_token": "alice"},
                    "question": {"id": 123, "title": "Why sky blue?"}},
            "457": {"id": 457, "content": "<p>Scatter</p>", "voteup_count": 4,
                    "comment_count": 0, "created_time": 1700000001, "updated_time": 1700000001,
                    "author": {"name": "Bob", "url_token": "bob"},
                    "question": {"id": 123, "title": "Why sky blue?"}},
            "999": {"id": 999, "content": "<p>Other</p>", "question": {"id": 555}},
        },
    }}
}

def test_parse_question():
    r = parse_question(INITIAL, {"question_id": "123"}, url="https://www.zhihu.com/question/123")
    assert r.type is ZhihuType.QUESTION
    assert r.title == "Why sky blue?"
    assert "Question detail" in r.content_markdown
    assert r.metadata["answer_count"] == 2
    assert r.metadata["follow_count"] == 50
    # embedded answers only for THIS question, full content, sorted by vote desc
    assert [a.answer_id for a in r.answers] == ["456", "457"]
    assert "Rayleigh" in r.answers[0].content_markdown
    assert r.answers[0].vote_count == 9
    assert r.answers[0].url == "https://www.zhihu.com/question/123/answer/456"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_parsers_question.py -v`
Expected: FAIL — `ModuleNotFoundError: zhihu.parsers.question`.

- [ ] **Step 3: Write the parser** — `src/zhihu/parsers/question.py`:

```python
from __future__ import annotations
from ..models import FetchResult, ZhihuType, EmbeddedAnswer
from ..markdown import html_to_markdown
from .._entities import entities, epoch_to_iso, parse_author


def parse_question(initial_data: dict, ids: dict, *, url: str) -> FetchResult | None:
    ent = entities(initial_data)
    qid = str(ids.get("question_id"))
    raw = ent.get("questions", {}).get(qid)
    if not raw:
        return None
    answers = _embedded_answers(ent.get("answers", {}), qid)
    return FetchResult(
        url=url,
        type=ZhihuType.QUESTION,
        title=raw.get("title", ""),
        author=parse_author(raw.get("author")),
        content_markdown=html_to_markdown(raw.get("detail", "")),
        metadata={
            "answer_count": raw.get("answerCount", raw.get("answer_count", 0)),
            "follow_count": raw.get("followerCount", raw.get("follower_count", 0)),
            "view_count": raw.get("visitCount", raw.get("visit_count", 0)),
        },
        fetched_at="",
        answers=answers,
        raw=raw,
    )


def _embedded_answers(answers_ent: dict, qid: str) -> list[EmbeddedAnswer]:
    items = []
    for aid, a in answers_ent.items():
        if str((a.get("question") or {}).get("id")) != qid:
            continue
        items.append(EmbeddedAnswer(
            answer_id=str(a.get("id", aid)),
            author=parse_author(a.get("author")),
            vote_count=a.get("voteup_count", 0),
            comment_count=a.get("comment_count", 0),
            created_at=epoch_to_iso(a.get("created_time")),
            updated_at=epoch_to_iso(a.get("updated_time")),
            url=f"https://www.zhihu.com/question/{qid}/answer/{a.get('id', aid)}",
            content_markdown=html_to_markdown(a.get("content", "")),
        ))
    items.sort(key=lambda x: x.vote_count, reverse=True)
    return items
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_parsers_question.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/zhihu/parsers/question.py tests/test_parsers_question.py
git commit -m "feat(SP-2): question parser with full-fidelity embedded answers"
```

---

## Task 8b: FetchResult.to_markdown

**Files:**
- Modify: `Engine/zhihu/src/zhihu/models.py` (replace `to_markdown` body)
- Test: `Engine/zhihu/tests/test_models.py` (add test)

- [ ] **Step 1: Add the failing test** — append to `tests/test_models.py`:

```python
def test_to_markdown_with_frontmatter():
    r = FetchResult(
        url="https://www.zhihu.com/answer/1", type=ZhihuType.ANSWER, title="T",
        author=Author(name="A"), content_markdown="Body text",
        metadata={"vote_count": 3, "comment_count": 1, "created_at": "2026-06-01T00:00:00Z",
                  "updated_at": None}, fetched_at="2026-06-01T00:00:00Z",
    )
    md = r.to_markdown(with_frontmatter=True)
    assert md.startswith("---\n")
    assert "title: T" in md
    assert "source: zhihu" in md
    assert "Body text" in md
    body_only = r.to_markdown(with_frontmatter=False)
    assert body_only == "Body text"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py::test_to_markdown_with_frontmatter -v`
Expected: FAIL — `NotImplementedError`.

- [ ] **Step 3: Replace `to_markdown`** in `src/zhihu/models.py` (top: add import; replace the method):

At the top of `models.py` add:
```python
from .markdown import render_frontmatter
```
Replace the `to_markdown` method body with:
```python
    def to_markdown(self, with_frontmatter: bool = True) -> str:
        if not with_frontmatter:
            return self.content_markdown
        meta = {
            "title": self.title,
            "author": self.author.name if self.author else None,
            "url": self.url,
            "type": self.type.value,
            "vote_count": self.metadata.get("vote_count"),
            "comment_count": self.metadata.get("comment_count"),
            "created_at": self.metadata.get("created_at"),
            "updated_at": self.metadata.get("updated_at"),
            "fetched_at": self.fetched_at,
            "source": "zhihu",
        }
        return render_frontmatter(meta) + "\n" + self.content_markdown
```

> Note: `models.py` importing `markdown.py` is acyclic (`markdown.py` imports only bs4/markdownify).

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py -v`
Expected: PASS (all).

- [ ] **Step 5: Commit**

```bash
git add src/zhihu/models.py tests/test_models.py
git commit -m "feat(SP-2): FetchResult.to_markdown with YAML frontmatter"
```

---

## Task 9: Comments (flatten + fetch)

**Files:**
- Create: `Engine/zhihu/src/zhihu/comments.py`
- Test: `Engine/zhihu/tests/test_comments.py`

> Schema: `comment_v5` root response = `{"data": [ {id, content, like_count, created_time, author:{member:{name,url_token}}, child_comments:[ {id, content, like_count, created_time, author:{member:{...}}, reply_to_author:{member:{name}}} ]} ], "paging": {"is_end": bool}}`. v1 flattens root + the inline `child_comments` (direct replies). Exhaustive child pagination via `/child_comment` is a documented v1.1 follow-up.

- [ ] **Step 1: Write the failing test** — `tests/test_comments.py`:

```python
import httpx
from zhihu.comments import flatten_comments, fetch_comments

ROOT_PAGE = {
    "data": [
        {"id": "c1", "content": "top one", "like_count": 5, "created_time": 1700000000,
         "author": {"member": {"name": "Alice", "url_token": "alice"}},
         "child_comments": [
             {"id": "c1a", "content": "reply", "like_count": 1, "created_time": 1700000001,
              "author": {"member": {"name": "Bob", "url_token": "bob"}},
              "reply_to_author": {"member": {"name": "Alice"}}},
         ]},
    ],
    "paging": {"is_end": True},
}

def test_flatten_two_layer():
    out = flatten_comments([ROOT_PAGE])
    assert [c.id for c in out] == ["c1", "c1a"]
    assert out[0].parent_id is None
    assert out[1].parent_id == "c1"
    assert out[1].reply_to_author == "Alice"
    assert out[0].author.name == "Alice"

def test_fetch_comments_paginates(httpx_mock):
    httpx_mock.add_response(
        url="https://www.zhihu.com/api/v4/comment_v5/answers/456/root_comment?order_by=score&limit=20&offset=0",
        json=ROOT_PAGE)
    out = fetch_comments("answer", "456", cookies={"d_c0": "x"}, limit=None)
    assert len(out) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_comments.py -v`
Expected: FAIL — `ModuleNotFoundError: zhihu.comments`.

- [ ] **Step 3: Write the implementation** — `src/zhihu/comments.py`:

```python
from __future__ import annotations
import httpx
from .models import Comment, Author
from ._entities import epoch_to_iso

_TYPE_PATH = {"answer": "answers", "article": "articles"}


def _author(raw: dict | None) -> Author | None:
    member = (raw or {}).get("member") or {}
    if not member:
        return None
    token = member.get("url_token")
    return Author(name=member.get("name", ""),
                  url=f"https://www.zhihu.com/people/{token}" if token else None)


def flatten_comments(root_pages: list[dict]) -> list[Comment]:
    """Flatten root comments + their inline child replies into a two-layer flat list."""
    out: list[Comment] = []
    for page in root_pages:
        for c in page.get("data", []):
            out.append(Comment(
                id=str(c.get("id")), parent_id=None, author=_author(c.get("author")),
                content=c.get("content", ""), like_count=c.get("like_count", 0),
                created_at=epoch_to_iso(c.get("created_time")),
            ))
            for ch in c.get("child_comments", []):
                reply_to = ((ch.get("reply_to_author") or {}).get("member") or {}).get("name")
                out.append(Comment(
                    id=str(ch.get("id")), parent_id=str(c.get("id")),
                    author=_author(ch.get("author")), content=ch.get("content", ""),
                    like_count=ch.get("like_count", 0),
                    created_at=epoch_to_iso(ch.get("created_time")),
                    reply_to_author=reply_to,
                ))
    return out


def fetch_comments(item_type: str, item_id: str, *, cookies: dict, limit: int | None,
                   headers: dict | None = None, page_size: int = 20) -> list[Comment]:
    """Paginate comment_v5 root_comment (plain cookies, no signature) and flatten.

    NOTE: if Zhihu returns 403 here, comment signing is hard-enforced — see design.md §9
    and the smoke gate; this function will need the RSSHub-MIT signer branch.
    """
    path = _TYPE_PATH[item_type]
    pages: list[dict] = []
    offset, collected = 0, 0
    while True:
        url = (f"https://www.zhihu.com/api/v4/comment_v5/{path}/{item_id}/root_comment"
               f"?order_by=score&limit={page_size}&offset={offset}")
        resp = httpx.get(url, cookies=cookies, headers=headers or {}, timeout=30.0)
        resp.raise_for_status()
        page = resp.json()
        pages.append(page)
        collected += len(page.get("data", []))
        offset += page_size
        if page.get("paging", {}).get("is_end", True) or (limit is not None and collected >= limit):
            break
    flat = flatten_comments(pages)
    return flat[:limit] if limit is not None else flat
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_comments.py -v`
Expected: PASS (2 cases).

- [ ] **Step 5: Commit**

```bash
git add src/zhihu/comments.py tests/test_comments.py
git commit -m "feat(SP-2): comment_v5 flatten + paginated fetch (two-layer flat)"
```

---

## Task 10: Fetcher (HTTP layer)

**Files:**
- Create: `Engine/zhihu/src/zhihu/fetcher.py`
- Test: `Engine/zhihu/tests/test_fetcher.py`

- [ ] **Step 1: Write the failing test** — `tests/test_fetcher.py`:

```python
from zhihu.fetcher import get_page, get_api_answer, NAV_HEADERS, API_HEADERS

def test_nav_and_api_headers_have_no_signature():
    assert "x-zse-96" not in {k.lower() for k in NAV_HEADERS}
    assert "User-Agent" in NAV_HEADERS
    assert API_HEADERS["x-requested-with"] == "fetch"

def test_get_page_returns_status_and_text(httpx_mock):
    httpx_mock.add_response(url="https://www.zhihu.com/answer/1", text="<html>hi</html>", status_code=200)
    status, text = get_page("https://www.zhihu.com/answer/1", cookies={"d_c0": "x"})
    assert status == 200
    assert "hi" in text

def test_get_api_answer(httpx_mock):
    httpx_mock.add_response(
        url="https://www.zhihu.com/api/v4/answers/1?include=content",
        json={"id": 1, "content": "<p>api body</p>"})
    data = get_api_answer("1", cookies={"d_c0": "x"})
    assert data["content"] == "<p>api body</p>"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_fetcher.py -v`
Expected: FAIL — `ModuleNotFoundError: zhihu.fetcher`.

- [ ] **Step 3: Write the implementation** — `src/zhihu/fetcher.py`:

```python
from __future__ import annotations
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


def get_page(url: str, *, cookies: dict, timeout: float = 30.0) -> tuple[int, str]:
    """GET a Zhihu page as a browser navigation. Returns (status_code, text). Does not raise on 4xx."""
    resp = httpx.get(url, cookies=cookies, headers=NAV_HEADERS, timeout=timeout,
                     follow_redirects=True)
    return resp.status_code, resp.text


def get_api_answer(answer_id: str, *, cookies: dict, timeout: float = 30.0) -> dict:
    """Unsigned /api/v4 answer fallback. Raises on non-2xx."""
    url = f"https://www.zhihu.com/api/v4/answers/{answer_id}?include=content"
    resp = httpx.get(url, cookies=cookies, headers=API_HEADERS, timeout=timeout)
    resp.raise_for_status()
    return resp.json()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_fetcher.py -v`
Expected: PASS (3 cases).

- [ ] **Step 5: Commit**

```bash
git add src/zhihu/fetcher.py tests/test_fetcher.py
git commit -m "feat(SP-2): HTTP fetcher (nav/api headers, no signature)"
```

---

## Task 11: Engine orchestration

**Files:**
- Create: `Engine/zhihu/src/zhihu/engine.py`
- Modify: `Engine/zhihu/src/zhihu/__init__.py` (public exports)
- Test: `Engine/zhihu/tests/test_engine.py`
- Fixture: `Engine/zhihu/tests/fixtures/answer_page.html`

- [ ] **Step 1: Create the fixture** — `tests/fixtures/answer_page.html`:

```html
<!doctype html><html><body>
<script id="js-initialData" type="text/json">{"initialState":{"entities":{"answers":{"456":{"id":456,"content":"<p>Engine body</p>","voteup_count":8,"comment_count":2,"created_time":1700000000,"updated_time":1700000000,"author":{"name":"Alice","url_token":"alice"},"question":{"id":123,"title":"Q?"}}}}}}</script>
</body></html>
```

- [ ] **Step 2: Write the failing test** — `tests/test_engine.py`:

```python
from conftest import load_fixture
from zhihu import fetch, FetchResult
from zhihu.models import ZhihuType

def test_fetch_answer_via_initialdata(httpx_mock):
    httpx_mock.add_response(url="https://www.zhihu.com/question/123/answer/456",
                            text=load_fixture("answer_page.html"), status_code=200)
    r = fetch("https://www.zhihu.com/question/123/answer/456", cookies={"d_c0": "x"})
    assert isinstance(r, FetchResult)
    assert r.type is ZhihuType.ANSWER
    assert "Engine body" in r.content_markdown
    assert r.metadata["vote_count"] == 8
    assert r.fetched_at != ""  # stamped by engine

def test_fetch_accepts_cookie_string(httpx_mock):
    httpx_mock.add_response(url="https://www.zhihu.com/question/123/answer/456",
                            text=load_fixture("answer_page.html"), status_code=200)
    r = fetch("https://www.zhihu.com/question/123/answer/456", cookies="d_c0=x; z_c0=y")
    assert r.content_markdown

def test_fetch_falls_back_to_api_on_403(httpx_mock):
    httpx_mock.add_response(url="https://www.zhihu.com/question/123/answer/456",
                            status_code=403, text="forbidden")
    httpx_mock.add_response(url="https://www.zhihu.com/api/v4/answers/456?include=content",
                            json={"id": 456, "content": "<p>API fallback body</p>",
                                  "voteup_count": 1, "comment_count": 0,
                                  "author": {"name": "Alice"}, "question": {"title": "Q?"}})
    r = fetch("https://www.zhihu.com/question/123/answer/456", cookies={"d_c0": "x"})
    assert "API fallback body" in r.content_markdown
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_engine.py -v`
Expected: FAIL — `ImportError: cannot import name 'fetch'`.

- [ ] **Step 4: Write the engine** — `src/zhihu/engine.py`:

```python
from __future__ import annotations
from datetime import datetime, timezone
from http.cookies import SimpleCookie

from .url_router import classify
from .models import ZhihuType, FetchResult, Author
from .errors import ZhihuFetchError
from .initialdata import extract_initial_data
from .markdown import html_to_markdown
from . import fetcher, comments as comments_mod
from .parsers.answer import parse_answer
from .parsers.article import parse_article
from .parsers.question import parse_question

_PARSERS = {ZhihuType.ANSWER: parse_answer, ZhihuType.ARTICLE: parse_article,
            ZhihuType.QUESTION: parse_question}
_COMMENTABLE = {ZhihuType.ANSWER: "answer", ZhihuType.ARTICLE: "article"}


def _normalize_cookies(cookies: dict | str | None) -> dict:
    if cookies is None:
        return {}
    if isinstance(cookies, dict):
        return cookies
    jar = SimpleCookie()
    jar.load(cookies)
    return {k: m.value for k, m in jar.items()}


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")


def fetch(url: str, cookies: dict | str | None = None, *, with_comments: bool = False,
          comment_limit: int | None = None, timeout: float = 30.0) -> FetchResult:
    ztype, ids = classify(url)
    jar = _normalize_cookies(cookies)
    attempts: list[str] = []

    status, text = fetcher.get_page(url, cookies=jar, timeout=timeout)
    result: FetchResult | None = None

    if status == 200:
        attempts.append("html-initialdata")
        data = extract_initial_data(text)
        if data is not None:
            result = _PARSERS[ztype](data, ids, url=url)

    if result is None and status == 403 and ztype is ZhihuType.ANSWER:
        attempts.append("api-fallback")
        result = _from_api_answer(url, ids, jar, timeout)

    if result is None:
        raise ZhihuFetchError(
            f"All fallbacks failed for {url}", url=url, attempts=attempts, status=status)

    result.fetched_at = _now_iso()

    if with_comments and ztype in _COMMENTABLE:
        item_id = ids.get("answer_id") or ids.get("article_id")
        result.comments = comments_mod.fetch_comments(
            _COMMENTABLE[ztype], item_id, cookies=jar, limit=comment_limit,
            headers=fetcher.API_HEADERS)

    return result


def _from_api_answer(url: str, ids: dict, jar: dict, timeout: float) -> FetchResult:
    data = fetcher.get_api_answer(ids["answer_id"], cookies=jar, timeout=timeout)
    author = data.get("author") or {}
    question = data.get("question") or {}
    return FetchResult(
        url=url, type=ZhihuType.ANSWER, title=question.get("title", ""),
        author=Author(name=author.get("name", "")) if author else None,
        content_markdown=html_to_markdown(data.get("content", "")),
        metadata={"vote_count": data.get("voteup_count", 0),
                  "comment_count": data.get("comment_count", 0)},
        fetched_at="", raw=data)
```

- [ ] **Step 5: Update public exports** — `src/zhihu/__init__.py`:

```python
"""Zhihu engine — one URL -> Markdown + metadata."""
from .engine import fetch
from .models import FetchResult, Author, EmbeddedAnswer, Comment, ZhihuType
from .errors import ZhihuFetchError

__all__ = ["fetch", "FetchResult", "Author", "EmbeddedAnswer", "Comment",
           "ZhihuType", "ZhihuFetchError"]
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/test_engine.py -v`
Expected: PASS (3 cases). Then full suite: `pytest -q` → all green.

- [ ] **Step 7: Commit**

```bash
git add src/zhihu/engine.py src/zhihu/__init__.py tests/test_engine.py tests/fixtures/answer_page.html
git commit -m "feat(SP-2): engine.fetch orchestration + fallback chain + public API"
```

---

## Task 12: CSS-selector fallback (body fallback 1)

**Files:**
- Modify: `Engine/zhihu/src/zhihu/engine.py` (insert CSS fallback before API fallback)
- Create: `Engine/zhihu/src/zhihu/parsers/html_scrape.py`
- Test: `Engine/zhihu/tests/test_html_scrape.py`

- [ ] **Step 1: Write the failing test** — `tests/test_html_scrape.py`:

```python
from zhihu.parsers.html_scrape import scrape_body

def test_scrape_answer_richcontent():
    html = '<div class="RichContent-inner"><p>Scraped answer</p></div>'
    assert "Scraped answer" in scrape_body(html)

def test_scrape_article_post_richtext():
    html = '<div class="Post-RichText"><p>Scraped article</p></div>'
    assert "Scraped article" in scrape_body(html)

def test_scrape_returns_none_when_no_match():
    assert scrape_body("<div>nothing useful</div>") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_html_scrape.py -v`
Expected: FAIL — `ModuleNotFoundError: zhihu.parsers.html_scrape`.

- [ ] **Step 3: Write the scraper** — `src/zhihu/parsers/html_scrape.py`:

```python
from __future__ import annotations
from bs4 import BeautifulSoup
from ..markdown import html_to_markdown

_SELECTORS = [
    ("div", {"class": "RichContent-inner"}),
    ("div", {"class": "Post-RichText"}),
    ("div", {"class": "RichText"}),
    ("div", {"class": "Post-content"}),
]


def scrape_body(html: str) -> str | None:
    """Last-resort CSS scrape of the rendered body div. None if no known container matches."""
    soup = BeautifulSoup(html or "", "lxml")
    for name, attrs in _SELECTORS:
        node = soup.find(name, attrs=attrs)
        if node:
            return html_to_markdown(str(node))
    return None
```

- [ ] **Step 4: Wire it into the engine** — in `src/zhihu/engine.py`, add import and insert the CSS fallback. Add at top: `from .parsers.html_scrape import scrape_body`. Then, immediately after the `if status == 200:` initialData block and before the 403/api block, insert:

```python
    if result is None and status == 200:
        attempts.append("html-css-scrape")
        body = scrape_body(text)
        if body:
            result = FetchResult(
                url=url, type=ztype, title="", author=None,
                content_markdown=body, metadata={}, fetched_at="", raw=None)
```

- [ ] **Step 5: Add an engine test for the CSS path** — append to `tests/test_engine.py`:

```python
def test_fetch_css_scrape_fallback(httpx_mock):
    html = '<html><body><div class="RichContent-inner"><p>CSS body</p></div></body></html>'
    httpx_mock.add_response(url="https://www.zhihu.com/answer/77", text=html, status_code=200)
    r = fetch("https://www.zhihu.com/answer/77", cookies={"d_c0": "x"})
    assert "CSS body" in r.content_markdown
```

- [ ] **Step 6: Run tests to verify pass**

Run: `pytest tests/test_html_scrape.py tests/test_engine.py -v`
Expected: PASS (all).

- [ ] **Step 7: Commit**

```bash
git add src/zhihu/parsers/html_scrape.py src/zhihu/engine.py tests/test_html_scrape.py tests/test_engine.py
git commit -m "feat(SP-2): CSS-selector body fallback in the fetch chain"
```

---

## Task 13: CLI

**Files:**
- Create: `Engine/zhihu/src/zhihu/cli.py`
- Test: `Engine/zhihu/tests/test_cli.py`

- [ ] **Step 1: Write the failing test** — `tests/test_cli.py`:

```python
import json
from pathlib import Path
from conftest import load_fixture
from zhihu import cli

def test_cli_outputs_markdown(httpx_mock, capsys, tmp_path):
    httpx_mock.add_response(url="https://www.zhihu.com/question/123/answer/456",
                            text=load_fixture("answer_page.html"), status_code=200)
    cookies_file = tmp_path / "c.json"
    cookies_file.write_text(json.dumps([{"name": "d_c0", "value": "x"}]), encoding="utf-8")
    rc = cli.main(["https://www.zhihu.com/question/123/answer/456",
                   "--cookies", str(cookies_file)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Engine body" in out
    assert "source: zhihu" in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py -v`
Expected: FAIL — `ModuleNotFoundError: zhihu.cli` / no `main`.

- [ ] **Step 3: Write the CLI** — `src/zhihu/cli.py`:

```python
from __future__ import annotations
import argparse
import json
import sys
from .engine import fetch


def _load_cookies(path: str | None) -> dict | None:
    if not path:
        return None
    raw = json.loads(open(path, encoding="utf-8").read())
    if isinstance(raw, list):  # browser-export form [{name, value}, ...]
        return {c["name"]: c["value"] for c in raw}
    return raw  # already a dict


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="zhihu", description="Fetch one Zhihu URL -> Markdown")
    parser.add_argument("url")
    parser.add_argument("--cookies", help="path to cookies.json (browser-export list or dict)")
    parser.add_argument("--comments", action="store_true")
    parser.add_argument("--no-frontmatter", action="store_true")
    args = parser.parse_args(argv)

    result = fetch(args.url, cookies=_load_cookies(args.cookies), with_comments=args.comments)
    print(result.to_markdown(with_frontmatter=not args.no_frontmatter))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/zhihu/cli.py tests/test_cli.py
git commit -m "feat(SP-2): thin CLI (python -m zhihu / zhihu entrypoint)"
```

---

## Task 14: Module docs (interface.md, README.md, architecture.md)

**Files:**
- Modify: `Engine/zhihu/docs/interface.md`
- Modify: `Engine/zhihu/docs/README.md`
- Modify: `Engine/zhihu/docs/architecture.md`

> Language policy: these are H2A (module-facing external docs) → **{user_language} = 中文** per `docs/RepoMem/persist/config.md`. Keep code identifiers / signatures ASCII.

- [ ] **Step 1: Write `docs/interface.md`** (the frozen public contract — Chinese prose, ASCII signatures):

Document exactly the §4 contract from design.md: `fetch(url, cookies, with_comments, comment_limit, timeout) -> FetchResult`; `FetchResult.to_markdown(with_frontmatter)`; the `FetchResult` / `EmbeddedAnswer` / `Comment` / `Author` fields; cookie input forms (dict | "k=v; ..." str | None); CLI `python -m zhihu <url> [--cookies] [--comments] [--no-frontmatter]`; `ZhihuFetchError` shape. State that the engine is pure-fetch (no LLM, no image download, cookies are injected input).

- [ ] **Step 2: Update `docs/README.md`** — replace the placeholder with a 1-screen: what it does, install (`pip install -e .` from `Engine/zhihu/`), a 3-line usage example, and pointers to `interface.md` + the design doc.

- [ ] **Step 3: Update `docs/architecture.md`** — replace placeholder with the §3 external architecture summary (units + the body fallback chain diagram + the "no signer" decision), pointing internal detail to `docs/RepoMem/architecture.md`.

- [ ] **Step 4: Commit**

```bash
git add Engine/zhihu/docs/interface.md Engine/zhihu/docs/README.md Engine/zhihu/docs/architecture.md
git commit -m "docs(SP-2): freeze interface.md + fill README/architecture"
```

---

## Task 15: Fixture capture + manual smoke (VERIFICATION GATE)

> This is the single mandatory verification gate (design.md §11). It needs **live injected cookies** pulled from SP-1 cookie-manager (`cookie-manager show domain=.zhihu.com`, or `GET /get/:uuid` + decrypt — meaningful: `z_c0`, `d_c0`, `__zse_ck`). Save them to a gitignored `tests/fixtures/cookies.local.json`.

- [ ] **Step 1: Acquire live cookies** and write `tests/fixtures/cookies.local.json` (browser-export list form). Confirm it is gitignored (`*.local.*` rule from Task 0).

- [ ] **Step 2: Smoke a real public answer**

Run: `python -m zhihu "<real answer url>" --cookies tests/fixtures/cookies.local.json`
Expected: YAML frontmatter + readable Markdown body. **Capture the page** for a real fixture:
```bash
python -c "import json,httpx; from zhihu.fetcher import NAV_HEADERS; \
c=json.load(open('tests/fixtures/cookies.local.json')); \
ck={x['name']:x['value'] for x in c}; \
open('tests/fixtures/real_answer.html.local','w').write(httpx.get('<real answer url>',cookies=ck,headers=NAV_HEADERS,follow_redirects=True).text)"
```
Inspect `real_answer.html.local` → confirm the `js-initialData` entity paths match Task 6's assumptions. **If they differ, fix `parsers/answer.py` + its test fixture, re-run `pytest`.**

- [ ] **Step 3: Smoke a real article and a real question**

Run the same for a `zhuanlan.zhihu.com/p/<id>` URL and a `zhihu.com/question/<id>` URL.
For the question, confirm `r.answers` is populated with **full** `content_markdown` from initialData (verifies the §1 tenet + Task 8 paths). If question initialData stores answers elsewhere, adjust `parsers/question.py._embedded_answers` + test.

- [ ] **Step 4: Smoke the comment path (settles the open empirical item)**

Run: `python -m zhihu "<real answer url>" --cookies tests/fixtures/cookies.local.json --comments`
- If comments come back → unsigned `comment_v5` works; record the result. ✅
- If it raises an HTTP **403** → comment signing is hard-enforced. **STOP and surface to the user** (sendbox blocker / chat): decide between (a) port RSSHub's MIT `x-zse-96` signer scoped to comments, or (b) ship bodies-only and document the limitation. Do **not** silently drop comments.

- [ ] **Step 5: Record smoke evidence** in `docs/RepoMem/temp/sp2-zhihu-engine/requirements.md` (update the OPEN section + smoke checklist with actual outcomes, status, and the comment_v5 verdict).

- [ ] **Step 6: Full suite + commit evidence**

Run: `pytest -q`
Expected: all green.
```bash
git add tests/fixtures/*.html tests/ src/zhihu Engine/zhihu/docs/RepoMem/temp/sp2-zhihu-engine/requirements.md
git commit -m "test(SP-2): real-fixture validation + manual smoke evidence (comment_v5 verdict recorded)"
```

---

## Self-Review

**1. Spec coverage:**
- design §1 scope (answer/article/question, cookies-as-input, optional comments, CLI) → Tasks 3,6,7,8,9,11,13 ✓
- design §1 design tenet (max extraction, consumers filter; full-fidelity embedded answers) → Task 8 ✓
- design §2 no-signer decision → Tasks 10 (no x-zse-96 in headers, asserted), 11 ✓
- design §3 architecture units → one task each ✓
- design §4 interface (signature, cookie forms, CLI, error) → Tasks 11,13,14 ✓
- design §5 models incl. flat two-layer comments → Tasks 2,9 ✓
- design §6 URL-type behavior → Tasks 3,6,7,8 ✓
- design §8 markdown + frontmatter (remote images) → Tasks 5,8b ✓
- design §9 fallback chain (initialData → CSS → /api/v4) + comment signing branch → Tasks 11,12,15 ✓
- design §10 packaging (httpx/bs4/lxml/markdownify, pyproject, src-layout) → Task 0 ✓
- design §11 testing + mandatory smoke → all tasks (TDD) + Task 15 ✓

**2. Placeholder scan:** No "TBD/TODO/handle edge cases" steps; every code step shows complete code. The one runtime `NotImplementedError` (Task 2 `to_markdown`) is deliberately replaced in Task 8b and tested. Task 14 prose-doc steps reference exact §-numbers of design.md to copy from (H2A Chinese), which is content-complete instruction, not a placeholder.

**3. Type consistency:** `fetch(url, cookies, with_comments, comment_limit, timeout)` consistent across Tasks 11/13/14. `FetchResult` fields (`url,type,title,author,content_markdown,metadata,fetched_at,answers,comments,raw`) consistent across Tasks 2,6,7,8,11,12. `EmbeddedAnswer`/`Comment` fields consistent Tasks 2,8,9. `classify() -> (ZhihuType, ids)` consistent Tasks 3,11. `get_page() -> (status, text)`, `get_api_answer() -> dict` consistent Tasks 10,11. `html_to_markdown`/`render_frontmatter` consistent Tasks 5,8b,6,7,8,12. `flatten_comments`/`fetch_comments` consistent Tasks 9,11.

---

**End of SP-2 plan.**
