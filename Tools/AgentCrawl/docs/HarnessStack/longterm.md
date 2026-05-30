# longterm.md

## Document Meta

- Repository: `<target-repo>` (placeholder — replace with the target repository identifier on activation)
- Effective From: `<YYYY-MM-DD>` (placeholder — set when this stack is first activated in the target repo)
- Source Template: `harness-factory/assets/templates/longterm/solo.md`
- Recipe Reference: `harness-factory/assets/templates/recipes/openspec-superpowers-repomem-sendbox-dashboard.md`
- OpenSpec Root: `docs/openspec/` (co-located with `docs/RepoMem/` and `docs/HarnessStack/`; switch to `./openspec/` only if the target repo strictly follows upstream OpenSpec convention)
- Last Updated Because: initial long-term contract; solo + long-lived platform repository that has explicitly opted into OpenSpec discipline AND runs multi-worktree / subagent-dispatch work, requiring formal change specs (OpenSpec) + cross-task memory (RepoMem) + asynchronous inter-session channel (sendbox) + pending-action projection (cc-dashboard).

## Current Long-Term Assessment

- Collaboration Scale: `solo`
- Repository Type: `platform`
- Project Horizon: `long-lived`
- Long-Term Knowledge Governance: `enabled`

## Current Active Long-Term Baseline

### 1. Primary Workflow Layer

- Default enabled: none
- Emergent Ownership: OpenSpec change cycle (proposal → specs → tasks → archive) plus Superpowers brainstorming and writing-plans jointly carry primary workflow responsibility.
- Default inactive: `BMAD`, `gstack`, `GSD`
- Upgrade trigger:
  - repository acquires a roadmap-heavy delivery mode that OpenSpec alone cannot orchestrate
  - task portfolio grows past what change-cycle discipline alone can carry

### 2. Spec Layer

- Default enabled: `OpenSpec`
- Default inactive: none
- Upgrade trigger:
  - spec layer ever needs to be replaced or augmented; OpenSpec is currently the only Spec-layer option

### 3. Execution Discipline Layer

- Default enabled: `Superpowers`
- Default inactive: none
- Upgrade trigger:
  - raise verification and review intensity when risk rises

### 4. Repository Memory Layer

- Default enabled: `RepoMem`
- Default inactive: none
- Upgrade trigger:
  - long-term memory pressure requires `RepoMem.prune / split`
  - memory governance needs harden into `ECC` hooks

### 5. Harness Enhancement Layer

- Default enabled: `sendbox-protocol`, `cc-dashboard`
- Default inactive: `ECC`, `ECC(light)`
- Upgrade trigger:
  - agent context quality, safety, or repeatability becomes a recurring problem — add `ECC(light)` or `ECC(medium)`
  - inter-session-comm convention is replaced by a different channel — re-evaluate dashboard fit per `methods/dashboard/embedding-playbook.md § 4`

Adoption note: sendbox + cc-dashboard are by-default `skip` for solo per their embedding-playbooks. This baseline overrides that default because the operator runs a multi-worktree / subagent-dispatch workflow. If that work mode stops, prefer leaving the layers active-but-unexercised rather than removing them (target-repo add-only).

## Pipeline

The Pipeline is the 13-step `openspec-superpowers-repomem` chain. sendbox letters and cc-dashboard rows are condition overlays, not new pipeline steps.

1. RepoMem.read — load long-term architecture and memory as task context
2. Superpowers.brainstorming — clarify vague intent
3. OpenSpec.explore / propose — convert intent into a formal change with specs
4. RepoMem.capture — open task-level temporary docs (requirement, architecture)
5. Superpowers.writing-plans — consume OpenSpec specs and tasks to produce executable plan
6. Superpowers.using-git-worktrees + executing-plans + TDD — implement
7. RepoMem.capture (continuous) — record tacit knowledge into temporary memory
8. Superpowers.verification-before-completion + OpenSpec.verify — dual-perspective verification
9. Superpowers.requesting-code-review
10. Superpowers.finishing-a-development-branch
11. OpenSpec.archive — freeze change record
12. RepoMem.merge (HITL) — promote stable knowledge from temporary to long-term
13. RepoMem.prune / split — periodic hygiene, not per-task

### Sendbox Triggers Across The Pipeline

