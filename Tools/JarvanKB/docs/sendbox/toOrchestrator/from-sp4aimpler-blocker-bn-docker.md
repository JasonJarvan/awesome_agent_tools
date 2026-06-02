---
from: SP4aImpler (Claude Opus 4.8, 1M context)
to: orchestrator (g3)
type: blocker
slug: sp4a-bilibili-engine
date: 2026-06-02
lifecycle: burn-after-read
tracks: UN-018
---

# SP-4a blocker — BiliNote docker reachable (Stage-3 gate)

**Status: all offline work done & green; the ONLY remaining step is the live manual smoke, which needs a
reachable BiliNote (BN). This is a USER action (per SP-1 precedent "起 Docker 容器是 user 操作").**

## What's done (plan Tasks 1–15, committed on `feat/agentcrawl-bootstrap`)
Full engine implemented TDD, subagent-driven, two-stage reviewed per task + a final whole-module review
(verdict: READY-FOR-SMOKE). **56 unit tests pass, zero live network in the suite, engine never calls an LLM.**
- 11 source units under `Engine/bilibili/src/bilibili/` (url_parser, models, errors, render, config,
  metadata, subtitle, bilinote_client, engine, cli, __init__) — network confined to 3 units, each split
  into a pure parser (fixture-tested) + a thin fetch.
- Frozen contract: `Engine/bilibili/docs/interface.md`. Design: `.../specs/2026-05-31-SP-4a-...-design.md`.
- BN deploy artifacts: `Engine/bilibili/deploy/bilinote/` (`docker-compose.yml` pinning
  `TRANSCRIBER_TYPE=bcut` + `.env.example` + a zh runbook). Config: module-local
  `Engine/bilibili/config/bilibili-engine.example.yaml`.

## The gate (UN-018) — what the user needs to do
1. `cd Engine/bilibili/deploy/bilinote && cp .env.example .env && docker compose up -d`
   (pulls `ghcr.io/jefferyhcool/bilinote:latest`; a source-build fallback is in that dir's README).
2. Open `http://localhost:3015` → 模型供应商 → add an LLM provider; note its `provider_id`.
3. Copy `Engine/bilibili/config/bilibili-engine.example.yaml` → `bilibili-engine.yaml`, fill
   `base_url` (`http://127.0.0.1:3015`), `provider_id`, `model_name`.
4. Confirm the endpoint is live (reply here or tell SP4aImpler in chat).

## Then I (SP4aImpler) finish (Task 16, I own it)
Mandatory manual smoke against the live BN: one BV **with** subtitle → subtitle path; one **without** →
bcut ASR path; show rendered Markdown for both → then `verification-before-completion` →
`requesting-code-review` + `finishing-a-development-branch` (ask-first) → Step 8 `RepoMem.merge`
(impler-owned closure; promote the reusable BN-client / subtitle-cascade root-cause to global persist).

## Convergence
I stay alive and own SP-4a to done incl. Step 8. Final `from-sp4aimpler-sp4a-done.md` at completion, then
burn the handoff. SP-2 sibling already merged independently — no shared state touched (disjoint module).
