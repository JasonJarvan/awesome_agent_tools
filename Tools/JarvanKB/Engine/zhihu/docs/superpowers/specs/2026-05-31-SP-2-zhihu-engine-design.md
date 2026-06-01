# SP-2 — Zhihu Engine Design

> **Status**: draft (awaiting user review)
> **Date**: 2026-05-31
> **Author**: SP2Impler session (Claude Opus 4.8), child-handoff under sendbox-protocol
> **Module**: `Engine/zhihu/`
> **Scope**: a pure-fetch Python library that turns ONE Zhihu URL (answer / article / question)
> into clean Markdown + structured metadata, consuming injected cookies.
> **Audience**: A2A (English per `docs/RepoMem/persist/config.md` language policy).

---

## 1. Purpose & scope

`Engine/zhihu/` is a **pure-fetch library**. Single URL in → one structured result out
(`FetchResult`: Markdown body + metadata, optional flat comments). It does **not** summarize,
translate, classify, save files, download images, poll favorites, or call an LLM. Those belong to
the SP-3 Skill, SP-5a Watcher, and SP-6 CrawlMdSaver layers.

### In scope (v1)
- Fetch one Zhihu URL → Markdown body + metadata (title, author, vote/comment counts, timestamps,
  url, fetched_at).
- Three URL types: **answer**, **article** (专栏), **question**.
- **Cookies injected as INPUT** (`dict | str | None`). The engine never fetches cookies from
  cookie-manager itself — that is the SP-3 Skill / SP-5a Watcher's job (see §7). Keeps the engine
  pure + unit-testable.
- **Comments** (optional, per-call): two-layer **flat** schema (top-level comments + their direct
  child replies as a flat list with a `parent_id` field). No custom comment tree.
- Importable Python API (frozen in `docs/interface.md`) + a thin CLI for manual testing.

