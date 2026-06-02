# SP-5a — Zhihu Watcher — Design

> **Status**: approved (user OK 2026-06-02)
> **Date**: 2026-06-02
> **Author**: SP5aImpler (Claude Code session, child of ZhihuCrawl SubOrche)
> **Module**: `Service/crawl/zhihu-watcher/` (type=service)
> **Scope**: a standalone daemon that polls the user's Zhihu favorites/collection folder(s) on a
> schedule, detects newly-favorited items, fetches each via the frozen SP-2 engine, and saves
> Markdown to a configured output dir. No user interaction (it is a daemon).

---

## 1. Background & locked boundaries

SP-5a is the **Zhihu favorites watcher**. It is a pure consumer of two upstream contracts:

- **SP-2 Zhihu Engine** (`Engine/zhihu/docs/interface.md`, frozen): `fetch(url, cookies, ...) -> FetchResult`.
- **SP-1 CookieManager** (`Service/crawl/cookie-manager/docs/interface.md`): cookie storage + retrieval.

**Cross-SP boundaries locked with the user (2026-06-02), NOT re-litigated here:**

- **Standalone service with its OWN scheduler** (not SP-1's cron hook). This is the isomorphic precedent for SP-5b (Bilibili Watcher).
- **Cookie = active PULL, never push.** Pull the latest cookie from SP-1 each cycle and inject into `fetch(cookies=...)`. Decrypt only transiently in memory — never persist plaintext cookies to disk. SP-1's push path is permanently cancelled.
- **Output = configurable output dir, vault-agnostic.** No GBrain frontmatter / no Obsidian taxonomy / no Thino (SP-6/SP-7 own that).
- **No LLM / no classification.** Unlike SP-3, the watcher does not use LLMClient and does not auto-classify.
- **Self-contained, parallel-independent.** No shared `Engine/common` helpers built competitively with SP-3; minor cookie-fetch/save duplication vs SP-3 is accepted for v1.
- **Frozen SP-2 engine** — pure consumer, never edit it.

**User design decisions (this brainstorm, 2026-06-02):**

| # | Decision | Choice |
|---|---|---|
| D1 | Cookie active-pull mechanism | **HTTP `GET /get/:uuid` + decrypt in pure Python** (no Node CLI in image) |
| D2 | Watermark / dedup mechanism | **Persistent seen-id set** (JSON), keyed on stable content id. NOT a content-`created` timestamp |
| D3 | Scheduler + deployment | **APScheduler `AsyncIOScheduler`** (interval, `max_instances=1`) + **docker-compose** |
| D4 | Output `.md` content format | Reference repo conventions (see §4), images = **remote URLs, not downloaded** |
| D5 | Filename / subfolder convention | Reference repo: subfolder-per-collection + `<title>.md` (collision → `_<url_id>`) |

> **Reference repo**: the user designated <https://github.com/JasonJarvan/Zhihu-Collections-MCP> as the
> authoritative reference; this watcher is a polling subset of it, and the **output format convention
> matches it** (filename, subfolder, `> url` first line, no frontmatter).

---

## 2. Zhihu collections API (verified against the reference repo)

The reference repo's collection-listing implementation resolves the open questions the generic web
sources left ambiguous. Findings (code-level):

- **Endpoint**: `GET https://www.zhihu.com/api/v4/collections/{collection_id}/items?offset={offset}&limit={limit}` (`limit` = 20).
- **Total count**: same base URL → response `paging.totals` (int).
- **Paging model**: **offset/limit** — loop `offset += limit` until `offset >= paging.totals`.
  We also defensively honor `paging.is_end == True` as a stop condition (covers either model;
  consistent with the `crawl-pipeline.md §知乎链路` idiom of following `paging` rather than self-constructing offsets).
- **Auth**: **plain cookies + browser-like headers, NO signing.** No `x-zse-96` / `x-zse-93` /
  cryptographic header. This confirms `crawl-pipeline.md §知乎链路` D5 ("`comment_v5` needs no `x-zse-96`")
  extends to the collections endpoint as of 2026-06.
- **Direct connect**: `trust_env=False` (Zhihu is a mainland site; the host's `HTTP_PROXY`/`ALL_PROXY`
  are for overseas sites — proxying Zhihu is slow + risk-flagged). Matches SP-2's stance.
- **Item schema** (fields the watcher reads from each element of `data`):
  - `content.type` — `"answer"` / `"article"` / ... (content type).
  - `content.url` — canonical URL of the favorited content (fed to SP-2 `fetch`).
  - `content.id` — content id; combined with `content.type` forms the **stable dedup key `type:id`**.
  - `content.title` (or, for answers, `content.question.title`) — title, used only as a fallback;
    the authoritative title for the saved file comes from SP-2's `FetchResult.title`.
- **Ordering**: Zhihu default is newest-favorited-first, but the watcher does NOT rely on ordering —
  the seen-id set (§3) makes ordering irrelevant for correctness.
- **No reliable per-item "favorited time" field**: the reference repo never reads one. The API's
  `content.created` is the **content's** creation time, not the favorite time — using it as a
  high-watermark would miss newly-favorited-but-old content. Hence D2 (seen-id set, not timestamp).
- **Collection id from URL**: `url.split('?')[0].split('/')[-1]` (e.g.
  `https://www.zhihu.com/collection/630144608` → `630144608`).

> **Residual risk (resolved at live-smoke, not blocking design/plan):** the no-signing finding is from
> the reference repo's code, not a 2026-06 live run by us. If the live smoke returns HTTP 403 on the
> collections endpoint (i.e. it unexpectedly needs `x-zse-96`), that is surfaced as a **blocker** to
> SubOrche + a Dashboard row — v1 does NOT introduce a signer.

---

## 3. Architecture

A resident daemon. `APScheduler.AsyncIOScheduler` fires one "poll all configured collections" cycle
every N minutes (`max_instances=1` so cycles never overlap; a slow cycle simply skips the next tick).

```
APScheduler (AsyncIOScheduler, interval = poll_interval_minutes, max_instances=1)
   └─> watcher.run_cycle()
         for collection in config.collections:
           cookies = cookie_provider.get_cookies()           # ① SP-1 GET + decrypt (transient)
           items   = favorites_client.list_items(collection.id, cookies)   # ② offset paging
           for item in items:
             if watermark_store.is_seen(collection.id, item.key):          # ③ seen-set dedup
                 continue
             result = fetcher.fetch(item.url, cookies)        # ④ frozen SP-2 engine
             if result is None:                               #    fetch failed → log, skip,
                 continue                                     #    DO NOT mark seen (retry next cycle)
             saver.save(collection, result.title, item.url, result.content_markdown)   # ⑤ save
             watermark_store.mark_seen(collection.id, item.key)            # ⑥ advance watermark
```

### 3.1 Components (each independently testable)

| Component | Responsibility | Key details |
|---|---|---|
| `config` | Load + validate YAML config | collections list, `poll_interval_minutes`, `output_dir`, `state_dir`, SP-1 connection (`base_url`, `uuid`, `password`). Dataclass/pydantic. |
| `cookie_provider` | Obtain `.zhihu.com` cookies from SP-1 | HTTP `GET {base_url}/get/{uuid}` → `{encrypted, crypto_type}` → decrypt in pure Python (§3.2) → parse inner `cookie_data` → extract `.zhihu.com` cookies → `dict[name,value]`. **Transient, never persisted.** May cache within a cycle + refresh per cycle. |
| `favorites_client` | List items in one collection | Builds browser-like headers; `httpx`/`requests` with `trust_env=False`; offset-paging loop (§2). Returns `list[CollectionItem]`. Raises a typed error on non-200 so the watcher can surface a blocker. |
| `watermark_store` | Seen-id dedup, persistent | One JSON file per collection under `state_dir` (e.g. `<state_dir>/seen-<collection_id>.json`). `load`, `is_seen(coll, key)`, `mark_seen(coll, key)`. Key = `"{content_type}:{content_id}"`. Atomic write (temp file + rename). Survives restart via mounted volume. |
| `fetcher` | Wrap the frozen SP-2 engine | `zhihu.fetch(url, cookies)` → return `(title, content_markdown)`; on `ZhihuFetchError` log + return `None` (graceful degrade; item is NOT marked seen → retried). |
| `saver` | Write Markdown to disk | Path `<output_dir>/<collection_name>/<sanitized_title>.md`; on collision append `_<url_id>`. Content = `> <url>\n` + `content_markdown`, **no frontmatter**, remote image URLs preserved. (§4) |
| `watcher` | Orchestrate a cycle + own the scheduler | `run_cycle()` (the loop above) and `main()` (start scheduler, run forever). Also a **`--once`** mode (run one cycle and exit) for the smoke test + CI. |

### 3.2 Cookie decryption (the only non-trivial crypto)

SP-1 stores cookies as CookieCloud-style ciphertext and `GET /get/:uuid` returns `{encrypted, crypto_type}`
without server-side decryption. The watcher decrypts in pure Python (dep: `pycryptodome`):

- **Key derivation (both modes)**: `the_key = md5(f"{uuid}-{password}").hexdigest()[:16]` (UTF-8, literal hyphen, first 16 hex chars).
- **`legacy` (default)**: ciphertext is an OpenSSL `Salted__` envelope (base64). Decode → assert 8-byte
  `Salted__` magic + 8-byte salt → `EVP_BytesToKey(MD5, the_key.encode(), salt, key_len=32, iv_len=16)`
  → AES-256-CBC decrypt → PKCS7 unpad → UTF-8 JSON.
- **`aes-128-cbc-fixed`**: `the_key`'s 16 UTF-8 bytes are the AES-128 key, IV = 16 zero bytes,
  AES-128-CBC + PKCS7, bare base64 (no `Salted__`).
- **Inner plaintext** (both): `{ cookie_data, local_storage_data, update_time }`; `cookie_data` is
  `domain -> [cookie objects]`. Extract the `.zhihu.com` entry → `{name: value}`.

Both modes are unit-tested against known vectors generated from the documented scheme; the live smoke
cross-checks against the real SP-1 box (and optionally the `cookie-manager show` CLI as an oracle).

### 3.3 Data flow types

```python
@dataclass
class CollectionItem:
    key: str          # stable dedup key: f"{content_type}:{content_id}"
    url: str          # content.url — fed to SP-2 fetch()
    content_type: str # "answer" | "article" | ...
    title: str        # fallback title (SP-2's FetchResult.title wins)

@dataclass
class CollectionConfig:
    id: str           # collection id (numeric string)
    name: str         # subfolder name under output_dir (from config; defaults to id)
```

---

## 4. Output format (matches the reference repo)

For each newly-favorited item that fetches successfully:

- **Directory**: `<output_dir>/<collection_name>/` (one subfolder per collection).
- **Filename**: `<sanitized_title>.md`. On collision with an existing *different* file, append the
  URL id: `<sanitized_title>_<url_id>.md`.
- **Title sanitization** (from the reference repo's `filter_title_str`):
  - `[\/\\"<>\|]` → space
  - `?` → `？` (full-width)
  - `:` → `：` (full-width)
- **File content**:
  ```
  > <canonical_url>
  <content_markdown from SP-2 FetchResult.content_markdown>
  ```
  - First line is a blockquote with the canonical URL.
  - **No YAML frontmatter** (deviates from SP-2's `.to_markdown()`, which would add one — we use
    `FetchResult.content_markdown` directly, not `.to_markdown()`).
  - **Images**: remote URLs preserved as-is (SP-2 does not download images; we do not either).

> The body text is produced by SP-2's parsers, so it will not be byte-identical to the reference repo's
> `markdownify` output — but the **convention** (url-prefix line + markdown body, no frontmatter,
> subfolder-per-collection, title-based filename) matches, which is what the user specified.

---

## 5. Error handling (the daemon must never crash)

| Failure | Handling |
|---|---|
| Cookie fetch / decrypt fails | Log; skip the whole cycle (no cookie ⇒ can't fetch). Daemon stays up; next tick retries. |
| Collection listing returns non-200 (e.g. 403 ⇒ unexpected `x-zse-96`, or network) | Log; skip that collection. **Persistent failure → write a blocker letter to SubOrche + emit a Dashboard row.** |
| SP-2 `fetch` raises `ZhihuFetchError` | Log (with `attempts`/`status`); skip the item; **do NOT mark seen** ⇒ retried next cycle. |
| Save to disk fails | Log; **do NOT mark seen** ⇒ retried next cycle. |
| Scheduler overlap | `max_instances=1` ⇒ a slow cycle simply causes the next tick to be skipped. |

Idempotency: an item is marked seen **only after** a successful fetch **and** save, so any failure path
leaves it eligible for retry without duplicate output.

---

## 6. Configuration & deployment

### 6.1 Config (`config/zhihu-watcher.example.yaml`)

```yaml
poll_interval_minutes: 45          # default 30–60; configurable
output_dir: /data/output           # where Markdown is written (may point at a vault subdir)
state_dir: /data/state             # where seen-id JSON lives (survives restart)

cookie_source:                     # SP-1 CookieManager connection
  base_url: http://127.0.0.1:48088 # or the LAN/public entry from SP-1 interface.md §8
  uuid: <cookiecloud-box-uuid>
  password: <cookiecloud-box-password>
  # crypto_type is read from GET /get/:uuid response; no need to configure

collections:
  - id: "630144608"                # from https://www.zhihu.com/collection/630144608
    name: "AI-papers"              # subfolder name under output_dir (optional; defaults to id)
  - id: "..."
    name: "..."
```

### 6.2 Deployment artifacts

- `Dockerfile` (python:3.x-slim; install deps; run `python -m zhihu_watcher`).
- `docker-compose.yml` — one service; volumes mount `output_dir`, `state_dir`, and the config file.
- `config/zhihu-watcher.example.yaml`.
- `docs/runbook.md` — config, volumes, how to bring up, SP-1 connection, common failures.

**Bringing the service UP is a USER operation** (per SP-1/SP-4a precedent: "起 Docker 容器是 user 操作").
The implementer delivers the artifacts and a `--once` smoke entrypoint; the user runs `docker compose up`.

---

## 7. Testing strategy (TDD)

**Unit:**
- `cookie_provider` decryption — both `legacy` and `aes-128-cbc-fixed` modes, against known vectors;
  `.zhihu.com` extraction from inner `cookie_data`.
- `favorites_client` paging — mock HTTP responses with `paging.totals`; assert it pages to completion,
  stops on `is_end`, parses `CollectionItem` fields, sets `trust_env=False`, sends no signing header.
- `watermark_store` — load/mark/is_seen; persistence across reload; atomic write.
- `saver` — title sanitization rules, collision `_<url_id>` suffix, subfolder, `> url` first line,
  no frontmatter, remote image URLs untouched.
- `fetcher` — wraps `zhihu.fetch`; returns `None` (not raise) on `ZhihuFetchError`.

**Integration:**
- Full `run_cycle()` with mocked SP-1 (`/get/:uuid`), mocked Zhihu collections API, and mocked SP-2
  `zhihu.fetch` → assert files saved under the right subfolder + seen-set advanced.
- **Second `run_cycle()` fetches nothing** (dedup/watermark works) — the core daemon invariant.

**Manual smoke (verification-before-completion gate):**
- Real SP-1 cookie + a real small collection → `--once`: watch a new item get fetched + saved as Markdown;
  run `--once` again → no new file (dedup confirmed); show the seen-id JSON.
- Bringing SP-1 up / ensuring a fresh `.zhihu.com` cookie is stored / `docker compose up` are **USER ops**
  → surfaced as a **gate** (Dashboard row + note to SubOrche). The gate does NOT block design/plan/code+unit/integration.

---

## 8. Module `docs/` deliverables (freeze the skeleton)

- `docs/README.md` — what it does / input / output / how to install (H2A, Chinese).
- `docs/interface.md` — config schema + CLI (`python -m zhihu_watcher [--once] [--config PATH]`) (H2A, Chinese).
- `docs/architecture.md` — external architecture summary (H2A, Chinese).
- `docs/runbook.md` — deploy/config/credentials/common failures (service ⇒ required) (H2A, Chinese).
- `docs/RepoMem/architecture.md` — internal architecture (A2A, English).
- `docs/RepoMem/decisions.md` — decision log D1–D5 above (A2A, English).

---

## 9. Out of v1 (noted as future, NOT implemented)

Captured from the user so they are not lost, but explicitly deferred:

- **Update detection**: if a content's last-updated time > its saved time, re-fetch it as an update.
- **Comment incremental pull**: pull comments on a ~90-day cadence (incremental-only, no deletion, to
  preserve data) to maintain comment volume — depends on the **v1.1 comment full-tree** (greenlight
  pending) and an **LLM comment-pruning** step (judge comment value, prune valueless comments). Both
  depend on capabilities outside v1 scope (comment-tree + LLMClient).
- **Favorited-timestamp watermark optimization**: an early-stop paging optimization, only if a future
  live probe confirms the API exposes a reliable favorite-time field with newest-first ordering.

---

## 10. Self-review

| Check | Result |
|---|---|
| Placeholder scan | No TBD/TODO; §9 future items explicitly marked out-of-v1 |
| Internal consistency | §2 API findings ↔ §3 components ↔ §4 output ↔ §7 tests all align; D1–D5 referenced consistently |
| Scope check | Single implementation plan: one daemon, 7 components, docker-compose. Future work fenced off in §9 |
| Ambiguity | Dedup key (`type:id`), filename collision rule, no-frontmatter, image policy, blocker-on-403 all made explicit |

---

**End of SP-5a design.md**
