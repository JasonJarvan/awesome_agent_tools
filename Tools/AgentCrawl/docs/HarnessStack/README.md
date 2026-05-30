# HarnessStack — `<target-repo>` at solo/long-lived

> One-time distillation source for an AI agent operating in the target
> repository. Read once, condense sections 1–4 into `CLAUDE.md`, then
> consult `longterm.md` for full detail. Re-read this file only on recipe
> upgrade.

## 1. Identity

This repository runs HarnessStack at `solo` scale, horizon `long-lived`, type `platform`.

- **Active recipe:** `openspec-superpowers-repomem-sendbox-dashboard`
- **Source template:** `harness-factory/assets/templates/longterm/solo.md`
- **OpenSpec Root:** `docs/openspec/`
- **Effective from:** `<YYYY-MM-DD>` (set on activation)

## 2. Active Methods

- `OpenSpec` — Spec layer; change cycle (propose → design → tasks → implement → archive). One task uses one `change-id`.
- `Superpowers` — execution discipline; brainstorming and writing-plans plus the OpenSpec change cycle jointly carry the emergent primary-workflow responsibility.
- `RepoMem` — long-term repository memory (persist + temporary split, HITL merge into long-term after `OpenSpec.archive`).
- `sendbox-protocol` — file-based asynchronous channel for multi-session / cross-worktree coordination. Main agent's `docs/sendbox/` is the single source of truth; side cwds write to it by relative or absolute path.
- `cc-dashboard` — single-file projection of pending user actions at `docs/Dashboard/index.md`. Atomic granularity (one letter with N asks → N rows). Independent lifecycle from letters.
- Inactive by default: `ECC` / `ECC(light)`, `BMAD` / `gstack` / `GSD`.

## 3. Per-Task Pipeline (Compressed)

> This is the compressed view. **It is not authoritative.** For the full
> step list, conflict rules, and exception handling, see
> `longterm.md § Pipeline`. Sendbox letter writes and dashboard row writes
> are side-effects of the steps below, not separate steps.

1. `RepoMem.read` — load long-term architecture and memory as task context.
2. `Superpowers.brainstorming` — clarify vague intent. (Spawning a subagent → `handoff.md`; Type-B dashboard row.)
3. `OpenSpec.explore / propose` — convert intent into a formal change with specs.
4. `RepoMem.capture` — open task-level temporary docs.
5. `Superpowers.writing-plans` — consume OpenSpec specs and tasks. (Subagent plan → `plan-ready.md`.)
6. Execute — `using-git-worktrees` + `executing-plans` + TDD; `RepoMem.capture` continuous. (A-12 boundary → blocker letter.)
7. `Superpowers.verification-before-completion` + `OpenSpec.verify` — dual-perspective verification.
8. `Superpowers.requesting-code-review`. (Bundled `decisions.md` letters MAY be written here.)
9. `Superpowers.finishing-a-development-branch`. (`archived.md` MAY be written here.)
10. `OpenSpec.archive` — freeze change record.
11. `RepoMem.merge` (HITL) — promote stable knowledge; any `promote-to-durable.md` content lands here.
12. `RepoMem.prune / split` — periodic hygiene, not per-task.

## 4. Hard Invariants

- **Add-only**: a method that has been activated never deactivates; upgrades are extensions, never replacements. Downgrades are NOT add-only — prefer leaving layers active-but-unexercised over removing them.
- **Dual-verification gate**: both `OpenSpec.verify` AND `Superpowers.verification-before-completion` MUST pass before `finishing-a-development-branch`. RepoMem, sendbox, and cc-dashboard have no verification role.
- **Merge ordering**: `RepoMem.merge` runs strictly AFTER `OpenSpec.archive`, never before, and is always HITL. Any sendbox `promote-to-durable.md` content flows through this gate, never via a parallel path.
- **Single task identifier**: `<task>` = `change-id` = `<slug>` — one identifier across OpenSpec, RepoMem, and HarnessStack docs.
- **No content duplication across task-level documents**: OpenSpec change docs own the per-change contract; RepoMem temporary memory owns WHY/context; writing-plans owns HOW. See `longterm.md § Cross-Layer Conflicts`.
- **Sendbox cannot override OpenSpec**: an archived OpenSpec change is the durable per-change contract. A letter MAY cite the spec; if the letter implies the spec is wrong, open a new OpenSpec change — do not edit the archived spec via a letter.
- **One sendbox per project**: the main agent's `docs/sendbox/` is canonical. Subagents in side cwds write to it by relative or absolute path — never fan out under their own cwd.
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
