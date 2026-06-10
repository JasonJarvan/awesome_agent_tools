# Design — Instantiate CodeTeam #3 (codegraph) + #4 (Lane Tiering) into JarvanKB recipe v2

> Task: `harnessstack-codegraph-lanetiering` (root-level governance task, HarnessStackImpler, 2026-06-10)
> Sources: CodeTeam issues #3 + #4 (authored on EverClaw, recipe `openspec-superpowers-repomem-ecc`)
> Target: JarvanKB recipe v2 `superpowers-repomem-sendbox-dashboard` — **translated**, not copied (no OpenSpec, no ECC here)
> User decisions captured 2026-06-10 via brainstorming gate (3 AskUserQuestion answers, all "Recommended" picks)

## 1. User decisions (the gate)

| # | Question | Decision |
|---|---|---|
| U1 | #3 codegraph adoption depth | **Full adoption**: install `npm i -g @colbymchenry/codegraph` now, add codegraph stdio server to `.mcp.json`, run `codegraph init` to validate; docs worded as landed. |
| U2 | #4 Lane Tiering adoption | **Adopt as drafted** (props 1/2/3b + invariant clauses, JarvanKB-translated; 3a + 4 recorded as does-not-map skips). |
| U3 | Where `Lane` is declared | **Plan-doc frontmatter** (`docs/superpowers/plans/YYYY-MM-DD-<slug>.md` Task Meta). Handoff letters MAY pre-declare; the plan doc is authoritative. Trivial tasks with no plan are implicitly `fast`. |
| U4 | #4 prop 4 `grill-with-docs` (mid-flight user directive, 2026-06-10) | **Adopt-adapted, overriding the initial does-not-map-skip draft**: the skill is absent in this environment, so AUTHOR a JarvanKB-local project skill at `.claude/skills/grill-with-docs/SKILL.md`, translated to v2 (see §3 item 4.4). User: "当前项目应添加 grill-with-docs skill". |

## 2. Per-item mapping (#3 codegraph)

