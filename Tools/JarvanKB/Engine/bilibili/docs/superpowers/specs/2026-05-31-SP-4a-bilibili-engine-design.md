# SP-4a — Bilibili Engine Design

> **Status**: draft (awaiting user review)
> **Date**: 2026-05-31
> **Author**: SP4aImpler session (Claude Opus 4.8, 1M context), child-handoff under sendbox-protocol
> **Module**: `Engine/bilibili/`
> **Scope**: a Python library that turns ONE Bilibili video reference (BV id / URL / aid) into clean
> Markdown + structured data: metadata + a transcript (subtitle-first, ASR fallback) + BiliNote's AI
> summary as a best-effort byproduct. Consumes injected credentials; delegates ASR + summarization to a
> self-hosted BiliNote (BN) Docker instance over HTTP.
> **Audience**: A2A (English per `docs/RepoMem/persist/config.md` language policy).

---

## 1. Purpose & scope

`Engine/bilibili/` is a **transcription library** and a **BiliNote HTTP client**. Single video reference
in → one structured result out (`BilibiliResult`: metadata + transcript + optional AI summary). It does
**not** poll favorites, wrap itself as a Skill, call an LLM directly, download/clip full video, or fetch
its own credentials. Those belong to the SP-4b Skill, SP-5b Watcher, SP-6 CrawlMdSaver, and SP-1
CookieManager layers.

### Design tenet — engine orchestrates, BN does the heavy lifting
The engine owns the **subtitle-first cascade** (so the path taken is observable + unit-testable) and
fetches metadata itself via `bilibili-api-python`. The expensive, license-heavy work — audio extraction,
ASR, and LLM note generation — is delegated to a **self-hosted BiliNote (BN) Docker instance** consumed
over its HTTP API. The engine is a thin, well-bounded client of BN; it never reimplements BN's pipeline.

### Relationship to sibling SP-2 (Zhihu Engine)
Same structural philosophy as `Engine/zhihu/`: **each unit has one job; network lives only in the HTTP
layer; everything else is a pure function** (fixture in → value out), so the engine is unit-testable
without network. Public API mirrors SP-2's frozen style: `from bilibili import ...`.

**Notable divergence from SP-2:** Zhihu Engine is pure-fetch and never touches an LLM (summarization is
pushed to the SP-3 Skill). Bilibili Engine necessarily routes through BN, which runs an LLM summary as
part of its bundled pipeline — you cannot get BN's ASR transcript out without it also producing the note.
The **engine itself still never calls an LLM** (satisfies the handoff invariant); the summary is BN's
byproduct, surfaced as a best-effort `summary_markdown`.

### In scope (v1)
- **Metadata** via `bilibili-api-python` (`Video.get_info`): title, up (owner), bvid, aid, cid, duration,
  pubdate, cover. `cid` is required downstream for subtitle fetch.
- **Transcript via a subtitle-first cascade, engine-driven:**
  1. **Subtitle first** — `bilibili-api-python.get_subtitle(cid)` → fetch the subtitle JSON → segments.
     Zero-cost when present. Sets `transcript.source = "subtitle"`.
  2. **ASR fallback** — submit the video URL to **BN with `TRANSCRIBER_TYPE=bcut`** (B站必剪 free cloud
     ASR). BN downloads audio + runs bcut. Sets `transcript.source = "asr"`.
- **AI summary** (best-effort) — BN's generated note Markdown, captured as `summary_markdown`. Chapters,
  when present, live as headings **within** that Markdown (BN exposes no separate structured chapters).
- **Output**: structured `BilibiliResult` + a `render()` that emits Markdown (transcript + summary) with
  configurable switches (§4).
- Importable Python API (frozen in `docs/interface.md`) + a thin CLI for manual testing.

### Out of scope (deferred / not ours)
- ❌ **NO 通义听悟 (Tingwu) / Aliyun OSS / yt-dlp-audio-pipeline owned by the engine.** That was the
  pre-R5 design and is **SUPERSEDED** (see `version-plan.md` + `credentials.md`). R5 switched ASR to
  **BiliNote + bcut**. `crawl-pipeline.md`'s Bilibili section is R5-superseded — ignored entirely.
- ❌ No full-video download / clipping (BN extracts audio internally; the engine never does).
- ❌ No summarization via `Engine/common` LLMClient (the engine does not call an LLM; BN does).
- ❌ No favorites polling (SP-5b Watcher) / no Skill wiring (SP-4b).
- ❌ No multi-part (分P) full enumeration — v1 handles the single part referenced (first `cid`, or the
  `?p=` part in the URL). Full multi-P is v2+.