### Out of scope (deferred / not ours)
- ❌ No summarization / translation / classification (SP-3 Skill, via `Engine/common` LLMClient).
- ❌ No favorites-folder polling / collection pagination (SP-5a Watcher — it iterates
  `/api/v4/collections/{id}/items` then calls this engine's `fetch()` per URL).
- ❌ No multi-page crawl / search / feed — single URL in, one page out.
- ❌ No image download / local-asset rewriting (SP-6 CrawlMdSaver / Skill layer). The engine emits
  standard Markdown with **remote** image URLs.

### Relationship to the reference project
The user's own `JasonJarvan/Zhihu-Collections-MCP` is the empirical reference. Its single-page fetch
maps to **SP-2**; its `/api/v4/collections/{id}/items` pagination maps to **SP-5a**. We **reimplement**
the approach rather than lift code (the reference is unlicensed = all-rights-reserved; JarvanKB targets
MIT OSS). Key empirical lesson it proves: **the x-zse-96 signature can be sidestepped** — authenticated
page-navigation GETs render the body server-side, and several `/api/v4/*` endpoints accept plain cookies.

---

## 2. The zse-96 decision (settled)

Zhihu gates its `/api/v4/*` AJAX API behind an `x-zse-96` request signature computed by obfuscated
browser JS. Three ways to produce it exist (real browser; extract+run the sign JS; pure-Python port).
**We produce none of them.** Per the reference project's lived experience and the user's direction:

> **Decision: pure cookie + HTTP, no browser, no signer.** Page-navigation HTML is the primary source
> (server-rendered, no signature needed); unsigned `/api/v4/*` endpoints that accept plain cookies are
> fallbacks. A signer is introduced **only if** empirical smoke proves a required endpoint (likely
> comments) hard-enforces the signature — and then by porting RSSHub's **MIT-licensed** `x-zse-96`
> implementation, not MediaCrawler's (NON-COMMERCIAL license — must not vendor).

Rationale: lightest runtime, headless-server-trivial, fully unit-testable, lowest maintenance, and it
matches a path the user has already run in production.

---

## 3. Architecture

Each unit has one job; everything except the HTTP layer is a pure function (fixture in → value out),
which is what makes the engine unit-testable without network.

| Unit | Responsibility | I/O? |
|---|---|---|
| `url_router` | classify URL → `(type, ids)`; reject unsupported | pure |
| `fetcher` | HTTP layer: inject cookies, GET page/API, realistic headers, retries, polite delay, 403 fallback chain | **network** |
| `initialdata` | extract & parse the `<script id="js-initialData">` JSON blob from page HTML | pure |
| `parsers/answer.py`, `article.py`, `question.py` | initialData/HTML/API payload → structured item | pure |
| `comments` | fetch `comment_v5` top-level + child replies, flatten to two-layer list | **network** |
| `markdown` | body HTML → Markdown (`markdownify` subclass; remote image URLs, references → footnotes) | pure |
| `models` | dataclasses: `Author`, `Comment`, `AnswerPreview`, `FetchResult` | — |
| `engine` | orchestrate `fetch(url, cookies, with_comments, ...)` | — |
| `cli` | thin CLI for manual testing | — |

Data flow:
```
url ─► url_router ─► fetcher (GET page HTML, cookies injected)
                         │
                         ▼
                   initialdata.parse ──► parsers/<type> ──► markdown ─┐
                         │ (missing / shape changed)                  │
                         ▼                                            ▼
                   CSS-selector scrape (fallback 1)            FetchResult
                         │ (403)                                      ▲
                         ▼                                            │
                   /api/v4 unsigned API (fallback 2) ────────────────┘
                         │ (all fail)
                         ▼
                   raise ZhihuFetchError(diagnostics)

with_comments=True ─► comments.fetch (comment_v5, unsigned) ─► flat list ─► FetchResult.comments
```

---

## 4. Public interface (frozen contract — mirrored to `docs/interface.md`)

```python
from zhihu import fetch, FetchResult, ZhihuFetchError

result: FetchResult = fetch(
    url: str,
    cookies: dict | str | None = None,   # d_c0 / z_c0 / __zse_ck; None = best-effort anonymous
    with_comments: bool = False,         # per-call; default off
    comment_limit: int | None = None,    # None = paginate all; else cap
    timeout: float = 30.0,
)

md: str = result.to_markdown(with_frontmatter=True)
```

CLI: `python -m zhihu <url> [--cookies cookies.json] [--comments] [--no-frontmatter]`

Cookie input accepts either a `dict` (`{"d_c0": ..., "z_c0": ...}`) or a raw Cookie header `str`
(`"d_c0=...; z_c0=..."`); both normalize to the same jar. `None` runs anonymous (public content only,
best-effort). Errors raise `ZhihuFetchError` carrying the URL, the fallback chain attempted, and the
last HTTP status — never silent `-1` sentinels.

---

## 5. Data model

```
FetchResult:
    url:              str
    type:             "answer" | "article" | "question"
    title:            str
    author:           Author | None
    content_markdown: str                  # body; "" for thin question detail
    metadata:         dict                  # vote_count, comment_count, created_at,
                                            # updated_at, view_count?, follow_count? ...
    answers_preview:  list[AnswerPreview]   # question type only; [] otherwise
    comments:         list[Comment]         # [] unless with_comments=True
    fetched_at:       str (ISO-8601)
    raw:              dict | None           # optional raw initialData/API slice, for debugging

Author:        name, url, headline?
AnswerPreview: answer_id, author, vote_count, excerpt, url     # preview only, NOT full body
Comment:       id, parent_id (None = top-level), author, content, like_count,
               created_at, reply_to_author?
```

Comments are a **flat two-layer list**: each top-level comment, then its direct child replies, all in
one list, related by `parent_id`. Zhihu itself flattens reply-to-reply chains under the root, so two
layers is the complete model. No tree construction.

---

## 6. URL-type behavior

| Type | URL shapes | Returns |
|---|---|---|
| **answer** | `…/question/{qid}/answer/{aid}`, `/answer/{aid}` | answer body Markdown + author + vote/comment counts + timestamps |
| **article** | `zhuanlan.zhihu.com/p/{pid}`, `/p/{pid}` | article body Markdown + author + counts + timestamps |
| **question** | `…/question/{qid}` (no `/answer/`) | question title + detail body + counts (`answer_count`, `follow_count`, `view_count`) **+ `answers_preview`** |

**Question handling (resolved with user):** a question page is fetched for its own value — title,
detail, counts — **plus** a top-answers **preview** list (`AnswerPreview`: author, vote_count, excerpt,
answer URL) extracted from the **same `js-initialData`** the page already ships. This is zero extra
requests, non-redundant (previews, not full bodies), and gives the discussion landscape at a glance.
The engine does **not** fetch full bodies of all answers (that is redundant — fetch a specific answer
URL for that) and does **not** paginate beyond the first page's embedded answers.

---

## 7. Cookie-injection boundary

The engine is a pure consumer of injected cookies. The meaningful Zhihu cookies are **`z_c0`** (login
token), **`d_c0`** (device id), **`__zse_ck`** (anti-bot). Who *sources* them from SP-1 cookie-manager
(`Service/crawl/cookie-manager/docs/interface.md` — pull `show domain=.zhihu.com` / `GET /get/:uuid`
+ decrypt, or a push hook writing a file) is the **SP-3 Skill / SP-5a Watcher's** job. This keeps the
engine free of the cookie-manager dependency and trivially unit-testable. (See
`docs/RepoMem/persist/architecture/credentials.md`.)

---

## 8. Markdown & frontmatter

`markdownify` subclassed: images → standard `![](remote-url)` (**no download**); Zhihu reference links
→ footnotes `[^n]`; `<style>` stripped. `to_markdown(with_frontmatter=True)` prepends YAML:

```yaml
title, author, url, type, vote_count, comment_count,
created_at, updated_at, fetched_at, source: zhihu
```

(Frontmatter field set approved by user.)

---

## 9. Fetch strategy & anti-bot posture

- **Body fallback chain:** initialData JSON (primary) → CSS-selector scrape of
  `RichContent-inner` / `Post-RichText` (fallback 1) → unsigned `/api/v4/answers/{id}?include=content`
  (fallback 2, on 403) → `ZhihuFetchError`.
- **Comments:** `/api/v4/comment_v5/{answers|articles}/{id}/root_comment` +
  `/comment/{cid}/child_comment`, plain cookies, paginated by `offset`/`limit`. **If a real 403 proves
  the signature is hard-enforced here**, the smoke gate (§11) decides between (a) porting RSSHub's MIT
  `x-zse-96` signer scoped to comments only, or (b) documenting the limitation and shipping bodies-only.
- **Posture:** realistic browser header set (a navigation set for HTML, an xhr set for API), a small
  randomized delay between comment-pagination requests. No proxy rotation in v1.

---

## 10. Dependencies & packaging

- Runtime: `httpx` (HTTP/2 — closer to a real browser, and async-ready for the SP-5a watcher),
  `beautifulsoup4`, `lxml`, `markdownify`.
- Dev: `pytest`, `pytest-httpx` (or `respx`) for network mocking.
- New `Engine/zhihu/pyproject.toml` so the module is independently installable (OSS-split-ready).
  Package source under `Engine/zhihu/src/`; tests under `Engine/zhihu/tests/`.
- **No dependency on `Engine/common` LLMClient** — SP-2 is pure fetch.

---

## 11. Testing strategy (TDD)

- **Pure unit tests** (no network), on captured fixtures (real HTML pages + initialData JSON + API
  JSON): `url_router`, `initialdata` parse, each `parsers/*`, `markdown` conversion, comment flattening,
  `to_markdown` frontmatter.
- **Network tests:** mock the HTTP layer (`pytest-httpx`/`respx`) — exercise the 403 fallback chain and
  comment pagination against recorded payloads.
- **Mandatory manual smoke (verification gate):** with live injected cookies, fetch one real public
  **answer**, one **article**, one **question**; show the Markdown + metadata; exercise the comment
  path (and thereby settle the comment_v5 signing question empirically).

---

## 12. Self-review

| Check | Result |
|---|---|
| **Placeholder scan** | No TBD/TODO. The single deferred-to-smoke item (comment_v5 signing) is explicitly framed as a §11 empirical gate with two pre-decided branches, not an open placeholder. |
| **Internal consistency** | §3 architecture ↔ §4 interface ↔ §5 model ↔ §9 fetch chain align; question-`answers_preview` appears in §5/§6 consistently; "no signer / no image download / no LLM" repeated identically across §1/§2/§7/§8. |
| **Scope check** | Single module, single implementation plan. Favorites/collections explicitly pushed to SP-5a; image localization to SP-6. |
| **Ambiguity** | URL-type routing table (§6) disambiguates question vs answer; cookie input forms (§4) explicit; comment schema (§5) explicitly flat-two-layer. |

---

**End of SP-2 design.md**
