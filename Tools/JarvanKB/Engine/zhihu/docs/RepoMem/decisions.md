# Module decision log

> Append-only, time-descending (newest at top).
> Each entry: date, slug, decision, rationale, what-changes-when-this-is-revisited.
> When a decision is promoted to global, leave a `[Promoted to global ↗]` marker pointing to `<root>/docs/RepoMem/persist/memory/`.

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
