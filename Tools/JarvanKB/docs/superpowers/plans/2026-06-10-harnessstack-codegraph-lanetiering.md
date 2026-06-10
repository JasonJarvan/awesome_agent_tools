# HarnessStack codegraph + Lane Tiering Instantiation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Lane:** full *(first Lane declaration under the rule this very task lands: produces `RepoMem/persist`-grade governance assets + net-new contract surface — dogfooding U3)*

**Goal:** Land CodeTeam #3 (codegraph code-map) + #4 (Lane Tiering) into JarvanKB's recipe-v2 HarnessStack docs, install codegraph (user-authorized U1), and author the project-local `grill-with-docs` skill (U4).

**Architecture:** Doc-governance task — no TDD (handoff §7). All always-loaded rules land compressed in `CLAUDE.md` with full detail in `longterm.md` v2 block (propagation principle, handoff §4). The v1 archive in `longterm.md` (from `## Archival: v1 Reference (DEPRECATED)` onward) is NEVER touched. Verification = two-pass doc review (cross-ref integrity + no semantic contradiction).

**Tech Stack:** Markdown governance docs; `@colbymchenry/codegraph` (npm global, Node 25 available); `.mcp.json` (machine-local, gitignored); git worktree off local `feat/agentcrawl-bootstrap`.

**Spec:** `docs/superpowers/specs/2026-06-10-harnessstack-codegraph-lanetiering-design.md` (item-by-item mapping, U1–U4).

---

### Task 1: Commit pre-work docs in main tree

**Files:**
- Already created: `docs/superpowers/specs/2026-06-10-harnessstack-codegraph-lanetiering-design.md`, `docs/RepoMem/temp/harnessstack-codegraph-lanetiering/decisions.md`, this plan.

- [ ] **Step 1: Commit with explicit pathspec** (shared index — memory rule: never bare `git commit`)

```bash
cd /home/shenzhou/Codes/awesome_agent_tools/Tools/JarvanKB
git add docs/superpowers/specs/2026-06-10-harnessstack-codegraph-lanetiering-design.md \
        docs/RepoMem/temp/harnessstack-codegraph-lanetiering/decisions.md \
        docs/superpowers/plans/2026-06-10-harnessstack-codegraph-lanetiering.md
git commit -m "docs(harnessstack): spec+plan for CodeTeam #3/#4 instantiation (codegraph + Lane Tiering)" \
  -- docs/superpowers/specs/2026-06-10-harnessstack-codegraph-lanetiering-design.md \
     docs/RepoMem/temp/harnessstack-codegraph-lanetiering/decisions.md \
     docs/superpowers/plans/2026-06-10-harnessstack-codegraph-lanetiering.md
```

### Task 2: Worktree off LOCAL branch

- [ ] **Step 1:** `git worktree add -b harnessstack-codegraph-lanetiering /home/shenzhou/Codes/awesome_agent_tools/.worktrees/harnessstack-codegraph-lanetiering feat/agentcrawl-bootstrap` (base = local branch, NOT origin/main — memory rule). All Task 3–6 edits happen under `<worktree>/Tools/JarvanKB/`.

### Task 3: `.gitignore` — `.codegraph/` + re-include `.claude/`

**Files:** Modify `Tools/JarvanKB/.gitignore`

- [ ] **Step 1: Append**

```gitignore
# codegraph local index — machine-local (see docs/HarnessStack/longterm.md §Harness Enhancement Layer (v2))
.codegraph/
# repo-root .gitignore ignores all .claude/ — re-include project-level skills here
# (.claude/settings.local.json stays ignored via the rule above)
!.claude/
```

- [ ] **Step 2: Verify** `git check-ignore -v .claude/skills/x .codegraph/foo .claude/settings.local.json .mcp.json` → expect: `.claude/skills/x` NOT ignored; other three ignored. If `!.claude/` fails to re-include (parent-dir exclusion edge case), fall back to `git add -f` for the skill file and note it in the done-letter.

### Task 4: Author project skill `grill-with-docs`

