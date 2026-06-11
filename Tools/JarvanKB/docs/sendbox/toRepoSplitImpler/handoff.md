> from: root orchestrator generation 4 (Claude Opus 4.8 1M, active 2026-06-07 →)
> recipient: RepoSplitImpler (a FUTURE Claude Code session — NOT to be started yet)
> mode: child-handoff (sendbox-protocol Mode A — root stays alive; converge back to `toOrchestrator/`)
> purpose: extract `Tools/JarvanKB/` out of the `awesome_agent_tools` monorepo into its OWN standalone repo,
>   leaving `awesome_agent_tools` holding only a LINK (submodule) to it
> status: ⛔ DEFERRED — do NOT start until the activation conditions in §1 are met and the user explicitly activates
> lifecycle: persist (this is a prepared future-task definition, not an active letter); becomes the live handoff
>   when root activates it. Durable record also in `version-plan.md §v1.0 OSS release plan`.
> date: 2026-06-11 (prepared)

# Handoff (DEFERRED) — RepoSplitImpler: extract JarvanKB as a standalone repo

## 0. What this is

A **prepared future task**, captured now while the intent is fresh. **Do not execute it yet.** It defines the
extraction of the JarvanKB project from the `awesome_agent_tools` monorepo into a standalone Git repository,
with `awesome_agent_tools` keeping only a link back. When activated, the executing session is a **direct child
of root orche g4** and converges to `toOrchestrator/`. Task identifier (reserved): **`repo-split-standalone`**.

## 1. ⛔ Activation conditions (ALL must hold before starting)

1. **v1 complete** — SP-0…SP-7 implemented + verified end-to-end. As of 2026-06-11, **SP-6 is in flight
   (UN-038) and SP-7 is not yet started** → not ready.
2. **Org / name decided** — UN-006 (GitHub Org name: JarvanKB / Jarvan / JarvanWorks) resolved.
3. **User explicitly activates** this task (it is destructive/outward-facing — history rewrite + a new public
   repo + a submodule swap in the parent).

## 2. The goal (user framing, 2026-06-11)

Move the **whole** current project — `awesome_agent_tools/Tools/JarvanKB/` — out into its **own standalone
repo** (`JarvanKB`). `awesome_agent_tools` then keeps **only a link** to it. The natural "link" is a **git
submodule** at `Tools/JarvanKB`, consistent with how `awesome_agent_tools` already links its other components
(`.gitmodules` today: `Skills/ops-doc-maintainer`, `Skills/cc-relocate-project`, `Tools/gstack`,
`Tools/claude-hud`, `CodeTeam`). Confirm submodule-vs-other-pointer with the user at activation.

## 3. Relationship to the existing §9 fractal split (RECONCILE at activation — do not assume)

`docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md §9` defines a **finer-grained** split:
JarvanKB monorepo → **one repo per sub-module** (`git filter-repo --subdirectory-filter Engine/zhihu/` etc.)
under an Org, with the monorepo as an umbrella. **This task is COARSER and at a different level**: extract
JarvanKB-as-a-whole first. The two are not the same operation. Open question for the activation brainstorm:
- Is whole-repo extraction the **new plan** (replacing per-SP fractal), or **step 1** before a later §9 fractal
  inside the standalone JarvanKB repo? The user's "作为独立仓库" reads as whole-repo; confirm + update §9 / the
  version-plan accordingly.

## 4. Key considerations / risks to resolve at activation (not now)

- **History lives on the feature branch, not main.** ALL JarvanKB work is on `feat/agentcrawl-bootstrap`
  (200+ commits ahead of `origin/main`, never merged to main). The extraction (`git filter-repo
  --subdirectory-filter Tools/JarvanKB/` on a fresh clone) must capture **this branch's** history, and the
  branch/main relationship in the parent must be settled first (does main get the JarvanKB work before/along
  with the split, or does the submodule just point at the feature branch?).
- **Self-containment is good** — `docs/{HarnessStack,RepoMem,sendbox,Dashboard,superpowers}`, `CLAUDE.md`,
  `Engine/`, `Service/`, `Skill/` all live *inside* `Tools/JarvanKB/`, so they travel cleanly. **Verify**
  nothing JarvanKB depends on lives *outside* `Tools/JarvanKB/` (e.g. parent-root `Skills/`, `.mcp.json`
  gitignored, the parent `.gitignore`'s `!.claude/` re-include — that rule must be reproduced in the new repo
  root or `.claude/skills/grill-with-docs` gets ignored).
- **No nested submodules inside JarvanKB today** (gstack is at the *sibling* `Tools/gstack`, not inside
  JarvanKB) → extraction is clean; re-verify at activation.
- **Path simplification:** after extraction the git root = JarvanKB itself; commit pathspecs, CLAUDE.md
  "Primary working directory", and sendbox/Dashboard pointers that currently assume `Tools/JarvanKB/` simplify.
- **Parent-side swap:** removing `Tools/JarvanKB/` from `awesome_agent_tools` and adding it back as a submodule
  touches the parent repo (and possibly its history). Outward-facing + hard to reverse → user-gated, and
  **the `Tools/gstack` submodule stays untouched** per standing invariant.
- **Public repo:** both repos are/become public — re-check no secrets enter tracked history during the rewrite.

## 5. When activated — pipeline

Light by design now; at activation run: `RepoMem.read` → **brainstorming with the user** (resolve §2 link
mechanism, §3 fractal reconciliation, §4 branch/history strategy, Org/name) → writing-plans → execute on a
disposable mirror clone first (never filter-repo the working repo in place) → verify the standalone repo
builds/tests + the parent submodule link resolves → user-gated push/creation → Step-8 (update version-plan +
SP-0 §9 to reflect reality). Lane: full.

## 6. Convergence (when activated)

- Parent cwd (absolute): `/home/shenzhou/Codes/awesome_agent_tools/Tools/JarvanKB/` (will change post-split).
- Done → `docs/sendbox/toOrchestrator/from-reposplitimpler-done.md`. Blocked → `...-blocker-<topic>.md`.

— root orche g4 (2026-06-11, prepared/deferred)
