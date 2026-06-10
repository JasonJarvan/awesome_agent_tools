# Module decision log

> Append-only, time-descending (newest at top).
> Each entry: date, slug, decision, rationale, what-changes-when-this-is-revisited.
> When a decision is promoted to global, leave a `[Promoted to global ↗]` marker pointing to `<root>/docs/RepoMem/persist/memory/`.

## 2026-06-10 · zhihu-engine-ratelimit-hardening (v1.2)

### D9 — nav-page HTML is `__zse_ck`-gated (time-sensitive); articles API is `x-zse-96`-gated  ⚠️ found at live smoke
Two distinct anti-bot gates surfaced when v1.2's live smoke ran with a STALE cookie — revising the earlier
optimistic "nav 200 is enough, no signature" read:
- **Navigation HTML** (`www.zhihu.com/...`, `zhuanlan.zhihu.com/p/...`) requires a FRESH `__zse_ck` cookie.
  Stale/absent → HTTP 403 returning an anti-bot CHALLENGE page (body carries `<meta id="zh-zse-ck">` + a
  `zse_ck` JS tracker), NOT the content. A fresh `__zse_ck` (browser-computed, synced by cookie-manager)
  passes transparently — which is why the 2026-06-07/09 probes saw 20/20 + 60/60 nav-200 (cookie was fresh
  then). Retry/backoff CANNOT recover this (every retry returns the same challenge); only a fresh `__zse_ck` does.
- **`/api/v4/articles/{id}`** (any `include=`) → 403 `code 10003` (signature gate), UNLIKE the unsigned
  `/api/v4/answers/{id}` (D5). So there is NO unsigned article api-fallback to mirror — v1.2 therefore did NOT
  add one and did NOT introduce a signer (honors D1). `api.zhihu.com/articles/{id}` → 403 `code 40362` (risk-control).
- **cookie domain-key gotcha**: cookie-manager stores zhihu cookies under **`.zhihu.com` (leading dot)**, not
  `zhihu.com` (the dotless key is empty). All consumers must pull with the dotted key.
Revisit if Zhihu drops the `__zse_ck` nav gate or starts gating the unsigned answer/comment APIs.

> D9 is cross-SP-reusable (SP-3 Skill / SP-5a Watcher both pull cookies + fetch nav pages). **[Promoted to global ↗]**
> `<root>/docs/RepoMem/persist/architecture/crawl-pipeline.md` §知乎链路 — promoted 2026-06-10 (HITL, user).

### D8 — engine has built-in proactive rate-limit + reactive 403/429 backoff (no signer)
All four outbound httpx call sites (`get_page`, `get_api_answer`, `fetch_comments`, `fetch_child_comments`)
route through one `fetcher._request`: a process-wide `_RateLimiter` (min-interval + jitter, shared so bulk
consumers self-pace while single-URL callers are ~unaffected) + retry on 403/429 with exponential backoff
honoring `Retry-After`. Empirical basis: Zhihu's throttle is BURST/CONCURRENCY-sensitive, not cumulative
(60 sequential nav-GETs @ ~2 req/s = zero throttle). Tunable via module-level `zhihu.configure(...)`;
conservative defaults (min_interval=0.3, jitter=0.2, max_retries=3); non-breaking (`fetch()`/`FetchResult`
unchanged). Mechanism lives in `src/zhihu/fetcher.py`; contract note in `docs/interface.md §11`. This hardens
against burst-throttle 403s; it does NOT solve the D9 `__zse_ck` nav gate (orthogonal — cookie freshness).
Revisit if a consumer needs a per-call rate override (add a param) or if Zhihu's throttle model changes.

