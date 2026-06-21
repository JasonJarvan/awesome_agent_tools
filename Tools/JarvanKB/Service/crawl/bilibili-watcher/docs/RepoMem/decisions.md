# Module decision log — bilibili-watcher

> Append-only, time-descending (newest at top).
> Each entry: date, slug, decision, rationale, what-changes-when-this-is-revisited.
> When a decision is promoted to global, leave a `[Promoted to global ↗]` marker pointing to
> `<root>/docs/RepoMem/persist/memory/` (or `architecture/`).

## 2026-06-10 · sp5b-bilibili-watcher · v1 design decisions (D1–D8)

Ratified by user 2026-06-10 after Stage-0 empirical investigation. Full Stage-0 record:
`docs/RepoMem/temp/sp5b-bilibili-watcher/favorites-api-fields.md`. Full decision context in
`docs/superpowers/specs/2026-06-07-SP-5b-bilibili-watcher-design.md §3`.

- **D1 — Cookie = active PULL via HTTP GET + in-memory decrypt (pure Python) + optional auth_token.**
  `GET {base_url}/get/{uuid}` (+ `X-CookieCloud-Token` header if `auth_token` configured) → decrypt by
  `crypto_type` (legacy / aes-128-cbc-fixed) with `cryptography` → extract `bilibili.com` cookies →
  build `BilibiliCredential`. Chosen over a shell-out so the Docker image needs no Node CLI. Cookies
  never persisted to disk. The `auth_token` field is the B站 delta vs SP-5a (SP-1 box may require it).
  Revisit: if SP-1 ever serves decrypted cookies, drop the local crypto.

- **D2 — Watermark / dedup = `fav_time` high-watermark (early-stop) + `bvid` seen-set (idempotency backstop).**
  `fav_time` = "stop paging early, save API requests"; seen-set = "never save twice, never drop".
  Stage-0 confirmed `fav_time` exists per item and IS the favorited-time (distinct from `pubtime`/`ctime`),
  and that `order=mtime` sorts by `fav_time` DESC — enabling early-stop. This supersedes the SP-5a v1
  "no favorited-time" conclusion (that was a Zhihu-specific finding, not a universal one).
  Watermark advance rule: `next_watermark(prev, listed, failed)` — no failures → advance to newest;
  any failure → hold at `min(failed)−1` (conservative, retry-safe). See `RepoMem/architecture.md §5`.
  Revisit: if paging order ever changes or `fav_time` precision drops below 1 second, revisit the rule.

- **D3 — Scheduler + deployment = APScheduler `BlockingScheduler` + docker-compose + `--once`.**
  Sync components (httpx sync + sync engine) ⇒ blocking scheduler with sync job (not AsyncIO).
  `max_instances=1` + `coalesce=True`. `docker-compose` with `network_mode: host` (must reach BN at
  `127.0.0.1:3015` and SP-1 at `127.0.0.1:48088`). Bringing the container up is a USER op (SP-1/SP-4a
  precedent). Revisit: if async engine is introduced, switch to `AsyncIOScheduler`.

- **D4 — Engine output = `result.render(RenderOptions(...)).main_markdown`, single self-contained .md.**
  `RenderOptions(include_transcript=True, include_timestamps=False, split_transcript=False)` by default
  (BN AI summary + readable-prose transcript, no timestamps). All three options exposed as `render.*`
  config. `split_transcript=True` is an out-of-v1 per-video heuristic (§11).
  Revisit: add auto single-vs-split judgment when length/duration threshold is calibrated (§11).

- **D5 — Filename + subfolder = `<output_dir>/<folder.name>/<sanitize(title)>.md`; collision → `_<bvid>`.**
  First line `> https://www.bilibili.com/video/<bvid>`; no GBrain frontmatter; remote images kept as URLs.
  Sanitization rules reused verbatim from SP-5a saver (identical invariants).
  Revisit: if offline image download is needed, add an opt-in download with standard `![](assets/..)`.

- **D6 — Only `type==2` (UGC video) items are processed.**
  Non-video items (audio type=12, 番剧, 合集, etc.) are logged + skipped + NOT marked seen or watermarked
  (D6 avoids noise; non-video items cannot be fed to the video transcription engine).
  Revisit: if audio transcription becomes supported, add a type==12 path.

- **D7 — Starter folders = AI生成 (`2216104467`) + 编程折腾 (`1195057867`).**
  A small set chosen by the user to smoke through v1. Other folders added via config at any time —
  no code change required. Stage-0 verified these `media_id` values are correct.
  Revisit: folder ids change only if the user restructures their B站 account.

- **D8 — Poll interval = 20 min (default); configurable.**
  SP-0 §7 specifies 15–30 min for watcher services. 20 min chosen as a conservative middle. The
  `poll_interval_minutes` config key allows the user to tune without redeployment.
  Revisit: if the user wants near-real-time or much longer batching, adjust the default.

### Global promotion candidates

- **`fav_time` = favorited-time, distinct from `pubtime`/`ctime`, confirmed B站 Stage-0 2026-06-10.**
  Extends `crawl-pipeline.md §B站链路`. Stage-0 empirical proof: `fav_time=2026-04-24` vs
  `pubtime=2026-04-16` for the same media. This is a load-bearing finding that enables the early-stop
  watermark optimization. **Pending HITL Step 8 merge to global `crawl-pipeline.md`.**
- **B站 fav API paging stop = `has_more`, never `media_count` (deleted-item gotcha).**
  `media_count` counts invalid/deleted items not returned in `medias[]`. Stage-0 proof: count=4, returned=3.
  **Pending HITL Step 8 merge to global `crawl-pipeline.md`.**

## Deploy notes (v1.1 WatcherDeploy, 2026-06-19)

- **No `backfill_on_first_run` flag (unlike SP-5a) → first cycle with watermark=0 backfills the WHOLE folder.**
  To deploy "from-now" (only NEW favorites, no history backfill), pre-seed each folder's
  `data/state/state-<id>.json` with `{"watermark": <now-epoch>, "seen": []}` BEFORE first `up -d`. Then
  `list_items(since_fav_time=now)` early-stops immediately → 0 new; only items favorited after `now` flow.
  (v1.1 seeded all 22 folders this way.)
- **Compose bind-mounts the host vault dir → `/data/output`** (config `output_dir: /data/output`); `state_dir`
  persisted via `./data/state`. `network_mode: host` already present (reaches BN `:3015` + SP-1 `:48088`).
  Defensive proxy-clear env added (runbook §5 socksio class).
- **BN provider key drift**: B站 transcription needs a valid LLM provider key in BN; it expires independently of
  repo `.env` and has no auto-refresh. See `crawl-pipeline.md §B站链路` (BN `/api/update_provider` SOP).
