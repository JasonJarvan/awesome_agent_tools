> from: ZhihuWatcherV11Impler (Claude Opus 4.8 1M, 2026-06-10)
> recipient: ZhihuCrawl SubOrche (my parent)
> mode: milestone-done + decisions (Step-8 global-promotion DELEGATED to you — see §3)
> purpose: SP-5a v1.1 done + merged; hand you the global `§知乎链路` promotion decision (it is cross-SP +
>   contended + persist-governance, and the user directed me to let you decide)
> lifecycle: persist until you (a) decide/apply the §3 promotion and (b) converge; then burn this + the
>   `toZhihuWatcherV11Impler/handoff.md` chain

# milestone-done — SP-5a Zhihu Watcher v1.1 (target-resolution + watermark + 403 backoff)

Task slug `sp5a-watcher-v1.1`. Full v2 pipeline executed end-to-end (brainstorm → spec → plan →
worktree+subagent-TDD → verify → finish). **Local-only; no push, no main.**

## 1. Delivered + merged
Merged `0489382` (`--no-ff`) into `feat/agentcrawl-bootstrap`; worktree + branch cleaned up. 11 commits.
- `targets` schema (clean replace of v1 `collections`): `type: collection` + `type: user` (auto-discover a
  user's NAMED collections). New `resolver.TargetResolver` (per-cycle expand → `list[CollectionConfig]`;
  collections-before-users so explicit names win; skip `is_default` unless `include_default`; skip empty;
  per-target graceful degradation). **Default `我的收藏` skipped by default** (reserved for the classifier SP).
- Watermark correction: `CollectionItem.favorited_at` from top-level `created`; optional `only_after`
  (tz-aware, naive rejected) + first-run per-collection baseline so a fresh by-user watch does NOT back-fill
  history. seen-id stays the dedup backbone. **No early-stop** (items not favorite-time-ordered).
- `failure_store.FailureStore` (time-window 403 backoff, DI clock).
- `favorites_client`: `list_user_collections` (people/collections paging) + `get_current_url_token` (/me).
- example config + module docs (interface/README/runbook) updated; `output_dir` = the Obsidian Zhihu library.

## 2. Verification (single gate — passed)
- **58 tests** pass (v1's 32 migrated for the rename + new Watcher DI signature; 26 new across
  config/favorites_client/resolver/failure_store/watermark/watcher incl. a real-resolver e2e test). Verified
  on the post-merge tree too.
- Independent code-review (subagent, code-reviewer template): 2 blocking issues fixed (tz-aware datetime
  guard; example config/docs) + unused import; verdict ready-to-merge.
- **Live smoke (real SP-1 + real account `zhao-cheng-57-99-79`, 2026-06-10):** `/api/v4/me` 200 unsigned →
  url_token resolved; by-user discovery **35 collections → 33** (skipped default `我的收藏` + 1 empty);
  first-run baseline → "0 new" (history not back-filled); explicit `量化` (backfill=true) → 2 fetched+saved;
  re-run → 0 new (dedup confirmed live).

## 3. DELEGATED TO YOU — Step-8 global `§知乎链路` promotion (decide + apply, or coordinate)
Module-local Step-8 closure is **DONE by me** (module `decisions.md` 2026-06-10 entry; module docs). The
**global** promotion I am handing to you because (a) `crawl-pipeline.md §知乎链路` is cross-SP and was being
edited by another session today (contention), (b) persist is your/root's governance, and (c) the user
explicitly directed me to let you decide. My promotion candidates (all cross-SP-reusable root-causes, not
code mechanism):

**A. Append to `crawl-pipeline.md §知乎链路`:**
```
- 收藏夹条目的「收藏时间」= 顶层 `created`(非 `content.created`)(SP-5a v1.1 真站确认,纠正 v1 误判):
  每条 data[] 有顶层 `created`(ISO8601)= 加入收藏夹时间;content.created/created_time 是发布时间。
  但条目不按收藏时间排序(实测:某夹 item[0] 收藏于 2025-08、item[1..2] 于 2026-05)→ 可按 created 过滤(跳旧),
  不可早停(会漏掉排在旧条目后的新条目)。
- `/api/v4/me` 同样无需 x-zse-96(纯 cookie 200,用于解析 url_token: me);/people/{url_token}/collections
  每个收藏夹带 is_default(仅默认夹「我的收藏」为 true)+ item_count。
```
**B. New global memory `docs/RepoMem/persist/memory/empirical-api-first.md` (+ index.md pointer):** the
methodology lesson — "don't armchair API field semantics from a reference repo; empirically crawl → document
each field → user-review → THEN implement watermark/paging logic." Root-caused by the SP-5a v1 `created`-field
bug; surfaced by you-the-vertical via the BilibiliCrawl SubOrche correction letter
(`toOrchestrator/from-bilibilicrawlorche-sp5a-watermark-correction.md`), already SP-5b's Stage-0 gate.
**C. Module-local fix** to v1 `2026-06-02-SP-5a-...design.md §2` (lines 68-70): annotate the false
"no favorited-time field" claim with a `> 更正(v1.1)` note pointing to the v1.1 field doc (don't delete history).

Full empirical evidence: `Service/crawl/zhihu-watcher/docs/RepoMem/temp/sp5a-watcher-v1.1/api-fields-empirical.md`.
If you'd rather I apply A/B/C myself once you've deconflicted §知乎链路 with the other session, say so in
`toZhihuWatcherV11Impler/` and I'll execute + show you the diff.

## 4. Out of scope — two findings already filed (this mailbox)
- `from-zhihuwatcherv11impler-default-collection-classify.md` — proposes the default-collection auto-classifier
  as a NEW SP (depends on v1.1's by-user discovery + the existing ~33 Obsidian subfolders + list excerpts).
- (My earlier `engine-article-403-gap.md` finding is **obsolete** — SP-2 v1.2 already probed it, found 专栏
  `/api/v4/articles` is x-zse-96-gated, you escalated UN-028, the user chose no signer. The letter was burned.)

## 5. User-facing
A `toUser/from-zhihuwatcherv11impler-v1.1-done.md` summary letter was written for the user (burn on convergence).

## 6. Lifecycle
Per `toZhihuWatcherV11Impler/handoff.md`: burn this + that handoff chain after you decide §3 and converge.

— ZhihuWatcherV11Impler
