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
| g4 | Claude Opus 4.8 (1M context) | 2026-06-07 → 2026-06-14 | Wrote `g5-handoff.md` after both crawl verticals converged (SubOrche era ended → flat root→impler); SP-0…SP-5b done, SP-6 in flight; landed no-push-lift + MCP-façade route (`Service/mcp/`) + Codex cross-runtime onboarding (cc-switch) + MiroThinker findings + CodeTeam #3/#4 (codegraph + Lane Tiering) + 48xxx port convention; prune-via-inheritance |
| g5 | TBD by user spawn (see Dashboard g5 row) | 2026-06-14 → | — (active); inherits 6 live implers (SP6/ZhihuClassify/GrillDocs/FutureFeatures/BiliRateLimit/WatcherDeploy) + 1 prepared (AntiCrawlMcp/UN-043). Near-term: SP-6 done → SP-7; then v2 arc (MCP façade → auto-researcher → repo index) + v1.0 OSS split |

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

### Prepared future task — whole-repo extraction (user framing 2026-06-11, by g4)

Distinct from the per-SP fractal above: **extract `awesome_agent_tools/Tools/JarvanKB/` as ONE standalone
repo `JarvanKB`; `awesome_agent_tools` keeps only a LINK (submodule, like its existing `Tools/gstack` /
`Skills/ops-doc-maintainer` / … links).** This is the *coarser, first-level* split — whether it REPLACES the
per-SP fractal (§9) or PRECEDES it (fractal later, inside the standalone repo) is an open question for the
activation brainstorm. Deferred handoff prepared at `docs/sendbox/toRepoSplitImpler/handoff.md` (Dashboard
UN-041). **Activation gated on:** v1 done (SP-6/SP-7 still pending) + Org name (UN-006) + explicit user
go-ahead. Key wrinkle recorded there: all JarvanKB history is on `feat/agentcrawl-bootstrap` (never merged to
main), so `git filter-repo --subdirectory-filter Tools/JarvanKB/` must target that branch; never filter-repo
in place (use a mirror clone); `Tools/gstack` stays untouched; reproduce the `!.claude/` gitignore re-include
in the new root.

## Compatibility / upgrade notes

- HarnessStack recipe upgrades: see `longterm.md` §Full Rewrite Conditions
- ASR strategy (D3 in `pre-openspec-decisions.md`) revised in R5 (2026-05-31): **v1 switched from 通义听悟 to BiliNote + bcut (B站必剪 free cloud ASR)**. D3 marked as superseded but file not deleted (historical trace)
- **Cookie delivery for all crawl consumers = active PULL** (user-ratified 2026-06-02, cross-vertical): consumers fetch SP-1 cookies via `GET /get/:uuid` + client decrypt (or `cookie-manager show domain=<x>`); the **SP-1 _push_ delivery path is permanently cancelled** (SP-1 hook engine retained but latent — a future non-decrypting consumer is a config entry, not new code). Relayed by ZhihuCrawl SubOrche; applies to SP-3/SP-5a now + **propagate to SP-4b/5b scope** when their handoffs are written. Detail: `architecture/credentials.md` §Integration contract.
- **Remote push of the feature branch is now ENABLED** (user decision 2026-06-10, by g4): the prior g1–g4 "local commits only — no push" invariant (g3-handoff §6/§8) is **lifted for `feat/agentcrawl-bootstrap` → `origin` only**. The branch was first published 2026-06-10 to the **PUBLIC** repo `github.com/JasonJarvan/awesome_agent_tools` (git root = `awesome_agent_tools`, JarvanKB is `Tools/JarvanKB/`); upstream tracking set. **Still NOT authorized without explicit user say-so:** merge/PR into `main`, history rewrite/rebase, touching the `Tools/gstack` submodule. Public-repo reminder: pushed content is world-visible/indexable — keep real secrets gitignored (`.mcp.json` is untracked; verified no real tokens in tracked files at first push).

## Shared LLM layer (LLMClient) — v1 landed (SP-3), LLMService v2 roadmap

- **v1 (landed 2026-06-07, SP-3):** `Engine/common` packaged as `jarvankb-common`; `LLMClient` real litellm
  body (`from jarvankb_common import LLMClient`). In-process **library**; single repo-root `config/llm.yaml`
  (profiles + `active` fallthrough; literal `api_base` for custom OpenAI-compatible providers, verified live
  with `mimo-v2.5-pro`). Consumers SP-4b/SP-6/SP-7 **reuse — do not reimplement**. Detail:
  `memory/llm-shared-layer.md` + `Engine/common/docs/interface.md`.
- **v2 (roadmap — new platform-level SP, decide with root/SubOrche):** promote LLMClient into a standalone
  `Service/.../llm-service` (HTTP, OpenAI-compatible) for runtime-central config / metering / rate-limit /
  cache / one endpoint / language-agnostic access, with per-consumer provider selection. **Non-breaking:**
  the `LLMClient` interface is frozen, so the swap (litellm-in-process → service call) leaves consumer call
  sites unchanged. (User decision 2026-06-05 "不扩": keep v1 a library; defer the service to v2.)

