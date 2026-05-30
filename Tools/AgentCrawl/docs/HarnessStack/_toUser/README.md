# Using HarnessStack — Human Operator Guide

> Human-facing manual for operating the HarnessStack activated at
> `docs/HarnessStack/` in this repository. For the authoritative contract,
> see `../longterm.md`. For the one-time AI distillation source, see
> `../README.md`.

## 1. What This Stack Activates

This repository activates the following workflow layers (see
`../longterm.md § Current Active Long-Term Baseline` for full detail):

- `OpenSpec` — Spec layer: every non-trivial change passes through propose → design → tasks → implement → archive. Spec root is at `docs/openspec/`. One `change-id` per task, shared with RepoMem `<slug>` and HarnessStack `<task>`.
- `Superpowers` — execution-discipline skills: brainstorming, writing-plans, using-git-worktrees, executing-plans, TDD, verification-before-completion, requesting-code-review, finishing-a-development-branch.
- `RepoMem` — long-term repository memory. Persistent docs under `docs/RepoMem/persist/`; task-scoped temp docs under `docs/RepoMem/temp/<slug>/`. Promotion temp → persist is HITL via `RepoMem.merge`, gated AFTER `OpenSpec.archive`.
- `sendbox-protocol` — asynchronous file-based channel for any work that crosses sessions or worktrees. The main agent's `docs/sendbox/` is the single source of truth. Letters address roles (`toOrchestrator/`, `toIpcAuthor/`, `toUser/`), not session names. Every letter has a lifecycle disposition (`burn` / `archive` / `persist`) and is cleaned up at two checkpoints (session end, task convergence).
- `cc-dashboard` — a single markdown file `docs/Dashboard/index.md` listing every pending action you owe, projected out of sendbox letters, handoff briefs, and OpenSpec proposal/archive HITL acks. Atomic granularity — one letter with three asks emits three rows. Independent lifecycle: rows go `open → done → archived` and stay in Archive for 14 rolling days.

Inactive by default: `ECC` / `ECC(light)`, `BMAD` / `gstack` / `GSD`. See `../longterm.md § Current Active Long-Term Baseline § Upgrade trigger` for when to extend.

## 2. Day-One Init

Run these once when this stack is first activated in your repository.

1. **Install the active methods in your agent harness.** Each method ships as a discoverable skill — install per its own README:
   - OpenSpec — install the OpenSpec CLI per upstream docs. Verify the `/opsx` or equivalent commands work in a fresh session.
   - Superpowers — installed as a Claude Code skill plugin (no per-repo install).
   - RepoMem — `~/.claude/skills/repo-mem` (verify it appears in the skill list at session start).
   - sendbox-protocol — symlink: `ln -s /home/<user>/Codes/cc-sendbox/skills/sendbox-protocol ~/.claude/skills/sendbox-protocol`.
   - cc-dashboard — symlink: `ln -s "$(realpath ${CC_DASHBOARD_REPO})/skills/cc-dashboard" ~/.claude/skills/cc-dashboard`.

2. **Distill `../README.md` sections 1–4 into your `CLAUDE.md`** (or the equivalent always-loaded instruction file).

3. **Scaffold OpenSpec.** Create `docs/openspec/` with `changes/`, `specs/`, and the OpenSpec config file per upstream docs. (If the repo strictly follows OpenSpec upstream convention, use `./openspec/` instead — update `longterm.md § Document Meta § OpenSpec Root` accordingly.)

4. **Scaffold RepoMem persistent layout.** Create `docs/RepoMem/persist/architecture/` and `docs/RepoMem/persist/memory/` (empty is fine — they fill on first `RepoMem.merge`). Optionally create `docs/RepoMem/persist/version-plan.md` to track stack evolution.

5. **DO NOT scaffold `docs/sendbox/`.** Per the sendbox embedding-playbook, the directory grows organically when the first letter is written. Pre-creating empty subdirectories is an anti-pattern.

6. **Create the dashboard hook config and seed file.**
   - Author `docs/HarnessStack/hooks/cc-dashboard.md` with all required sections (Status / Scope / Skip-protocol / Authority frontmatter, Purpose, Data Location, **Language Policy** for this repo, Row Schema, Action Types A–F, Write Triggers including OpenSpec proposal/archive HITL ack, Mark-Done Protocol — pick option (a)/(b)/(c)/(d), Archive Protocol, Sendbox-protocol Coupling note, Hook Boundary).
   - Seed `docs/Dashboard/index.md` from the template in cc-dashboard SKILL.md (Active and Archive sections, empty tables).
   - Add to your `CLAUDE.md` / `AGENTS.md` "Where to Look" table: `| Know what the user owes now | docs/Dashboard/index.md (protocol: docs/HarnessStack/hooks/cc-dashboard.md) |`.