| Pipeline step | Trigger condition | Canonical letter type |
|---|---|---|
| Step 2 | Spawning a fresh recipient session (subagent, sibling worktree, inheritance) | `handoff.md` to `to<Role>/` (mode = child or inheritance) |
| Step 3 | OpenSpec proposal awaiting greenlight from a remote reviewer | `from-<sender>-proposal-ready.md` ↔ `from-<orche>-<x>-greenlight.md` |
| Step 5–6 | Implementer awaits orchestrator greenlight on writing-plans output | `from-<sender>-plan-ready.md` ↔ `from-<orche>-<x>-greenlight.md` |
| Step 6 | A-12 stop-and-ask hit | `from-<sender>-blocker-<topic>.md` |
| Step 8 | Vertical-slice acceptance gate hit by a subagent | `from-<sender>-<milestone>-done.md` |
| Step 9 | Orchestrator owes N decisions to one recipient | `from-<orche>-<recipient>-decisions.md` (bundled) |
| Step 10 | Branch close-out summary | `from-<sender>-archived.md` |
| Step 11 | OpenSpec change being archived contains decisions worth broadcasting | `toAllActiveSessions/from-<orche>.md` (broadcast with supersession rule) |
| Step 12 | A sendbox letter contains a lesson worth promoting to RepoMem persist | `from-<sender>-promote-to-durable.md` (route content through `RepoMem.merge`) |

### Dashboard Writes Across The Pipeline

One letter → N rows. Mark-done default option (a) — any session or the user.

| Trigger | Row count | Typical type |
|---|---|---|
| Writing `docs/sendbox/toUser/*.md` | 1..N | A / C / D |
| Writing `docs/sendbox/to<Implementer>/handoff.md` | ≥1 | B |
| OpenSpec proposal awaiting user review/approval | 1 | A |
| OpenSpec change ready to archive (HITL ack) | 1 | C |
| Identifying a user-blocking action with no sendbox doc | 1 | C / D / F |

## Cross-Layer Conflicts

| Overlap | Conflict | Resolution |
|---|---|---|
| Early-phase intent convergence | Superpowers.brainstorming vs OpenSpec.explore | brainstorming first when intent is vague; switch to OpenSpec once intent is formalizable as a change intent |
| Plan concept | Superpowers.writing-plans vs OpenSpec.tasks | OpenSpec.tasks defines WHAT contract; writing-plans defines HOW execution; the latter consumes the former |
| Verification | OpenSpec.verify vs Superpowers.verification-before-completion | run both — different lenses |
| Doc sedimentation | OpenSpec change docs vs RepoMem temporary memory vs HarnessStack temporary contract | OpenSpec is the authoritative per-change source; RepoMem extracts durable lessons at archive time and never duplicates the change record; HarnessStack temporary is task-scoped workflow patch only |
| Sendbox promotion vs RepoMem merge | `from-<x>-promote-to-durable.md` content vs `docs/RepoMem/persist/` | Letter content is promoted through `RepoMem.merge`, not by a parallel write path. The letter is then burned. |
| Sendbox vs OpenSpec authority | A sendbox letter contradicting an archived OpenSpec change | OpenSpec change is the durable contract; sendbox letter is transient. If a letter implies the spec is wrong, open a new OpenSpec change — do not mutate the spec via a letter. |
| Sendbox lifecycle vs dashboard lifecycle | Burning a letter vs dashboard row status | Lifecycles are independent. Burning a letter does NOT cascade-delete any dashboard row; marking a row done does NOT trigger letter cleanup. |
| Dashboard row vs OpenSpec change / L2 tracker | A dashboard row vs an OpenSpec change-id or tracker ticket | Dashboard rows are user-action granularity; OpenSpec change-ids and tracker tickets are work-unit granularity. Do NOT mirror them into the dashboard. |
| Dashboard granularity vs letter content | One letter with three asks | One letter → three rows. Never collapse one letter to one row. |
| Sendbox cwd fan-out | Subagent in a side cwd writing to its own `docs/sendbox/` | Forbidden. The main agent's `docs/sendbox/` is the single source of truth. Side cwds write to it by relative or absolute path. |

## Verification Topology

- `OpenSpec.verify` — "did we deliver what the spec promised?"
- `Superpowers.verification-before-completion` — "is the implemented behavior actually correct?"
- Both run before `requesting-code-review`. A change cannot enter `finishing-a-development-branch` unless both pass.
- RepoMem has no verification role — it does not gate completion.
- sendbox has no verification role — letters are operational. A `from-<x>-blocker-<topic>.md` is a coordination gate, not a verification gate.
- cc-dashboard has no verification role and never gates any pipeline step. It is read-only by the user.

## Merge Gates

