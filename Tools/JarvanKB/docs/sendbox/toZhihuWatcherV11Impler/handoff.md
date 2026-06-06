> from: SP5aImpler (outgoing v1 impler) — drafted for dispatch by ZhihuCrawl SubOrche
> recipient: ZhihuWatcherV11Impler (a fresh Claude Code peer session, cwd = repo root)
> parent: ZhihuCrawl SubOrche (you converge back to it, like the v1 impler did)
> mode: child-handoff (sendbox-protocol Mode A)
> purpose: SP-5a v1.1 — add two collection-target-resolution modes to the (merged, working) Zhihu Watcher
> lifecycle: burn after you write `from-zhihuwatcherv11impler-done.md` and SubOrche reads it

# SP-5a v1.1 Handoff — Zhihu Watcher: collection target-resolution modes

## 0. What this is

SP-5a **v1 is DONE and merged** to `feat/agentcrawl-bootstrap` (merge `7acacb2`): a polling daemon that
watches an **explicit list** of Zhihu collections, pulls cookies from SP-1, fetches each new item via the
frozen SP-2 engine, and saves Markdown. 32 tests + a passing live smoke (140/168 items saved, dedup
confirmed). You are extending it; do NOT rebuild it.

Read first (full context):
- `Service/crawl/zhihu-watcher/docs/superpowers/specs/2026-06-02-SP-5a-zhihu-watcher-design.md`
- `Service/crawl/zhihu-watcher/docs/superpowers/plans/2026-06-02-SP-5a-zhihu-watcher-plan.md`
- `Service/crawl/zhihu-watcher/docs/RepoMem/{architecture,decisions}.md` (decisions has the live-smoke
  findings + the v1+ notes)
- `docs/RepoMem/persist/architecture/crawl-pipeline.md §知乎链路` (now records: collections + people/collections
  endpoints need **no x-zse-96**, offset paging stop rule, and the ARTICLE-403-no-fallback gotcha)

## 1. Scope — two target-resolution modes (the watcher currently only does the explicit list)

The watcher's per-collection poll loop, fetch, dedup, save, scheduler are all done and frozen-good. v1.1
only changes **how the list of collections-to-watch is resolved** from config. Add:

- **Mode 1 — by user (NEW, the real work): auto-discover all of a user's collections.**
  Enumerate via `GET https://www.zhihu.com/api/v4/people/{url_token}/collections?include=data%5B*%5D.updated_time%2Canswer_count%2Cfollower_count%2Ccreator%2Cdescription%2Cis_following%2Ccomment_count%2Ccreated_time%3Bdata%5B*%5D.creator.kvip_info%3Bdata%5B*%5D.creator.vip_info&offset=0&limit=20`
  (offset paging, same idioms as the items endpoint — plain cookie, no x-zse-96, `trust_env=False`, follow
  `paging`). Each `data[]` has the collection `id`, `title` (→ subfolder name), etc. Watch ALL of them (or
  a filter — decide in brainstorm). `{url_token}` is the account whose collections to list; the user's
  example `zhao-cheng-57-99-79` is the **current cookie user's** token, so consider supporting `"me"`
  (derive the current user's url_token — e.g. via `/api/v4/me` — or just config the token).

- **Mode 2 — explicit list (MOSTLY DONE): keep + optionally adapt config shape.**
  v1 already supports `collections: [{id, name}]` where `id` may be a full collection URL. The user
  referenced the Zhihu-Collections-Saver `config.json` shape:
  `{ "zhihuUrls": [{name, url}], "outputPath", "os", "openCollection" }`. If byte-compat is wanted, add a
  thin config adapter (`zhihuUrls`→collections, `outputPath`→`output_dir`); **drop `os`/`openCollection`**
  (Windows-desktop-app concepts, meaningless for a Linux daemon). Confirm with the user whether they want
  this adapter or just keep the current YAML schema.

The user also said "should be able to fill multiple collection URLs" — v1 ALREADY supports a multi-entry list.

## 2. LOCKED decision (do not re-litigate): target resolution lives in the SERVICE, not the Engine

The SP-2 engine (`Engine/zhihu/`) is **frozen** and scoped to "one content URL → Markdown". Collection
listing and user-collections listing are **navigation/discovery** = target resolution → they belong in the
**watcher service** (where `favorites_client.py` already lives), NOT the engine. Build a small resolver in
front of the existing per-collection loop:
- add `favorites_client.list_user_collections(url_token, cookies)` (or a sibling `collections_client`);
- a resolver turns the config (explicit list OR by-user) into `list[CollectionConfig]` → feed the existing
  loop unchanged.
(Future: if SP-3/others also need listing, extract a shared Zhihu-listing module — deferred per handoff;
do NOT build `Engine/common` competitively now.)

## 3. Optional secondary item (confirm scope with user — may be separate)

**v1+ retry/backoff for permanently-403 items.** The v1 live smoke showed 28 専欄 ARTICLE items 403 with no
SP-2 api-fallback; the watcher re-attempts them EVERY cycle (not marked seen → bounded, no infinite loop,
but wasteful). Consider a failed-attempt counter / backoff (e.g. after N consecutive failures, skip for a
while). Decide in brainstorm whether this is in v1.1 or deferred.

## 4. Pipeline (v2 8-step) + governance

Run the full v2 pipeline (`CLAUDE.md §3`). Your brainstorm is **compressed**: the Server-placement is locked
(§2); brainstorm only the config schema for the two modes (how to express "watch all my collections" vs an
explicit list vs a mix; Mode-1 url_token vs "me"; whether to add the Mode-2 config adapter; the retry/backoff
scope). **You own Step 8 RepoMem.merge closure** (impler-owned, HITL) — `CLAUDE.md §4`. Use a worktree
**branched from the LOCAL `feat/agentcrawl-bootstrap`** (NOT origin/main — that would drop sibling work);
subagent-driven TDD; ask-first on code-review + finishing; local commits only, prefix `feat(SP-5a):` /
`docs(SP-5a):`.

## 5. Convergence

| Event | Write to |
|---|---|
| plan-ready | `docs/sendbox/toZhihuCrawlOrche/from-zhihuwatcherv11impler-plan-ready.md` |
| blocker | `docs/sendbox/toZhihuCrawlOrche/from-zhihuwatcherv11impler-blocker-<topic>.md` |
| done | `docs/sendbox/toZhihuCrawlOrche/from-zhihuwatcherv11impler-done.md` |

Inbound replies: `docs/sendbox/toZhihuWatcherV11Impler/from-zhihucrawlorche-*.md`.

## 6. Out of scope

- Editing the frozen SP-2 engine; building competing `Engine/common` helpers.
- Re-doing v1 (cookie pull, fetch, dedup, save, scheduler — all done).
- LLM / classification / Obsidian-GBrain-Thino semantics; image download.
- `git push` / merge-to-main.

**Begin at Step 1 (RepoMem.read both layers), then a compressed Step 2 brainstorm with the user on the
config schema.** The endpoints + no-signing + paging idioms are already proven (see §知乎链路).
