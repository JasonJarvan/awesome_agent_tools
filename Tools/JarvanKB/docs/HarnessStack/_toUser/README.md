# Using HarnessStack — Human Operator Guide

> Human-facing manual for operating the HarnessStack activated at
> `docs/HarnessStack/` in this repository. For the authoritative contract,
> see `../longterm.md`. For the one-time AI distillation source, see
> `../README.md`.
>
> **Recipe v2** (`superpowers-repomem-sendbox-dashboard`, effective 2026-05-31).
> The Spec layer was removed in the v1→v2 Full Rewrite — see `../longterm.md §Recipe v1→v2 Migration`.

## 1. What This Stack Activates

This repository activates the following workflow layers (see
`../longterm.md § Pipeline v2` and `§ Hard Invariants (v2)` for full detail):

- `Superpowers` — execution-discipline skills: brainstorming, writing-plans, using-git-worktrees, executing-plans, TDD, verification-before-completion, requesting-code-review, finishing-a-development-branch.
- `RepoMem` — long-term repository memory, **layered**: global persistent docs under `docs/RepoMem/persist/`; per-module memory under `<module>/docs/RepoMem/`; task-scoped temp docs under `<module>/docs/RepoMem/temp/<slug>/`. Promotion temp → persist is HITL via `RepoMem.merge`, gated AFTER `finishing-a-development-branch`.
- `sendbox-protocol` — asynchronous file-based channel for any work that crosses sessions or worktrees. The main agent's `docs/sendbox/` is the single source of truth. Letters address task-scoped roles via the `to{Prefix}{Role}/` mailbox pattern (`toOrchestrator/`, `toSP0Impler/`, `toZhihuCrawlOrche/`, `toUser/`), not session names. Every letter has a lifecycle disposition (`burn` / `archive` / `persist`) and is cleaned up at two checkpoints (session end, task convergence). See `../longterm.md § Local sendbox conventions`.
- `cc-dashboard` — a single markdown file `docs/Dashboard/index.md` listing every pending action you owe, projected out of sendbox letters and handoff briefs. Atomic granularity — one letter with three asks emits three rows. Independent lifecycle: rows go `open → done → archived` and stay in Archive for 14 rolling days.

Removed in v2: the Spec layer. See `../longterm.md § Recipe v1→v2 Migration`.
Inactive by default: `ECC` / `ECC(light)`, `BMAD` / `gstack` / `GSD`. See `../longterm.md § Current Active Long-Term Baseline § Upgrade trigger` for when to extend.

## 2. Day-One Init

Run these once when this stack is first activated in your repository.

1. **Install the active methods in your agent harness.** Each method ships as a discoverable skill — install per its own README:
   - Superpowers — installed as a Claude Code skill plugin (no per-repo install).
   - RepoMem — `~/.claude/skills/repo-mem` (verify it appears in the skill list at session start).
   - sendbox-protocol — symlink: `ln -s /home/<user>/Codes/cc-sendbox/skills/sendbox-protocol ~/.claude/skills/sendbox-protocol`.
   - cc-dashboard — symlink: `ln -s "$(realpath ${CC_DASHBOARD_REPO})/skills/cc-dashboard" ~/.claude/skills/cc-dashboard`.

2. **Distill `../README.md` sections 1–4 into your `CLAUDE.md`** (or the equivalent always-loaded instruction file).

3. **Scaffold RepoMem persistent layout.** Create `docs/RepoMem/persist/architecture/` and `docs/RepoMem/persist/memory/` (empty is fine — they fill on first `RepoMem.merge`). Optionally create `docs/RepoMem/persist/version-plan.md` to track stack evolution. Per-module memory lives under each `<module>/docs/RepoMem/`.

4. **DO NOT scaffold `docs/sendbox/`.** Per the sendbox embedding-playbook, the directory grows organically when the first letter is written. Pre-creating empty subdirectories is an anti-pattern.

