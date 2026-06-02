---
slug: zhihu-engine-comment-tree
status: merged
task_type: feature
domains: [crawl-pipeline, zhihu]
updated_at: 2026-06-02
merged_to: [Engine/zhihu/docs/RepoMem/decisions.md (D7 + Done-in-v1.1), docs/RepoMem/persist/architecture/crawl-pipeline.md (§知乎链路 child_comment gotcha)]
---

# Zhihu Engine v1.1 — full comment-tree crawl (task working state)

> Source-of-truth handoff: `<root>/docs/sendbox/toZhihuCommentImpler/handoff.md` (slug
> `zhihu-engine-comment-tree`). Module decision log: `../../decisions.md` (D1–D6 + Deferred item #1).
> **Do not duplicate** those here — this file tracks only the task's working state + open questions.

## The gap (one line)
v1 `comments.py` flattens only the **inline `child_comments` preview** the root response ships. It does
NOT paginate a root comment's full child set. Close that.

## Deliverable
For each root comment, fetch ALL its child replies (not just the inline preview), still flattened
two-layer (`parent_id` = root id, `reply_to_author` resolved). Bounded by `comment_limit`, loop-guarded.

## Acceptance (mirrors handoff §6 — the verification gate)
- Unit: child-pagination flattening (fixtures), loop-guard on the child endpoint, `comment_limit` caps total.
- **Mandatory live smoke**: a real answer with a root comment having > page_size children →
  count fetched == `child_comment_count`, no hang, correct `parent_id` / `reply_to_author`.

## Out of scope (handoff §8)
Image dedup (v1.1 #2), question answer-list pagination (SP-5a).
