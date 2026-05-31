# version-plan.md

> Long-term version / roadmap notes for JarvanKB.
> Explicitly named in `docs/HarnessStack/longterm.md` §Related Documents.

## Recipe version history

| Version | Recipe ID | Effective | Notes |
|---|---|---|---|
| v1 | `openspec-superpowers-repomem-sendbox-dashboard` | 2026-05-26 → 2026-05-31 | Bootstrap. Deprecated via Full Rewrite. |
| **v2** | `superpowers-repomem-sendbox-dashboard` | 2026-05-31 → | OpenSpec removed for thin-layer formation. See longterm.md §Recipe v1→v2 Migration. |

## Project rename

- **AgentCrawl** (2026-05-26 → 2026-05-31): original scope = Zhihu + Bilibili crawlers
- **JarvanKB** (2026-05-31 → ): scope expanded to crawl + ingester + future knowledge tooling; personal-brand naming for OSS release

Physical rename `Tools/AgentCrawl/` → `Tools/JarvanKB/` performed in a separate session (tracked as Dashboard UN-005).

## Current phase

- **SP-0 in progress** (2026-05-31): repo skeleton + HarnessStack v2 migration. Design in `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md`. Plan in `docs/superpowers/plans/2026-05-31-SP-0-jarvankb-skeleton.md`. Impler session at `docs/sendbox/toSP0Impler/handoff.md`.

## Planned sub-projects (10 v1 + 1 v1+) — SP status board

> This table doubles as the JarvanKB SP-level kanban (per R9 调研结论 "方案 1 增强"). When ≥2 implers run concurrently / single SP task count ≥10 / per-task comments needed → migrate to `antopolskiy/kanban-md`.
> Status emoji: 🟡 wip / 🔴 blocked / ⚫ done / ⚪ queued / 🟢 ready

| ID | Path | Name | Status | Owner Agent | Phase enter gate |
|---|---|---|---|---|---|
| SP-0 | `<root>/` | Skeleton + recipe v2 migration | 🟡 wip | sp0impler | (none — current) |
| SP-1 | `Service/crawl/cookie-manager/` | CookieManager (fork CookieCloud + hook) | ⚪ queued | (none) | SP-0 done |
| SP-2 | `Engine/zhihu/` | Zhihu Engine | ⚪ queued | (none) | SP-0 done + SP-1 protocol agreed |
| SP-3 | `Skill/crawl/zhihu-crawl/` | Zhihu Skill | ⚪ queued | (none) | SP-2 implemented |
| SP-4a | `Engine/bilibili/` | Bilibili Engine | ⚪ queued | (none) | SP-0 done; BN docker reachable |
| SP-4b | `Skill/crawl/bilibili-crawl/` | Bilibili Skill | ⚪ queued | (none) | SP-4a implemented |
| SP-5a | `Service/crawl/zhihu-watcher/` | Zhihu favorites watcher | ⚪ queued | (none) | SP-2 implemented |
| SP-5b | `Service/crawl/bilibili-watcher/` | Bilibili favorites watcher | ⚪ queued | (none) | SP-4a implemented |
| SP-6 | `Skill/ingester/crawl-md-saver/` | CrawlMdSaver Skill | ⚪ queued | (none) | SP-3 / SP-4b crawl skills register |
| SP-7 | `Service/ingester/thino-ingester/` | Thino Ingester | ⚪ queued | (none) | SP-6 implemented |
| SP-8 (v1+) | `Skill/router/web-search/` | Web Search Router | ⚪ queued | (none) | v1 done; Zhihu API key acquired |

## v1.0 OSS release plan

When all v1 sub-projects (SP-0 through SP-7) verified end-to-end:

1. Choose Organization name (candidates: `JarvanKB`, `Jarvan`, `JarvanWorks`) — tracked as Dashboard UN-006
2. Execute fractal split per `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` §9:
   - `git filter-repo --subdirectory-filter <module>/` per sub-project
   - Inherit `docs/HarnessStack/` into each child
   - Initialize child-repo own `docs/{sendbox,Dashboard,RepoMem/persist}/`
   - Create new GitHub repo under Organization, push
3. Mark monorepo (this repo) as umbrella for HarnessStack template + cross-module integration tests

## Compatibility / upgrade notes

- HarnessStack recipe upgrades: see `longterm.md` §Full Rewrite Conditions
- ASR strategy (D3 in `pre-openspec-decisions.md`) reviewed in R5 (2026-05-31): **switched from 通义听悟 to BiliNote/bcut for v1**. D3 marked as superseded but not deleted (historical record).

## How this doc is updated

Append-most. Major changes (phase scope reshuffle, recipe upgrade, project rename) go through `RepoMem.merge` HITL review.

> **Note**: This file's content is mirrored by plan Task 8.2 heredoc in `docs/superpowers/plans/2026-05-31-SP-0-jarvankb-skeleton.md`. When impler executes Task 8, the heredoc overwrites this file with identical content (eager-materialization pattern). If you edit this file before impler runs, edit the plan heredoc to match.