- `RepoMem.merge` MUST run after `OpenSpec.archive`, never before.
- `RepoMem.merge` is HITL — a human reviews promotion candidates before they enter the long-term layer.
- `from-<x>-promote-to-durable.md` content MUST flow through `RepoMem.merge`'s HITL gate before the letter is burned. No parallel promotion path.
- `OpenSpec.archive` is half-irreversible — confirm completeness before triggering (per Execution Policy).
- sendbox letter lifecycle (`burn` / `archive` / `persist`) is executed at the two sendbox cleanup checkpoints (session end, task convergence) by the authoring or receiving session — NOT by any Superpowers or OpenSpec pipeline step.
- cc-dashboard row lifecycle (`open → done → archived → garbage-collected`) is independent of any merge gate. Mark-done is per-row, opportunistic.
- `RepoMem.prune / split` runs on a different cadence than per-task work.

## Execution Policy

| # | Step | Policy | Skip Criteria (auto-judge only) | Notes |
|---|---|---|---|---|
| 1 | RepoMem.read | auto | — | Read-only context load. Idempotent. |
| 2 | Superpowers.brainstorming | auto-judge | Intent is already `clear` per task contract, or task is a trivial fix / pure refactor. | When a subagent is being spawned, write sendbox `handoff.md` before brainstorming hands off context. |
| 3 | OpenSpec.explore / propose | auto-judge | Trivial fix / pure refactor / `<3h test` / declared spike with no spec impact. | Skipping #3 implies skipping #11 (archive) — log both together. |
| 4 | RepoMem.capture (open temp docs) | auto | — | Mechanical folder creation. |
| 5 | Superpowers.writing-plans | auto-judge | OpenSpec.tasks already lists atomic steps that map 1:1 to execution. | If a subagent produces the plan, write `from-<sender>-plan-ready.md` for orchestrator greenlight. |
| 6 | using-git-worktrees + executing-plans + TDD | auto-judge | No isolation needed; small change with no parallel work. TDD scope follows plan. | A-12 blocker letter MAY fire here. |
| 7 | RepoMem.capture (continuous) | auto | — | Passive tacit-knowledge recording. |
| 8 | verification-before-completion + OpenSpec.verify | auto | — | Both lenses required. Subagent `milestone-done` letter MAY fire here. |
| 9 | Superpowers.requesting-code-review | ask-first | — | External visibility: opens a review request. Bundled `decisions.md` letters MAY be written here. |
| 10 | Superpowers.finishing-a-development-branch | ask-first | — | Multi-step git state change. Confirm scope. `from-<sender>-archived.md` MAY be written here. |
| 11 | OpenSpec.archive | ask-first | — | Half-irreversible: freezes the change record. Confirm completeness. Broadcast letter MAY fire here. |
| 12 | RepoMem.merge | HITL | — | Contract-mandated human review. Never downgradable. Any `from-<x>-promote-to-durable.md` content lands here. |
| 13 | RepoMem.prune / split | auto | — | Periodic hygiene, not per-task. Runs on its own cadence. |

Sendbox letter writes and cc-dashboard row writes are side-effects of the above steps, not standalone pipeline steps.

## Suitability Envelope

### Fits

- one active contributor who has explicitly opted into OpenSpec discipline AND routinely dispatches subagents or runs multi-worktree parallel work
- long-lived platform / library / product repositories where architecture and decisions accumulate AND scope must be sliced into discrete OpenSpec change units AND multi-session coordination is recurring
- risk medium to high

### Does Not Fit

- pure spike or probe experiments — OpenSpec friction is too high
- solo work that is strictly single-session, linear, no subagents — drop to `openspec-superpowers-repomem`
- short-lived or disposable repositories — drop to `superpowers`
- multi-team large-scale coordination — needs a heavier primary workflow layer

## Temporary Contractor Boundary Rules

### Temporary Contractor May Adjust

- skip `OpenSpec.explore / propose` (and thereby `OpenSpec.archive`) for declared trivial fix / pure refactor / `<3h test` / spike with no spec impact — log both skips in `Auto-Skip Log`
- raise or lower `Superpowers` intensity
- enable lightweight `ECC` for a task
- skip `RepoMem.capture` for trivial `<3h test` tasks (still must read long-term memory)
- choose not to exercise sendbox / cc-dashboard for a single-session linear task — declare the suppression in the task contract; do NOT remove the layers from the long-term baseline

### Temporary Contractor May Not Override