7. **Backfill the dashboard** by scanning any existing sendbox letters / handoffs / OpenSpec proposals awaiting review / external tracker tickets — mark already-completed actions directly into `## Archive`, NOT `## Active`.

8. Read this manual end-to-end before starting your first task.

## 3. Per-Task Iteration Loop

For each task:

1. **Read context.** Run `RepoMem.read <slug>` to load long-term memory. Use `--scoped` for a tighter context window once the task scope is fixed.

2. **Clarify intent.** Run `Superpowers.brainstorming` unless intent is already crystal clear. If you decide to dispatch a subagent here, write a sendbox `handoff.md` to `to<Role>/` first (mode = child if the parent session persists; mode = inheritance if the parent is ending). Append a Type-B dashboard row.

3. **Open OpenSpec change.** Run `OpenSpec.explore` then `OpenSpec.propose` to formalize intent as `docs/openspec/changes/<change-id>/`. The `change-id` MUST equal `<slug>` and the HarnessStack `<task>`. If the proposal awaits remote review, write `from-<sender>-proposal-ready.md` and append a Type-A dashboard row.

4. **Open task memory docs.** Run `RepoMem.capture <slug>` to open `docs/RepoMem/temp/<slug>/` (requirements.md, architecture.md, memory.md as needed). Do NOT duplicate OpenSpec change-record content here — RepoMem owns WHY/context only.

5. **Plan.** Run `Superpowers.writing-plans` consuming the OpenSpec tasks. If a subagent produces the plan, write `from-<sender>-plan-ready.md` to the orchestrator; orchestrator replies with `from-<orche>-<sender>-greenlight.md`.

6. **Implement.** Use `git-worktrees` + `executing-plans` + TDD per the plan. If you hit an A-12 boundary (scope mismatch with the OpenSpec change, destructive op, ambiguous upstream directive), STOP and write `from-<sender>-blocker-<topic>.md` with options table and your tentative pick — do not silently proceed. A blocker letter MAY cite the OpenSpec spec but MUST NOT mutate it; if the spec is wrong, open a new OpenSpec change.

7. **Capture continuously.** Record tacit knowledge into `docs/RepoMem/temp/<slug>/memory.md` as you go.

8. **Verify (dual).** Run BOTH `Superpowers.verification-before-completion` AND `OpenSpec.verify`. Subagents reaching a vertical-slice acceptance gate write `from-<sender>-<milestone>-done.md`. A change cannot proceed unless both verifications pass.

9. **Review.** Run `Superpowers.requesting-code-review`. If you owe multiple decisions to one recipient, bundle them into ONE `from-<orche>-<recipient>-decisions.md` letter.

10. **Finish branch.** Run `Superpowers.finishing-a-development-branch`. Optionally write `from-<sender>-archived.md` for the close-out summary.

11. **Archive OpenSpec.** Run `OpenSpec.archive` to freeze `docs/openspec/changes/<change-id>/`. This is half-irreversible — confirm completeness first. Append a Type-C dashboard row if the archive awaits HITL ack. If the archive contains decisions worth broadcasting, write `toAllActiveSessions/from-<orche>.md` with a clear supersession rule.

12. **Promote memory.** Run `RepoMem.merge <slug>` (HITL — review promotion candidates before they enter long-term memory). If any sendbox letter contains a lesson worth keeping, route it through this gate via a `from-<sender>-promote-to-durable.md` letter — the letter is burned after merge, never written directly into `docs/RepoMem/persist/`. The HITL reviewer rejects any temp content that duplicates the archived OpenSpec record.

13. **Sweep sendbox.** At session end OR task convergence, scan `docs/sendbox/` for letters whose lifecycle condition has triggered. Execute the disposition (`burn` via `git rm`, `archive` to `docs/sendbox/archive/`, `persist` after promotion). Letter pairs to burn together: handoff + milestone-done; plan-ready + greenlight; blocker + decisions; proposal-ready + greenlight.

14. **Sweep dashboard.** Move any `done` rows from `## Active` to `## Archive` in the same commit. Garbage-collect rows older than 14 days from `## Archive` opportunistically.

If a task introduces constraints the long-term contract does not cover, create a `temporary-<task>.md` patch per `../longterm.md § Temporary Contractor Boundary Rules`.

