---
from: SP4aImpler (Claude Opus 4.8, 1M context)
to: orchestrator (g3)
type: plan-ready
slug: sp4a-bilibili-engine
date: 2026-06-02
lifecycle: burn-after-read
---

# SP-4a plan-ready — Bilibili Engine

Stage 1 (design) + Stage 2 (plan) done. **Offline execution (plan Tasks 1–14, all unit-tested with
mocks) can proceed without orche sign-off** (handoff §3.C — plan-ready is for review, not a gate).
The **live manual smoke (Tasks 15–16) is genuinely gated on a reachable BiliNote (BN)** — Dashboard
**UN-018**. Pending the user's execution-approach choice (subagent-driven vs inline).

## Key outcomes from brainstorming (all confirmed with the user)
- **BN is the ASR + summary backend; the engine is a thin BN HTTP client.** It does NOT speak the bcut
  cloud API directly and does NOT call an LLM itself (BN does, internally).
- **Engine-driven subtitle-first cascade.** Engine fetches metadata + subtitle via `bilibili-api-python`;
  on a hit it feeds the subtitle to BN as `prefetched_transcript` (BN runs summary only, zero ASR cost);
  on a miss BN downloads audio + runs `TRANSCRIBER_TYPE=bcut`. The engine therefore *knows* which path
  ran (`transcript.source` ∈ `subtitle|asr`) — exactly what the mandatory smoke must prove.
- **BN is a hard dependency in v1; both paths produce a summary.** Rationale: the user's
  progressive-disclosure render mode (`split_transcript` → summary-as-index + separate transcript file)
  needs a *consistent* summary; a subtitle video that skipped BN would have no index. "BN-optional /
  `summarize=False` offline mode" is deferred to v2+.
- **Manual LLM-provider config** (engine reads `provider_id`/`model_name` from `config/bilibili-engine.yaml`;
  pure read-side consumer — never writes BN's provider DB). **Best-effort cookie push** to BN on the ASR
  path. **Structured `BilibiliCredential`** input (engine never fetches cookies — SP-4b/5b inject from SP-1).
- **Render switches** (user-set defaults): `include_transcript=True`, `include_timestamps=False`
  (→ deterministic prose-merge, no LLM), `split_transcript=False`. v2+ "smart switches" recorded as future.

## Two empirical items that settle during execution (not blockers, concrete actions in the plan)
1. **`bilibili-api-python` get_info / get_subtitle exact shapes** — plan Tasks 8/9 TDD the *pure parsers*
   against recorded fixtures (shapes verified from BiliNote's own `BilibiliSubtitleFetcher`); the thin
   fetch wrappers carry a "record a real fixture + confirm" step. Field-mapping risk is contained.
2. **BN published image tag** — plan Task 14 uses `ghcr.io/jefferyhcool/bilinote:latest` per upstream
   README; confirmed at deploy time, with a build-from-source fallback documented.

## Artifacts
- design: `Engine/bilibili/docs/superpowers/specs/2026-05-31-SP-4a-bilibili-engine-design.md` (commits f8c103e, d640635)
- plan: `Engine/bilibili/docs/superpowers/plans/2026-05-31-SP-4a-bilibili-engine-plan.md` (16 TDD tasks)
- BN deploy artifacts: produced by plan Task 14 → `Engine/bilibili/deploy/bilinote/` (unblocks UN-018)

## Convergence
I own SP-4a end-to-end incl. Step 8 `RepoMem.merge` closure (recipe v2, CLAUDE.md §3/§4). Will write
`from-sp4aimpler-sp4a-done.md` at completion, then burn the handoff. SP-2 sibling is independent — no
shared state touched (different module dir; SP-2's merge into the branch already landed cleanly above me).
