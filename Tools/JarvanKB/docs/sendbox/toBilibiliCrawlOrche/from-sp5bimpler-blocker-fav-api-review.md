> from: SP5bImpler (Claude Code peer session, child of BilibiliCrawl SubOrche; cwd = repo root; active 2026-06-10)
> recipient: BilibiliCrawl SubOrche (my parent; root delegated the Bilibili vertical to it)
> purpose: Stage-0 HITL gate — I empirically crawled the REAL Bilibili favorites API; the fields doc is
>   written and awaits the USER's review/edit before I design the watermark. This is a planned gate, not a failure.
> lifecycle: burn after the user ratifies the fields doc and I proceed to Step 2 (design); SubOrche may ack via
>   `toSP5bImpler/from-bilibilicrawlorche-*.md` but the binding gate is the USER's edit of the doc.
> date: 2026-06-10

# Stage-0 gate — Bilibili favorites-API fields doc ready for USER review

## 1. TL;DR

Stage 0 done **empirically** (real API call with the user's live cookie, account `21309967`, 2026-06-10 —
NOT from memory/docs). The handoff's central worry is **resolved in the user's favor**: ⭐ **`fav_time` really
exists per favorited item and is the collected-time, distinct from `pubtime`/`ctime`** (hard proof: media[0]
`fav_time=2026-04-24` vs `pubtime=2026-04-16`, 8 days apart). So unlike SP-5a's armchair "no reliable
favorite-time" conclusion, **B站 favorites DO carry `fav_time`** — the default `fav_time` high-watermark
(SP-0 §7 + the user's prior) is empirically supported.

Fields doc (the user-review artifact):
`Service/crawl/bilibili-watcher/docs/RepoMem/temp/sp5b-bilibili-watcher/favorites-api-fields.md`.

**I am now stopped at the Stage-0 gate.** The user reviews + edits that doc; only after ratification do I run
brainstorming + design the watermark against the *user-reviewed* doc. Dashboard row **UN-029** emitted.

## 2. Empirical findings (full detail in the doc)

- **Endpoints** (all `api.bilibili.com`, plain cookie + browser headers, **no signing**):
  `GET /x/web-interface/nav` (mid) · `GET /x/v3/fav/folder/created/list-all?up_mid=` (22 folders found) ·
  `GET /x/v3/fav/resource/list?media_id=&pn=&ps=&order=mtime` (items). All need SESSDATA (private account data).
- ⭐ **`fav_time` = collected time, ≠ `pubtime`/`ctime`** (the crux — proven, not assumed).
- ⭐ **Ordering**: `order=mtime` ⇒ `medias` sorted by `fav_time` DESC (newest-favorited first) — verified.
  Enables the early-stop the spec wanted.
- ⚠️ **Paging gotcha (lived it)**: folder `media_count=4` but only **3** items returned + `has_more=false`
  (deleted/invalid videos count toward `media_count` but aren't returned). → **stop on `has_more`, NEVER on
  `len(collected) >= media_count`** — the B站 twin of the §知乎链路 "don't early-stop from totals" lesson.
- **Item → engine**: feed `bvid` (e.g. `BV1orQJB2Edt`) to `engine.transcribe(bvid, credential=cred)`.
- **type field**: `type=2` = UGC video; non-2 (audio/番剧/合集) likely unsupported by the engine → propose filter.
- **cookie**: `domain=bilibili.com` (NO dot, credentials.md authoritative) holds SESSDATA + bili_jct; raw value
  never persisted/printed. (The SP-5a cookie_provider decrypt routine reuses 1:1, swapping the domain extraction.)

## 3. Open decisions surfaced to the user (in the doc §7)

1. Which of the 22 folders to watch (all / a subset).
2. Watermark shape: **`fav_time` high-watermark + seen-id idempotency backstop (my recommendation)** /
   pure `fav_time` / pure seen-id (fallback). Rationale in doc §6.
3. type filter: process only `type==2`, skip the rest?

## 4. State

No worktree, no code, no commits to src yet — only the Stage-0 fields doc + this letter + Dashboard row,
committed with `docs(SP-5b):`. SP-5b status-board cell updated (still 🟡 wip; Stage 0 ⚫, awaiting fav-API review).
Engine untouched (frozen). No git push.