---

## 2. Key decisions (settled)

| Dimension | Decision | Rejected alternative |
|---|---|---|
| BN role | Engine is a **BN HTTP client**; BN does ASR (bcut) + LLM summary | ❌ Engine speaks the bcut cloud API directly (re-implements BN's upload/poll; loses BN's subtitle cascade + summary) |
| Cascade ownership | **Engine-driven** — engine fetches metadata + subtitle, decides path | ❌ BN-driven (engine blind to which path was taken; smoke can't prove it) |
| BN LLM provider | **Manual config** — engine reads `provider_id` + `model_name` from `config/bilibili-engine.yaml`; engine is a pure read-side consumer of BN, never writes BN's provider DB | ❌ Auto-register via `POST /api/provider/add_provider` (couples engine to BN's provider API; idempotency + holding the LLM api_key) |
| Cookie → BN | **best-effort push** of SESSDATA to BN (`POST /api/update_downloader_cookie`) on the ASR path, to cover member/charged videos | ❌ Never push (restricted-video ASR fails) |
| Credential input | **Structured** `BilibiliCredential(sessdata, bili_jct?, buvid3?)` (exactly what `bilibili-api-python` needs); BN cookie string derived from it | ❌ Raw cookie string only (harder to test; engine would re-parse) |
| **BN dependency in v1** | **Hard-required; both paths route through BN; summary always produced** | ❌ BN-optional subtitle path / `summarize=False` (→ v2+) |

### 2.1 BN is a hard dependency in v1 (both paths produce a summary)

The render layer supports **progressive disclosure**: `split_transcript=True` makes the main file an
**index** (frontmatter + AI summary + chapter headings) that links to a separate transcript file. The
summary IS the index layer. If a subtitle-path video skipped BN, it would have no summary → no index →
the progressive-disclosure mode would be empty for those videos. To keep output **consistent** (every
video has a summary regardless of path), the subtitle path also routes through BN — by passing the
already-fetched subtitle as BN's `prefetched_transcript`, BN **skips download + ASR** and runs **only**
the LLM summary (zero ASR cost, one LLM call). Consequence: every video incurs one BN summary call and
requires BN online. The "BN-optional / `summarize=False` offline mode" is explicitly deferred to v2+.

### 2.2 BN exposes no structured chapters

`NoteResult` from BN is `{ markdown, transcript, audio_meta }`. There is no separate chapters array;
chapter structure (when the LLM produces it) lives as headings inside `markdown`. v1 therefore models
"summary + chapters" as a single `summary_markdown: Optional[str]`. Extracting structured chapters is
v2+.

---

## 3. Architecture

Each unit has one job; network is confined to three units (`metadata`, `subtitle`, `bilinote_client`);
the rest are pure and fully unit-testable without a live BN or network.

| Unit | Responsibility | I/O |
|---|---|---|
| `url_parser` | classify + normalize a video reference (BV id / `bilibili.com` URL / aid) → `(bvid, part?)`; reject unsupported | pure |
| `models` | dataclasses: `BilibiliMetadata`, `TranscriptSegment`, `Transcript`, `BilibiliResult`, `BilibiliCredential`, `EngineConfig`, `RenderOptions`, `RenderedOutput` | — |
| `metadata` | `bilibili-api-python` `Video.get_info` → `BilibiliMetadata` (title, up, bvid, aid, cid, duration, pubdate, cover) | **network** |
| `subtitle` | `get_subtitle(cid)` → pick best track (prefer `zh`, then AI CC) → fetch `subtitle_url` JSON → `Transcript(source="subtitle")` or `None` when no track | **network** |
| `bilinote_client` | BN HTTP: `push_cookie`, submit `generate_note` (with/without `prefetched_transcript`), poll `task_status`, parse `NoteResult` → `(transcript?, summary_markdown)` | **network** |
| `engine` | orchestrate the cascade: `BilibiliEngine.transcribe(...)` | — |
| `render` | prose-merge, frontmatter, timestamps, split/index → `RenderedOutput` | **pure** |
| `config` | load `config/bilibili-engine.yaml` → `EngineConfig` | file |
| `cli` | thin CLI for manual testing | — |

### Data flow