> D8 mechanism stays in code — NOT promoted (step-8 standard: mechanism in code / codegraph-derivable is not
> promoted). The cross-SP root-cause ("throttle is burst-sensitive → engine paces + backs off, tune via
> `configure`") rides along as a one-liner under the §知乎链路 promotion below.

## 2026-06-02 · zhihu-engine-comment-tree (v1.1 follow-up)

### D7 — child_comment is OFFSET-paginated, but `paging.next`-verbatim is the safe driver  ⚠️ verified live
The full child-reply endpoint `/api/v4/comment_v5/comment/{root_id}/child_comment` is **offset**-based
(its `paging.next` embeds `offset=`; paging keys `is_end/is_start/next/previous/totals`) — *different* from
`root_comment`, which is cursor-based (D3). We deliberately do NOT construct `offset` ourselves; we follow
`paging.next` **verbatim** (same discipline as `fetch_comments`), which works for cursor AND offset models
and stays immune to the D3 offset-poison hang regardless. Two live gotchas (answer 2045055171106009805,
root 11497692920, 28 children): (a) the root response's `child_comment_next_offset` was **`None` even
though 28 children exist and the inline preview was empty** — so the decision "does this root need a child
fetch?" must key off `child_comment_count > len(inline preview)`, **NOT** off `child_comment_next_offset`;
(b) no `x-zse-96` on the child endpoint either (HTTP 200 plain cookies — D5 extends to child_comment).
Mechanism lives in `src/zhihu/comments.py` (`fetch_child_comments` + the `fetch_comments` expansion block).
Revisit if Zhihu changes the child-comment pagination contract.

> D7 cross-SP-reusable gotcha (SP-5a Watcher fetches the same comment substrate). **[Promoted to global ↗]**
> `<root>/docs/RepoMem/persist/architecture/crawl-pipeline.md` §知乎链路 — promoted 2026-06-02 (HITL-approved,
> user). Global copy holds only the non-code gotcha; mechanism stays here + in code (no-duplication).

## 2026-06-02 · sp2-zhihu-engine

### D6 — Design tenet: engine maximizes extraction, consumers filter
The engine returns full-fidelity data for whatever a single page load yields (incl. question pages'
embedded answers in FULL content, not truncated previews); it never pre-judges value/redundancy. The
only boundary is the **request boundary** — no extra requests beyond one page (answer-list pagination,
collection iteration belong to SP-5a). Revisit if a consumer needs a lighter payload (add an opt-in
projection param rather than truncating in the engine).

### D5 — comment_v5 needs NO signature (verified live)
`/api/v4/comment_v5/{answers|articles}/{id}/root_comment` returns 200 with plain cookies
(d_c0/z_c0/__zse_ck). The pre-implementation worry that comments might hard-enforce x-zse-96 was
**disproven at smoke**. No RSSHub signer needed. Revisit only if Zhihu starts 403-ing comment calls.

### D4 — `trust_env=False` on all httpx calls (direct connect for Zhihu)
Zhihu is hit **directly**, bypassing any system proxy (the host has `HTTP_PROXY`/`ALL_PROXY` for
foreign sites; Zhihu is a mainland site reachable directly and routing it through a foreign proxy is
slower + risk-control-suspect). Also dodges a SOCKS-transport init crash in proxied envs. Revisit if a
deployment legitimately needs an egress proxy → then expose an explicit `proxy=` param (do NOT re-enable
env-proxy autodiscovery).

### D3 — comment_v5 is CURSOR-paginated, NOT offset  ⚠️ bug found at smoke
Passing `offset` to the comment endpoint returns **empty `data` + a self-referential `paging.next`** →
the original offset-loop hung forever. Correct model: first call `?order_by=score&limit=N` (no offset),
then follow `paging.next` verbatim until `is_end`. Guarded with max_pages + a seen-cursor set + an
empty-data break. Revisit if Zhihu changes the comment pagination contract.

### D2 — Zhihu `js-initialData` uses camelCase keys  ⚠️ bug found at smoke
initialData entity fields are camelCase (`voteupCount`/`commentCount`/`createdTime`/`updatedTime`,
author `urlToken`), while the `/api/v4` JSON uses snake_case. Parsers read **camelCase-first with
snake_case fallback** via `_entities.first(raw, *keys)`, so both the primary initialData path and the
api-fallback path work. Article timestamps are `created`/`updated` (not `createdTime`). Revisit if
Zhihu's frontend state schema changes.

### D1 — zse-96 sidestepped: pure cookie + HTTP, no browser, no signer
The engine does NOT compute the `x-zse-96` signature. Page-navigation HTML (server-rendered, embeds
`js-initialData`) is the primary source; CSS-selector scrape is fallback 1; unsigned
`/api/v4/answers/{id}` is fallback 2 (on 403). Rationale: lightest runtime, headless-server-trivial,
fully unit-testable, lowest maintenance — and it matches a path the user runs in production
(`JasonJarvan/Zhihu-Collections-MCP`). MediaCrawler's signer is NON-COMMERCIAL-licensed (must not
vendor); RSSHub's is MIT and was the documented fallback if a signed endpoint ever became unavoidable —
not needed for v1 (see D5). Revisit if Zhihu starts gating the HTML page or the unsigned `/api/v4`
endpoints behind the signature. Full rationale: `../superpowers/specs/2026-05-31-SP-2-zhihu-engine-design.md`.

> D1–D5 reusable by SP-5a Zhihu Watcher (same fetch substrate). **[Promoted to global ↗]**
> `<root>/docs/RepoMem/persist/architecture/crawl-pipeline.md` §知乎链路（SP-2 实现）— promoted
> 2026-06-02 (HITL-approved, user). Global copy holds only the non-code root-causes/gotchas; mechanism
> stays here + in code + interface.md (no-duplication).

## Done in v1.1

- **Comment full-tree crawl** — ✅ **DONE 2026-06-02** (merge `9081cbc`, task slug `zhihu-engine-comment-tree`,
  58 unit tests + live smoke). Each root comment's FULL child set is now paginated via
  `/api/v4/comment_v5/comment/{cid}/child_comment` and flattened two-layer (was: inline preview only).
  See **D7** above for the empirical model/gotchas. Was Deferred item #1 (top priority).

## Deferred → still open (not in v1 / v1.1 scope)

Priority order (user-set 2026-06-02): ~~comment full-tree~~ (done) > image dedup.

1. Image dedup — Zhihu HTML ships the same `<img>` twice (noscript + lazy-load) → Markdown shows
   `![](url)![](url)`. Dedup by `src` in the markdown converter. Cosmetic; lower priority.
2. Question answer-list pagination — intentionally NOT done (design tenet: single page in; full
   answer-list belongs to SP-5a Watcher).
