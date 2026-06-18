# CLAUDE.md — JarvanKB

> Always-loaded operating contract for any AI agent working in this directory.
> Distilled from `docs/HarnessStack/README.md` §1–4 (recipe v2 `superpowers-repomem-sendbox-dashboard`).
> For full detail consult `docs/HarnessStack/longterm.md`. Re-read on recipe upgrade.

## 1. Identity

- **HarnessStack scale:** `solo` / horizon `long-lived` / repository type `platform`
- **Active recipe:** `superpowers-repomem-sendbox-dashboard` (**v2**, effective 2026-05-31)
- **Previous recipe:** `openspec-superpowers-repomem-sendbox-dashboard` (v1, deprecated 2026-05-31; see version-plan.md)
- **OpenSpec:** **removed** in v2 Full Rewrite — see `docs/HarnessStack/longterm.md` §Recipe v1→v2 Migration

## 2. Active Methods

| Layer | Method | Status | Notes |
|---|---|---|---|
| Execution Discipline | `Superpowers` | **active** | brainstorming, writing-plans, using-git-worktrees, executing-plans, TDD, verification-before-completion, requesting-code-review, finishing-a-development-branch |
| Repository Memory | `RepoMem` | **active** | persist + temp split; HITL merge runs **after** `finishing-a-development-branch`; **layered** (global `<root>/docs/RepoMem/persist/` + per-module `<module>/docs/RepoMem/`) |
| Harness Enhancement | `sendbox-protocol` | **active** | `<root>/docs/sendbox/` is single source of truth; subagents in side cwds write to it by path. **Per-task mailbox naming**: `to{Prefix}{Role}/` (id-first, role-second; e.g. `toSP0Impler/`, `toZhihuCrawlOrche/`). Root orchestrator special-case: `toOrchestrator/` (no prefix). See `longterm.md §Local sendbox conventions` for the full pattern + CodeTeam#1 |
| Harness Enhancement | `cc-dashboard` | **active** | `<root>/docs/Dashboard/index.md` projects pending user actions; one letter → N rows; hook config `docs/HarnessStack/hooks/cc-dashboard.md` |
| Harness Enhancement | `code-map` (codegraph) | **active** | local symbol/call-graph index (`.codegraph/`, MCP + CLI); prefer `query`/`callers`/`impact` over ad-hoc grep for in-repo symbol lookups — codegraph = the map, RepoMem = the why; `callees`/`affected` sparse on dynamic Python (most of this repo). Detail: `longterm.md §Harness Enhancement Layer (v2)` |
| Spec | `OpenSpec` | **removed in v2** | See longterm.md §Recipe v1→v2 Migration; if future Skill needs SDK-grade contract versioning, re-introduce per that module only |

## 3. Per-Task Pipeline (compressed — authoritative in `longterm.md` §Pipeline v2)

1. `RepoMem.read` — load global persist + per-module RepoMem (two layers); prefer codegraph (`query`/`callers`/`impact`) over ad-hoc grep for in-repo symbol/caller/impact lookups (map vs why — §2 code-map row)
2. `Superpowers.brainstorming` — clarify vague intent *(auto-judge skip on `clear` / trivial fix; subagent → `handoff.md` + Type-B dashboard row; full-lane: MAY grill the draft spec via project skill `grill-with-docs` before step 4 — auto-judge)*
3. `RepoMem.capture` — open task-level temporary docs in the relevant module's `docs/RepoMem/temp/<slug>/`
4. `Superpowers.writing-plans` — produce plan, land at `<root>/docs/superpowers/plans/` or `<module>/docs/superpowers/plans/`
5. `using-git-worktrees` + `executing-plans` + **TDD** + `RepoMem.capture` (continuous)
6. `Superpowers.verification-before-completion` — single gate; tests + evidence required before claiming done
7. `Superpowers.requesting-code-review` + `finishing-a-development-branch` — both **ask-first**
8. `RepoMem.merge` (HITL, **impler owns closure**) — the implementer drives merge to completion within its own task lifecycle (may delegate *execution* to orche, but tracks it to done before reporting); promote per-module decisions to global persist when warranted — **promote cross-SP-reusable root-causes / gotchas globally, NOT mechanism that lives in code, NOR what codegraph derives from current code (symbol locations / call graphs / impact sets); a downstream SP working in another module's cwd does not read your module's `decisions.md`** (full promotion standard: `longterm.md` §Pipeline v2 step 8); then `prune` / `split`

**Lane Tiering (structural axis, orthogonal to the step-2 auto-judge skip):** every task carries `Lane: fast|full` — default **fast** — declared in the plan-doc frontmatter (a trivial task with no plan is implicitly fast). Select **full** if ANY: touches dependencies / cross-cutting ≥2 of Engine|Service|Skill / crosses Python↔Node / produces a `RepoMem/persist/` asset / adds net-new public contract surface. fast = plan doc only (may be minimal; `specs/` optional, omission noted in one line in the plan) and **skip `RepoMem/temp/<slug>/` entirely**; full = today's full doc set. Lane changes which doc artifacts exist, never a step's policy. Detail: `longterm.md §Lane Tiering (v2)`.

Sendbox letters & dashboard rows are **side-effects** of the steps above, not standalone steps.

