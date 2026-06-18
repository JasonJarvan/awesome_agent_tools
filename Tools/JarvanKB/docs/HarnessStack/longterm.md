# HarnessStack longterm — JarvanKB

> Authoritative full contract. Loaded on recipe upgrade, not every session.
> Session-level always-loaded contract = `CLAUDE.md` (distilled).

## Recipe v1 → v2 Migration (2026-05-31, Full Rewrite)

**Trigger**: scope expansion of `AgentCrawl` → `JarvanKB` 10-sub-project family; OpenSpec value assessment (subagent R8) recommended removal for thin-layer formation.

**Decision**: drop OpenSpec from the recipe. Compress pipeline 13 → 8 steps.

**Compliance path**: Full Rewrite under §Full Rewrite Conditions (this section). NOT a stealth downgrade — `add-only` invariant honored via versioned recipe migration.

**Net changes**:
| Aspect | v1 | v2 |
|---|---|---|
| Recipe ID | `openspec-superpowers-repomem-sendbox-dashboard` | `superpowers-repomem-sendbox-dashboard` |
| Active methods | 5 (incl. OpenSpec) | 4 |
| Pipeline length | 13 steps | 8 steps |
| Verification gate | dual (OpenSpec verify + Superpowers verification-before-completion) | single (Superpowers verification-before-completion) |
| Slash commands | `/opsx:propose/apply/verify/archive` | none added; rely on Skill tool |
| Change ID | `change-id` (= slug) tied to OpenSpec workspace | `slug` only (tied to git worktree + RepoMem temp dir) |
| Per-task contract docs | `openspec/changes/<id>/{proposal,design,specs,tasks}.md` | `<module>/docs/RepoMem/temp/<slug>/` + `<module>/docs/superpowers/{specs,plans}/` |
| `openspec/` workspace | required, symlinked from repo root | removed |
| `.claude/skills/openspec-*` | 4 skills installed | removed |
| `.claude/commands/opsx/` | 4 commands | removed |

**Detailed migration actions** logged in `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` §6.5.

**Reintroduction conditions**: a sub-project whose external interface becomes a versioned SDK / API consumed by third parties MAY re-introduce OpenSpec **scoped to that module only**, via a new Full Rewrite entry. Cross-cutting reintroduction requires recipe v3.

---

## Pipeline v2 (authoritative)

The 8-step per-task pipeline (compressed view also in `CLAUDE.md` §3):

1. **`RepoMem.read`** — Subagent in `<module>/` cwd reads two layers: `<root>/docs/RepoMem/persist/` (background) + `<module>/docs/RepoMem/{architecture,decisions}.md` (actionable). Main orchestrator reads only global. For in-repo **symbol / caller / impact lookups**, prefer the codegraph code-map (`codegraph query|callers|impact`, MCP or CLI) over ad-hoc grep — codegraph is the up-to-date structural map; RepoMem stays the durable why-layer. Fall back to grep where the graph is sparse (`callees`/`affected` on dynamic Python — most of this repo). See §Harness Enhancement Layer (v2).

2. **`Superpowers.brainstorming`** — Clarify vague intent. Auto-judge skip on:
   - intent already `clear` and producing-the-design would be redundant
   - trivial fix (typo, single-line bugfix, dep bump)
   - pure refactor with no behavior change
   - spike / <3h exploration with throwaway code
   When spawning subagent for brainstorming, write `handoff.md` letter to `<root>/docs/sendbox/to<Role>/` and open a Type-B dashboard row. On a **full-lane** task, after a draft design/spec exists and before step 4, the agent MAY run project skill `grill-design` (auto-judge: grill when a non-trivial design exists, else skip with a one-line note in the plan; renamed from `grill-with-docs` 2026-06-11 — that name now belongs to the community CONTEXT.md-glossary skill, see §Lane Tiering (v2) note). See §Lane Tiering (v2).

3. **`RepoMem.capture`** — Open task-level temp docs in the relevant module: `<module>/docs/RepoMem/temp/<slug>/{requirements,architecture,decisions}.md`. Cross-module task: open at `<root>/docs/RepoMem/temp/<slug>/` instead.

4. **`Superpowers.writing-plans`** — Produce a step-by-step implementation plan. Land at `<module>/docs/superpowers/plans/YYYY-MM-DD-<slug>.md` (or root if cross-module). When subagent produces plan, send `plan-ready.md` letter back. The plan-doc frontmatter carries the task's `Lane:` declaration (§Lane Tiering (v2)).

