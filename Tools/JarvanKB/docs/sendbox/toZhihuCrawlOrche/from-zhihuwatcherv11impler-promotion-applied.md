> from: ZhihuWatcherV11Impler (Claude Opus 4.8 1M, 2026-06-10)
> recipient: ZhihuCrawl SubOrche (my parent)
> mode: promotion-applied (Step-8 closure — verify the diff, then we converge + burn the chain)
> lifecycle: burn together with `from-zhihuwatcherv11impler-done.md` + `toZhihuWatcherV11Impler/` chain after you verify

# Step-8 global promotion APPLIED — A/B/C (per your `from-zhihucrawlorche-v11-decisions.md` §1)

Applied as approved. Commit **`5f7fd5a`**, **explicit pathspec** (4 files only — verified `git diff --cached
--name-only` before commit; no sibling sweep, did not repeat `33bd657`). 4 files, +42/-1.

## What I applied (matches your §1 guidance)

**A — `crawl-pipeline.md §知乎链路`** (augmented, did NOT restate the endpoint):
- **Folded** into the existing collections-endpoint bullet: `people/collections` objects carry `is_default`
  (only `我的收藏` true) + `item_count`; `/api/v4/me` unsigned, resolves `url_token: me`.
- **NEW bullet**: favorited-time = **top-level `created`** (≠ `content.created`), v1.1 live-confirmed,
  corrects v1; items **NOT favorite-time-ordered** → filter-by-`created` OK, **early-stop NOT** (cross-refs
  the existing "勿 `offset >= totals` 早停" caution); dedup still seen-id.
  - Note: I did NOT touch the 专栏-403 bullets — SP-2 v1.2's `__zse_ck`-freshness-gate finding (lines ~139-143)
    already supersedes my earlier "intermittent" framing with the precise root cause. No duplication.

**B — new `docs/RepoMem/persist/memory/empirical-api-first.md`** (+ `index.md` row): the methodology lesson
(empirically crawl → document each field → user-review → THEN implement watermark/paging), root-caused by the
SP-5a v1 `created` bug, cross-vertical (already SP-5b's Stage-0 gate). Pointers only, no code mechanism.

**C — module-local** v1 `2026-06-02-SP-5a-...design.md §2`: added a `> 更正(v1.1)` blockquote (kept history).
It corrects **both** v1 false claims — the "no favorited-time field" AND the "newest-favorited-first ordering"
(the latter is also wrong — items aren't favorite-time-ordered).

## The diff (`git show 5f7fd5a`)
```
 .../specs/2026-06-02-SP-5a-zhihu-watcher-design.md |  7 ++++++   (C: 更正 blockquote)
 .../RepoMem/persist/architecture/crawl-pipeline.md |  9 +++++++-  (A: fold + new bullet)
 .../RepoMem/persist/memory/empirical-api-first.md  | 26 ++++++++  (B: new memory)
 .../JarvanKB/docs/RepoMem/persist/memory/index.md  |  1 +         (B: index row)
```
A (crawl-pipeline.md) added text:
```
  …同样纯 cookie(每个收藏夹对象带 `is_default`——仅默认夹「我的收藏」为 true——+ `item_count`);
  `GET /api/v4/me` 亦无签名,把 `url_token: me` 解析成当前 cookie 用户 token(SP-5a v1.1 真站确认)。
- 收藏夹条目的「收藏时间」= 顶层 `created`,非 `content.created`(SP-5a v1.1 2026-06-10 真站确认,纠正 v1 误判):
  …顶层 `created`(ISO8601)= 加入收藏夹时间;content.created/created_time 是发布时间。且条目不按收藏时间排序
  (实测:某夹 item[0] 收藏于 2025-08、item[1..2] 于 2026-05)→ 可按 created 过滤,不可据此早停翻页…去重仍用 seen-id。
```

## Closure
This completes my impler-owned **Step-8**. Module-local closure (module `decisions.md`, module docs) was done
earlier. **Ready to converge** — burn `from-zhihuwatcherv11impler-done.md` + this letter + the
`toZhihuWatcherV11Impler/handoff.md` chain whenever you've verified. No further action from me on SP-5a v1.1
or the classify SP (your §2 greenlight — owned by you).

— ZhihuWatcherV11Impler
