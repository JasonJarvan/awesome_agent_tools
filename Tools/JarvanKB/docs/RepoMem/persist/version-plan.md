---
language: en
audience: A2A
---

# version-plan.md

> Long-term version / roadmap notes for JarvanKB.
> Referenced by `docs/HarnessStack/longterm.md` §Related Documents.
>
> **Audience**: A2A (agent reference). SP status board is NOT here — it lives in `docs/Dashboard/index.md` §SP Status Board (H2A surface). This file holds recipe version history, project rename history, OSS release plan, compatibility notes.

## Recipe version history

| Version | Recipe ID | Effective | Notes |
|---|---|---|---|
| v1 | `openspec-superpowers-repomem-sendbox-dashboard` | 2026-05-26 → 2026-05-31 | Bootstrap. Deprecated via Full Rewrite. |
| **v2** | `superpowers-repomem-sendbox-dashboard` | 2026-05-31 → | OpenSpec removed for thin-layer formation. See longterm.md §Recipe v1→v2 Migration. |

## Orchestrator generations

Distinct from recipe version: same recipe can span multiple orchestrator sessions; a generation ends when the session writes an inheritance handoff letter (`docs/sendbox/toOrchestrator/g{N}-handoff.md`) and a new CC session is spawned to inherit.

| Generation | Identity | Active range | EOL reason |
|---|---|---|---|
| g1 | bootstrap-orchestrator | 2026-05-26 → 2026-05-30 | Wrote inheritance `handoff.md` post-Phase-1 doc skeleton; burned in SP-0 closure commit (5c28447) |
| g2 | Claude Opus 4.7 (this session) | 2026-05-30 → 2026-05-31 | Wrote `g3-handoff.md` post-SP-0 done + SP-1 launched; context heavy with R1–R9 调研 + 7 governance patches, prune-via-inheritance preferred over `/compact` |
| g3 | Claude Opus 4.8 (1M context) | 2026-05-31 → 2026-06-07 | Wrote `g4-handoff.md` after fanning out 2 SubOrche verticals (ZhihuCrawl + BilibiliCrawl); SP-0/1/2/4a done, SP-3/5a wip; landed UN-015 merge-ownership + RepoMem.merge promotion standard + cookie-PULL decision; prune-via-inheritance |
| g4 | TBD by user spawn (see Dashboard UN-023) | 2026-06-07 → | — (active) |

Naming convention: `g{N}-handoff.md` placed in `docs/sendbox/toOrchestrator/` (same box as inbound letters; new orche replaces predecessor, no parallel box). Letter lifecycle: `burn` after inheritor logs first orche-attributable commit (decision letter / Dashboard archive / new SP brainstorming kickoff).

## Project rename

- **AgentCrawl** (2026-05-26 → 2026-05-31): original scope = Zhihu + Bilibili crawlers
- **JarvanKB** (2026-05-31 → ): scope expanded to crawl + ingester + future knowledge tooling; personal-brand naming for OSS release
- Physical rename `Tools/AgentCrawl/` → `Tools/JarvanKB/` performed in a separate session (tracked as Dashboard UN-005)

## Current phase

- **SP-0 in progress** (2026-05-31): repo skeleton + HarnessStack v2 migration
  - Design: `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md`
  - Plan: `docs/superpowers/plans/2026-05-31-SP-0-jarvankb-skeleton.md`
  - Impler handoff: `docs/sendbox/toSP0Impler/handoff.md`
- **Live SP status board** (kanban-like): `docs/Dashboard/index.md` §SP Status Board — single H2A surface for sub-project status, owner agent, phase enter gates

## v1.0 OSS release plan

When all v1 sub-projects (SP-0 through SP-7) verified end-to-end:

1. Choose Organization name (candidates: `JarvanKB` / `Jarvan` / `JarvanWorks`) — tracked as Dashboard UN-006
2. Execute fractal split per `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` §9:
   - `git filter-repo --subdirectory-filter <module>/` per sub-project
   - Inherit `docs/HarnessStack/` into each child
   - Initialize child-repo own `docs/{sendbox,Dashboard,RepoMem/persist}/`
   - Create new GitHub repo under Organization, push
3. Mark monorepo (this repo) as umbrella for HarnessStack template + cross-module integration tests

## Compatibility / upgrade notes

- HarnessStack recipe upgrades: see `longterm.md` §Full Rewrite Conditions
- ASR strategy (D3 in `pre-openspec-decisions.md`) revised in R5 (2026-05-31): **v1 switched from 通义听悟 to BiliNote + bcut (B站必剪 free cloud ASR)**. D3 marked as superseded but file not deleted (historical trace)
- **Cookie delivery for all crawl consumers = active PULL** (user-ratified 2026-06-02, cross-vertical): consumers fetch SP-1 cookies via `GET /get/:uuid` + client decrypt (or `cookie-manager show domain=<x>`); the **SP-1 _push_ delivery path is permanently cancelled** (SP-1 hook engine retained but latent — a future non-decrypting consumer is a config entry, not new code). Relayed by ZhihuCrawl SubOrche; applies to SP-3/SP-5a now + **propagate to SP-4b/5b scope** when their handoffs are written. Detail: `architecture/credentials.md` §Integration contract.

## How this doc is updated

Append-most. Major changes (phase scope reshuffle, recipe upgrade, project rename) go through `RepoMem.merge` HITL review.

> **Eager-materialization sync note**: This file's content is mirrored by plan Task 8.2 heredoc in `docs/superpowers/plans/2026-05-31-SP-0-jarvankb-skeleton.md`. Impler's Task 8 overwrites this file with identical content (idempotent). If editing this file before impler runs, edit the plan heredoc to match.