- the existence of long-term repository memory once enabled
- the OpenSpec change-cycle contract for any non-trivial change
- long-term governance and safety constraints
- the sendbox single-source-of-truth principle (one `docs/sendbox/` per project, held by the main agent — see Cross-Method Invariants)
- cc-dashboard's hard dependency on sendbox (cannot exercise dashboard without sendbox)
- pipeline ordering, merge gates, and verification topology — recipe invariants; exceptions require a declared `Recipe Invariant Exceptions` section with reason and compensating action
- this document's collaboration-scale assumption without full rewrite

## Full Rewrite Conditions

- repository moves from solo to large-team collaboration
- repository horizon flips to short-lived
- default primary workflow needs to become permanently heavier (BMAD / gstack / GSD)
- the operator stops doing multi-worktree / subagent-dispatch work permanently AND chooses to retire the sendbox + dashboard layers (note: per add-only, prefer leaving them active-but-unexercised)
- the operator stops doing OpenSpec discipline permanently AND chooses to retire the spec layer

(Note: switching from `openspec-superpowers-repomem-sendbox-dashboard` to a superset recipe such as a future `bmad-openspec-superpowers-repomem-sendbox-dashboard-ecc` is an extension under add-only — update `Recipe Reference` in place; not a full rewrite.)

## Related Documents

- `docs/HarnessStack/temporary-<task>.md` (when a task is in progress)
- `docs/RepoMem/persist/version-plan.md`
- `docs/openspec/changes/<change-id>/` (per-change OpenSpec records)
- `docs/HarnessStack/hooks/cc-dashboard.md` (hook config with repo-local Language Policy — created on activation)
- Related RepoMem architecture and memory docs

## Hooks

| Hook | Status | Purpose |
|---|---|---|
| [`hooks/cc-dashboard.md`](hooks/cc-dashboard.md) | active | Maintain `docs/Dashboard/index.md` as SSOT for pending user actions; trigger on any session write to `docs/sendbox/`, any OpenSpec proposal/archive HITL ack, or identification of a new user-blocking action |

## Cross-Method Invariants

These rules bind HarnessStack to its companion methods. They are not part of any single layer and therefore live here at the long-term contract level.

- **Single task identifier.** The OpenSpec `change-id`, the RepoMem `<slug>`, and the HarnessStack `<task>` MUST be the same string: `<task>` = `change-id` = `<slug>`. Diverging on naming defeats per-task cross-referencing across the three method layers.
- **No content duplication across per-task document sets.** OpenSpec change docs (`docs/openspec/changes/<id>/`), RepoMem temp docs (`docs/RepoMem/temp/<slug>/`), and the HarnessStack per-task contract (`docs/HarnessStack/temporary-<task>.md`) each answer a distinct question and MUST NOT restate each other's content. The reviewer at `RepoMem.merge` rejects (deletes, does not merge) any temp content that duplicates the archived OpenSpec record.
- **Multi-session work uses sendbox-protocol.** When a task involves multiple
  sessions, dispatched subagents, or cross-worktree coordination, the
  `sendbox-protocol` skill (see `~/.claude/skills/sendbox-protocol/SKILL.md`)
  is the canonical asynchronous channel. The main agent's `docs/sendbox/` is
  the single source of truth, and subagents in side cwds write to it by
  relative or absolute path — never fan out under their own cwd. See
  `methods/sendbox/embedding-playbook.md` for the embedding playbook.
- **Pending user actions are projected into a single dashboard.** When sendbox-protocol is active, the `cc-dashboard` skill (see `~/.claude/skills/cc-dashboard/SKILL.md`) maintains `docs/Dashboard/index.md` as the single source of truth for pending user actions. Any session writing a `toUser/` letter or a `to<Implementer>/handoff.md` MUST append one row per atomic user action. Mark-done lifecycle is independent from letter lifecycle. See `methods/dashboard/embedding-playbook.md` for the embedding playbook.
- **Sendbox-to-RepoMem promotion goes through `RepoMem.merge`.** A `from-<x>-promote-to-durable.md` letter is a *candidate* for long-term knowledge; the actual write into `docs/RepoMem/persist/` happens through the `RepoMem.merge` HITL gate, never via a parallel path. The letter is burned after merge.
- **Sendbox cannot override OpenSpec authority.** An archived OpenSpec change is the durable per-change contract. A sendbox letter MAY cite a spec but MUST NOT mutate or replace it. If a letter implies the spec is wrong, open a new OpenSpec change — do not edit the archived spec via a letter.
- Divergence from any rule above requires a `Recipe Invariant Exception` in the task contract with reason and compensating action.