5. **Create the dashboard hook config and seed file.**
   - Author `docs/HarnessStack/hooks/cc-dashboard.md` with all required sections (Status / Scope / Skip-protocol / Authority frontmatter, Purpose, Data Location, **Language Policy** for this repo, Row Schema, Action Types A–F, Write Triggers, Mark-Done Protocol — pick option (a)/(b)/(c)/(d), Archive Protocol, Sendbox-protocol Coupling note, Hook Boundary).
   - Seed `docs/Dashboard/index.md` from the template in cc-dashboard SKILL.md (Active and Archive sections, empty tables).
   - Add to your `CLAUDE.md` / `AGENTS.md` "Where to Look" table: `| Know what the user owes now | docs/Dashboard/index.md (protocol: docs/HarnessStack/hooks/cc-dashboard.md) |`.

6. **Backfill the dashboard** by scanning any existing sendbox letters / handoffs / external tracker tickets — mark already-completed actions directly into `## Archive`, NOT `## Active`.

7. Read this manual end-to-end before starting your first task.

## 3. Per-Task Iteration Loop

The v2 loop is 8 steps (authoritative in `../longterm.md § Pipeline v2`). Sendbox sweeps and dashboard sweeps are operational hygiene, not separate pipeline steps.

1. **Read context.** Run `RepoMem.read <slug>` to load memory. A session working in a `<module>/` cwd reads two layers: global `docs/RepoMem/persist/` + that module's `docs/RepoMem/`.

2. **Clarify intent.** Run `Superpowers.brainstorming` unless intent is already crystal clear. If you decide to dispatch a subagent here, write a sendbox `handoff.md` to the recipient's `to{Prefix}{Role}/` mailbox first (mode = child if the parent session persists; mode = inheritance if the parent is ending). Append a Type-B dashboard row.

3. **Open task memory docs.** Run `RepoMem.capture <slug>` to open `<module>/docs/RepoMem/temp/<slug>/` (requirements.md, architecture.md, decisions.md as needed). A cross-module task opens at `docs/RepoMem/temp/<slug>/` instead.

4. **Plan.** Run `Superpowers.writing-plans`. Land the plan at `<module>/docs/superpowers/plans/YYYY-MM-DD-<slug>.md` (or `docs/superpowers/plans/` if cross-module). If a subagent produces the plan, write `from-<sender>-plan-ready.md` to the orchestrator's mailbox; the orchestrator replies with a greenlight letter.

5. **Implement.** Use `git-worktrees` + `executing-plans` + TDD per the plan; capture tacit knowledge into `temp/<slug>/decisions.md` as you go. If you hit an A-12 boundary (scope mismatch, destructive op, ambiguous upstream directive), STOP and write `from-<sender>-blocker-<topic>.md` with an options table and your tentative pick — do not silently proceed.

6. **Verify (single gate).** Run `Superpowers.verification-before-completion`: tests + lint + typecheck + manual smoke as applicable, with evidence (commands run + outputs). No claim of "done" without this output. Subagents reaching a vertical-slice acceptance gate write `from-<sender>-<milestone>-done.md`.

7. **Review + finish branch (both ask-first).** Run `Superpowers.requesting-code-review`, then `Superpowers.finishing-a-development-branch`. If you owe multiple decisions to one recipient, bundle them into ONE `from-<orche>-<recipient>-decisions.md` letter. Optionally write `from-<sender>-archived.md` for the close-out summary.

8. **Promote memory.** Run `RepoMem.merge <slug>` (HITL — review promotion candidates) AFTER finishing the branch. Module-scope decisions stay in `<module>/docs/RepoMem/decisions.md`; global-scope decisions are promoted to `docs/RepoMem/persist/memory/` with a `[Promoted to global ↗]` marker in the module log. Route any sendbox lesson through this gate via `from-<sender>-promote-to-durable.md` — the letter is burned after merge, never written directly into `docs/RepoMem/persist/`. Then `RepoMem.prune / split` on its own cadence.

**Sweep sendbox** (session end OR task convergence): scan `docs/sendbox/` for letters whose lifecycle condition has triggered and execute the disposition (`burn` via `git rm`, `archive` to `docs/sendbox/archive/`, `persist` after promotion). Letter pairs to burn together: handoff + milestone-done; plan-ready + greenlight; blocker + decisions.

**Sweep dashboard**: move any `done` rows from `## Active` to `## Archive` in the same commit. Garbage-collect rows older than 14 days from `## Archive` opportunistically.

If a task introduces constraints the long-term contract does not cover, create a `temporary-<task>.md` patch per `../longterm.md § Temporary Contractor Boundary Rules`.

