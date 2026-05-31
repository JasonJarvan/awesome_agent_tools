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
| Spec | `OpenSpec` | **removed in v2** | See longterm.md §Recipe v1→v2 Migration; if future Skill needs SDK-grade contract versioning, re-introduce per that module only |

## 3. Per-Task Pipeline (compressed — authoritative in `longterm.md` §Pipeline v2)

1. `RepoMem.read` — load global persist + per-module RepoMem (two layers)
2. `Superpowers.brainstorming` — clarify vague intent *(auto-judge skip on `clear` / trivial fix; subagent → `handoff.md` + Type-B dashboard row)*
3. `RepoMem.capture` — open task-level temporary docs in the relevant module's `docs/RepoMem/temp/<slug>/`
4. `Superpowers.writing-plans` — produce plan, land at `<root>/docs/superpowers/plans/` or `<module>/docs/superpowers/plans/`
5. `using-git-worktrees` + `executing-plans` + **TDD** + `RepoMem.capture` (continuous)
6. `Superpowers.verification-before-completion` — single gate; tests + evidence required before claiming done
7. `Superpowers.requesting-code-review` + `finishing-a-development-branch` — both **ask-first**
8. `RepoMem.merge` (HITL) — promote per-module decisions to global persist when warranted; then `prune` / `split`

Sendbox letters & dashboard rows are **side-effects** of the steps above, not standalone steps.

## 4. Hard Invariants

- **Single task identifier.** `<task> = <slug>` — one string across HarnessStack and RepoMem docs.
- **Add-only.** An active method never deactivates by stealth. Recipe upgrades (e.g. v1→v2 removal of OpenSpec) require a **Full Rewrite** entry in longterm.md.
- **Single verification gate.** `Superpowers.verification-before-completion` is the only mandatory pre-commit check. RepoMem, sendbox, cc-dashboard have no verification role.
- **Merge ordering.** `RepoMem.merge` runs strictly AFTER `finishing-a-development-branch`, never before, always HITL.
- **No content duplication** across per-task document sets (RepoMem temp / HarnessStack `temporary-<task>.md`). HITL reviewer rejects duplicated content.
- **Sendbox is canonical.** The main agent's `<root>/docs/sendbox/` is the only sendbox. Side cwds write to it by path — never fan out.
- **Per-task mailbox.** Every parallel non-root session (sub-orche, impler, reviewer, ...) reads/writes to its own task-scoped mailbox `to{Prefix}{Role}/`. A single shared `toImpler/` or `toOrche/` is **forbidden** when ≥2 sessions of that role can run concurrently. Hierarchies supported: Orche → Impler, Orche → SubOrche → Impler.
- **Layered RepoMem.** Subagent in `<module>/` cwd reads two layers (global persist + module memory) on `RepoMem.read`. Writes go to module unless the decision is global-scope, in which case HITL merge promotes it.
- **One letter → N dashboard rows.** Each atomic user action emits its own row.
- **Sendbox & dashboard lifecycles independent.** Burning a letter does NOT cascade-delete rows; marking a row done does NOT trigger letter cleanup.

## Where to Look

| Need | Path |
|---|---|
| Full HarnessStack contract | `docs/HarnessStack/longterm.md` |
| Day-One Init / per-task / long-term usage manual | `docs/HarnessStack/_toUser/README.md` |
| Task-level recipe patch (global scope) | `docs/HarnessStack/temporary-<task>.md` |
| Task-level recipe patch (module scope) | `<module>/docs/HarnessStack/temporary-<task>.md` |
| Repo-local cc-dashboard hook config | `docs/HarnessStack/hooks/cc-dashboard.md` |
| Know what the user owes right now | `docs/Dashboard/index.md` |
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
