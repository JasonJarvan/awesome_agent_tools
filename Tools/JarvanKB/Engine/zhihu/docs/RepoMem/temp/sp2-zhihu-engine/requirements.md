---
slug: sp2-zhihu-engine
status: in-progress
task_type: feature
domains: [crawl, zhihu]
updated_at: 2026-06-01
---

# SP-2 Zhihu Engine — task working state

> Task-scoped scratch. The authoritative design is
> `../../superpowers/specs/2026-05-31-SP-2-zhihu-engine-design.md` — **do not duplicate it here**.
> This file tracks only working state, open empirical questions, and the smoke checklist.

## Pipeline position
- Step 1 RepoMem.read ✓ · Step 2 brainstorming ✓ (design landed `d9d28f8`) · Step 3 capture (this) ·
  Step 4 writing-plans (next).

## Settled decisions (full rationale in design.md / will promote to decisions.md at Step 8)
- zse-96: **pure cookie + HTTP, no browser, no signer** (aligns user's Zhihu-Collections-MCP).
- Body: initialData JSON primary → CSS-selector → unsigned /api/v4 fallback.
- Image: engine emits remote URLs only (localization is SP-6).
- Question URL: return question + embedded answers in **full fidelity** (design tenet — engine
  maximizes extraction, consumers filter; request-boundary not value-judgment).
- Reimplement, do NOT lift reference code (reference unlicensed; JarvanKB → MIT).

## RESOLVED at smoke (verification gate, 2026-06-02, live cookies)
1. **comment_v5 signing: NO signature needed.** `/api/v4/comment_v5/answers/{id}/root_comment`
   returns 200 with plain cookies (d_c0/z_c0/__zse_ck). **No RSSHub signer required.** ✅
2. **Question initialData carries embedded answers in FULL content** — confirmed (bodies 53/3137/34
   chars, real votes 1269/694/333 sorted desc). Design tenet holds on live data. ✅
3. **Unsigned `/api/v4/answers/{id}?include=content` 403-fallback** path exists; not exercised live
   because the HTML-initialData primary path succeeded for all three types (no 403 hit). Fallback is
   unit-tested (engine test). ✅ (behavior verified by tests, not live — acceptable: it only fires on 403.)

## Two real bugs found by smoke + fixed (commit c3a4e0c, a919721)
- **initialData uses camelCase keys** (`voteupCount`/`commentCount`/`createdTime`/`updatedTime`,
  author `urlToken`), NOT snake_case. Parsers were reading snake_case → vote/time = 0/None. Fixed via
  `first(raw, camel, snake)` fallback (works for both initialData camelCase + /api/v4 snake_case).
- **comment_v5 is CURSOR-paginated, not offset.** Passing `offset` returns empty data + a
  self-referential `paging.next` → INFINITE LOOP. Fixed: first call `?order_by=score&limit=N` (no
  offset), follow `paging.next`, guarded (max_pages + seen-cursor set + empty-data break).
- Comment author is inline (`author.name`/`url_token`), child reply linkage via `reply_comment_id`
  (resolved to name via id→name map). Comment content now HTML→Markdown converted (a919721).

## Smoke checklist (live cookies — ALL PASSED 2026-06-02)
- [x] answer URL → markdown + metadata (vote=692, comment=110, real timestamps)
- [x] article (zhuanlan) URL → markdown + metadata (vote=68, comment=2)
- [x] question URL → title + detail + 5 embedded answers FULL content (real votes, vote-desc)
- [x] comments path → 15 comments (9 top + 6 child), cursor pagination, reply_to resolved, NO hang

## Decisions to promote at Step 8 merge (global-scope candidates)
- **Zhihu initialData camelCase** + **comment_v5 cursor-pagination (offset is poison)** are reusable
  facts for SP-5a Zhihu Watcher → promote to `docs/RepoMem/persist/architecture/crawl-pipeline.md`.
- `trust_env=False` direct-connect for Zhihu (China host; system proxy is for foreign sites) — module
  decision; note in module decisions.md.

## Cookies for smoke (how it was done)
Pulled from SP-1 cookie-manager via its own CLI (no build/edit): from `Service/crawl/cookie-manager`,
`COOKIE_MANAGER_CONFIG=config/cookie-manager.yaml node_modules/.bin/tsx src/cli.ts show domain=zhihu.com`
(box `jasonjarvan`, domain key `zhihu.com` holds d_c0/z_c0/__zse_ck). Extracted to gitignored
`tests/fixtures/cookies.local.json`. Engine takes cookies as injected input; sourcing is the consumer's job.
