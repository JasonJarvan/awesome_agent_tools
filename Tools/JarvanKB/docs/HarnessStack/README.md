# HarnessStack — `JarvanKB` at solo/long-lived

> One-time distillation source for an AI agent operating in the target
> repository. Read once, condense sections 1–4 into `CLAUDE.md`, then
> consult `longterm.md` for full detail. Re-read this file only on recipe
> upgrade.

## 1. Identity

This repository runs HarnessStack at `solo` scale, horizon `long-lived`, type `platform`.

- **Active recipe:** `superpowers-repomem-sendbox-dashboard` (**v2**, effective 2026-05-31)
- **Source template:** `harness-factory/assets/templates/longterm/solo.md`
- **Spec layer:** removed in the v2 Full Rewrite — see `longterm.md §Recipe v1→v2 Migration`, which records the prior (v1) recipe id and the full migration detail.
- **Effective from:** 2026-05-31

## 2. Active Methods

- `Superpowers` — execution discipline; brainstorming and writing-plans carry the emergent primary-workflow responsibility.
- `RepoMem` — long-term repository memory (persist + temporary split; HITL merge into long-term after `finishing-a-development-branch`); **layered** (global `<root>/docs/RepoMem/persist/` + per-module `<module>/docs/RepoMem/`).
- `sendbox-protocol` — file-based asynchronous channel for multi-session / cross-worktree coordination. Main agent's `docs/sendbox/` is the single source of truth; side cwds write to it by relative or absolute path. Per-task mailbox naming `to{Prefix}{Role}/` (see `longterm.md §Local sendbox conventions`).
- `cc-dashboard` — single-file projection of pending user actions at `docs/Dashboard/index.md`. Atomic granularity (one letter with N asks → N rows). Independent lifecycle from letters.
- Removed in v2: the Spec layer. See `longterm.md §Recipe v1→v2 Migration`.
- Inactive by default: `ECC` / `ECC(light)`, `BMAD` / `gstack` / `GSD`.

## 3. Per-Task Pipeline (Compressed)

> This is the compressed view. **It is not authoritative.** For the full
> step list, conflict rules, and exception handling, see
> `longterm.md § Pipeline v2`. Sendbox letter writes and dashboard row writes
> are side-effects of the steps below, not separate steps.

1. `RepoMem.read` — load global persist + per-module RepoMem (two layers).
2. `Superpowers.brainstorming` — clarify vague intent. (Spawning a subagent → `handoff.md`; Type-B dashboard row.)
3. `RepoMem.capture` — open task-level temporary docs in the relevant module's `docs/RepoMem/temp/<slug>/`.
4. `Superpowers.writing-plans` — produce plan; land at `<root>/docs/superpowers/plans/` or `<module>/docs/superpowers/plans/`. (Subagent plan → `plan-ready.md`.)
5. Execute — `using-git-worktrees` + `executing-plans` + TDD; `RepoMem.capture` continuous. (A-12 boundary → blocker letter.)
6. `Superpowers.verification-before-completion` — single gate; tests + evidence required before claiming done.
7. `Superpowers.requesting-code-review` + `finishing-a-development-branch` — both ask-first.
8. `RepoMem.merge` (HITL) — promote per-module decisions to global persist when warranted; any `promote-to-durable.md` content lands here; then `prune` / `split`.

## 4. Hard Invariants

- **Add-only**: a method that has been activated never deactivates by stealth; recipe upgrades (e.g. the v1→v2 removal of the Spec layer) require a **Full Rewrite** entry in `longterm.md`. Downgrades are NOT silent — prefer leaving layers active-but-unexercised over removing them.
- **Single verification gate**: `Superpowers.verification-before-completion` is the only mandatory pre-commit check. RepoMem, sendbox, and cc-dashboard have no verification role.
- **Merge ordering**: `RepoMem.merge` runs strictly AFTER `finishing-a-development-branch`, never before, and is always HITL. Any sendbox `promote-to-durable.md` content flows through this gate, never via a parallel path.
- **Single task identifier**: `<task>` = `<slug>` — one identifier across HarnessStack and RepoMem docs.
- **No content duplication across task-level documents**: RepoMem temporary memory owns WHY/context; writing-plans owns HOW. See `longterm.md § Cross-Layer Conflicts`.
- **One sendbox per project**: the main agent's `docs/sendbox/` is canonical. Subagents in side cwds write to it by relative or absolute path — never fan out under their own cwd.
- **Per-task mailbox**: every parallel non-root session reads/writes its own `to{Prefix}{Role}/` mailbox; a single shared role-only mailbox is forbidden for concurrent roles. See `longterm.md §Local sendbox conventions`.
- **Layered RepoMem**: a module reads two layers (global persist + module memory), writes one; HITL promotes module → global.
- **One letter → N dashboard rows**: each atomic user action emits its own row.
- **Sendbox and dashboard lifecycles are independent**: burning a letter does NOT cascade-delete dashboard rows; marking a row done does NOT trigger letter cleanup.

## 5. Where To Read More

- Full long-term contract: `./longterm.md`
- Full usage manual (Day-One Init, per-task iteration, long-term iteration): `./_toUser/README.md`
- Task-level patch (if a task is in progress): `./temporary-<task>.md`

## 6. For AI Consumers

Distill sections 1–4 into `CLAUDE.md` (or the equivalent always-loaded
instruction file in your harness). Do not duplicate `longterm.md` verbatim;
the contract remains the authoritative source for details. Re-read this
README only on recipe upgrade or full rewrite events.