```
video_ref ─► url_parser ─► bvid (+ optional part)
                            │
                  metadata.fetch(bvid, cred) ─► BilibiliMetadata (incl. cid)
                            │
                  subtitle.fetch(cid, cred) ─► Transcript?  (source="subtitle")
                            │
        ┌── subtitle found ─► bilinote_client.generate(url, prefetched_transcript=subtitle)
        │                         └─► BN skips download+ASR, runs LLM summary only ─► summary_markdown
        │
        └── no subtitle ───► bilinote_client.push_cookie(cred)        [best-effort, decision (a)]
                             bilinote_client.generate(url) ─► poll task_status ─► NoteResult
                                   ├─ transcript (source="asr", from bcut)
                                   └─ summary_markdown
                            │
                  BilibiliResult(metadata, transcript, summary_markdown)
                            │
                  result.render(opts) ─► RenderedOutput(main_markdown, transcript_markdown?, suggested_names)
```

### BiliNote API surface consumed (verified against upstream `JefferyHcool/BiliNote`)

All routers are mounted under the `/api` prefix (verified: `backend/app/__init__.py`), and every response
is wrapped by `ResponseWrapper` as `{ code, msg, data }` (`code == 0` = success) — the client unwraps `data`.

- `POST /api/generate_note` — body (`VideoRequest`): `video_url`, `platform="bilibili"`,
  `quality` (`DownloadQuality` ∈ `fast`/`medium`/`slow`; engine uses `fast` — audio-only is enough for ASR),
  `model_name`, `provider_id`, optional `prefetched_transcript={language, full_text, segments[{start,end,text}]}`,
  optional `format=[]`, `style`, `screenshot=false`, `link=false`. Returns `data={ task_id }`. When
  `prefetched_transcript` is supplied, BN writes it to its transcript cache and skips download + ASR.
- `GET /api/task_status/{task_id}` — returns `data={ status, message?, result? }`. `status` ∈
  `PENDING/PARSING/DOWNLOADING/TRANSCRIBING/SUMMARIZING/FORMATTING/SAVING/SUCCESS/FAILED`. On `SUCCESS`,
  `result` = `NoteResult` (`{ markdown, transcript:{language, full_text, segments[]}, audio_meta }`).
- `POST /api/update_downloader_cookie` — body `{ platform:"bilibili", cookie:"<string>" }`.
  The only way to give BN a cookie (BN has no per-request cookie field). Used on the ASR path.
- `GET /api/sys_health` (or `/api/sys_check`) — readiness probe; used by `bilinote_client` to fail fast
  with `BiliNoteUnavailable` when BN is unreachable.

> Note: bcut needs **no** cookie itself; the cookie matters only for BN's yt-dlp audio download of
> member/charged content. `TRANSCRIBER_TYPE=bcut` is set in **BN's** environment by the user at deploy
> time (§6) — the engine does not configure BN's transcriber.

---

## 4. Public interface (frozen contract — mirrored to `docs/interface.md`)

```python
from bilibili import (
    BilibiliEngine, BilibiliCredential, EngineConfig, RenderOptions,
    BilibiliResult, transcribe, BilibiliEngineError,
)

cred = BilibiliCredential(sessdata="...", bili_jct=None, buvid3=None)  # sessdata required; others optional

# Construct from config file (config/bilibili-engine.yaml) ...
engine = BilibiliEngine.from_config()
# ... or explicitly:
engine = BilibiliEngine(EngineConfig(
    bn_base_url="http://127.0.0.1:3015",
    provider_id="<from BN web UI>",
    model_name="gpt-4o-mini",
    poll_interval_s=3,
    poll_timeout_s=600,
    style="summary",
))

result: BilibiliResult = engine.transcribe("BV1xx...", credential=cred)

result.metadata.title           # str
result.metadata.cid             # int
result.transcript.source        # "subtitle" | "asr"
result.transcript.language      # str | None
result.transcript.full_text     # str
result.transcript.segments      # list[TranscriptSegment(start: float, end: float, text: str)]
result.summary_markdown         # str | None   (BN's AI note; chapters as headings within)

rendered = result.render(RenderOptions(
    include_transcript=True,     # default True
    include_timestamps=False,    # default False → readable prose
    split_transcript=False,      # default False → transcript inline in one file
    slug=None,                   # default = bvid; used for split filenames + the inline link
))
rendered.main_markdown          # str
rendered.transcript_markdown    # str | None   (non-None only when split_transcript=True)
rendered.suggested_names        # {"main": "<slug>.md", "transcript": "<slug>.transcript.md"}

# convenience: transcribe(...) builds a default engine (from config file, or a passed EngineConfig)
# and returns a BilibiliResult, so .to_markdown() / .render() chain off it
md: str = transcribe("BV1xx", credential=cred).to_markdown()   # == render(default).main_markdown
```

