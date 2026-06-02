---
from: SP2Impler (Claude Opus 4.8) — your predecessor on Engine/zhihu
to: ZhihuCommentImpler (a future Claude Code session, cwd = repo root)
type: handoff
slug: zhihu-engine-comment-tree
created: 2026-06-02
lifecycle: persist-until-picked-up (burn after you write a done letter and orche reads it)
---

# Handoff — Zhihu Engine v1.1: full comment-tree crawl

## 0. What this is
A **follow-up task** on the already-merged `Engine/zhihu/` (SP-2, done 2026-06-02, merge `f8c14cb`).
You are the successor. Scope is narrow: make comment fetching **exhaustive** (full tree), which v1
deliberately deferred. Run the v2 8-step pipeline, but it's small — brainstorming will likely auto-skip.

## 1. The gap to close
v1 `Engine/zhihu/src/zhihu/comments.py` flattens **only the inline `child_comments`** that the
`root_comment` response ships (a truncated preview of direct replies). It does NOT paginate a root
comment's full child set. The user set priority: **comment full-tree > image dedup** — this is the
top v1.1 item.

**Deliver:** for each root comment, fetch ALL its child replies (not just the inline preview), still
flattened two-layer (`parent_id` = root id, `reply_to_author` resolved). Keep it bounded by
`comment_limit` and loop-guarded.

## 2. The endpoint (verified live 2026-06-02)
- Root comments (already implemented, cursor-paginated): `GET /api/v4/comment_v5/{answers|articles}/{id}/root_comment?order_by=score&limit=N` → follow `paging.next`.
- **Child replies (NEW work):** `GET /api/v4/comment_v5/comment/{root_comment_id}/child_comment?order_by=ts&limit=N&offset=...` — the root response carries `child_comment_count` and `child_comment_next_offset` per root; use those to decide whether to paginate children. **VERIFY the child endpoint's pagination model at smoke** — root_comment is cursor-based and `offset` is poison there; the child endpoint MAY differ. Do not assume; test it live first (see §4 gotchas).
- No `x-zse-96` signature needed (plain cookies) — confirmed for root; re-confirm for child at smoke.

## 3. Where the code is (all under `Engine/zhihu/`)
- `src/zhihu/comments.py` — `flatten_comments(root_pages)` + `fetch_comments(item_type, item_id, *, cookies, limit, headers, page_size, max_pages)`. Extend here.
- `src/zhihu/models.py` — `Comment(id, parent_id, author, content, like_count, created_at, reply_to_author)`. Flat two-layer; do NOT build a tree.
- `tests/test_comments.py` — existing unit tests (real-schema fixtures, cursor pagination, infinite-loop guard). Add child-pagination tests.
- `pip install -e ".[dev]"` from `Engine/zhihu/`; `pytest`. (Your own fresh venv — the predecessor's `.venv` was in a now-removed worktree.)

## 4. Critical gotchas (from `Engine/zhihu/docs/RepoMem/decisions.md` D2–D5 — READ IT)
- **`offset` is poison on `root_comment`** → empty data + self-referential cursor → infinite loop. The child endpoint may or may not share this; **test before trusting offset**.
- `js-initialData`=camelCase, `/api/v4`=snake_case. Comment API author is inline snake_case (`author.name`/`url_token`).
- `trust_env=False` on all httpx calls (Zhihu direct; host proxy is for foreign sites).
- comment content is HTML → run through `html_to_markdown` (v1 already does for inline children — keep consistent).
- Guard every pagination loop: `max_pages` + seen-cursor/offset set + empty-data break. The predecessor's smoke HUNG on an unguarded loop — do not repeat.

## 5. Cookies for smoke (consumer path)
From `Service/crawl/cookie-manager` (service runs on `127.0.0.1:48088`):
`COOKIE_MANAGER_CONFIG=config/cookie-manager.yaml node_modules/.bin/tsx src/cli.ts show domain=zhihu.com`
(box `jasonjarvan`; meaningful cookies `d_c0`/`z_c0`/`__zse_ck`). Write to a **gitignored**
`Engine/zhihu/tests/fixtures/cookies.local.json` (the `*.local*` gitignore rule already covers it).
NEVER commit cookies.

## 6. Acceptance (verification-before-completion)
- Unit: child-pagination flattening (fixtures), loop-guard for child endpoint, `comment_limit` caps the total.
- **Mandatory live smoke**: a real answer with a root comment having >N children → confirm you fetch
  ALL of them (count == `child_comment_count`), no hang, flattened with correct `parent_id`/`reply_to_author`.
- Use TDD + subagent-driven (the user's standing preference). Keep the engine pure-fetch.

## 7. Closure
This is an `Engine/zhihu` follow-up — **you own Step 8 RepoMem.merge closure** (impler owns merge,
recipe v2). Update `Engine/zhihu/docs/RepoMem/decisions.md` (move item #1 out of Deferred). Write a
done letter to `docs/sendbox/toOrchestrator/`. Branch off `feat/agentcrawl-bootstrap` in a worktree
(local commits only, no push). Then burn this handoff.

## 8. Out of scope
Image dedup (lower priority, v1.1 item #2 — leave it), question answer-list pagination (that's SP-5a).
