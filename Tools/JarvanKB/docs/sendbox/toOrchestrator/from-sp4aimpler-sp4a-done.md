---
from: SP4aImpler (Claude Opus 4.8, 1M context)
to: orchestrator (g3)
type: milestone-done
slug: sp4a-bilibili-engine
date: 2026-06-02
lifecycle: burn-after-read (also burn the SP-4a sendbox chain: toSP4aImpler/handoff.md + from-orche-sp4a-greenlight.md + plan-ready + blocker)
---

# SP-4a Bilibili Engine — DONE ✅

Full v2 pipeline (steps 1–8) closed end-to-end. Engine + Skill-grade contract delivered, verified against
a live BiliNote + real bilibili, Step 8 merge done (impler-owned, HITL-confirmed).

## Delivered
- `Engine/bilibili/` — 11 source units (url_parser, models, errors, render, config, metadata, subtitle,
  bilinote_client, engine, cli, __init__), src-layout package `bilibili`. **59 unit tests green**; network
  confined to 3 units (each = thin fetch + pure parser, fixture-tested, no live calls in the suite).
- Frozen contract `Engine/bilibili/docs/interface.md`; design `…/specs/2026-05-31-SP-4a-…-design.md`;
  plan `…/plans/2026-05-31-SP-4a-…-plan.md` (16 TDD tasks, subagent-driven + per-task two-stage review +
  final whole-module review).
- BN deploy artifacts `Engine/bilibili/deploy/bilinote/` (compose maps host→backend :8483; bcut).

## Verification (fresh evidence, both paths against live BN + real bilibili)
- **ASR path** `BV1GJ411x7h7` (no cred → subtitle skipped → bcut): `source=asr`, 61 segs, mimo summary, 28s.
- **Subtitle path** `BV1BXQABNE4y` (SESSDATA from SP-1 cookie-manager → AI subtitle → prefetched to BN):
  `source=subtitle`, 456 segs, `ai-zh`, mimo-v2.5-pro summary (~2.6k), 84s.
- Prose-merge (user requirement) confirmed on real data: 456 segs → ~27 paragraphs, not line-per-segment.
- Evidence: `Engine/bilibili/docs/RepoMem/temp/sp4a-bilibili-engine/smoke.md`.

## 3 smoke-found defects fixed (committed; user waived re-review)
1. `get_subtitle` raises without SESSDATA → `fetch_subtitle` degrades to ASR (engine now cookie-less on public).
2. BN `latest` image nginx broken → map host port to backend :8483; set `TRANSCRIBER_TYPE` via API.
3. ASR branch raises `TranscriptionFailed` on empty BN transcript.

## Step 8 RepoMem.merge (HITL-confirmed) — promoted globally for SP-4b/SP-5b
- `architecture/credentials.md`: **bilibili cookies live under `domain=bilibili.com` (no leading dot)**,
  not `.bilibili.com`; `get_subtitle` needs SESSDATA; engine cookie-less on public videos.
- `architecture/crawl-pipeline.md` §B站链路: real BN+bcut pipeline + reusable ops gotchas (latest-image
  nginx→map :8483, TRANSCRIBER_TYPE via API, add_provider/OpenAI-compatible, bcut needs no cookie).
- Module specifics → `Engine/bilibili/docs/RepoMem/decisions.md` (D-4a.1..4 + smoke-fixes).

## Live env state (for SP-4b/SP-5b)
BN running as container `jarvankb-bilinote` (`127.0.0.1:3015`→backend, bcut, provider `xiaomitokenplan`
= xiaomi mimo `mimo-v2.5-pro`). Engine config at `Engine/bilibili/config/bilibili-engine.yaml` (gitignored).

## Unblocks
SP-4b (Bilibili Skill) + SP-5b (Bilibili Watcher) — both consume this engine's `interface.md`.

## Convergence / housekeeping for you (orche)
Please burn the SP-4a sendbox chain on reading this: `toSP4aImpler/handoff.md`,
`toSP4aImpler/from-orche-sp4a-greenlight.md`, `from-sp4aimpler-plan-ready.md`,
`from-sp4aimpler-blocker-bn-docker.md`. Dashboard SP-4a→done + UN-018→resolved updated by me.
