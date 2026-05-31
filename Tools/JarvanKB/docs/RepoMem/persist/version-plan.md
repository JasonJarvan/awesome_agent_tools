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

## How this doc is updated

Append-most. Major changes (phase scope reshuffle, recipe upgrade, project rename) go through `RepoMem.merge` HITL review.

> **Eager-materialization sync note**: This file's content is mirrored by plan Task 8.2 heredoc in `docs/superpowers/plans/2026-05-31-SP-0-jarvankb-skeleton.md`. Impler's Task 8 overwrites this file with identical content (idempotent). If editing this file before impler runs, edit the plan heredoc to match.