**Files:** Create `Tools/JarvanKB/.claude/skills/grill-with-docs/SKILL.md`

- [ ] **Step 1: Write SKILL.md** (agentskills.io-compliant; A2A English; full content in spec §3 item 4.4 — final text below)

```markdown
---
name: grill-with-docs
description: Use when a full-lane task has a draft design/spec in docs/superpowers/specs/ and writing-plans has not run yet — stress-tests the draft against RepoMem architecture/decisions and current-code ground truth (codegraph), sharpening terminology and surfacing contradictions before they become an execution plan.
---

# Grill With Docs (JarvanKB v2 adaptation)

Deep design review of a DRAFT spec, grounded in the repository's durable knowledge. Adapted from the community grill-with-docs (ADR/CONTEXT.md-based) to recipe v2: the doc context here is RepoMem, NOT docs/adr/ or CONTEXT.md — do not create those.

## When to run (auto-judge)

- Full-lane tasks only (fast lane has no design tree).
- Window: after a draft spec exists in `docs/superpowers/specs/` (or `<module>/docs/superpowers/specs/`), BEFORE invoking writing-plans.
- Auto-judge tier: run when there is a non-trivial design worth grilling (new architecture, new contract surface, cross-module behavior). Skip mechanically-full tasks (e.g. dependency bumps) with a one-line note in the plan: `grill-with-docs: skipped — <reason>`.

## Process

### 1. Gather context (in order)
1. Global: `docs/RepoMem/persist/architecture/` + `docs/RepoMem/persist/memory/` (decision rationale, gotchas).
2. Module: `<module>/docs/RepoMem/{architecture,decisions}.md` for every module the design touches.
3. Current-code ground truth: codegraph `query`/`callers`/`impact` on the symbols the design names (grep fallback where the graph is sparse — dynamic-Python callees).
4. Prior specs in `docs/superpowers/specs/` overlapping this design's scope.

### 2. Grill the draft
1. **Domain fidelity** — does the design use the vocabulary already established in RepoMem architecture docs? Same concept, same name?
2. **Decision consistency** — does it contradict a recorded decision (spec `### Dn`, module `decisions.md`, `persist/memory/`)? Flag: either the design changes, or the old decision is explicitly superseded — say which.
3. **Reality check** — do the symbols/flows the design references exist as described (codegraph)? A design built on a stale mental model fails here.
4. **Module depth & leakage** — simple interfaces, deep implementations? Does it leak one module's knowledge into another?
5. **Contract surface** — does it add public contract surface without declaring it? (That flips the Lane selection rule — re-check the lane.)

### 3. Write findings back (write-sinks)
- Sharpened terminology + corrected statements → edit the spec text in place.
- Decision-worthy outcomes → the spec's `### Dn` decision list.
- Implementation-time gotchas discovered while grilling → `RepoMem/temp/<slug>/` (full lane has it).
- Do NOT create `CONTEXT.md`, `docs/adr/`, or any new doc category.

