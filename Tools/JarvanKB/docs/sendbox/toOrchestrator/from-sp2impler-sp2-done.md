---
from: SP2Impler (Claude Opus 4.8)
to: orchestrator (g3)
type: milestone-done
slug: sp2-zhihu-engine
date: 2026-06-02
lifecycle: burn-after-read
---

# SP-2 DONE — Zhihu Engine

## 1. Status
`Engine/zhihu/` complete, verified, **merged locally** into `feat/agentcrawl-bootstrap`
(merge commit `f8c14cb`; you continued on top with `d640635`). 51 unit tests + live smoke
(answer/article/question/comments) all green. v2 pipeline steps 1–8 closed by me (impler owns closure).

- Pure-fetch lib: one URL → Markdown + metadata + optional flat two-layer comments.
- **zse-96 sidestepped**: cookie + HTTP, no browser, no signer (page-HTML `js-initialData` primary →
  CSS scrape → unsigned `/api/v4` on 403). Aligns the user's `JasonJarvan/Zhihu-Collections-MCP`.
- Contract frozen: `Engine/zhihu/docs/interface.md`. Decisions: `Engine/zhihu/docs/RepoMem/decisions.md` (D1–D6).

## 2. Two real bugs the smoke gate caught (not findable by synthetic tests)
- Zhihu `js-initialData` is **camelCase** (`voteupCount`/`createdTime`…), `/api/v4` is snake_case →
  parsers now read camelCase-first with snake fallback.
- `comment_v5` is **cursor-paginated; `offset` is poison** (empty data + self-referential cursor →
  infinite loop) → fixed to follow `paging.next`, loop-guarded.
- Settled the big open question: **`comment_v5` needs NO signature** (plain cookies, verified live).

## 3. RepoMem.merge (Step 8) done — HITL-approved by user
- Module decisions D1–D6 written.
- **Global promotion (user-approved):** updated `docs/RepoMem/persist/architecture/crawl-pipeline.md`
  §知乎链路 — superseded the old (wrong) CDP→Jina speculation; promoted ONLY the non-code root-causes/
  gotchas SP-5a needs (offset-poison, camelCase, no-signing, direct-connect). Mechanism stays in code +
  interface.md + module decisions (no-duplication).

## 4. ⭐ ACTION FOR YOU — record this promotion standard (governance)
The user asked that the **promotion standard** I applied be recorded by you (governance is your job,
not mine). Please codify it — suggest `longterm.md` §Pipeline v2 step 8 (or a RepoMem.merge guideline):

> **RepoMem.merge promotion standard:** When promoting module findings to global `persist/`, promote
> ONLY what is NOT derivable from code/interface.md/module-decisions — decision rationale, root causes,
> gotchas, and cross-SP guidance. Never duplicate mechanism that lives in code. **Crucially**, promote
> cross-SP-reusable gotchas to global persist *because the layered-read protocol means a downstream SP
> in another module's cwd does NOT read the originating module's `decisions.md`* — if a reusable gotcha
> lives only in the origin module, the next SP will rediscover it the hard way.

(This is the concrete lesson from SP-2: the offset-poison/camelCase gotchas had to go global so SP-5a
Watcher — which runs in `Service/crawl/zhihu-watcher/` cwd — will see them.)

## 5. Unlocks (dependency graph)
SP-2 done → **SP-3 (Zhihu Skill)** and **SP-5a (Zhihu Watcher)** entry conditions now MET (were "等 SP-2").
Both can be queued for new implers. SP-5a especially should read the promoted crawl-pipeline.md §知乎链路.

## 6. v1.1 follow-up — handed off (per user priority: comment-tree > image-dedup)
**Comment full-tree crawl** (exhaustive child-reply pagination) is handed off to a successor session:
`docs/sendbox/toZhihuCommentImpler/handoff.md` (slug `zhihu-engine-comment-tree`). The user will spawn it.
Lower-priority deferrals (image dedup, question answer-list) recorded in module decisions §Deferred.

## 7. Sendbox closure
- `from-sp2impler-plan-ready.md` (earlier) + this letter: **you may burn both after reading.**
- **Please burn `docs/sendbox/toSP2Impler/handoff.md`** (my inbound handoff) per its §8 — gated on you
  reading this done letter. I left it for you (couldn't observe your read myself).
- Dashboard SP-2 row → ⚫ done (updated by me in the same closure commit).

SP-2 converges back to you. No further work owned by SP2Impler.
