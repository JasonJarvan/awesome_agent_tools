# CLAUDE.md — AgentCrawl

> Always-loaded operating contract for any AI agent working in this directory.
> Distilled from `docs/HarnessStack/README.md` §1–4 (recipe `openspec-superpowers-repomem-sendbox-dashboard`).
> For full detail consult `docs/HarnessStack/longterm.md`. Re-read the HarnessStack README only on recipe upgrade.

## 1. Identity

- **HarnessStack scale:** `solo` / horizon `long-lived` / repository type `platform`
- **Active recipe:** `openspec-superpowers-repomem-sendbox-dashboard`
- **OpenSpec Root:** `docs/openspec/`
- **Effective from:** 2026-05-26

## 2. Active Methods

| Layer | Method | Status | Notes |
|---|---|---|---|
| Spec | `OpenSpec` | **active** *(CLI install pending — see UN-001)* | change cycle: explore → propose → apply → verify → archive; one task = one `change-id` |
| Execution Discipline | `Superpowers` | **active** | brainstorming, writing-plans, using-git-worktrees, executing-plans, TDD, verification-before-completion, requesting-code-review, finishing-a-development-branch |
| Repository Memory | `RepoMem` | **active** | persist + temp split; HITL merge runs **after** `OpenSpec.archive` |
| Harness Enhancement | `sendbox-protocol` | **active** | `docs/sendbox/` is the single source of truth; subagents in side cwds write to it by absolute/relative path |
| Harness Enhancement | `cc-dashboard` | **active** | `docs/Dashboard/index.md` projects pending user actions; one letter → N rows; hook config `docs/HarnessStack/hooks/cc-dashboard.md` |
| Primary Workflow | `BMAD` / `gstack` / `GSD` | inactive | emergent ownership via OpenSpec change cycle + Superpowers brainstorming/writing-plans |
| Harness Enhancement | `ECC` / `ECC(light)` | inactive | add `ECC(light)` only when memory/hooks/verification loops would benefit |

## 3. Per-Task Pipeline (compressed — authoritative version in `longterm.md` §Pipeline)

1. `RepoMem.read` — load long-term architecture + memory
2. `Superpowers.brainstorming` — clarify vague intent *(auto-judge skip on `clear` / trivial fix; spawning subagent → `handoff.md` + Type-B dashboard row)*
3. `OpenSpec.explore / propose` — convert intent into a formal change with specs *(auto-judge skip on trivial / pure refactor / `<3h test` / spike; skipping #3 implies skipping #11)*
4. `RepoMem.capture` — open task-level temporary docs
5. `Superpowers.writing-plans` — consume OpenSpec specs and tasks *(subagent plan → `plan-ready.md`)*
6. `using-git-worktrees` + `executing-plans` + **TDD** *(A-12 boundary → blocker letter)*
7. `RepoMem.capture` (continuous) — record tacit knowledge
8. **`Superpowers.verification-before-completion` + `OpenSpec.verify`** — dual-perspective verification, both must pass
9. `Superpowers.requesting-code-review` — **ask-first**
10. `Superpowers.finishing-a-development-branch` — **ask-first**
11. `OpenSpec.archive` — **ask-first**, half-irreversible, freezes the change record
12. `RepoMem.merge` — **HITL**, promote `temp/<slug>/` lessons; any `from-<x>-promote-to-durable.md` lands here
13. `RepoMem.prune / split` — periodic hygiene, not per-task

Sendbox letters & dashboard rows are **side-effects** of the steps above, not standalone steps.

## 4. Hard Invariants

- **Single task identifier.** `<task> = change-id = <slug>` — one string across HarnessStack, OpenSpec, and RepoMem docs.
- **Add-only.** An active method never deactivates; upgrades are supersets. Downgrades NOT add-only — prefer leaving layers active-but-unexercised.
- **Dual verification gate.** Both `OpenSpec.verify` AND `Superpowers.verification-before-completion` MUST pass before `finishing-a-development-branch`. RepoMem, sendbox, cc-dashboard have no verification role.
- **Merge ordering.** `RepoMem.merge` runs strictly AFTER `OpenSpec.archive`, never before, always HITL.
- **No content duplication** across per-task document sets (OpenSpec change docs / RepoMem temp / HarnessStack `temporary-<task>.md`). HITL reviewer rejects duplicated content.
- **Sendbox cannot override OpenSpec.** A letter MAY cite an archived spec; it MUST NOT mutate it. If the spec is wrong, open a new OpenSpec change.
- **One sendbox per project.** The main agent's `docs/sendbox/` is canonical. Side cwds write to it by path — never fan out.
- **One letter → N dashboard rows.** Each atomic user action emits its own row.
- **Sendbox & dashboard lifecycles independent.** Burning a letter does NOT cascade-delete rows; marking a row done does NOT trigger letter cleanup.
- **No silent invariant skips.** Pipeline ordering, merge gates, verification topology are recipe invariants. Exceptions require a declared `Recipe Invariant Exception` in the task contract with reason + compensating action.

## Where to Look

| Need | Path |
|---|---|
| Full HarnessStack contract | `docs/HarnessStack/longterm.md` |
| Day-One Init / per-task / long-term usage manual | `docs/HarnessStack/_toUser/README.md` |
| Task-level patch (when a task is in progress) | `docs/HarnessStack/temporary-<task>.md` |
| Repo-local cc-dashboard hook config | `docs/HarnessStack/hooks/cc-dashboard.md` |
| Know what the user owes right now | `docs/Dashboard/index.md` |
| RepoMem layout overview | `docs/RepoMem/README.md` |
| Long-term memory (loaded by `RepoMem.read`) | `docs/RepoMem/persist/{config,version-plan}.md` + `architecture/` + `memory/` |
| Frozen pre-OpenSpec decisions (D1–D7) | `docs/RepoMem/persist/memory/pre-openspec-decisions.md` |
| Per-task temp memory | `docs/RepoMem/temp/<slug>/` |
| Per-change OpenSpec record | `docs/openspec/changes/<change-id>/` (root `openspec/` is a symlink → `docs/openspec/` so the CLI discovers it from repo root) |
| OpenSpec slash commands / skills | `.claude/commands/opsx/*` + `.claude/skills/openspec-*` (restart IDE to load) |
| Sendbox letters (multi-session coordination) | `docs/sendbox/to<Role>/` |
| Caller-agent contract for USING AgentCrawl | `docs/sendbox/toAgent/handoff.md` (persist-lifecycle) |
| Project README (human-facing) | `README.md` |