| Item | Verdict | JarvanKB translation | Target |
|---|---|---|---|
| 3.1 `code-map` as Harness Enhancement method | **adapt** | Third Harness Enhancement method, peer to `sendbox-protocol` + `cc-dashboard`. The v2 section of `longterm.md` has **no** Harness Enhancement Layer section (the handoff's "§5 ~L200" pointer lands in the deprecated v1 archive) → **add a new `## Harness Enhancement Layer (v2)` section** to the v2 block. | `CLAUDE.md §2` table row + new `longterm.md` v2 section |
| 3.2 MCP server registration + install | **adopt (user-authorized U1)** | `npm i -g @colbymchenry/codegraph`; add `codegraph` stdio server beside `tavily` in `.mcp.json`. **Correction during planning:** `.mcp.json` is gitignored in JarvanKB (plaintext API key) — so the edit is machine-local, same spirit as EverClaw's overlay; the canonical server snippet is documented in `longterm.md` so other machines can replicate. `.codegraph/` added to `Tools/JarvanKB/.gitignore` (verified not yet ignored). | `.mcp.json` (local-only), `.gitignore` |
| 3.3 Pipeline step-1 "prefer codegraph" | **adapt, weakened wording** | Amend Pipeline v2 **step 1 `RepoMem.read`**: prefer codegraph for in-repo symbol/call-graph lookups over ad-hoc grep — codegraph is the map, RepoMem the why. **Caveat baked into the rule**: JarvanKB is predominantly dynamic Python (Engine/Service/Skill; only cookie-manager is Node), where `callees`/`affected` are sparse; `query`/`callers`/`impact` are the strong commands. Wording: "prefer for symbol location & caller/impact lookups; fall back to grep where the graph is sparse (dynamic-Python callees)". No ECC.research-first analog exists — step 1 is the only read step. | `CLAUDE.md §3` step 1 + `longterm.md §Pipeline v2` step 1 |
| 3.4 CLI fallback in worktrees | **adapt** | JarvanKB leans on `using-git-worktrees` (step 5). Add: after `git worktree add`, `CODEGRAPH_NO_DAEMON=1 codegraph sync` for one-shot refresh, then `query`/`impact` as sync CLI; budget one-time `codegraph init` (~30s/~30 MB) per worktree. | `longterm.md §Pipeline v2` step 5 |

## 3. Per-item mapping (#4 Lane Tiering)

| Item | Verdict | JarvanKB translation | Target |
|---|---|---|---|
| 4.1 `Lane: fast\|full` field, default `fast` | **adapt** | Structural axis (which doc artifacts exist), orthogonal to the **procedural** auto-judge skip (`CLAUDE.md §3` step 2). Declared in **plan-doc frontmatter** (U3), not `temporary-<task>.md` (JarvanKB has zero instances; it is an optional recipe patch here, not a per-task doc — forcing it would add a tax #4 exists to cut). Selection rule (full if ANY): touches dependencies; cross-cutting ≥2 of Engine\|Service\|Skill; crosses Python↔Node boundary; produces a `RepoMem/persist/` asset; adds net-new public contract surface. Else fast. | `CLAUDE.md §3` (new Lane paragraph) + new `longterm.md §Lane Tiering (v2)` section |
| 4.2 fast-lane doc set | **translate** | No `proposal.md`/`tasks.md` in v2 — the writing-plans **plan doc is the analog** (carries scope + steps). Fast lane = plan doc only (may be minimal), **skip `RepoMem/temp/<slug>/` entirely**, brainstorming-`specs/` optional-by-default (omission noted in one line in the plan). Full lane = today's full set (specs + plan + temp/<slug>/). `temporary-<task>.md` stays what it is in v2: an optional recipe patch, required on **neither** lane. | same as 4.1 |
| 4.3a drop `00-INDEX` self-attestation | **does not map — skip** | JarvanKB never had `00-INDEX`; non-duplication is already HITL-enforced at `RepoMem.merge` (`CLAUDE.md §4`). Spirit already holds; adding then dropping would be ceremony. | recorded here only |
| 4.3b collapsible design doc | **adapt (light)** | A `specs/` design doc MAY be just its decision list (`### Dn`) when the decision count is small; no forced long-form. | `longterm.md §Lane Tiering (v2)` |
| 4.4 `grill-with-docs` design gate | **adopt-adapted (U4)** | Skill absent in this environment → **author it as a JarvanKB project skill** (`.claude/skills/grill-with-docs/SKILL.md`, agentskills.io-compliant). Translation to v2: a **full-lane-only, auto-judge design gate** that stress-tests a draft `specs/` design doc BEFORE `writing-plans` (window: between brainstorming's spec draft and the plan). Doc context = JarvanKB's analogs of ADR/CONTEXT.md: `docs/RepoMem/persist/architecture/` + `<module>/docs/RepoMem/{architecture,decisions}.md` (do NOT invent `CONTEXT.md`/`docs/adr/`). Write-sinks redirected per #4: domain terms + sharpened wording → the `specs/` doc itself; decision-worthy outcomes → the spec's `### Dn` decision list; implementation-time gotchas → `RepoMem/temp/<slug>/`. Auto-judge tier: agent judges whether a non-trivial design exists worth grilling; skips with a one-line note in the plan otherwise (e.g. mechanically-full dep-bump tasks). Fast lane: ineligible (no design tree). | new `.claude/skills/grill-with-docs/SKILL.md` + wiring in `longterm.md §Lane Tiering (v2)` + one-line mention in `CLAUDE.md §3` step 2 |
| 4.5 promote-time codegraph de-dup | **adapt (lands because #3 landed, U1)** | Extend the step-8 promotion standard: do NOT promote to RepoMem what codegraph can derive from current code (symbol locations, call graphs, impact sets); `persist/architecture/` holds only what codegraph cannot derive — decisions, constraints, rejected alternatives, the why. Promote-time counterpart of the step-1 read-time rule. | `CLAUDE.md §3` step 8 + `longterm.md §Pipeline v2` step 8 promotion standard |
| 4.i invariant clauses | **adapt** | (a) **Single-identifier vacuous satisfaction**: fast lane produces no `temp/<slug>/`, so `<task> = <slug>` holds vacuously — absence of the temp dir is NOT a divergence, no Recipe Invariant Exception. (b) **Absence-by-lane ≠ Skip-Mechanism skip**: a doc absent because the lane doesn't require it needs no Auto-Skip log / exception; steps with external side effects keep their policy on both lanes. (c) **Reversible**: `fast→full` mid-flight is cheap (flip the field in the plan doc, create `temp/<slug>/`, back-fill); residual under-classification risk mitigated by fast default + cheap promotion + `RepoMem.merge` HITL reviewer. | `CLAUDE.md §4` + `longterm.md §Hard Invariants (v2)` |

## 4. Add-only vs Full Rewrite determination (handoff §5)

**Determination: additive amendment — NOT a Full Rewrite.** Adding codegraph is a new Harness Enhancement method (add-only). Lane Tiering adds a structural axis with default `fast`, removes **no** layer, step, gate, or method (per #4's own "Invariants preserved": no data migration, Pipeline ordering / merge gates / verification topology unchanged), and is reversible per task. No existing v2 layer/step is removed or overridden → no escalation needed. Recorded here per handoff §5.

## 5. Propagation principle compliance (handoff §4)

Every rule an impler must FOLLOW lands in `CLAUDE.md` (always-loaded), compressed; full detail in `longterm.md` v2 block. Concretely:
- `CLAUDE.md §2`: + `code-map (codegraph)` row.
- `CLAUDE.md §3`: step 1 += codegraph-preference clause; step 8 += codegraph de-dup clause; new compact Lane paragraph (axis, default, declaration point, selection rule, doc-set mapping).
- `CLAUDE.md §4`: + Lane invariant bullet (vacuous satisfaction, absence-by-lane, reversibility).
- `CLAUDE.md §Where to Look`: pointer to `longterm.md §Lane Tiering (v2)`.
- `longterm.md` v2 block: new `## Harness Enhancement Layer (v2)` + new `## Lane Tiering (v2)` sections; step 1/5/8 amendments; Hard Invariants bullet. **v1 archive (≥ "Archival" marker) untouched.**

## 5b. Skill-gap survey (2026-06-10, prompted by U4)

Skills the governance contract / upstream issues reference vs. what is installed in this environment:

| Referenced by | Skill | Status here |
|---|---|---|
| CLAUDE.md §2 | Superpowers suite (brainstorming…finishing-a-development-branch) | ✅ installed (plugin) |
| CLAUDE.md §2 | `repo-mem`, `sendbox-protocol`, `cc-dashboard` | ✅ installed (`~/.claude/skills/`) |
| Issue #4 prop 4 | `grill-with-docs` | ❌ absent → **authored locally this task (U4)** |
| Issue #3 (ECC tooling peers) | `pre-commit-eval`, `security-scan` | ❌ absent — ECC-recipe tools, NOT referenced by JarvanKB v2 contract; no gap to close (out of scope; revisit only if a future proposal targets them) |
| — | JarvanKB project-local `.claude/skills/` + `.claude/commands/` | empty until now; `grill-with-docs` becomes the first project-local skill |

## 6. Out of scope

Upstream `harness-stack` template repo (not in checkout); OpenSpec reintroduction; any edit to the deprecated v1 block; other sessions' in-flight files; Dashboard SP rows for other SPs.

## 7. Verification (step 6 of this task)

Two-pass doc review, as #4 itself prescribes: (a) cross-reference integrity — every CLAUDE.md rule has its longterm detail and vice-versa, no dangling pointers; (b) no semantic contradiction with existing v2 invariants / pipeline / sendbox + dashboard layers / auto-judge skip. Plus: codegraph install validated by `codegraph init` + a real `codegraph query` against this repo.
