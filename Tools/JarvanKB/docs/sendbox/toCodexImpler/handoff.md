> from: root orchestrator generation 4 (Claude Opus 4.8 1M, active 2026-06-07 →)
> recipient: CodexImpler — an OpenAI Codex CLI session (`codex-cli` on this machine) joining JarvanKB as an implementer
> mode: child-handoff (sendbox-protocol Mode A — root stays alive; you converge back to `toOrchestrator/` with a readiness report)
> purpose: ONBOARD a Codex session as a first-class JarvanKB impler — install the missing skills, learn the
>   tool mapping, internalize the recipe-v2 pipeline + HarnessStack contract — so root can then assign you real SP work
> lifecycle: burn after root reads your `from-codeximpler-ready.md`
> date: 2026-06-11

# Handoff — CodexImpler onboarding (cross-runtime: Codex as a JarvanKB impler)

## 0. What you are

You are a **Codex CLI** session becoming a JarvanKB **implementer**, a **direct child of root orche g4**.
You are the **first foreign-runtime participant** — every prior impler was Claude Code. This handoff bootstraps
you; your deliverable is **readiness** (a report), not yet a feature. Root stays alive and will assign you a
concrete SP task once you report ready. Task identifier: **`codex-impler-onboarding`**.

**Working dir:** `/home/shenzhou/Codes/awesome_agent_tools/Tools/JarvanKB/` (the git root is the parent
`awesome_agent_tools`; you operate inside `Tools/JarvanKB/`). The canonical sendbox is **this repo's**
`docs/sendbox/` — there is exactly one; never create another.

## 1. Runtime translation — the cross-runtime essentials (read FIRST)

The whole methodology is written in **Claude Code** tool names. Translate as you go:

- **Read `~/.codex/superpowers/skills/using-superpowers/references/codex-tools.md`** — the authoritative
  CC→Codex map. Summary: `Task`→`spawn_agent`; parallel `Task`→multiple `spawn_agent`; `TodoWrite`→
  `update_plan`; `Skill` tool→skills load natively (just follow the instructions); `Read`/`Write`/`Edit`/
  `Bash`→your native file/shell tools.
- If you will dispatch subagents (skills `subagent-driven-development`, `dispatching-parallel-agents`), enable
  in `~/.codex/config.toml`: `[features]\ncollab = true`.
- **Entry-doc difference:** Claude Code auto-loads `CLAUDE.md`; Codex auto-loads `AGENTS.md`. JarvanKB has a
  `CLAUDE.md` (the always-loaded contract) but **no `AGENTS.md` yet** — so you must read `CLAUDE.md`
  **manually** (§3). Optional readiness deliverable: create a **thin** `Tools/JarvanKB/AGENTS.md` that POINTS
  to `CLAUDE.md` + notes the Codex tool-map + the OpenSpec caveat (§5) — a pointer, **not** a copy (the
  no-duplication invariant forbids forking CLAUDE.md's content). Propose it in your readiness report.

## 2. What's already on this machine vs. what you must install

Verified by root on 2026-06-11:
- ✅ **`~/.codex/superpowers/`** is a full superpowers install — brainstorming, writing-plans, TDD,
  executing-plans, verification-before-completion, requesting-code-review, finishing-a-development-branch,
  using-git-worktrees, etc. are available to you natively. Confirm they load.
- ✅ `~/.codex/skills/` has `code-reader-zh`, `ops-doc-maintainer`, and `openspec-*` (see §5 caveat).
- ❌ **MISSING — the 4 JarvanKB-critical project skills.** Install these into `~/.codex/skills/` (the
  agentskills.io `SKILL.md` is cross-runtime — the same file works in Codex; copy or symlink each skill dir):

  | skill | source to install from |
  |---|---|
  | `repo-mem` | `~/.claude/skills/repo-mem/` |
  | `sendbox-protocol` | `~/.claude/skills/sendbox-protocol/` |
  | `cc-dashboard` | `~/.claude/skills/cc-dashboard/` |
  | `grill-with-docs` | `Tools/JarvanKB/.claude/skills/grill-with-docs/` (project-local) — **but see §5: it may be mid-replacement (UN-034); check before relying on its semantics** |

  After install, verify each loads in a fresh Codex session (appears in your skill list / is invokable).

## 3. The contract + pipeline you must internalize (read, in order)

1. **`Tools/JarvanKB/CLAUDE.md`** — the always-loaded operating contract. §1 identity/recipe (**v2
   `superpowers-repomem-sendbox-dashboard`**), §2 active methods, §3 the **8-step per-task pipeline**, §4
   **hard invariants**. This is non-negotiable; read it fully.
2. **`docs/HarnessStack/longterm.md`** (v2 block only — the part from `# longterm.md` ~L190+ onward is the
   DEPRECATED v1 archive, ignore it): **§Pipeline v2** (authoritative 8 steps), **§Hard Invariants (v2)**,
   **§Lane Tiering (v2)** (the `Lane: fast|full` axis — declare it in your plan-doc frontmatter),
   **§Harness Enhancement Layer (v2)**, **§Local sendbox conventions** (mailbox naming).
3. The pipeline in one line: `RepoMem.read` (two layers) → `brainstorming` (with the user) → `RepoMem.capture`
   (temp) → `writing-plans` → `worktree`+`executing`+**TDD**+capture → `verification-before-completion`
   (single mandatory gate) → `requesting-code-review`+`finishing-a-development-branch` (both ask-first) →
   **`RepoMem.merge`** (HITL — **the impler owns merge closure within its own lifecycle**, never fire-and-forget).

## 4. The conventions that make you a functioning impler

- **sendbox-protocol** (invoke the skill for the full spec): you receive a task as a `handoff.md` in your
  task mailbox `to<Prefix><Role>/`; you report back to the parent's mailbox with
  `from-<you>-<milestone>-done.md`, or `from-<you>-blocker-<topic>.md` (stop-and-ask: 2–3 options + your pick)
  when you hit a boundary. **You report to root at `docs/sendbox/toOrchestrator/`** unless a task handoff
  names a different parent. Burn matched letter pairs at convergence.
- **RepoMem** (invoke `repo-mem`): on `RepoMem.read` load **two layers** — global `docs/RepoMem/persist/` +
  the module's `<module>/docs/RepoMem/`. Capture task notes in `<module>/docs/RepoMem/temp/<slug>/`. At
  Step-8 **you** drive the merge (HITL): promote only cross-SP-reusable, non-code-derivable gotchas to global
  `persist/`; keep mechanism in the module; then prune temp.
- **cc-dashboard** (invoke `cc-dashboard`): the user-facing pending-action board is `docs/Dashboard/index.md`.
  Update your SP row / Active rows as your work changes state.
- **Language policy (important):** reply to the **user in chat in 中文**; write **all A2A artifacts**
  (sendbox letters, RepoMem docs, specs, plans, commit messages) **in English**. (Repo Language Policy /
  `persist/config.md`.)
- **Single task identifier:** one `<slug>` string across all your docs (CLAUDE.md §4).

## 5. ⚠️ Traps specific to you (Codex) — do NOT step on these

- **OpenSpec is REMOVED in JarvanKB v2.** Your `~/.codex/skills/` has `openspec-propose`/`openspec-apply-
  change`/`openspec-archive-change`/`openspec-explore`. **Do NOT use them here** — JarvanKB has no
  OpenSpec/`spec.md`/`change-id`/`proposal.md` flow. Design lands in `docs/superpowers/specs/`, plans in
  `docs/superpowers/plans/`. (Reintroducing OpenSpec requires a Full Rewrite — not yours to do.)
- **grill-with-docs is mid-replacement.** A separate task (UN-034) is replacing the project-local
  grill-with-docs semantics. Don't treat its current content as settled; check `docs/Dashboard/index.md`
  UN-034 status before using it.
- **Don't touch:** the `Tools/gstack` submodule, `.claire/`, `.mcp.json` (gitignored, holds a plaintext key —
  **the repo is PUBLIC**), or any other session's uncommitted in-flight files (several implers are active:
  SP6Impler, GrillDocsImpler, ZhihuClassifyImpler, BN412Impler).