**Stability**: the constructors, `BilibiliCredential`, `EngineConfig`, `RenderOptions`,
`transcribe()`, `engine.transcribe()`, `result.render()`, `result.to_markdown()`, and the dataclass
field names above are the **v1 frozen contract**. Internals may change freely behind them.

**Packaging**: `Engine/bilibili/src/bilibili/` is the `bilibili` package (src-layout, `pyproject.toml`),
installable with `pip install -e .` so `from bilibili import ...` resolves. This mirrors SP-2's frozen
public-import convention.

---

## 5. Output rendering

Switches and their defaults (settled with the user):

| Switch | Default | Effect |
|---|---|---|
| `include_transcript` | **True** | whether the transcript body appears in output at all |
| `include_timestamps` | **False** | False → segments merged into **readable paragraphs**; True → `[mm:ss] text` list |
| `split_transcript` | **False** | True → main file = frontmatter + summary + chapter headings (the **index**) + a relative link to a separate transcript file; transcript body returned in `transcript_markdown`. False → transcript inlined in the main file |

**Interaction rules:**
- `include_transcript=False` → `split_transcript` is moot (ignored); main = frontmatter + summary only.
- **Progressive disclosure = `include_transcript=True` + `split_transcript=True`**: summary/chapters are
  the index layer; the transcript file is the detail layer.

**Readable-prose merge (the key rendering concern, no LLM):** when `include_timestamps=False`, segment
fragments are merged into flowing paragraphs by a **deterministic heuristic** — concatenate consecutive
segment texts; insert a paragraph break when the inter-segment time gap exceeds a threshold OR when the
accumulated paragraph length exceeds a character budget. Chinese text (no inter-word spaces) is joined
without inserted spaces; latin text is space-joined. No LLM is used (handoff invariant). When
`include_timestamps=True`, the transcript degrades to a `[mm:ss] text` list (one line per segment or
per merged chunk).

**Engine purity — render returns content, never writes files.** Splitting is a layout choice expressed
as *which strings are returned*, not as file I/O. `render()` returns `RenderedOutput`:
- `main_markdown: str` — always present.
- `transcript_markdown: str | None` — non-None only when `split_transcript=True`.
- `suggested_names: dict` — `{"main": "<slug>.md", "transcript": "<slug>.transcript.md"}`; the caller
  (thin CLI / SP-4b / SP-5b / SP-6) decides final paths and writes the files.

**Default frontmatter** (YAML) includes: `bvid`, `title`, `up`, `url`, `duration`, `pubdate`,
`transcript_source`.

---

## 6. Credential integration & BiliNote deployment

### 6.1 Credentials (input only)
The engine accepts a structured `BilibiliCredential(sessdata, bili_jct?, buvid3?)` as **input** and never
fetches credentials itself (keeps it pure + testable). `sessdata` feeds `bilibili-api-python` for
metadata + subtitle (AI subtitles require a logged-in session). On the ASR path, a cookie string derived
from the credential is **best-effort pushed** to BN. Downstream SP-4b Skill / SP-5b Watcher obtain
credentials from **SP-1 CookieManager** (`domain=.bilibili.com`, see
`Service/crawl/cookie-manager/docs/interface.md`) and inject them here — the engine does not depend on
SP-1.

### 6.2 BiliNote deployment (Stage-2 → Stage-3 gate, Dashboard UN-018)
BN is a third-party self-hosted Docker tool consumed as a client. Running it is a **USER action** (per
the SP-1 precedent "起 Docker 容器是 user 操作"). Deliverables produced by this module:
- `Engine/bilibili/deploy/bilinote/docker-compose.yml` + `.env.example` — minimal compose that pulls
  BN's published image and sets `TRANSCRIBER_TYPE=bcut` + ports; **does not vendor BN's full source**.
- `Engine/bilibili/deploy/bilinote/README.md` — runbook pointing to upstream `JefferyHcool/BiliNote`,
  the one-time LLM-provider setup in BN's web UI, and how to read back `provider_id` for the engine
  config.

At the gate, the implementer writes a blocker letter
(`docs/sendbox/toOrchestrator/from-sp4aimpler-blocker-bn-docker.md`) and tracks Dashboard **UN-018**,
asking the user to bring BN up and confirm its endpoint. Stage 1/2 are NOT blocked on this.

