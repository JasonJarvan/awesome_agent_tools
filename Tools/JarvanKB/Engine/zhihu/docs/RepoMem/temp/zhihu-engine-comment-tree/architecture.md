---
slug: zhihu-engine-comment-tree
status: active
domains: [crawl-pipeline, zhihu]
updated_at: 2026-06-02
---

# Design notes — full comment-tree crawl

## Approach (decided, no brainstorming needed)
1. **New fn `fetch_child_comments(root_comment_id, *, cookies, headers, page_size, max_pages, limit)`**
   → returns `list[dict]` of raw child-comment dicts in the SAME schema as inline `child_comments`.
2. **`fetch_comments` orchestration:** after collecting root `pages`, for each root comment where
   `child_comment_count > len(inline child_comments)`, call `fetch_child_comments` and **replace**
   `c["child_comments"]` with the full set. Then `flatten_comments(pages)` works unchanged
   (it already reads each root's `child_comments` and builds the `id→name` map across them).
3. **Replace, not merge** the inline preview — avoids a dedup pass; refetching from scratch costs at most
   one extra page. (Engine design tenet D6: maximize extraction, correctness > minimizing requests.)

## Pagination model — the one open empirical question
- Root `root_comment` is **cursor**-paginated; `offset` is poison there (D3 — empty data + self-ref cursor → hang).
- Child `child_comment` model is **UNKNOWN** until smoke. Handoff §2: endpoint takes `?order_by=ts&limit=N&offset=...`
  and root carries `child_comment_count` / `child_comment_next_offset`.
- **Decision: follow `paging.next` VERBATIM** (same discipline as `fetch_comments`) — never construct
  `offset` ourselves. `next` embeds whatever the server needs (cursor OR offset), so this is immune to the
  D3 offset-poison regardless of which model child uses. Same loop guard: `max_pages` + seen-`next` set +
  empty-data break + `is_end` break.
- **IF smoke shows** child returns no usable `paging.next` (only `child_comment_next_offset`) → fall back to
  server-provided offset THEN, informed by live behavior. Do NOT add speculative offset code before smoke.

## Loop-guard / limit
- `comment_limit` caps the TOTAL flattened list (`flat[:limit]`, already there). Add early-stop: stop
  attaching more children once running total ≥ limit (avoids over-fetch), final slice is the hard cap.
- `trust_env=False` on the new httpx call (D4). content → `html_to_markdown` (handled by `flatten_comments`).

## Smoke findings (RESOLVED — live, 2026-06-02, answer 2045055171106009805)
- **child endpoint pagination model = OFFSET** (`paging.next` embeds `offset=`; paging keys
  `is_end/is_start/next/previous/totals`). DIFFERENT from root_comment (cursor). BUT following
  `paging.next` VERBATIM works perfectly and stays immune to the D3 poison (we never construct offset).
  → **no code change needed**; the paging.next-verbatim design held on live data.
- child data schema = snake_case `id/content/like_count/created_time/author/reply_comment_id` — all
  present; `flatten_comments` consumes child-endpoint dicts unchanged.
- count == child_comment_count: **28 == 28 ✅** for root 11497692920 (fetch_child_comments page_size=5).
- end-to-end `fetch_comments`: 125 roots, target root's 28 children fully present in the two-layer flat
  list (total 197), every non-root `parent_id` → a root, `reply_to_author` resolved 28/28.
- no `x-zse-96` on child endpoint (HTTP 200 plain cookies) — D5 extends to child_comment.
- **gotcha confirmed:** root's `child_comment_next_offset` was `None` AND inline preview was empty (0)
  while `child_comment_count=28` → deciding pagination off `child_comment_count > len(inline)` (not off
  next_offset) is correct; the child endpoint's OWN `paging.next` drives pagination, not the root's hint.
- side note: server returns its own default page (20/page) even when `limit=5` is requested — harmless;
  pagination via `next` still reaches all children.