## 4. Long-Term Iteration

`../longterm.md` is authoritative. Update it only when:

- a Full Rewrite Condition triggers (see `../longterm.md § Full Rewrite Conditions`) — the v1→v2 migration that removed the Spec layer is the worked example already recorded there, OR
- you switch to a superset recipe via the add-only principle — a single-line `Recipe Reference` change plus a `Last Updated Because` entry, NOT a rewrite. Likely future supersets:
  - addition of a primary workflow framework (`BMAD` / `gstack` / `GSD`) — when the project portfolio outgrows brainstorming + writing-plans orchestration.
  - addition of `ECC(light)` or `ECC(medium)` to the Harness Enhancement layer (when agent context quality / safety / repeatability becomes a recurring problem).

Routine task work does NOT modify `longterm.md` directly — use `temporary-<task>.md` for task-scoped adjustments.

## 5. Tracking HarnessStack Evolution (Optional)

Because RepoMem is active in this stack, place the version-plan at `docs/RepoMem/persist/version-plan.md`. The `repo-mem` skill maintains this naturally.

HarnessFactory does not ship a version-plan skeleton inside the bundle. Stack-evolution tracking is target-repo state, not factory output.

## 6. Pointers

- Authoritative contract: `../longterm.md`
- AI distillation source: `../README.md`
- Task-level patch (if active): `../temporary-<task>.md`
- Recipe binding + migration history: `../longterm.md § Recipe v1 → v2 Migration`
- Local sendbox conventions (mailbox naming): `../longterm.md § Local sendbox conventions`
- Hook config: `../hooks/cc-dashboard.md`
- Sendbox embedding playbook: `methods/sendbox/embedding-playbook.md` in HarnessFactory
- Dashboard embedding playbook: `methods/dashboard/embedding-playbook.md` in HarnessFactory

## 7. Common Questions

**Q: I just want to run a quick experiment — do I still need the full loop?**

See `../longterm.md § Temporary Contractor Boundary Rules`. For declared `<3h test` / pure refactor / trivial fix targets, the temporary contract may skip `Superpowers.brainstorming` (and `writing-plans` where the change is mechanical) AND suppress sendbox/dashboard exercise for the task (single-session, no subagent). Declare every skip in the temporary contract; do NOT remove the layers from the long-term baseline.

**Q: My work is single-session and linear today — should I just remove sendbox and cc-dashboard from this stack?**

No. Per the add-only principle, leave the layers active-but-unexercised. If multi-worktree work returns later (and it likely will), the channel is already wired in. Skip writing letters and dashboard rows for now; they cost nothing when unused.

**Q: A subagent in `/tmp/` (no shared git tree) needs to send me a letter — what's the path?**

Write to the main agent's sendbox by **absolute path**: `/<main-project>/docs/sendbox/to{Prefix}{Role}/...`. Do NOT create `docs/sendbox/` under your own cwd. Sendboxes do not fan out — there is exactly one per project, held by the main agent.

**Q: Two implementers report to me on the same task — which mailbox does each read?**

Give each its own task-scoped mailbox under the `to{Prefix}{Role}/` pattern, appending a numeric discriminator when two peers share a role: `toSP0Impler1/`, `toSP0Impler2/`. A single shared `toImpler/` is forbidden whenever ≥2 sessions of that role run concurrently. Prefer task-decomposition (different prefixes) over peer multiplication. See `../longterm.md § Local sendbox conventions`.

**Q: A task seems to violate the contract — what do I do?**

First check whether it's a temporary-contract case (see § 3 above). If the contract itself is wrong, see `../longterm.md § Full Rewrite Conditions` to decide whether a rewrite is justified. Do not silently rewrite the contract.

**Q: A letter is rotting unburned in `docs/sendbox/` — what's the cleanup rule?**

At session end or task convergence, sweep all letters whose lifecycle condition has triggered and execute their disposition. See `../longterm.md § Merge Gates` and the sendbox-protocol skill's "Cleanup checkpoints" section. Monotonically-growing sendbox dirs are the #1 hygiene failure.

**Q: A dashboard row is stale (work was done but row still says `open`) — who marks it done?**

By default option (a) — any session OR the user. Mark done, move from `## Active` to `## Archive` in the same commit. Occasional double-marks are harmless.
