# SP-5b — Bilibili Watcher — Design

> **Status**: approved (user OK 2026-06-10)
> **Date**: 2026-06-10 (Stage-0 empirical investigation + brainstorm same day; filename keeps the
> handoff-specified `2026-06-07` slug for cross-reference stability)
> **Author**: SP5bImpler (Claude Code session, child of BilibiliCrawl SubOrche)
> **Module**: `Service/crawl/bilibili-watcher/` (type=service)
> **Scope**: a standalone daemon that polls the user's Bilibili favorite folder(s) on a schedule,
> detects newly-favorited videos, transcribes each via the frozen SP-4a engine, and saves Markdown
> to a configured output dir. No user interaction (it is a daemon).

---

## 1. Background & locked boundaries

SP-5b is the **Bilibili favorites watcher** — the structural twin of the shipped **SP-5a Zhihu Watcher**
(⚫ done + merged 2026-06-07). It is a pure consumer of two upstream contracts:

- **SP-4a Bilibili Engine** (`Engine/bilibili/docs/interface.md`, **frozen**):
  `engine.transcribe(video_ref, credential=BilibiliCredential(...)) -> BilibiliResult`, then
  `result.render(RenderOptions(...)).main_markdown`. The engine is a client of self-hosted **BiliNote (BN)**
  + **bcut** ASR; it never calls an LLM itself (BN does internally).
- **SP-1 CookieManager** (`Service/crawl/cookie-manager/docs/interface.md`): cookie storage + retrieval.

**Cross-SP boundaries locked with the user (handoff §1, symmetric to the Zhihu vertical — NOT re-litigated):**

- **Standalone service with its OWN scheduler** (`BlockingScheduler`, `max_instances=1`), NOT SP-1's cron hook.
- **Cookie = active PULL, never push.** Pull SESSDATA + bili_jct from SP-1 each cycle, decrypt transiently in
  memory (never persist plaintext), build `BilibiliCredential`, inject into the engine. SP-1 push is cancelled.
- **Cookie domain = `bilibili.com` (NO leading dot)** — `credentials.md §Bilibili` is authoritative; the engine
  `interface.md §5`'s `.bilibili.com` is stale. The box holds `SESSDATA` + `bili_jct` (no `buvid3`).
- **Output = configurable output dir, vault-agnostic.** No GBrain frontmatter / no Obsidian taxonomy / no Thino.
- **No LLM / no classification.** Unlike SP-4b, the watcher does not use LLMClient and does not auto-classify.
- **Self-contained, parallel-independent** of SP-4b; minor cookie/save duplication accepted for v1.
- **Frozen SP-4a engine** — pure consumer, never edit `Engine/bilibili/`.

**This design mirrors SP-5a 1:1 EXCEPT the two B站 deltas: (Δ1) the engine, (Δ2) the watermark.**
For the unchanged mechanisms (cookie-decrypt crypto, scheduler choice, daemon-never-crashes posture,
docker-compose shape, `--once`) this doc references SP-5a's design rather than re-deriving them.

---

## 2. Stage-0 ratified findings (the empirical basis for the watermark)

