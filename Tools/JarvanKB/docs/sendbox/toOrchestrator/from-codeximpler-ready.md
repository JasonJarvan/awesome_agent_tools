> from: CodexImpler
> recipient: root orchestrator generation 4
> mode: child convergence
> purpose: report readiness after CodexImpler onboarding
> lifecycle: burn with `docs/sendbox/toCodexImpler/handoff.md` after root reads this report
> date: 2026-06-11

# CodexImpler Ready

Task identifier: `codex-impler-onboarding`.

## Readiness Summary

CodexImpler is ready to receive a real JarvanKB task handoff.

Installed and load-verified project-critical skills for Codex:

| Skill | Source | Codex path | Verification |
|---|---|---|---|
| `repo-mem` | `/home/shenzhou/.claude/skills/repo-mem` | `/home/shenzhou/.codex/skills/repo-mem` | `SKILL.md` loadable |
| `sendbox-protocol` | `/home/shenzhou/.claude/skills/sendbox-protocol` | `/home/shenzhou/.codex/skills/sendbox-protocol` | `SKILL.md` loadable |
| `cc-dashboard` | `/home/shenzhou/.claude/skills/cc-dashboard` | `/home/shenzhou/.codex/skills/cc-dashboard` | `SKILL.md` loadable |
| `grill-with-docs` | `Tools/JarvanKB/.claude/skills/grill-with-docs` | `/home/shenzhou/.codex/skills/grill-with-docs` | `SKILL.md` loadable |

Notes:

- Used `cc-switch skills import-from-apps`, `cc-switch skills list`, and `cc-switch skills sync -a codex`.
- `cc-switch` showed the four skills enabled for Codex, but did not materialize the expected files under `~/.codex/skills/`, so I added explicit symlink fallback entries there.
- During that fallback, I detected and fixed self-referential symlinks for `repo-mem`, `sendbox-protocol`, and `cc-dashboard` under `~/.claude/skills/`, restoring them to their real source directories.
- Codex `collab` support is enabled in `~/.codex/config.toml`:
  ```toml
  [features]
  collab = true
  ```
- I added a thin `AGENTS.md` pointer in `Tools/JarvanKB/` so future Codex sessions know to read `CLAUDE.md`, use the Codex tool map, and avoid OpenSpec in JarvanKB v2.

## Contract Internalized

Read and internalized:

- `CLAUDE.md`
- `docs/HarnessStack/longterm.md` v2 sections through `Hard Invariants (v2)`; deprecated v1 archive ignored
- `~/.codex/superpowers/skills/using-superpowers/references/codex-tools.md`
- Current `docs/Dashboard/index.md` rows relevant to Codex onboarding and `grill-with-docs`
- Sample active handoff: `docs/sendbox/toSP6Impler/handoff.md`

Codex tool mapping:

| Claude Code term in skills | Codex action |
|---|---|
| `Task` | `spawn_agent` |
| parallel `Task` calls | multiple `spawn_agent` calls |
| task result | `wait` |
| completed task cleanup | `close_agent` |
| `TodoWrite` | `update_plan` |
| `Skill` | native skill instructions; read and follow `SKILL.md` |
| `Read` / `Write` / `Edit` / `Bash` | native Codex file and shell tools |

## JarvanKB v2 Pipeline

The active per-task pipeline is:

1. `RepoMem.read` two layers: global `docs/RepoMem/persist/` plus module `docs/RepoMem/`.
2. `Superpowers.brainstorming` unless the v2 auto-judge allows a skip.
3. `RepoMem.capture` for task temp docs, except fast-lane tasks skip temp by lane definition.
4. `Superpowers.writing-plans`, with `Lane: fast|full` in plan frontmatter when a plan exists.
5. Worktree execution with `using-git-worktrees`, `executing-plans`, TDD, and continuous RepoMem capture.
6. `verification-before-completion` as the single mandatory verification gate.
7. `requesting-code-review` and `finishing-a-development-branch`, both ask-first.
8. `RepoMem.merge` after finishing, HITL, with implementer-owned closure.

Key invariants I will follow:

- Single task slug across docs.
- Canonical sendbox is `Tools/JarvanKB/docs/sendbox/`; no shadow sendboxes.
- Per-task mailbox naming is `to{Prefix}{Role}/`; root remains `toOrchestrator/`.
- No OpenSpec in JarvanKB v2. The installed `openspec-*` skills are not to be used here.
- Dashboard rows are user-action projections; sendbox lifecycle and dashboard lifecycle are independent.
- `grill-with-docs` is currently mid-replacement: UN-034 is open, so I will check its state before relying on current semantics.
- Do not touch `Tools/gstack`, `.claire/`, `.mcp.json`, or unrelated sessions' in-flight files.

## Dry-Run Self-Check

Sample handoff read:

- `docs/sendbox/toSP6Impler/handoff.md` is a Mode A child handoff.
- It reports back to `docs/sendbox/toOrchestrator/from-sp6impler-done.md`.
- Its blocker path is `docs/sendbox/toOrchestrator/from-sp6impler-blocker-<topic>.md`.
- It declares a full-lane task and requires its own brainstorm, design, plan, TDD execution, verification, ask-first finishing, and implementer-owned Step 8 RepoMem.merge.

Where I would write:

- Done letter for this onboarding: `docs/sendbox/toOrchestrator/from-codeximpler-ready.md`.
- Future task done letter: the parent mailbox named by that task handoff, normally `docs/sendbox/toOrchestrator/from-<impler>-<milestone>.md`.
- Dashboard row updates: `docs/Dashboard/index.md`.
- RepoMem temporary notes: module `docs/RepoMem/temp/<slug>/` for full-lane module work, root `docs/RepoMem/temp/<slug>/` for cross-module full-lane work.

## Convergence

CodexImpler has completed onboarding and is ready to receive a concrete SP/task handoff from root.
