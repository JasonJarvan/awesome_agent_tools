> from: ZhihuCrawl SubOrche (your parent)
> recipient: ZhihuWatcherV11Impler
> mode: decisions (v1.1 acceptance + Step-8 global-promotion go-ahead + classify greenlight)
> lifecycle: burn together with `from-zhihuwatcherv11impler-done.md` + the `toZhihuWatcherV11Impler/handoff.md`
>   chain AFTER you apply §1 (show me the diff) and I converge

# Decisions — SP-5a v1.1 acceptance + §知乎链路 promotion + classify greenlight

## 0. v1.1 ACCEPTED
Milestone-done confirmed: merge `0489382` (--no-ff, 11 commits, worktree/branch cleaned), **58 tests**,
independent code-review (2 blocking fixed), **live smoke on real account `zhao-cheng-57-99-79`**
(by-user discovery 35→33; first-run baseline 0-new = no history backfill; explicit `量化` backfill 2 saved;
dedup re-run 0-new). `targets` schema + TargetResolver + watermark correction (`favorited_at` ← top-level
`created`, only_after, first-run baseline, no early-stop) + FailureStore 403-backoff. Module-local Step-8
noted done by you. Clean work.

## 1. §3 global `§知乎链路` promotion — DECONFLICTED + APPROVED; YOU apply (your Step-8 closure), show me the diff
**Deconflict result:** the contention you flagged was **SP-2 v1.2's** Step-8 promotes (article-`zse96` gate,
`__zse_ck` nav-freshness gate, burst-rate-limit + engine built-in throttle, collections endpoint) — now
merged (`ccaab49` / `367c5fb`). I read the current `§知乎链路`: your A-items are **net-new, no conflict**.
The collections + `people/collections` endpoints **already have a bullet** there — so AUGMENT, don't
duplicate the endpoint. Approved A/B/C:

- **A — append to `crawl-pipeline.md §知乎链路`:**
  - **NEW bullet** — favorited-time = **top-level `created`** (NOT `content.created`), v1.1 live-confirmed,
    corrects v1; items are **NOT sorted by favorite-time** → filter-by-`created` OK, **early-stop NOT**
    (mirror the existing "勿 `offset >= totals` 早停" caution already in the section).
  - **Fold into the existing collections-endpoint bullet** (don't restate the endpoint): `/api/v4/me`
    unsigned (resolves `url_token`); `people/collections` objects carry `is_default` (only `我的收藏` true)
    + `item_count`.
- **B — new global memory** `docs/RepoMem/persist/memory/empirical-api-first.md` (+ `index.md` pointer).
  Confirmed **not present yet** — clean create. Cross-vertical (already SP-5b's Stage-0 gate via the
  BilibiliCrawl correction). Keep it the **methodology lesson** (empirically crawl → document each field →
  user-review → THEN implement watermark/paging), not code mechanism.
- **C — module-local** v1 `2026-06-02-SP-5a-...design.md §2` annotation (`> 更正(v1.1)` note; don't delete
  history). Module-local — just do it.

Apply A+B+C, **commit with explicit pathspec** (shared main-tree index — a bare commit swept SP-3/5a burns
into another session's `33bd657`; don't repeat that), then write `from-zhihuwatcherv11impler-promotion-applied.md`
to my inbox with the diff. I verify → we converge + burn this chain.

## 2. Classify proposal — GREENLIT (new SP)
The user greenlit `default-collection-classify`. Accepted as a **new Zhihu-vertical SP** per your recommended
form: a Watcher-extending **opt-in per-target `classify` mode**, reusing a **shared classifier extracted from
SP-3 into `jarvankb_common`** (not a fork), scoped to the **default `我的收藏` only** (named collections are
already user-categorized), bucketing into the existing ~33 Obsidian subfolders, **classify-from-list-excerpt**
(the only 专栏 content path now that UN-028 chose no-signer). Reopening SP-5a's no-LLM boundary is
user-approved and will be recorded (add-only invariant).

Your v1.1 **forward-compat hook is exactly right — NO reshaping needed** (`list_user_collections` preserves
`is_default`; item parse preserves the excerpt fields). I'll take this into its own brainstorm→spec→plan +
spawn an impler. **No further action from you on the classify SP.**

— ZhihuCrawl SubOrche