Full record + user ratification: `docs/RepoMem/temp/sp5b-bilibili-watcher/favorites-api-fields.md`
(empirically crawled with the user's live cookie 2026-06-10; user-reviewed, §9 ratified). Load-bearing facts:

- **Endpoint**: `GET https://api.bilibili.com/x/v3/fav/resource/list?media_id={folder_id}&pn={n}&ps=20&order=mtime&type=0&platform=web`
  — plain cookie (SESSDATA) + browser headers, **no signing**. Response wrapper `{code,message,ttl,data}` (`code==0` ok).
  Direct connect (`proxies` disabled / `trust_env=False` — B站 is a mainland site).
- ⭐ **`fav_time` exists per item and IS the collected-time, distinct from `pubtime`/`ctime`** (proof: media[0]
  `fav_time`=2026-04-24 vs `pubtime`=2026-04-16). This *validates* the `fav_time` high-watermark and refutes the
  SP-5a-style "no reliable favorite-time" armchair conclusion.
- ⭐ **`order=mtime` ⇒ `data.medias[]` sorted by `fav_time` DESC** (newest-favorited first) — enables early-stop.
- ⚠️ **Paging**: `pn`/`ps` page model; **stop on `data.has_more == False`**. `data.info.media_count` counts
  invalid/deleted items that are NOT returned in `medias[]` (folder showed count=4, returned 3) →
  **NEVER stop on `len(collected) >= media_count`** (the B站 twin of the §知乎链路 "don't stop from totals" lesson).
- **Item → engine**: feed `bvid` (e.g. `BV1orQJB2Edt`). `type==2` = UGC video.
- Folder `id` from `list-all` is the `media_id` used directly in `resource/list` (config gives ids, so the watcher
  needs no `nav`/`list-all` at runtime — those were Stage-0 discovery only).

---

## 3. User design decisions (ratified 2026-06-10)

| # | Decision | Choice |
|---|---|---|
| D1 | Cookie active-pull mechanism | **HTTP `GET /get/:uuid` + decrypt in pure Python** (reuse SP-5a `cookie_provider`; no Node CLI in image). Extract `bilibili.com` cookies → build `BilibiliCredential(sessdata=SESSDATA, bili_jct=bili_jct)`. Optional `X-CookieCloud-Token` if the box has `auth_token`. |
| D2 | **Watermark / dedup (Δ2)** | **`fav_time` high-watermark (early-stop) + seen-id set keyed on `bvid` (idempotency backstop).** fav_time = "stop paging early, save requests"; seen-id = "never save twice, never drop". (§5) |
| D3 | Scheduler + deployment | **APScheduler `BlockingScheduler`** (interval, `max_instances=1`) + **docker-compose** + a **`--once`** smoke mode. Identical rationale to SP-5a D3 (sync components ⇒ blocking scheduler + sync job). |
| D4 | **Engine output shape (Δ1)** | `result.render(RenderOptions(include_transcript=True, include_timestamps=False, split_transcript=False)).main_markdown` → a **single self-contained .md** (BN AI summary + readable-prose transcript). RenderOptions exposed as **config** (`render.*`); defaults to this. |
| D5 | Filename / subfolder convention | Mirror SP-5a `saver`: `<output_dir>/<folder_name>/<sanitized_title>.md`; collision → `_<bvid>`; first line `> <video_url>`; **no frontmatter** beyond what the engine renders. Sanitization rules reused verbatim. |
| D6 | type filter | **Process only `type==2` (UGC video)**; non-video items (audio/番剧/合集) are logged + skipped + **not** marked seen-or-watermarked (avoids noise). |
| D7 | Folders to watch (v1 start) | **`AI生成` (id `2216104467`) + `编程折腾` (id `1195057867`)** — a small set to smoke through; others added later via config. |
| D8 | Poll interval | default **20 min** (SP-0 §7 "15–30 min"); configurable. |

---

## 4. Architecture

A resident daemon. `BlockingScheduler` fires one "poll all configured folders" cycle every N minutes
(`max_instances=1` so cycles never overlap; a slow cycle simply skips the next tick).

```
BlockingScheduler(interval = poll_interval_minutes, max_instances=1)
  └─> watcher.run_cycle()
        cookies = cookie_provider.get_cookies()          # ① SP-1 GET + decrypt (transient, bilibili.com)
        cred    = build_credential(cookies)              #    BilibiliCredential(sessdata, bili_jct)
        for folder in config.folders:
          state = watermark_store.load(folder.id)        # {watermark: fav_time, seen: {bvid}}
          items = favorites_client.list_items(           # ② order=mtime paging, type==2 only,
                      folder.id, cookies,                 #    early-stop when fav_time <= state.watermark,
                      since_fav_time=state.watermark)     #    page-stop on has_more==False
          failed_fav_times = []
          for item in items:                             #    items are newest-fav-first
            if item.bvid in state.seen: continue         # ③ seen-set dedup
            md = fetcher.fetch(item.bvid, cred)           # ④ frozen SP-4a engine -> main_markdown
            if md is None:                                #    transcribe failed -> retry next cycle
              failed_fav_times.append(item.fav_time)
              continue                                    #    NOT marked seen / NOT watermarked
            saver.save(folder, md.title, item.bvid, md.markdown)  # ⑤ save
            state.seen.add(item.bvid)                     # ⑥ idempotency advance (persist immediately)
          watermark_store.advance(folder.id, items, failed_fav_times)   # ⑦ early-stop watermark (§5)
```

### 4.1 Components (each independently testable — mirrors SP-5a's 7)

| Component | Responsibility | Δ vs SP-5a |
|---|---|---|
| `config` | Load + validate YAML → dataclasses. `folders` list, `poll_interval_minutes`, `output_dir`, `state_dir`, `cookie_source` (`base_url`/`uuid`/`password`/optional `auth_token`), `render` (RenderOptions). | `folders` (was `collections`) + `render` block + optional `auth_token`. |
| `cookie_provider` | `GET {base}/get/{uuid}` (+optional token) → decrypt (pure Python, §3.2 of SP-5a) → extract **`bilibili.com`** cookies → `dict[name,value]`. Transient, never persisted. | domain `bilibili.com` (was `zhihu.com`); crypto identical. |
| `favorites_client` | List one folder's items: browser headers, proxies disabled; `order=mtime` page loop; **filter `type==2`**; **early-stop on `fav_time <= since_fav_time`**; **page-stop on `has_more==False`**. Returns `list[BiliFavItem(bvid, fav_time, title, type)]`. Typed error on non-200/`code!=0`. | **new endpoint + fav_time early-stop + has_more paging + type filter** (Δ2). |
| `watermark_store` | Per-folder JSON `<state_dir>/state-<folder_id>.json` = `{watermark:int, seen:[bvid]}`. `load`, `mark_seen`, `advance` (§5). Atomic write (temp+rename). Survives restart. | **adds the `fav_time` watermark field + `advance` logic** alongside the seen-set (Δ2; SP-5a had seen-set only). |
| `fetcher` | Wrap the frozen engine: `engine.transcribe(bvid, credential=cred)` → `result.render(RenderOptions from config).main_markdown` → `FetchedDoc(title, markdown)`. On `BilibiliEngineError` (incl. `BiliNoteUnavailable`/`TranscriptionFailed`/timeout) → log + return `None` (graceful degrade; item NOT advanced → retried). | **SP-4a engine** (was SP-2 `zhihu.fetch`) (Δ1). |
| `saver` | `<output_dir>/<folder_name>/<sanitized_title>.md`; collision → `_<bvid>`; content = `> <video_url>\n` + `main_markdown`; no GBrain frontmatter. | `_<bvid>` (was `_<url_id>`); video_url = `https://www.bilibili.com/video/<bvid>`. Sanitization identical. |
| `watcher` | Orchestrate a cycle + own the scheduler; `--once` mode; `main()`. Collaborators injected (testable with fakes). Daemon never crashes — every failure path logs + continues. | engine credential build; watermark `advance` call. |

### 4.2 Cookie → credential
`cookie_provider.get_cookies()` returns the `bilibili.com` cookie dict. `favorites_client` uses it directly for
the HTTP `cookies=` (SESSDATA authenticates). `fetcher` builds `BilibiliCredential(sessdata=cookies["SESSDATA"],
bili_jct=cookies.get("bili_jct"))` (`buvid3=None` — box has none; engine is degrade-capable). Crypto routine
reused verbatim from SP-5a `cookie_provider` (the credentials.md-verified `legacy`/`aes-128-cbc-fixed` decrypt).

---

## 5. Watermark mechanism (Δ2 — the one big delta, ratified D2)

Two cooperating layers per watched folder:

1. **seen-id set (keyed `bvid`) — correctness/idempotency.** A video is saved **at most once**, regardless of
   ordering, equal `fav_time`, re-favoriting, or retries. Persisted immediately after each successful save
   (≤1-item crash window, mirroring SP-5a).
2. **`fav_time` high-watermark `W` — early-stop optimization.** Invariant: *every favorited item with
   `fav_time > W` has been successfully saved.* Each cycle lists with `order=mtime` (fav_time DESC) and
   **stops paging as soon as it sees an item with `fav_time <= W`** (and on `has_more==False`).

**`advance(folder, items, failed_fav_times)` rule (conservative, retry-safe):**
- If **no failures** this cycle: `W ← max(W, newest fav_time among items)`.
- If **any failure**: `W ← min(failed_fav_times) − 1`. This keeps every failed item (and only those, plus
  already-saved newer items which the seen-set skips) listable next cycle, so failures are retried while
  successes are never re-fetched. (1-second granularity; `fav_time` is unix seconds.)
- First run (no state): `W = 0` ⇒ full backfill of the folder (paging stops on `has_more`).

> Why both: pure `fav_time` risks boundary loss on equal timestamps / re-favorites; pure seen-set (SP-5a) is
> correct but must page the whole folder every cycle. Together: O(new-only) listing + exactly-once saves.

---

## 6. Output format (D4/D5)

Per newly-favorited `type==2` video that transcribes successfully:
- **Dir**: `<output_dir>/<folder_name>/` (one subfolder per folder).
- **Filename**: `<sanitized_title>.md`; collision → `<sanitized_title>_<bvid>.md`.
  Sanitization (reused from SP-5a): `[\/\\"<>\|]`→space, `?`→`？`, `:`→`：`, strip, empty→`untitled`.
- **Content**: `> https://www.bilibili.com/video/<bvid>\n` + `result.render(...).main_markdown`.
  `main_markdown` = BN AI summary + readable-prose transcript (no timestamps) per D4. No GBrain/Obsidian
  frontmatter. Remote image/cover URLs preserved (engine does not download).

---

## 7. Error handling (daemon must never crash)

| Failure | Handling |
|---|---|
| Cookie fetch/decrypt fails, or no SESSDATA | Log; skip the whole cycle (no cookie ⇒ can't list/transcribe). Daemon stays up; next tick retries. |
| `favorites_client` non-200 / `code!=0` (e.g. -101 not-logged-in ⇒ expired cookie, or network) | Log; skip that folder. **Persistent failure → blocker letter to SubOrche + Dashboard row.** |
| Engine raises `BilibiliEngineError` (`BiliNoteUnavailable` / `TranscriptionFailed` / timeout / invalid ref) | `fetcher` logs + returns `None`; item NOT advanced ⇒ retried. Persistent `BiliNoteUnavailable` (BN down) → blocker (it is the Stage-3 gate). |
| Non-`type==2` item | Log + skip; not seen-marked, not watermarked (D6). |
| Save to disk fails | Log; item NOT advanced ⇒ retried. |
| Scheduler overlap | `max_instances=1` ⇒ a slow cycle skips the next tick. |

Idempotency: an item is seen-marked **only after** successful transcribe **and** save; the watermark advances
per §5 — any failure leaves the item eligible for retry without duplicate output.

---

## 8. Configuration & deployment

### 8.1 Config (`config/bilibili-watcher.example.yaml`)
```yaml
poll_interval_minutes: 20            # SP-0: 15–30; configurable
output_dir: /data/output
state_dir: /data/state               # per-folder state-<id>.json (watermark + seen); survives restart

cookie_source:
  base_url: http://127.0.0.1:48088
  uuid: <cookiecloud-box-uuid>
  password: <cookiecloud-box-password>
  auth_token: <optional X-CookieCloud-Token if the box sets server.auth_token>

engine:                              # SP-4a engine connection (else from Engine/bilibili config)
  bn_base_url: http://127.0.0.1:3015 # BN backend (host maps :8483; see crawl-pipeline.md §B站链路)
  provider_id: <BN provider id>
  model_name: <model>

render:
  include_transcript: true
  include_timestamps: false
  split_transcript: false

folders:
  - id: "2216104467"                 # AI生成
    name: "AI生成"
  - id: "1195057867"                 # 编程折腾
    name: "编程折腾"
```

### 8.2 Deployment artifacts (mirror SP-5a)
- `Dockerfile` (python:3.x-slim; install deps incl. `Engine/bilibili` engine pkg + `bilibili-api-python`; run `python -m bilibili_watcher`).
- `docker-compose.yml` — one service; volumes mount `output_dir`, `state_dir`, config; **must reach BN** (`network_mode: host` or a shared network to `127.0.0.1:3015`).
- `config/bilibili-watcher.example.yaml`; `docs/runbook.md`.

**Bringing the service UP / `docker compose up` / ensuring a fresh `bilibili.com` cookie / BN being up are USER
operations** (per SP-1/SP-4a/SP-5a precedent). The implementer delivers artifacts + a `--once` entrypoint.

---

## 9. Testing strategy (TDD)

**Unit:**
- `cookie_provider`: both decrypt modes (known vectors) + **`bilibili.com` extraction** (no dot) + credential build.
- `favorites_client`: mock HTTP — pages with `order=mtime`; **stops on `has_more==False`**; **early-stops on
  `fav_time <= since_fav_time`**; **filters `type!=2`**; parses `BiliFavItem`; proxies disabled; raises on non-200/`code!=0`;
  **never stops from `media_count`** (regression for the count=4/returned=3 gotcha).
- `watermark_store`: load/mark/advance; **`advance` no-failure vs failure rule (§5)**; persistence across reload; atomic write; corrupt-file tolerance.
- `fetcher`: wraps engine; passes RenderOptions; returns `FetchedDoc` on success, `None` on `BilibiliEngineError`.
- `saver`: sanitization, `_<bvid>` collision, subfolder, `> <video_url>` first line, no frontmatter.

**Integration:**
- Full `run_cycle()` with mocked SP-1 `/get/:uuid`, mocked favorites API, mocked engine → files saved under right
  subfolder + watermark + seen-set advanced.
- **Second `run_cycle()` saves nothing** (dedup/watermark works) — the core daemon invariant.
- **Failure mid-cycle** → watermark held below the failure (§5) → next cycle re-lists + retries only the failure.

**Manual smoke (verification-before-completion gate):**
- Real SP-1 cookie + the 2 real folders (`2216104467`/`1195057867`) → `--once`: a new video transcribed via the
  engine (BN at `127.0.0.1:3015`) → saved Markdown; `--once` again → no new file; show the state JSON.
- **BN must be up** (USER op; it already is) / fresh cookie / `docker compose up` → surfaced as a **gate**
  (Dashboard row + note to SubOrche). The gate does NOT block design/plan/code+unit/integration.

---

## 10. Module `docs/` deliverables (freeze the skeleton)
- `docs/README.md` — what/input/output/install (H2A, 中文).
- `docs/interface.md` — config schema + CLI `python -m bilibili_watcher [--once] [--config PATH]` (H2A, 中文).
- `docs/architecture.md` — external architecture summary (H2A, 中文).
- `docs/runbook.md` — deploy/config/credentials/BN-dependency/common failures (service ⇒ required) (H2A, 中文).
- `docs/RepoMem/architecture.md` — internal architecture (A2A, English).
- `docs/RepoMem/decisions.md` — decision log D1–D8 (A2A, English).

---

## 11. Out of v1 (noted as future, NOT implemented)
- **Auto single-vs-split judgment** (user-raised 2026-06-10): per-video heuristic to set `split_transcript`
  automatically (e.g. long transcript / long duration → split summary + transcript file; short → single file),
  vs v1's static `render.*` config toggle. Needs a length/duration threshold + possibly user calibration.
- **Credential refresh / keep-alive** on cookie expiry (shared open item with SP-5a; pull-cadence is the watcher's).
- **Cross-folder dedup** (same video in two folders saved twice) — v1 keeps per-folder state (acceptable).
- **Update detection / re-transcribe** if a video changes — out of v1 (same posture as SP-5a §9).

---

## 12. Self-review
| Check | Result |
|---|---|
| Placeholder scan | No TBD/TODO; §11 future items explicitly out-of-v1 |
| Internal consistency | §2 findings ↔ §3 decisions ↔ §4 components ↔ §5 watermark ↔ §6 output ↔ §9 tests align; D1–D8 referenced consistently |
| Scope check | Single plan: one daemon, 7 components, compose. Future fenced in §11 |
| Ambiguity | watermark `advance` rule (§5), has_more vs media_count stop, type==2 filter, `_<bvid>` collision, no-frontmatter all explicit |
| Δ-isolation | The only deltas vs SP-5a are Δ1 engine (fetcher) + Δ2 watermark (favorites_client + watermark_store); everything else reused/mirrored |

---

**End of SP-5b design.md**