5. **`using-git-worktrees` + `executing-plans` + TDD + `RepoMem.capture` (continuous)** — Execute the plan in an isolated worktree. TDD discipline. Capture tacit knowledge to `temp/<slug>/decisions.md` as decisions are made. Subagent boundary at ~A-12 → blocker letter. Worktrees are separate checkouts: budget a one-time `codegraph init` (~30 s, ~30 MB) per worktree, or run `CODEGRAPH_NO_DAEMON=1 codegraph sync` for a one-shot incremental refresh (no file watcher in sandboxed worktrees), then `codegraph query`/`impact` as plain synchronous CLI.

6. **`Superpowers.verification-before-completion`** — Single mandatory gate. Run tests + lint + typecheck + manual smoke as applicable; output evidence (commands run + outputs). No claim of "done" without this output.

7. **`Superpowers.requesting-code-review` + `finishing-a-development-branch`** — Both **ask-first**. Reviewer (subagent or user) validates against spec + plan. Finishing produces merge / PR / cleanup decision.

8. **`RepoMem.merge` (HITL — implementer owns closure)** — **The implementer closes merge within its OWN task lifecycle**: runs it HITL after `finishing-a-development-branch`, or delegates *execution* to orche but tracks it to completion before reporting done — never fire-and-forget. Impler-handoff briefs MUST state this ownership (never frame Step 8 as "NOT YOUR JOB"); they may name orche as delegated executor, but the impler remains the closer. Promote `temp/<slug>/` lessons to durable layer. Module-scope decisions stay in `<module>/docs/RepoMem/decisions.md`. Global-scope decisions get promoted to `<root>/docs/RepoMem/persist/memory/` with `[Promoted to global ↗]` marker in module decisions. Any `from-<x>-promote-to-durable.md` letter lands here. Then `prune/split` per RepoMem hygiene.

   > **RepoMem.merge promotion standard** (codified from the SP-2 empirical lesson, 2026-06-02): When promoting module findings to global `persist/`, promote **ONLY what is NOT derivable from code / `interface.md` / module `decisions.md`** — decision rationale, root causes, gotchas, and cross-SP guidance. **Never duplicate mechanism that lives in code** (no-duplication invariant). **Crucially, cross-SP-reusable gotchas MUST be promoted to global persist**, because the **layered-read protocol** means a downstream SP working in *another module's cwd* does NOT read the originating module's `decisions.md`; a reusable gotcha left only in the origin module will be rediscovered the hard way by the next SP. *(Concrete case: SP-2's `comment_v5` offset-poison + `js-initialData` camelCase gotchas had to go to `architecture/crawl-pipeline.md` §知乎链路 so SP-5a Watcher — running in `Service/crawl/zhihu-watcher/` cwd — will see them.)* **Codegraph de-dup rule (promote-time counterpart of the step-1 read-time rule):** do NOT promote structural facts codegraph answers from current code — symbol locations, call graphs, impact sets. `persist/architecture/` holds only what codegraph cannot derive: decisions, constraints, rejected alternatives, the WHY.

Sendbox letters & dashboard rows are **side-effects** of the steps above, not standalone steps.

---

## Local sendbox conventions (JarvanKB)

In addition to the upstream cc-sendbox protocol (`~/.claude/skills/sendbox-protocol/SKILL.md`), JarvanKB enforces the following project-local conventions. These augment the upstream "roles over sessions" principle and are tracked upstream in CodeTeam#1.

### Mailbox naming pattern

**`docs/sendbox/to{Prefix}{Role}/`**

- **`{Prefix}`** = a stable task-scope id, capitalized PascalCase. Examples: `SP0`, `SP1`, `ZhihuCrawl`, `BilibiliWatcher`, `CookieManager`. The prefix is omitted **only** for the singleton root orchestrator role (`toOrchestrator/`), preserving the cc-sendbox v0.2.1 legacy.
- **`{Role}`** = the function of the session that reads this box. Canonical roles: `Orche`, `SubOrche`, `Impler`, `Reviewer`, `Author`. New roles MAY be coined per project need; document them where they first appear.

### Supported hierarchies

```
Root Orche ──(handoff)──> Impler                     # e.g. toOrchestrator → toSP0Impler
Root Orche ──(handoff)──> SubOrche ──> Impler        # e.g. toOrchestrator → toZhihuCrawlOrche → toZhihuCrawlImpler
Root Orche ──(handoff)──> SubOrche ──> SubOrche → …  # deeper nesting allowed; same naming pattern
```

The convergence letter from a child session always lands in the **parent's** mailbox, named `from-<child-id-lower>-<topic>.md` (e.g. `from-sp0impler-sp0-done.md`).

### Multiple peers of the same role

If two implers report to the same orchestrator on the same task, append a numeric discriminator:
- `toSP0Impler1/`, `toSP0Impler2/`

This is rare; prefer task-decomposition (different prefixes) over peer multiplication.

### Hard invariant

**A single shared `toImpler/` or `toOrche/` (no prefix on a non-root role) is forbidden** whenever ≥2 sessions of that role can run concurrently. This was the failure mode that motivated the convention (see CodeTeam#1).

---

## Harness Enhancement Layer (v2)

Three active methods enhance the harness around the pipeline (compressed rows in `CLAUDE.md §2`):

1. **`sendbox-protocol`** — asynchronous file-based agent↔agent mail. Full local conventions: §Local sendbox conventions above.
2. **`cc-dashboard`** — `docs/Dashboard/index.md` projects pending user actions. Hook config: `docs/HarnessStack/hooks/cc-dashboard.md`.
3. **`code-map` (codegraph)** — structured local code map (CodeTeam #3, instantiated 2026-06-10):
   - **What:** https://github.com/colbymchenry/codegraph — MIT, Node, local SQLite + tree-sitter index in `.codegraph/` (gitignored, machine-local). CLI + on-demand stdio MCP server; no resident daemon, no autostart; the MCP server is spawned per Claude Code session, scoped to this repo.
   - **Install (machine-local):** `npm i -g @colbymchenry/codegraph` (no sudo). `.mcp.json` is gitignored here (holds keys), so each machine adds the server entry locally:
     `"codegraph": { "type": "stdio", "command": "codegraph", "args": ["serve", "--mcp"] }`
   - **Usage rule (Pipeline step 1):** prefer codegraph for in-repo symbol/caller/impact lookups over ad-hoc grep. **Map vs why:** codegraph answers what-is-where / what-calls-what from current code; RepoMem holds decisions, constraints, rationale.
   - **Strength caveat:** `query`/`callers`/`impact` are the strong commands; `callees`/`affected` are sparse on dynamic Python — and JarvanKB is predominantly Python (Engine/Service/Skill; only cookie-manager is Node). Fall back to grep where the graph is sparse.
   - **Worktree fallback (Pipeline step 5):** each worktree is a separate checkout — one-time `codegraph init` (~30 s, ~30 MB) per worktree, or `CODEGRAPH_NO_DAEMON=1 codegraph sync` for a one-shot refresh without the file watcher; then `query`/`impact` as synchronous CLI.
   - **Promote-time de-dup (Pipeline step 8):** never promote to RepoMem what codegraph derives from code.

---

## Lane Tiering (v2)

Instantiated from CodeTeam #4 (2026-06-10), translated from the OpenSpec-based original to v2 doc sets. Full item-by-item mapping: `docs/superpowers/specs/2026-06-10-harnessstack-codegraph-lanetiering-design.md`.

**Axis.** Every task carries `Lane: <fast|full>`, default **fast**. `Lane` is the STRUCTURAL axis — which document artifacts must exist. The step-2 auto-judge skip is the PROCEDURAL axis — how readily a step is skipped. They are orthogonal; all four combinations are valid; `Lane` never changes a step's policy (steps with external side effects keep their policy on both lanes).

**Declaration.** In the plan-doc frontmatter (`docs/superpowers/plans/YYYY-MM-DD-<slug>.md`), e.g. `**Lane:** full`. A handoff letter MAY pre-declare a lane; the plan doc is authoritative. A task trivial enough to have no plan is implicitly fast.

**Selection rule (full if ANY, else fast):**
- touches dependencies
- cross-cutting: ≥2 of Engine|Service|Skill, or crosses the Python↔Node boundary
- produces a durable `RepoMem/persist/` asset
- adds net-new reusable public contract surface

**Lane → document set:**

| Artifact | fast | full |
|---|---|---|
| `docs/superpowers/plans/` plan doc | required (may be minimal) | required |
| `docs/superpowers/specs/` design doc | optional-by-default; omission noted in one line in the plan | expected; collapsible — MAY be just its `### Dn` decision list when the decision count is small |
| `RepoMem/temp/<slug>/` | **skipped entirely** | per RepoMem capture rules |
| `temporary-<task>.md` | unchanged from v2: optional recipe patch on BOTH lanes (required on neither) | same |
| `grill-design` design gate (`.claude/skills/grill-design/`) | ineligible (no design tree) | MAY run (auto-judge); window: draft spec → before writing-plans |

> **Skill naming note (2026-06-11, task `grill-with-docs-restore`):** the design gate above was authored 2026-06-10 under the name `grill-with-docs` (CodeTeam #4 prop 4 adaptation) and RENAMED to `grill-design` — semantics unchanged, no deactivation. The name `grill-with-docs` is now the **community original** (Matt Pocock, `mattpocock/skills@e3b90b5`, installed verbatim at `.claude/skills/grill-with-docs/`): an interactive grilling session that maintains the project glossary (`CONTEXT-MAP.md` + per-module-group `CONTEXT.md` — glossary only, complement to RepoMem, no implementation details). JarvanKB-local write-sink override when running it: decision-worthy outcomes passing its 3-condition ADR test go to RepoMem (`temp/<slug>/decisions.md` → HITL promote), NOT `docs/adr/` — RepoMem remains the single durable decision memory (CLAUDE.md §4). Decisions D1–D3: `docs/superpowers/plans/2026-06-11-grill-with-docs-restore.md`.

**Fast-lane promote-candidate lesson:** if a fast-lane task still surfaces a genuinely durable lesson, it goes through step-8 HITL merge directly from the session (no temp staging) — the merge reviewer is the existing non-duplication checkpoint.

**Invariants (translated from #4 "Invariants preserved"):**
- No data migration: Lane governs NEW tasks only; existing docs keep their structure.
- No layer removed: `persist/` untouched; pipeline ordering, merge gate, verification topology unchanged.
- Single-identifier vacuous satisfaction: a fast-lane task produces no `temp/<slug>/`; `<task> = <slug>` (CLAUDE.md §4) holds vacuously. Absence of the temp dir is NOT a divergence and needs NO Recipe Invariant Exception.
- Absence-by-lane ≠ skip: a document absent because the lane does not require it is absence-by-lane-definition, not an auto-judge skip — no skip note beyond the one-liners defined above.
- Reversible: `fast→full` mid-flight is cheap — flip the field in the plan doc, create `temp/<slug>/`, back-fill. Residual under-classification risk is mitigated by the fast default, the cheap promotion path, and the step-8 HITL reviewer.

**Not mapped from #4 (recorded, intentionally skipped):** the `00-INDEX` self-attestation drop (JarvanKB never had `00-INDEX`; non-duplication is already HITL-enforced at step 8); `proposal.md`/`tasks.md` doc names (v2 has no OpenSpec — the plan doc is the analog).

---

## Milestone Gating (v2)

Instantiated 2026-06-18 (user directive). Adds a **capability-milestone axis** on top of the SP-N implementation
axis, plus a standing orchestrator rule. **Additive amendment — NOT a Full Rewrite** (no method removed; pipeline
ordering, merge gate, verification topology unchanged — this only adds an orchestrator check at task completion).

**Two axes (orthogonal):**
- **SP-N — implementation axis.** The existing sub-project tracking in `Dashboard §SP Status Board`. Unchanged.
- **vN — user-facing capability milestones.** `version-plan.md §Capability Milestones` (canonical, A2A) +
  `Dashboard §里程碑` (H2A 中文 projection). One milestone may span multiple SPs; one SP may serve multiple
  milestones. The current ladder: v1 (Hermes conversational ingest) → v1.1 (favorites watchers) → v1.2 (Thino
  link ingest) → v2 (followed-people crawl+filter) → v3 (deep research) → v4 (memory system) → v5+ (research-agent
  long-horizon).

**The standing rule:**
1. **Milestone-unlock check at every task completion.** Whenever a task closes (impler done / SP merged / a
   decision lands), the orchestrator re-evaluates: did this complete, or bring within reach, any vN milestone?
   Update the status in `Dashboard §里程碑`.
2. **Last-mile handoff.** When a milestone **unlocks or nears completion**, the orchestrator hands off an impler
   (via the normal §Pipeline-v2 / §Local-sendbox handoff flow — handoff letter + Dashboard row + user-booted
   session) whose charter is to take the user through the **last mile** to the *delivered capability*: the
   integration / UX / ops / deploy glue that turns "the SPs are technically done" into "the user can use the
   capability end-to-end." This is a deliverable distinct from any single SP's technical completion.
3. **Scope.** Root applies this across all milestones; a SubOrche applies it to its own vertical's milestone(s).

**Why a separate rule (not just SP status):** an SP merge is a *technical* done; a milestone is a *user
capability*. The gap between them — deploy, wire-up, conversational UX, vault placement, the "make it real for the
user" mile — is exactly what the last-mile handoff owns, and it is easy to drop if only SP-done is tracked.

---

## Hard Invariants (v2)

(See `CLAUDE.md` §4 for the compressed version. Both must stay in sync.)

- **Single task identifier.** `<task> = <slug>`.
- **Add-only on methods, with Full Rewrite escape valve.** Methods do not silently deactivate. Recipe migrations require a Full Rewrite entry in this file (as the v1→v2 entry above demonstrates).
- **Single verification gate.** `Superpowers.verification-before-completion`. No replacements.
- **Merge ordering & ownership.** `RepoMem.merge` AFTER `finishing-a-development-branch`, HITL, never before. **The implementer owns merge closure** (runs it within its own lifecycle, or delegates *execution* to orche but tracks to done — never fire-and-forget). Impler-handoff §3.F wording must reflect this.
- **No content duplication** across per-task doc sets.
- **One sendbox per project.** `<root>/docs/sendbox/` only. Side cwds write by path.
- **Per-task mailbox.** Every parallel non-root session reads/writes its own `to{Prefix}{Role}/` mailbox; shared role-only mailboxes forbidden for concurrent roles. See §Local sendbox conventions.
- **Layered RepoMem.** Module reads two layers, writes one; HITL promotes module → global.
- **Lane axis: structural, additive, reversible.** `Lane: fast|full` (default fast, declared in the plan doc) changes only which doc artifacts exist, never a step's policy. Fast-lane absence of `temp/<slug>/` vacuously satisfies the single-task-identifier invariant; absence-by-lane is NOT an auto-judge skip; `fast→full` promotion is cheap. See §Lane Tiering (v2).
- **One letter → N dashboard rows.** Independent lifecycles.
- **No silent invariant skips.** Pipeline ordering, merge gates, verification topology are recipe invariants. Exceptions require a declared `Recipe Invariant Exception` in the relevant `temporary-<slug>.md` with reason + compensating action.

---

## Full Rewrite Conditions

A recipe Full Rewrite (versioned migration like v1→v2) is allowed when:

- Strategic scope changes (e.g. monolithic tool → multi-sub-project family)
- A method's value/cost ratio becomes net negative for the project's formation (e.g. OpenSpec for thin-layer projects per R8 analysis)
- Cross-platform constraints force a structural change

Each Full Rewrite MUST:
- Document the trigger, decision, net changes, and reintroduction conditions in this file
- Reference the design/spec that motivated it
- Be committed atomically with the code/doc changes that effect the migration

---

## Related Documents

- `CLAUDE.md` — distilled session-load contract
- `docs/HarnessStack/_toUser/README.md` — user-facing manual
- `docs/HarnessStack/hooks/` — repo-local hook configs (e.g. cc-dashboard)
- `docs/RepoMem/persist/version-plan.md` — phase plan, recipe version history
- `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` — v2 migration design
- `docs/superpowers/specs/2026-06-10-harnessstack-codegraph-lanetiering-design.md` — CodeTeam #3/#4 instantiation mapping (U1–U4)

---

## Archival: v1 Reference (DEPRECATED)

The v1 recipe `openspec-superpowers-repomem-sendbox-dashboard` was active 2026-05-26 → 2026-05-31. Its 13-step pipeline added OpenSpec steps 3 (explore/propose), 5 (consume specs+tasks), 8b (verify), and 11 (archive) — these are now obsolete.

The original v1 longterm.md content is preserved below for historical reference only. **Do not follow it.**

---

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