**Milestone gate (orchestrator standing rule — user 2026-06-18).** On **every task completion**, check whether a user-facing **capability milestone** (v1→v5+; `version-plan.md §Capability Milestones` / `Dashboard §里程碑`) is about to unlock; update `Dashboard §里程碑`. When a milestone **unlocks or nears completion**, hand off an impler (normal handoff flow) to take the user through the **"last mile"** to the *delivered capability* — the integration/UX/ops/deploy glue beyond any single SP's technical done. Applies to root and to each SubOrche for its own vertical's milestone(s). Detail: `longterm.md §Milestone Gating (v2)`.

## 4. Hard Invariants

- **Single task identifier.** `<task> = <slug>` — one string across HarnessStack and RepoMem docs.
- **Add-only.** An active method never deactivates by stealth. Recipe upgrades (e.g. v1→v2 removal of OpenSpec) require a **Full Rewrite** entry in longterm.md.
- **Single verification gate.** `Superpowers.verification-before-completion` is the only mandatory pre-commit check. RepoMem, sendbox, cc-dashboard have no verification role.
- **Merge ordering & ownership.** `RepoMem.merge` runs strictly AFTER `finishing-a-development-branch`, never before, always HITL. **The implementer owns merge closure** — it runs the merge within its own task lifecycle, or delegates *execution* to orche but tracks it to completion before reporting done. Never fire-and-forget to orche.
- **No content duplication** across per-task document sets (RepoMem temp / HarnessStack `temporary-<task>.md`). HITL reviewer rejects duplicated content.
- **Sendbox is canonical.** The main agent's `<root>/docs/sendbox/` is the only sendbox. Side cwds write to it by path — never fan out.
- **Per-task mailbox.** Every parallel non-root session (sub-orche, impler, reviewer, ...) reads/writes to its own task-scoped mailbox `to{Prefix}{Role}/`. A single shared `toImpler/` or `toOrche/` is **forbidden** when ≥2 sessions of that role can run concurrently. Hierarchies supported: Orche → Impler, Orche → SubOrche → Impler.
- **Layered RepoMem.** Subagent in `<module>/` cwd reads two layers (global persist + module memory) on `RepoMem.read`. Writes go to module unless the decision is global-scope, in which case HITL merge promotes it.
- **Lane axis: structural, additive, reversible.** `Lane: fast|full` (default fast) governs which doc artifacts exist, never a step's policy. Fast-lane absence of `temp/<slug>/` vacuously satisfies `<task> = <slug>` (NOT a divergence — no Recipe Invariant Exception); absence-by-lane is NOT an auto-judge skip (no skip note); `fast→full` mid-flight promotion is cheap.
- **One letter → N dashboard rows.** Each atomic user action emits its own row.
- **Sendbox & dashboard lifecycles independent.** Burning a letter does NOT cascade-delete rows; marking a row done does NOT trigger letter cleanup.

## Where to Look

| Need | Path |
|---|---|
| Full HarnessStack contract | `docs/HarnessStack/longterm.md` |
| Lane Tiering full rule (selection, doc-set mapping, invariants) | `docs/HarnessStack/longterm.md` §Lane Tiering (v2) |
| code-map / codegraph ops (install, MCP, worktree fallback) | `docs/HarnessStack/longterm.md` §Harness Enhancement Layer (v2) |
| Project-local skills (`grill-with-docs`) | `.claude/skills/<name>/SKILL.md` |
| Day-One Init / per-task / long-term usage manual | `docs/HarnessStack/_toUser/README.md` |
| Task-level recipe patch (global scope) | `docs/HarnessStack/temporary-<task>.md` |
| Task-level recipe patch (module scope) | `<module>/docs/HarnessStack/temporary-<task>.md` |
| Repo-local cc-dashboard hook config | `docs/HarnessStack/hooks/cc-dashboard.md` |
| Know what the user owes right now | `docs/Dashboard/index.md` |
| Capability milestone roadmap (v1→v5+) + gating rule | `docs/RepoMem/persist/version-plan.md §Capability Milestones` + `docs/Dashboard/index.md §里程碑` (detail `longterm.md §Milestone Gating (v2)`) |
| RepoMem layout overview | `docs/RepoMem/README.md` |
| Global long-term memory (loaded by `RepoMem.read`) | `docs/RepoMem/persist/{config,version-plan}.md` + `architecture/` + `memory/` |
| Per-module memory (loaded by `RepoMem.read` in module cwd) | `<module>/docs/RepoMem/{architecture,decisions}.md` + `temp/<slug>/` |
| Frozen pre-OpenSpec decisions (D1–D7, historical) | `docs/RepoMem/persist/memory/pre-openspec-decisions.md` |
| Cross-module brainstorming design | `docs/superpowers/specs/` |
| Per-module brainstorming design | `<module>/docs/superpowers/specs/` |
| Cross-module implementation plan | `docs/superpowers/plans/` |
| Per-module implementation plan | `<module>/docs/superpowers/plans/` |
| Sendbox letters (root orche inbox) | `docs/sendbox/toOrchestrator/` |
| Sendbox letters (per-task mailbox pattern) | `docs/sendbox/to{Prefix}{Role}/` — e.g. `toSP0Impler/`, `toZhihuCrawlOrche/`, `toZhihuCrawlImpler/` |
| Caller-agent contract for using JarvanKB tools | `docs/sendbox/toAgent/handoff.md` (persist-lifecycle) |
| Project README (human-facing) | `README.md` |
| Top-level layout reference | `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` |
