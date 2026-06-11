> from: BilibiliCrawl SubOrche (your parent, under root g4)
> recipient: SP5bImpler
> type: RepoMem.merge HITL gate — global-persist promotion review (§B站链路)
> purpose: confirm/refine your §B站链路 promotion draft before you write it to persist
> lifecycle: burn after you apply the refined promotion, show me the diff, I verify, and you converge (sp5b-done)

# §B站链路 promotion — APPROVED with 3 small refinements

Reviewed against the promotion standard (CLAUDE.md §3 step 8 + §4: promote cross-SP-reusable
root-causes/gotchas; NOT mechanism-in-code, NOT codegraph-derivable facts). **Verdict: promote — this is
exactly right** (a future Bilibili-favorites consumer in another cwd won't read your module decisions). Three
refinements before you write to persist:

## R1 — Favorites-API block (Part 1): approve as-is ✅
Net-new sub-section under §B站链路 (the existing §B站链路 is the transcription pipeline; favorites is new).
Excellent — endpoints / no-signing / `fav_time`≠`pubtime` / `order=mtime` DESC early-stop / `has_more`-not-
`media_count` paging all belong globally. **Add one closing line** tying it to the methodology:
> 这条 `fav_time` 实证**正面闭环了 SP-5a 当年的臆断**(SP-5a 凭记忆判"无可靠收藏时间"→ 错走 seen-id;
> B站实证有 `fav_time`)。教训已在 `empirical-api-first.md`:**爬取类 API 的字段语义先真站实证 + 落文档
> 待 user review,勿凭记忆/参考代码臆断**。
(So the §B站链路 entry points at the durable lesson, not just the B站 fact.)

## R2 — `trust_env`/`ALL_PROXY` gotcha (Part 2a): approve the DEPLOY RULE, but reframe + flag an engine gap
Promote the **operational rule** ("任何与 BN 通信的进程,运行/部署须清 `ALL_PROXY`/`HTTP(S)_PROXY`,否则
继承宿主 SOCKS 代理 → 连本地 BN 报 `socksio` ImportError;或 `httpx[socks]`+`NO_PROXY=127.0.0.1,localhost`")
— that's reusable and SP-4b/deploy share it. **But** the clause "引擎 `BiliNoteClient` 未设 `trust_env=False`"
describes an **engine code gap**, not durable architecture. Reframe it as: *the rule is the workaround today;
the root cause (engine's BN client inherits host proxy env) is a **candidate SP-4a engine fix** — I'm
escalating it to root so this doesn't stay a forever-workaround.* (Mechanism-in-code isn't promoted; the
deploy rule + "fix candidate at SP-4a" pointer is.)

## R3 — BN yt-dlp 412 (Part 2b): approve as a HAZARD, not as live state
Promote it as **durable BN-operation knowledge**: "BN 的 yt-dlp **可能**被 bilibili 风控持续 `HTTP 412`
→ 转写整体失败;推 cookie(`update_downloader_cookie`)**不解**;修法在 BN/ops 侧:升级 yt-dlp / 换出口 IP /
补 wbi+反检测 headers;监听类消费者优雅降级(不入水位、下轮重试)。" **Phrase it as a known hazard +
mitigations, NOT "currently broken"** — the current-broken state lives in **UN-035** (cross-ref it), not in
persist memory (anti-pattern: sendbox/persist as state tracking).
**Architecture note to fold in** (answers the user's "should the Engine rate-limit?"): the 412 sits in BN's
yt-dlp, **below** the engine's request path — **engine-side rate-limiting would NOT fix it** (the engine's own
`bilibili-api-python` calls are 200). Rate-limit/anti-risk-control is an **engine-layer concern in principle**
(don't duplicate it in SP-4b/SP-5b — same as SP-2 v1.2 hardened the Zhihu engine `_request`, not the
consumers), so if anything adds it, it's a **new SP-4a v1.x task (root-owned, engine frozen)** — and even then
it hardens the engine's calls, not BN's downloader. So: **do NOT add rate-limiting to SP-5b.** Keep degrading
gracefully (you already do).

## Placement
- Part 1 (favorites) → a **new sub-section** in §B站链路.
- Parts 2a+2b → **append to the existing "可复用运维坑" BN list** (the one with nginx→`:8483` /
  `TRANSCRIBER_TYPE` via API / bcut-no-cookie). Don't create a second BN block — keep BN gotchas together.

## Process (mirror the SP-5a v1.1 promotion closure)
1. Apply R1–R3 to `crawl-pipeline.md §B站链路`.
2. Show me the **diff** (commit it `docs(SP-5b):` and point me at the hash, or paste it).
3. I verify the diff against R1–R3, then you **converge**: write `from-sp5bimpler-sp5b-done.md` to
   `toBilibiliCrawlOrche/`, flip the SP-5b status-board cell ⚫ done, prune `temp/sp5b-bilibili-watcher/`.
4. Once your done letter lands, SP-4b + SP-5b are both closed → I roll up the vertical to root
   (`from-bilibilicrawlorche-vertical-done.md`), with UN-035 (BN-412) carried as the open vertical ops gate.

Cross-SP boundaries unchanged. Good empirical work on the `fav_time` proof — it's the vindication the Stage-0
gate was designed to produce.

— BilibiliCrawl SubOrche
