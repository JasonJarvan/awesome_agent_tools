# Module decision log — zhihu-watcher

> Append-only, time-descending (newest at top).
> Each entry: date, slug, decision, rationale, what-changes-when-this-is-revisited.
> When a decision is promoted to global, leave a `[Promoted to global ↗]` marker pointing to
> `<root>/docs/RepoMem/persist/memory/` (or `architecture/`).

## 2026-06-10 · sp5a-watcher-v1.1 · target-resolution + watermark correction + 403 backoff (live-smoked)

**Delivered** (branch `sp5a-watcher-v1.1`, off local `feat/agentcrawl-bootstrap` `b654662`; not yet merged):
- **`targets` schema** replaces v1 `collections` (clean break, no alias): `type: collection` (explicit) +
  `type: user` (auto-discover a user's NAMED collections). New `resolver.TargetResolver` expands targets →
  `list[CollectionConfig]` per cycle (collections-before-users so explicit names win dedup; skip `is_default`
  unless `include_default`; skip empty; per-target graceful degradation).
- **Watermark correction** (the v1 "no favorited-time" claim was a BUG): parse top-level `created` →
  `CollectionItem.favorited_at`; optional `only_after` (tz-aware, naive rejected) + first-run per-collection
  baseline (`WatermarkStore.get/set_baseline`) so a fresh by-user watch does NOT back-fill history. seen-id set
  stays the dedup backbone. **No early-stop** — items are NOT favorite-time-ordered (filter safe, early-stop unsafe).
- **403 backoff** (`failure_store.FailureStore`, time-window cooldown, DI clock): bounds re-attempts of
  permanently-failing items.
- `favorites_client` gained `list_user_collections` (people/collections paging) + `get_current_url_token` (/me).
- v1.1 Mode-1 **skips default 我的收藏** by default (`include_default: false`, user-decided) — the default inbox
  is reserved for the separate classifier SP. `output_dir` set to the existing Obsidian Zhihu library.

**Tests:** 58 pass (v1's 32 migrated for the `collections`→`targets` rename + new Watcher DI signature, + 26
new across config/favorites_client/resolver/failure_store/watermark/watcher, incl. a real-resolver e2e test).
Code-review (independent subagent): 2 blocking issues fixed (tz-aware datetime guard; example config/docs) +
unused-import; verdict ready-to-merge.

**Live smoke (real SP-1 + real account `zhao-cheng-57-99-79`, 2026-06-10):**
- **`/api/v4/me` HTTP 200 unsigned** → url_token resolved (Mode-1 `me` viable; residual risk closed).
- by-user discovery listed **35 collections → resolver kept 33** (skipped the default `我的收藏` + 1 empty
  `产品思维`); `我的收藏` confirmed absent from the polled set. **`is_default` flag drives the skip.**
- first-run baseline (`backfill=false`): every collection "0 new" — history NOT back-filled (baseline works,
  favorited_at parsed without crashing).
- full pipeline (explicit `量化`/998866113, `backfill=true`): **2 items fetched + saved** (one answer + one
  专栏 article — NB some 专栏 nav-GETs DO succeed; the 403 is a subset, not universal); re-run `--once` →
  **0 new (dedup invariant confirmed live)**.

**Pending at Step 8 (impler-owned HITL merge — NOT done here, global persist is governance-gated):** promote to
global `crawl-pipeline.md §知乎链路` — top-level `created` = favorite-time (correcting the v1 false claim),
items-NOT-favorite-time-ordered (early-stop unsafe), `/api/v4/me` + people/collections unsigned, `is_default`
flags the default collection; + the **methodology lesson** (empirically crawl + document + user-review before
watermark/paging logic) per the BilibiliCrawl SubOrche correction letter. Also fix v1 SP-5a design §2's false
"no favorited-time" claim. Empirical field doc: `docs/RepoMem/temp/sp5a-watcher-v1.1/api-fields-empirical.md`.

## 2026-06-07 · sp5a-zhihu-watcher · Step 8 merge closure + live smoke

**v1 merged** to `feat/agentcrawl-bootstrap` (merge `7acacb2`); worktree + branch cleaned up.

**Live smoke (real SP-1 + real collection 343827655, 2026-06-07):**
- Cookie pull from SP-1 + in-memory decrypt: OK (15 `.zhihu.com` cookies).
- Collections endpoint **HTTP 200, no `x-zse-96`** — 168 items over 9 offset pages. **Confirms the
  promotion candidate by our own live run** (not just the reference repo).
- 140/168 fetched + saved (`> url` + body, no frontmatter). The 28 failures are **专栏 ARTICLE**
  (`zhuanlan.zhihu.com/p/...`): the SP-2 engine's api-fallback only covers ANSWER+403, so articles 403
  with no fallback. Watcher degraded gracefully (no crash, exit 0).
- **Dedup invariant confirmed live**: 2nd `--once` → "0 new item(s)", only re-attempted the 28 unsaved.

**[Promoted to global ↗]** the no-`x-zse-96` + offset-paging + article-403 findings →
`<root>/docs/RepoMem/persist/architecture/crawl-pipeline.md §知乎链路` (now live-confirmed, not a candidate).

**v1+ note**: the 28 permanently-403 articles are re-attempted every cycle (not marked seen). Bounded
(no infinite loop within a cycle) but wasteful → a failed-attempt counter / backoff is a v1+ improvement.
This + the two target-resolution modes (by-userId list-all; explicit list) are the SP-5a v1.1 increment.

## 2026-06-05 · sp5a-zhihu-watcher · Implementation deltas vs the approved plan

Three corrections made during subagent-driven implementation (all reviewer- or empirically-confirmed):

1. **Paging stop guard = `len(items) >= totals`, not `offset >= totals`.** The plan's `offset >= totals`
   breaks after page 0 when the API reports `totals` larger than one page's worth but is_end arrives late
   (or when fewer real items than `totals` are split across pages). Reviewer-confirmed correct; the loop
   still terminates via `is_end` + empty-data safety. Revisit: if a real collection ever shows the loop not
   terminating, add a hard max-pages guard.
2. **Per-item processing wrapped in a broad `except Exception`** (not just `save`). A code review noted the
   frozen SP-2 engine could in rare cases leak a non-`ZhihuFetchError`; one bad item must never abort the
   cycle. Item is not marked seen on any failure → retried next cycle.
3. **Removed `add_job(next_run_time=None)`.** Empirically verified (APScheduler 3.11.2): an explicit
   `next_run_time=None` adds the interval job PAUSED → it never fires → the daemon would poll once and never
   again. Omitting the arg lets APScheduler schedule the first fire at now+interval; the explicit startup
   `run_cycle()` covers the immediate run. Revisit: if startup double-run is ever unwanted, drop the manual
   call instead.

Also guarded `watermark_store.load()` against a corrupt state file (skip that collection, don't crash).

## 2026-06-02 · sp5a-zhihu-watcher · v1 design decisions (D1–D5)

- **D1 — Cookie = active PULL via HTTP GET + in-memory decrypt (pure Python).** `GET {base_url}/get/{uuid}`
  → decrypt by `crypto_type` (legacy / aes-128-cbc-fixed) with `cryptography`. Chosen over a `cookie-manager
  show` CLI shell-out so the Docker image needs no Node CLI. Cookies never persisted to disk. This is the
  isomorphic precedent for SP-5b. Revisit: if SP-1 ever serves decrypted cookies, drop the local crypto.
- **D2 — Dedup = persistent seen-id set (JSON per collection), key `type:id`.** NOT a `content.created`
  timestamp watermark — the collections API doesn't reliably expose a favorited time, and `content.created`
  is content-creation time (≠ favorite time). Revisit: if a reliable favorited-time field + newest-first
  ordering are confirmed, add a timestamp early-stop optimization (still backed by the seen-set).
- **D3 — Scheduler = APScheduler `BlockingScheduler`, deploy = docker-compose.** Sync components ⇒ a blocking
  scheduler with a sync job (not `AsyncIOScheduler`). `max_instances=1` + `coalesce=True`. Bringing the
  container up is a USER op (SP-1/SP-4a precedent).
- **D4 — Output format = Zhihu-Collections-MCP reference convention.** User-designated reference repo. Fetch
  via SP-2 `fetch()` but serialize as `> url\n<body>` (no frontmatter); we deliberately do NOT use SP-2's
  `.to_markdown()`. Subfolder per collection; filename `<sanitize(title)>.md` (collision `_<url_id>`).
- **D5 — Images = remote URLs, not downloaded.** Matches SP-2 (no image download) and the handoff's
  "no Obsidian taxonomy / vault-agnostic" boundary (so no `![[...]]` wikilinks, no `assets/`). Revisit: if a
  later vertical wants offline images, add an opt-in download that emits standard `![](assets/..)` links.

### Global promotion — DONE at Step 8 (2026-06-07, HITL)

- **"The Zhihu collections-items endpoint needs no `x-zse-96` (plain cookie + browser headers)."**
  Extends `crawl-pipeline.md §知乎链路` D5 (no-signing on the answer/comment path) to the collections +
  user-collections-list endpoints. **[Promoted to global ↗]** `crawl-pipeline.md §知乎链路` — the 2026-06-07
  live smoke confirmed it by our own run (200, 168 items, plain cookie), so it is no longer a candidate
  caveated to the reference repo. The offset-paging stop rule and the ARTICLE-403-no-fallback gotcha were
  promoted alongside it.