### 6.3 Engine config
`config/bilibili-engine.example.yaml` (committed) / `config/bilibili-engine.yaml` (gitignored), mirroring
SP-1's config pattern:

```yaml
bilinote:
  base_url: http://127.0.0.1:3015     # BN nginx APP_PORT
  provider_id: ""                     # paste from BN web UI after configuring an LLM provider
  model_name: "gpt-4o-mini"
  poll_interval_s: 3
  poll_timeout_s: 600                  # bcut ASR can run for minutes
  style: "summary"                     # BN note style
# credentials are NOT stored here — passed as input / sourced from SP-1 cookie-manager
```

---

## 7. Error handling

All raise a subclass of `BilibiliEngineError`:

| Error | Raised when |
|---|---|
| `InvalidVideoRef` | `url_parser` cannot resolve a bvid from the input |
| `CredentialError` | `sessdata` missing/expired where required (metadata/subtitle 4xx) |
| `BiliNoteUnavailable` | BN health probe fails / connection refused (the Stage-3 gate, surfaced clearly) |
| `TranscriptionFailed` | BN `task_status` returns `FAILED` (wraps BN's `message`) |
| `TranscriptionTimeout` | polling exceeds `poll_timeout_s` |

The subtitle path returning no track is **not** an error — it is the normal trigger for the ASR fallback.

---

## 8. Testing strategy (TDD)

- **Pure units first** (`render` incl. prose-merge + split, `url_parser`, `models`): write tests before
  code; full coverage with no network.
- **Network units** (`metadata`, `subtitle`, `bilinote_client`): unit-test against **mocked HTTP +
  recorded fixtures** — real `get_info` JSON, real subtitle JSON, real BN `generate_note` /
  `task_status` responses. No live calls in the unit suite.
- **Cascade** (`engine`): mock the three network units → assert the subtitle path feeds
  `prefetched_transcript` and sets `source="subtitle"`; the no-subtitle path pushes the cookie + submits
  the full job and sets `source="asr"`.
- **Mandatory manual smoke (Stage 3, against a live BN)** — handoff requirement: one BV **with** a
  subtitle → subtitle path; one BV **without** → bcut ASR path; show the rendered Markdown for both.

---

## 9. Out of scope — v2+ futures

Explicitly NOT in v1:
- **Smart switches** (user's idea): logic that auto-decides switch values — e.g. auto-`split` when the
  transcript exceeds N characters; auto-enable timestamps for certain content types.
- **BN-optional subtitle path / `summarize=False` offline mode**: skip BN entirely when only the raw
  transcript is wanted (no LLM cost, no BN dependency for subtitle videos).
- **Multi-part (分P) full enumeration**: v1 handles the single referenced part.
- **Structured chapters extraction** from BN's note Markdown; deep-linking chapters → transcript anchors.
- BN's `link`/`screenshot` note formats (timestamped clickable chapters, frame screenshots).

---

## 10. Dependencies

- `bilibili-api-python` (>= 17.x) — metadata + subtitle; fully async (the engine wraps the async calls).
- `httpx` (or `requests`) — BN HTTP client.
- `PyYAML` — config loading.
- `pytest` (+ `respx`/`httpx` mock or `responses`) — tests.
- Packaging: src-layout `pyproject.toml`, package name `bilibili`.

---

## 11. File layout

```
Engine/bilibili/
├── pyproject.toml                      # package "bilibili", src-layout
├── src/bilibili/
│   ├── __init__.py                     # public API exports (§4)
│   ├── models.py
│   ├── url_parser.py
│   ├── metadata.py                     # bilibili-api-python get_info
│   ├── subtitle.py                     # get_subtitle(cid) + fetch subtitle JSON
│   ├── bilinote_client.py              # BN HTTP client
│   ├── engine.py                       # BilibiliEngine.transcribe cascade
│   ├── render.py                       # RenderedOutput, prose-merge, split
│   ├── config.py                       # EngineConfig loader
│   └── cli.py                          # thin CLI
├── tests/                              # pytest; fixtures under tests/fixtures/
├── deploy/bilinote/                    # docker-compose.yml + .env.example + README (the gate)
└── docs/
    ├── interface.md                    # frozen public contract (mirror of §4)
    ├── architecture.md                 # external summary
    ├── README.md
    └── RepoMem/{architecture,decisions}.md
```

(Engine config lives at repo root `config/bilibili-engine.{yaml,example.yaml}`, per SP-1's pattern.)