## MiroThinker research integration + anti-crawl MCP (future items — research-backed, live-tested 2026-06-12/13)

Research (MiroResearchImpler, **live-tested with the user's MiroMind key**) established the hosted
`mirothinker-1-7-deepresearch` is a **closed server-side agent**: it ignores caller-supplied OpenAI `tools`
(uses its own server-side `web-processing.google_search`), and the only official "subscription + your own tool"
channel — `mcp_servers` — returns `403 mcp_servers_not_allowed` (gated behind a beta this account lacks). Net:
external tooling has exactly one legal entry (`mcp_servers`), currently disabled. MiroFlow ships **no** browsing
MCP on any branch (only a Playwright `browser_session.py`), so an anti-crawl MCP must be user-supplied regardless.
Full detail: `docs/sendbox/toMiroResearchImpler/miromind-repos-and-anticrawl.zh.md`.

1. **MiroResearch as a JarvanKB research skill.** A CLI-wrapper skill over the MiroMind Responses API
   (`MIROMIND_API_KEY`), living in the parent repo `Skills/MiroResearch`. **Soft-linked into JarvanKB at
   `Skill/research/MiroResearch` → `../../../../Skills/MiroResearch`** (new `Skill/research/` category; relative,
   monorepo-portable; done 2026-06-13). Not an MCP; no anti-crawl of its own. **Long-term form decision
   (deferred):** keep symlink / vendor copy / submodule — **must be resolved at the standalone-repo extraction
   (UN-041)**, since the link points OUTSIDE JarvanKB into the parent `Skills/` and breaks on extraction.

2. **Repo MCP façade v1 — crawl/anti-crawl tools first (no-dependency — start anytime).** Framed (user
   2026-06-14) as the **first slice of a repo-wide MCP façade**, NOT a one-off: a thin aggregator that
   re-exposes existing capability as MCP tools, built to grow tool-modules (one per engine/skill) toward "one
   MCP = the agent toolbox" — NOT a god-process that absorbs logic (keep Engine/Service/Skill as the
   implementation; MCP = the 4th surface). v1 wraps the crawl path (zhihu-crawl / bilibili-crawl + engines) with
   structured output (content, source_url, fetch_method, auth_context, failure_reason, needs_human_action). One
   MCP serves BOTH downstream paths (item 3), so it does **not** depend on the MiroMind beta reply — the
   no-regret first move. **Placement = new `Service/mcp/` subcategory** (user decision 2026-06-14: option 2 —
   group MCP servers under their own `Service/` subcat; it IS a long-running server like cookie-manager, so it
   lives under Service, wrapping Engine + Skill/crawl as libs). **Granularity rule:** Engine `fetch`/`transcribe`
   + Skill/crawl → request/response tools; **Services/watchers = daemons → only *control* tools (status/once),
   the daemon stays a Service**. **Compliance boundary baked in:** authorized sessions/cookies only, rate-limit +
   cache + provenance, manual handoff on CAPTCHA/access walls — NO CAPTCHA bypass / access-control evasion /
   identity rotation. **Consumption rule of thumb (2026-06-14):** stateful/shared-backend capability (crawl +
   anti-crawl: cookies, rate-limit, cache) → expose + consume as **MCP** (one central backend, all runtimes incl.
   Hermes); pure-instruction / agent-local capability (research prompts, grill-with-docs, classify heuristics) →
   stays a **Skill**. Don't double-front the same capability (once crawl is MCP, don't also sync the crawl Skill
   to Hermes).

3. **Pending user decision — Path A vs Path C** (surfaced to user 2026-06-13; tracked Dashboard UN-042; the
   `mcp_servers` beta request was already sent to MiroMind, awaiting reply):
   - **(A) Subscription path** — once MiroMind grants the `mcp_servers` beta, attach the item-2 MCP to the hosted
     mirothinker. Lightest ops, uses the subscription; blocked until beta granted; MCP must be publicly reachable.
   - **(C) Self-host now** — MiroFlow + a third-party brain (Claude/GPT/Gemini) + the item-2 MCP. Works today,
     full local control; does **not** consume the MiroMind subscription.
   - Path B (MiroFlow + hosted mirothinker as brain) is **eliminated** by the evidence. Decision = wait for
     Miro's reply, then branch; item-2 is the no-regret first move under both.

## How this doc is updated

Append-most. Major changes (phase scope reshuffle, recipe upgrade, project rename) go through `RepoMem.merge` HITL review.

> **Eager-materialization sync note**: This file's content is mirrored by plan Task 8.2 heredoc in `docs/superpowers/plans/2026-05-31-SP-0-jarvankb-skeleton.md`. Impler's Task 8 overwrites this file with identical content (idempotent). If editing this file before impler runs, edit the plan heredoc to match.