## Principles
- Docs are the spec, code is the implementation; when they disagree, flag it and say which should change.
- The grill teaches: cite the RepoMem doc or codegraph evidence behind each finding.
- Missing docs are no excuse: grill against code ground truth and note what RepoMem should have contained.
```

### Task 5: `CLAUDE.md` edits (always-loaded, compressed)

**Files:** Modify `Tools/JarvanKB/CLAUDE.md`

- [ ] **Step 1 (§2 table):** add row after the `cc-dashboard` row:

```markdown
| Harness Enhancement | `code-map` (codegraph) | **active** | local symbol/call-graph index (`.codegraph/`, MCP + CLI); prefer `query`/`callers`/`impact` over ad-hoc grep for in-repo symbol lookups — codegraph = the map, RepoMem = the why; `callees`/`affected` sparse on dynamic Python (most of this repo). Detail: `longterm.md §Harness Enhancement Layer (v2)` |
```

- [ ] **Step 2 (§3 step 1):** replace step-1 line with:

```markdown
1. `RepoMem.read` — load global persist + per-module RepoMem (two layers); prefer codegraph (`query`/`callers`/`impact`) over ad-hoc grep for in-repo symbol/caller/impact lookups (map vs why — §2 code-map row)
```

- [ ] **Step 3 (§3 step 2):** append to the step-2 line, inside the trailing parenthetical, after "Type-B dashboard row": `; full-lane: MAY grill the draft spec via project skill `grill-with-docs` before step 4 (auto-judge)`

- [ ] **Step 4 (§3 step 8):** after "NOT mechanism that lives in code", insert: `, NOR what codegraph derives from current code (symbol locations / call graphs / impact sets)`

- [ ] **Step 5 (§3, after the 8-step list, before the "Sendbox letters … side-effects" line):** insert paragraph:

```markdown
**Lane Tiering (structural axis, orthogonal to the step-2 auto-judge skip):** every task carries `Lane: fast|full` — default **fast** — declared in the plan-doc frontmatter (a trivial task with no plan is implicitly fast). Select **full** if ANY: touches dependencies / cross-cutting ≥2 of Engine|Service|Skill / crosses Python↔Node / produces a `RepoMem/persist/` asset / adds net-new public contract surface. fast = plan doc only (may be minimal; `specs/` optional, omission noted in one line in the plan) and **skip `RepoMem/temp/<slug>/` entirely**; full = today's full doc set. Lane changes which doc artifacts exist, never a step's policy. Detail: `longterm.md §Lane Tiering (v2)`.
```

- [ ] **Step 6 (§4):** add bullet after the "Layered RepoMem." bullet:

```markdown
- **Lane axis: structural, additive, reversible.** `Lane: fast|full` (default fast) governs which doc artifacts exist, never a step's policy. Fast-lane absence of `temp/<slug>/` vacuously satisfies `<task> = <slug>` (NOT a divergence — no Recipe Invariant Exception); absence-by-lane is NOT an auto-judge skip (no skip note); `fast→full` mid-flight promotion is cheap.
```

- [ ] **Step 7 (§Where to Look):** add rows:

```markdown
| Lane Tiering full rule (selection, doc-set mapping, invariants) | `docs/HarnessStack/longterm.md` §Lane Tiering (v2) |
| code-map / codegraph ops (install, MCP, worktree fallback) | `docs/HarnessStack/longterm.md` §Harness Enhancement Layer (v2) |
| Project-local skills (`grill-with-docs`) | `.claude/skills/<name>/SKILL.md` |
```

### Task 6: `longterm.md` edits (v2 block ONLY — nothing at/after `## Archival: v1 Reference (DEPRECATED)`)

**Files:** Modify `Tools/JarvanKB/docs/HarnessStack/longterm.md`

- [ ] **Step 1 (Pipeline v2 step 1):** append: ` For in-repo **symbol / caller / impact lookups**, prefer the codegraph code-map (`codegraph query|callers|impact`, MCP or CLI) over ad-hoc grep — codegraph is the up-to-date structural map; RepoMem stays the durable why-layer. Fall back to grep where the graph is sparse (`callees`/`affected` on dynamic Python — most of this repo).`

- [ ] **Step 2 (step 2):** append: ` On a **full-lane** task, after a draft design/spec exists and before step 4, the agent MAY run project skill `grill-with-docs` (auto-judge: grill when a non-trivial design exists, else skip with a one-line note in the plan). See §Lane Tiering (v2).`

- [ ] **Step 3 (step 4):** append: ` The plan-doc frontmatter carries the task's `Lane:` declaration (§Lane Tiering (v2)).`

- [ ] **Step 4 (step 5):** append: ` Worktrees are separate checkouts: budget a one-time `codegraph init` (~30 s, ~30 MB) per worktree, or `CODEGRAPH_NO_DAEMON=1 codegraph sync` for a one-shot incremental refresh (no file watcher in sandboxed worktrees), then `codegraph query`/`impact` as plain synchronous CLI.`

