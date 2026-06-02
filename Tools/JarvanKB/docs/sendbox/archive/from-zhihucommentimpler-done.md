> from: ZhihuCommentImpler session (Claude Opus 4.8 1M, 2026-06-02)
> recipient: orchestrator (and any future orchestrator)
> mode: milestone-done
> purpose: confirm Zhihu engine v1.1 (full comment-tree crawl) completion; close the zhihu-engine-comment-tree handoff
> lifecycle: persist until next milestone, then archive

# milestone-done — Zhihu Engine v1.1: full comment-tree crawl

Task slug `zhihu-engine-comment-tree` (the SP-2 v1.1 follow-up you handed off via `toZhihuCommentImpler/handoff.md`).

## What was delivered

- `Engine/zhihu/src/zhihu/comments.py`: new module-level `fetch_child_comments(root_comment_id, ...)` that
  paginates a root comment's FULL child set via `/api/v4/comment_v5/comment/{id}/child_comment`, following
  `paging.next` **verbatim** (never constructing `offset`). `fetch_comments` now expands each root whose
  `child_comment_count > len(inline preview)` by REPLACING the inline `child_comments` preview with the full
  fetched set, then reuses the unchanged `flatten_comments` to emit the whole two-layer flat list. Bounded by
  `comment_limit` (final `flat[:limit]` is the hard cap; a counter only suppresses needless requests),
  loop-guarded (max_pages + seen-`next` set + empty-data break — same discipline as the root loop).
- 6 new unit tests (child pagination, two loop guards, full-tree orchestration, no-over-fetch, comment_limit
  cap, multi-root) + the code-review minor fixes.

## Verification (single gate, v2)

- **58 unit tests pass** (51 baseline + 7 new) — fresh run on the merged `feat/agentcrawl-bootstrap`.
- **Mandatory live smoke PASSED** (real cookies via SP-1 cookie-manager; answer `2045055171106009805`,
  root comment `11497692920` with 28 children): fetched 28/28 (== `child_comment_count`), no hang, two-layer
  flatten correct (every non-root `parent_id` → a root), `reply_to_author` resolved 28/28, HTTP 200 plain cookies.
- Code review: dispatched a fresh reviewer (verdict **Ready to merge: Yes**, 0 Critical/Important); its 3
  actionable Minors (multi-root test + 2 clarifying comments) were applied before merge.

## Open empirical question from your handoff — RESOLVED

Your §2 flagged "VERIFY the child endpoint's pagination model at smoke; offset may be poison like root."
**Live finding:** the child endpoint is actually **OFFSET-based** (its `paging.next` embeds `offset=`),
*different* from `root_comment` (cursor). But following `paging.next` verbatim handled it correctly and stays
immune to the D3 offset-poison regardless — **no code change was needed.** Two gotchas worth knowing:
(a) the root's `child_comment_next_offset` was `None` even with 28 children + empty inline preview, so the
"need a child fetch?" decision keys off `child_comment_count`, NOT that hint; (b) the child endpoint needs no
`x-zse-96` either (D5 extends).

## Step 8 RepoMem.merge — CLOSED (impler-owned, HITL-approved by user)

- Module `Engine/zhihu/docs/RepoMem/decisions.md`: added **D7** (child_comment offset model + gotchas);
  moved Deferred item #1 (comment full-tree) into a "Done in v1.1" section.
- Global promotion (per the step-8 standard): added the cross-SP-reusable child_comment gotcha to
  `docs/RepoMem/persist/architecture/crawl-pipeline.md` §知乎链路 (gotcha only; mechanism stays in code) —
  so SP-5a Watcher (which won't read `Engine/zhihu`'s module memory) sees it. Consistent with the SP-2 D1–D5 promotion.
- Temp docs `temp/zhihu-engine-comment-tree/{requirements,architecture}.md` marked `status: merged` (kept for SP-5a reference).

## Commit chain (branch merged into `feat/agentcrawl-bootstrap`, local, no push)

`dd323c4` fetch_child_comments · `d499acb` loop-guard tests · `c8928e3` fetch_comments expansion ·
`1fe829c` no-over-fetch + limit-cap tests · `ca4a7f7` plan + temp docs · `0bca3d9` code-review minors ·
merge commit `9081cbc` (--no-ff). Feature branch `feat/zhihu-comment-tree` + its worktree removed post-merge.
Step-8 doc edits (decisions/crawl-pipeline/Dashboard/temp-status) + this letter land in a follow-up closure commit.

## Disposition of the handoff

`docs/sendbox/toZhihuCommentImpler/handoff.md` — **burned** (git rm) in the closure commit, per handoff §7.

## Dashboard

SP-2 row annotated: v1.1 comment-tree ⚫ done (merge `9081cbc`, 58 tests + live smoke; Step 8 closed).

## Notes for the vertical

- **SP-5a Zhihu Watcher** impler: if you touch comment pagination, read `crawl-pipeline.md` §知乎链路 — the
  child_comment offset/`next_offset`-trap gotcha is now there alongside the root offset-poison.
- No overlap with the concurrent SP-4a bilibili work; merge was conflict-free.

— ZhihuCommentImpler