## 4. Long-Term Iteration

`../longterm.md` is authoritative. Update it only when:

- a Full Rewrite Condition triggers (see `../longterm.md § Full Rewrite Conditions`), OR
- you switch to a superset recipe via the add-only principle — a single-line `Recipe Reference` change plus a `Last Updated Because` entry, NOT a rewrite. Likely future supersets:
  - `bmad-openspec-superpowers-repomem-sendbox-dashboard-ecc` (or similar) — when the project portfolio outgrows the OpenSpec-only orchestration and a primary workflow framework is needed.
  - addition of `ECC(light)` or `ECC(medium)` to the Harness Enhancement layer (when agent context quality / safety / repeatability becomes a recurring problem).

Routine task work does NOT modify `longterm.md` directly — use `temporary-<task>.md` for task-scoped adjustments.

## 5. Tracking HarnessStack Evolution (Optional)

Because RepoMem is active in this stack, place the version-plan at `docs/RepoMem/persist/version-plan.md`. The `repo-mem` skill maintains this naturally.

HarnessFactory does not ship a version-plan skeleton inside the bundle. Stack-evolution tracking is target-repo state, not factory output.

## 6. Pointers

- Authoritative contract: `../longterm.md`
- AI distillation source: `../README.md`
- Task-level patch (if active): `../temporary-<task>.md`
- Recipe binding: `../longterm.md § Document Meta § Recipe Reference`
- OpenSpec Root: `../longterm.md § Document Meta § OpenSpec Root`
- Hook config: `../hooks/cc-dashboard.md`
- Sendbox embedding playbook: `methods/sendbox/embedding-playbook.md` in HarnessFactory
- Dashboard embedding playbook: `methods/dashboard/embedding-playbook.md` in HarnessFactory

## 7. Common Questions

**Q: I just want to run a quick experiment — do I still need the full loop?**

See `../longterm.md § Temporary Contractor Boundary Rules`. For declared `<3h test` / pure refactor / trivial fix targets, the temporary contract may skip `OpenSpec.explore / propose` (which implies skipping `OpenSpec.archive` — log both together) AND suppress sendbox/dashboard exercise for the task (single-session, no subagent). Declare every skip in the temporary contract; do NOT remove the layers from the long-term baseline.

**Q: My work is single-session and linear today — should I just remove sendbox and cc-dashboard from this stack?**

No. Per the add-only principle, leave the layers active-but-unexercised. If multi-worktree work returns later (and it likely will), the channel is already wired in. Skip writing letters and dashboard rows for now; they cost nothing when unused.

**Q: A subagent in `/tmp/` (no shared git tree) needs to send me a letter — what's the path?**

Write to the main agent's sendbox by **absolute path**: `/<main-project>/docs/sendbox/to<Role>/...`. Do NOT create `docs/sendbox/` under your own cwd. Sendboxes do not fan out — there is exactly one per project, held by the main agent.

**Q: A sendbox letter says the archived OpenSpec change is wrong — can I edit the spec?**

No. An archived OpenSpec change is the durable per-change contract. The letter MAY cite the spec, but the spec itself is only mutated by a new OpenSpec change. Open `OpenSpec.propose` for a new `change-id` that supersedes the previous one; do NOT edit the archived directory.

**Q: I want to drop OpenSpec for one task — how?**

Use the Skip Criteria in Execution Policy: declared spike with no spec impact / pure refactor / `<3h test`. Log the skip of both `OpenSpec.explore / propose` and `OpenSpec.archive` in `temporary-<task>.md § Auto-Skip Log`. To drop OpenSpec from the long-term baseline, that is a Full Rewrite Condition.

**Q: A task seems to violate the contract — what do I do?**

First check whether it's a temporary-contract case (see § 3 above). If the contract itself is wrong, see `../longterm.md § Full Rewrite Conditions` to decide whether a rewrite is justified. Do not silently rewrite the contract.

**Q: A letter is rotting unburned in `docs/sendbox/` — what's the cleanup rule?**

At session end or task convergence, sweep all letters whose lifecycle condition has triggered and execute their disposition. See `../longterm.md § Merge Gates` and the sendbox-protocol skill's "Cleanup checkpoints" section. Monotonically-growing sendbox dirs are the #1 hygiene failure.

**Q: A dashboard row is stale (work was done but row still says `open`) — who marks it done?**

By default option (a) — any session OR the user. Mark done, move from `## Active` to `## Archive` in the same commit. Occasional double-marks are harmless.