- [ ] **Step 5 (step 8 promotion-standard blockquote):** append: ` **Codegraph de-dup rule (promote-time counterpart of the step-1 read-time rule):** do NOT promote structural facts codegraph answers from current code — symbol locations, call graphs, impact sets. `persist/architecture/` holds only what codegraph cannot derive: decisions, constraints, rejected alternatives, the WHY.`

- [ ] **Step 6:** insert two new sections between `## Local sendbox conventions` section end and `## Hard Invariants (v2)`: `## Harness Enhancement Layer (v2)` + `## Lane Tiering (v2)` — full text as drafted in spec §2 item 3.1 / §3 items 4.1–4.5 (codegraph what/install/usage/caveat/worktree/de-dup; Lane axis/declaration/selection/doc-set table incl. fast-lane promote-candidate path + grill row; invariants incl. vacuous satisfaction, absence-by-lane, reversibility; "Not mapped from #4" record pointing at the spec).

- [ ] **Step 7 (Hard Invariants v2):** add bullet mirroring CLAUDE.md §4 Lane bullet, ending `See §Lane Tiering (v2).`

- [ ] **Step 8 (Related Documents):** add: `- docs/superpowers/specs/2026-06-10-harnessstack-codegraph-lanetiering-design.md — CodeTeam #3/#4 instantiation mapping (U1–U4)`

- [ ] **Step 9: Commit (worktree, pathspec):** `git commit -m "docs(harnessstack): instantiate CodeTeam #3 codegraph + #4 Lane Tiering into recipe v2" -- Tools/JarvanKB/CLAUDE.md Tools/JarvanKB/docs/HarnessStack/longterm.md Tools/JarvanKB/.gitignore Tools/JarvanKB/.claude/skills/grill-with-docs/SKILL.md`

### Task 7: codegraph install + validation (machine-global + main tree; user-authorized U1)

- [ ] **Step 1:** `npm i -g @colbymchenry/codegraph && codegraph --version`
- [ ] **Step 2:** main tree `cd Tools/JarvanKB && codegraph init` → expect index built (files/nodes/edges counts), `.codegraph/` created (ignored after Task 3 merges; meanwhile untracked).
- [ ] **Step 3:** validate: pick a real symbol (`grep -rn "^class " Engine/ | head`), run `codegraph query <Symbol>` → expect exact span. Record output for the done-letter.
- [ ] **Step 4:** add to `.mcp.json` `mcpServers` (machine-local, NOT committed): `"codegraph": { "type": "stdio", "command": "codegraph", "args": ["serve", "--mcp"] }`

### Task 8: Verification (two-pass, handoff §7)

- [ ] **Pass A — cross-ref integrity:** every new CLAUDE.md rule has its longterm detail and vice-versa; all §-pointers resolve (`§Lane Tiering (v2)`, `§Harness Enhancement Layer (v2)`, spec path); no edit at/after the v1 archive marker (`git diff` line ranges).
- [ ] **Pass B — no semantic contradiction:** new text vs v2 invariants (single identifier, add-only, single verification gate, merge ordering, no-duplication, sendbox, layered RepoMem, no-silent-skips) + auto-judge skip wording + sendbox/dashboard layers. Specifically check Lane wording never licenses skipping a *step* (only artifacts).

### Task 9: Finish branch (ask-first) + Step 8 closure

- [ ] **Step 1:** `superpowers:finishing-a-development-branch` — ask user; expected: merge `harnessstack-codegraph-lanetiering` → local `feat/agentcrawl-bootstrap`, no push, remove worktree.
- [ ] **Step 2:** `RepoMem.merge` (HITL, impler owns closure): promote-light — spec already durable; decide whether D3 (stale §5 pointer) / D6 (`.claude` gitignore) warrant a persist note; prune `temp/harnessstack-codegraph-lanetiering/`.
- [ ] **Step 3:** done-letter `docs/sendbox/toOrchestrator/from-harnessstackimpler-done.md` (mapping table, add-only determination, commits, codegraph install + `.mcp.json` state) + Dashboard row(s) for anything user-facing left.
