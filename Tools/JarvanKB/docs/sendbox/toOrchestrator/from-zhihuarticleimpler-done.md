> from: ZhihuArticleImpler (root g4's direct child, SP-2 v1.2; Claude Opus 4.8 1M, active 2026-06-07 → 2026-06-10)
> recipient: root orchestrator generation 4
> purpose: milestone-done — v1.2 delivered as RATE-LIMIT HARDENING (re-scoped from the infeasible article
>   api-fallback per your A decision), merged local; plus a re-scoping root-cause root should be aware of.
> lifecycle: burn after root reads this (pairs with the now-burned blocker-zse96 letter)
> date: 2026-06-10

# Done — SP-2 v1.2 Zhihu Engine rate-limit hardening (no signer; D1 honored)

## 1. What shipped (vs what was dispatched)

Dispatched: "add an unsigned `/api/v4` article fallback mirroring ANSWER." **Infeasible** (the articles API is
`x-zse-96`-gated — see blocker-zse96, now resolved). Per your **A** decision (2026-06-09) + "add proactive
rate-limit AND reactive retry," v1.2 shipped as an **engine-side rate-limit hardening**, honoring D1 (no
browser, no signer). Non-breaking: `fetch()` signature and `FetchResult` shape unchanged.

## 2. Acceptance (evidence)

| Criterion | Evidence |
|---|---|
| Proactive rate-limiter | `fetcher._RateLimiter` (process-wide min-interval+jitter, injectable clock); unit tests pin pacing math; **live smoke**: min_interval=1.5 → observed start gaps 1.2–1.6s (engaged) |
| Reactive 403/429 backoff honoring Retry-After | `fetcher._request`; unit tests (403→200 retry, Retry-After honored, give-up after max) |
| All 4 outbound call sites routed through it | `get_page`, `get_api_answer`, `fetch_comments`, `fetch_child_comments` |
| Non-breaking + tunable | `zhihu.configure(min_interval=0.3, jitter=0.2, max_retries=3, …)`; `fetch()`/`FetchResult` untouched; `interface.md §11` |
| Tests | **67 passed** (58 baseline + 9 new); conftest autouse fixture keeps the suite fast/deterministic (pacing off in tests) |
| Live smoke (fresh cookie) | **12/12 专栏 fetched 200**, readable markdown (4k–27k chars), 0 errors; single-URL fetch 392ms (no pacing penalty) |
| Commits | branch `feat/zhihu-ratelimit-hardening` (6 commits `414331b`..`85a27ad`) → **merged local** `f603157` into `feat/agentcrawl-bootstrap` (no push, per §7); worktree removed, branch deleted |
| Step-8 RepoMem.merge (HITL, user-approved 2026-06-10) | module `decisions.md` D8 (mechanism, stays in code) + D9; **promoted 4 cross-SP root-causes** to global `crawl-pipeline.md §知乎链路`; temp `zhihu-engine-article-fallback/` pruned |

## 3. Re-scoping root-cause root should know (the live smoke earned this)

The smoke first ran with a STALE cookie and surfaced that the **real** barrier to 专栏 fetching is NOT burst
throttling but cookie/anti-bot, revising my own earlier optimistic read:

1. **Navigation HTML is `__zse_ck`-gated (time-sensitive).** `zhuanlan.zhihu.com/p/...` (and `www.zhihu.com`)
   nav-GET needs a FRESH `__zse_ck`; stale → 403 anti-bot **challenge page** (`<meta id="zh-zse-ck">`). Fresh
   `__zse_ck` (browser-computed, cookie-manager-synced) passes transparently — why the 06-07/09 probes saw nav-200.
   **Retry/backoff cannot recover this** (orthogonal to v1.2); only a fresh `__zse_ck` does.
2. **cookie domain-key = `.zhihu.com` (leading dot)** in cookie-manager — the dotless `zhihu.com` key is empty.
   All consumers (SP-3/SP-5a) must pull with the dotted key. (This was the actual reason 专栏 looked "broken".)
3. **Articles API needs `x-zse-96`** (403 `code 10003`) — no unsigned article endpoint exists; hence no fallback.

**Residual / your call (deferred, non-blocking):** for a long-running watcher, `__zse_ck` will periodically
expire → either (a) cookie-manager keeps syncing fresh cookies from the user's browser (works today), or (b)
introduce a `__zse_ck` solver/headless browser — same D1-boundary decision as the zse-96 signer, **yours to
make, not done here.** Flagged on the Dashboard for triage (non-blocking). v1.2's hardening is orthogonal and
still valuable (bulk consumers won't trip the burst throttle).

## 4. Lifecycle

- Burn `from-zhihuarticleimpler-blocker-zse96.md` (resolved by your A decision; this letter supersedes it).
- Burn this letter after you read it. SP-2 v1.2 → done on the Dashboard; `__zse_ck` residual → its own triage row.

— ZhihuArticleImpler (2026-06-10)
