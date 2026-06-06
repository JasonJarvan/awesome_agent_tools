> from: SP5aImpler session (Claude Opus 4.8 1M, 2026-06-07)
> recipient: ZhihuCrawl SubOrche (my parent)
> mode: milestone-done
> purpose: SP-5a Zhihu Watcher v1 complete + merged; Step 8 closed; v1.1 handoff drafted
> lifecycle: persist until SubOrche reads + converges; then this + the `toSP5aImpler/handoff.md` chain may burn

# milestone-done — SP-5a Zhihu Watcher v1

Task slug `sp5a-zhihu-watcher`. Full v2 8-step pipeline executed end-to-end.

## What was delivered

A standalone polling daemon at `Service/crawl/zhihu-watcher/` (Python, `src/` layout):
- `config` (YAML→dataclasses), `cookie_provider` (SP-1 HTTP GET + in-memory CookieCloud decrypt:
  legacy + aes-128-cbc-fixed, **never persists plaintext**), `favorites_client` (collections API offset
  paging, plain cookie / no x-zse-96 / `trust_env=False`), `watermark_store` (persistent seen-id set,
  atomic), `fetcher` (wraps frozen SP-2 `zhihu.fetch`, graceful degrade), `saver` (reference-repo format:
  `> url` + body, no frontmatter, remote images), `watcher` (DI orchestration), `__main__`
  (CLI `--once`/`--config` + `BlockingScheduler`). Deployment: Dockerfile + docker-compose + example config.
- Module docs frozen (README/interface/architecture/runbook + RepoMem architecture/decisions).

## Verification (single gate, v2)

- **32 unit/integration tests pass** (incl. the dedup-invariant integration test: 2nd cycle = no-op).
- compileall + all-modules-import clean.
- **Live smoke PASSED** (real SP-1 box `jasonjarvan` + real collection `343827655`, 2026-06-07):
  cookie pull OK (15 cookies); collections endpoint **HTTP 200, no x-zse-96**, 168 items / 9 offset pages;
  **140/168 fetched + saved** (`> url`+body, no frontmatter); **dedup confirmed live** (2nd `--once` → 0 new).
  The 28 failures are 専欄 ARTICLE (`zhuanlan.zhihu.com/p/...`): SP-2's api-fallback only covers ANSWER+403,
  so articles 403 with no fallback — watcher degraded gracefully (no crash, exit 0).
- Final holistic code review: **Ready to merge — Yes** (0 Critical/Important).

## Notable corrections caught during build/verify (all fixed + tested)

1. Paging stop guard `offset >= totals` → `len(items) >= totals` (plan bug; reviewer-confirmed).
2. Per-item broad `except` so one bad item never aborts the cycle; guard on corrupt seen-file.
3. `add_job(next_run_time=None)` removed — it PAUSED the interval job (daemon would poll once only;
   empirically verified on APScheduler 3.11.2).
4. `cookie_provider` client `trust_env=False` — a smoke caught it inheriting the host's SOCKS proxy
   (`ALL_PROXY`) and crashing at construction. SP-1 is direct-connect, same as the Zhihu client.

## Finishing + Step 8 (impler-owned closure, done in my lifecycle)

- Merged to `feat/agentcrawl-bootstrap` (merge `7acacb2`, --no-ff); worktree + branch cleaned up.
- **Step 8 RepoMem.merge closed** (`4a0b45c`, HITL): promoted to global `crawl-pipeline.md §知乎链路`
  (live-confirmed) — collections + people/collections endpoints need no x-zse-96, the offset-paging stop
  rule, and the ARTICLE-403-no-fallback gotcha. Module `decisions.md` records the live-smoke closure.

## Follow-on (per user direction): SP-5a v1.1 handoff drafted

The user requested two collection **target-resolution modes**: (1) by-userId auto-discover-all via
`/api/v4/people/{url_token}/collections`, (2) explicit list (≈ already done; optional config-adapter for the
Zhihu-Collections-Saver shape). **Decision locked with the user: these live in the SERVICE, not the frozen
engine.** I drafted the v1.1 handoff at `docs/sendbox/toZhihuWatcherV11Impler/handoff.md` for you to dispatch
a fresh impler. A new Dashboard UN row tracks "start the v1.1 impler" as a user action.

## Lifecycle

Per `toSP5aImpler/handoff.md §8`: burn the SP-5a v1 handoff chain after you read this. The SP-5a Status
Board row is flipped to ⚫ done.
