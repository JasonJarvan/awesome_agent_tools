> from: SP5bImpler (Claude Code peer session, child of BilibiliCrawl SubOrche; cwd = repo root; active 2026-06-10)
> recipient: BilibiliCrawl SubOrche (my parent)
> purpose: plan-ready — Stage-0 + design + writing-plans done & user-approved; entering execution (Step 5-7).
> lifecycle: burn after SubOrche reads (or folds into the eventual sp5b-done convergence).
> date: 2026-06-10

# Plan-ready — SP-5b Bilibili Watcher (design + plan approved, executing next)

## 1. TL;DR
Stage-0 gate (UN-029) cleared by the user; design + plan written, committed, user-approved. Proceeding to
worktree + subagent-driven TDD (the user's standing preference). No greenlight needed from you — the cross-SP
boundaries were locked in your handoff and all YOU-owned decisions are user-ratified. This letter is the
convergence checkpoint, not a blocker.

## 2. What's decided (all user-ratified 2026-06-10)
- **Δ2 watermark**: `fav_time` high-watermark (`order=mtime` early-stop) **+ `bvid` seen-set** idempotency
  backstop; advance held below failures for retry-safety (design §5).
- **Δ1 engine**: `fetcher` wraps the frozen SP-4a engine (`engine.transcribe(bvid, credential).render(...).main_markdown`).
- **Output**: single self-contained `.md` (summary + readable transcript); `RenderOptions` is config (`render.*`).
- **type==2 only**; **folders** = `AI生成` (2216104467) + `编程折腾` (1195057867) to start; **poll 20 min**.
- Cookie active-PULL, `bilibili.com` (no dot), SESSDATA+bili_jct → `BilibiliCredential`; reuse SP-5a decrypt.

## 3. Artifacts (committed on `feat/agentcrawl-bootstrap`, `docs(SP-5b):`/`feat(SP-5b):`)
- Stage-0 fields doc (user-reviewed, §9 ratified): `Service/crawl/bilibili-watcher/docs/RepoMem/temp/sp5b-bilibili-watcher/favorites-api-fields.md` (`2393d17`)
- design.md: `…/docs/superpowers/specs/2026-06-07-SP-5b-bilibili-watcher-design.md` (`6c27afc`)
- plan.md (Lane: full, 12 TDD tasks): `…/docs/superpowers/plans/2026-06-07-SP-5b-bilibili-watcher-plan.md` (`0d47338`)

## 4. Next (Step 5-7)
- Worktree `.worktrees/sp5b-bilibili-watcher/` branched from local `feat/agentcrawl-bootstrap` (NOT origin/main).
- Subagent-driven TDD over the 12 tasks (config → cookie_provider → favorites_client → watermark_store →
  fetcher → saver → watcher → __main__ → deploy → docs).
- **verification-before-completion = live `--once` smoke** needs BN up at `127.0.0.1:3015` (already up),
  a fresh `bilibili.com` cookie, a real config + BN `provider_id`. Those are USER ops → I'll surface a
  Dashboard row + note if they gate the smoke. Code+unit do NOT depend on them.
- `requesting-code-review` + `finishing-a-development-branch` both ask-first; then **I own the Step-8 merge**
  (promote the user-reviewed favorites-API field semantics → `crawl-pipeline.md §B站链路`).

## 5. State
docs-only commits so far on the shared branch (no src yet, no worktree, engine untouched, no push).
SP-5b status-board cell updated (🟡 wip; Stage 0 ⚫ + plan-ready).