- **Git discipline:** branch base = local `feat/agentcrawl-bootstrap` (NOT `origin/main`). Push to
  `origin feat/agentcrawl-bootstrap` is **enabled** (no-push lifted 2026-06-10). **Do NOT merge to `main`,
  rebase, or rewrite history** without explicit user say-so. Scope every commit with explicit pathspec (shared
  tree → expect "modified since read", re-read+retry).

## 6. Your deliverable = readiness (Mode A convergence)

This onboarding is **not** a feature task — produce a **readiness report**, then wait for root to assign real
work. Concretely:

1. Install the 4 skills (§2); verify they + the superpowers skills load in Codex.
2. Read & internalize §3 (CLAUDE.md + longterm v2) and §4 conventions; read the codex-tools map (§1).
3. (Optional) propose the thin `AGENTS.md` pointer (§1).
4. **Do a dry-run self-check:** can you (a) read a sample existing handoff (e.g. an active `to*Impler/
   handoff.md`), (b) state the 8-step pipeline back, (c) name where you'd write a done letter and a Dashboard
   row, (d) confirm the tool translations for Task/TodoWrite? Capture the answers — they prove readiness.
5. **Converge:** write `docs/sendbox/toOrchestrator/from-codeximpler-ready.md` (English) listing: skills
   installed + load-verified, tool-map understood, pipeline + invariants internalized, OpenSpec-not-used
   acknowledged, AGENTS.md proposal (if any), and "ready to receive a task handoff." Then **stop and wait** —
   root will dispatch a concrete SP (likely SP-7 after SP-6 lands, or another increment) to a task-scoped
   mailbox.

## 7. Out of scope

- Do NOT start any SP feature yet — readiness only; root assigns the task next.
- Do NOT install OpenSpec flows / use the openspec-* skills here.
- Do NOT modify CLAUDE.md / longterm.md (governance edits are root-dispatched, e.g. UN-034); the AGENTS.md
  pointer is the one allowed thin addition, and only if you propose it in the readiness report.
- Do NOT redo another session's RepoMem.merge.

## 8. Convergence path

- **Parent cwd (absolute):** `/home/shenzhou/Codes/awesome_agent_tools/Tools/JarvanKB/`
- **Ready →** `docs/sendbox/toOrchestrator/from-codeximpler-ready.md` (§6.5).
- **Blocked (e.g. a skill won't load in Codex, or the tool-map is insufficient for a needed skill) →**
  `docs/sendbox/toOrchestrator/from-codeximpler-blocker-<topic>.md` (what failed + 2–3 options + your pick).

Welcome to JarvanKB, CodexImpler. Same recipe, same sendbox, same RepoMem — just a different runtime under it.

— root orche g4 (2026-06-11)
