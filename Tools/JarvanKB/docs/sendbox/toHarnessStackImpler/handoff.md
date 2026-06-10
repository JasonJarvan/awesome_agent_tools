> from: root orchestrator generation 4 (Claude Opus 4.8 1M, active 2026-06-07 →)
> recipient: HarnessStackImpler (a new Claude Code peer session you are about to become)
> mode: child-handoff (sendbox-protocol Mode A — root stays alive; you converge back to `toOrchestrator/`)
> purpose: instantiate two upstream HarnessStack governance proposals (CodeTeam #3 codegraph code-map +
>   #4 Lane Tiering) into THIS repo's HarnessStack — TRANSLATED to JarvanKB's recipe v2, not copied verbatim
> lifecycle: burn after root reads your `from-harnessstackimpler-done.md`
> date: 2026-06-10

# Handoff — HarnessStackImpler (instantiate CodeTeam #3 + #4 into JarvanKB v2)

## 0. What you are

You are a **bounded governance-docs impler**, a **direct child of root orche g4** (HarnessStack is
repo-global governance = root's domain, **not** a crawl SubOrche's). Root stays alive. You read two upstream
issues, **translate** their proposals into JarvanKB's recipe-v2 HarnessStack, edit the docs, verify
cross-reference integrity, then report `from-harnessstackimpler-done.md` to `toOrchestrator/` and disappear.

Task identifier (single, per CLAUDE.md §4 hard invariant): **`harnessstack-codegraph-lanetiering`**.

## 1. The subtask scope

Read CodeTeam issues **#3** (codegraph code-map) and **#4** (Lane Tiering) and instantiate their adopted
parts into JarvanKB's **own local** HarnessStack docs (`docs/HarnessStack/longterm.md` v2 section +
`CLAUDE.md`, and `.mcp.json` only if codegraph is authorized). Success = the adopted proposals are reflected
**consistently and non-contradictorily** across the always-loaded contract + longterm detail, with the
recipe mismatch correctly translated (see §3 — this is the whole job).

Fetch the issues (the plain `gh issue view` hits a deprecated-GraphQL bug — use the JSON selector):
```
gh issue view 3 --repo JasonJarvan/CodeTeam --json number,title,body --jq '.body'
gh issue view 4 --repo JasonJarvan/CodeTeam --json number,title,body --jq '.body'
```

## 2. ⚠️ The central catch — recipe mismatch (read before ANYTHING)

Both issues were authored on **EverClaw**, which runs recipe **`openspec-superpowers-repomem-ecc`**. They
target the upstream **recipe TEMPLATE** (`harness-stack/assets/templates/...`). **JarvanKB is a *consuming*
repo running recipe v2 `superpowers-repomem-sendbox-dashboard`** (see `CLAUDE.md §1`). Two structural
differences mean you **CANNOT copy the proposals verbatim — you must translate**:

| Upstream concept (in the issues) | JarvanKB v2 reality | Translation |
|---|---|---|
| **OpenSpec** (`proposal.md`, `tasks.md`, `spec.md`, `OpenSpec.propose` step, `change-id`, OpenSpec archive lifecycle, `00-INDEX`) | **REMOVED in v2 Full Rewrite** (`longterm.md §Recipe v1→v2 Migration`) | Map to JarvanKB's doc-set: `docs/superpowers/specs/` (brainstorming design) + `docs/superpowers/plans/` (writing-plans) + `RepoMem/temp/<slug>/` + `temporary-<task>.md`. **Do NOT reintroduce OpenSpec** (that needs a Full Rewrite — `longterm.md §Full Rewrite Conditions`). |
| **ECC** (`ECC.research-first`, "ECC Harness Enhancement Layer", `ECC.session-state`) | JarvanKB has **no ECC**; Harness Enhancement = `sendbox-protocol` + `cc-dashboard` (`CLAUDE.md §2`, `longterm.md §5`) | "research-first / step-1 read" → v2 **Pipeline step 1 `RepoMem.read`**. "Harness Enhancement Layer" → JarvanKB's §5 layer. |
| `change-id` = `<slug>` three-identifier invariant | JarvanKB's **single task identifier** `<task> = <slug>` (`CLAUDE.md §4`) | Translate #4's "vacuous satisfaction" clause to JarvanKB's single-identifier wording. |
| upstream template files | JarvanKB instantiates **locally** in its own `longterm.md`/`CLAUDE.md` | You are NOT editing the upstream `harness-stack` repo (not in this checkout). Local instantiation only. |

You are doing what the issues' "Local-overlay note (downstream instantiation)" section describes: a consuming
repo instantiating the proposal **into its own recipe**. Where a proposal item is *purely* an OpenSpec/ECC
mechanism with no JarvanKB analog, the correct outcome may be **"does not map — note and skip"**, not a
forced port. Judge each item; record the mapping decision.

## 3. Per-issue translation guidance (your starting analysis — confirm in brainstorming)

**#3 codegraph code-map:**
- Add `code-map` (codegraph) as a **third Harness Enhancement method**, peer to `sendbox-protocol` +
  `cc-dashboard`: `CLAUDE.md §2` table + `longterm.md §5 Harness Enhancement Layer` (~line 200).
- Amend **Pipeline v2 step 1 (`RepoMem.read`)** to prefer codegraph for in-repo symbol/call-graph lookups
  over ad-hoc grep; **RepoMem stays the "why" layer** (codegraph = the map, RepoMem = the why).
- CLI fallback for sandboxed worktrees (`CODEGRAPH_NO_DAEMON=1 codegraph sync`) — **directly relevant**:
  JarvanKB leans on `using-git-worktrees`. Note per-worktree `codegraph init` cost.
- **Caveat that matters here:** codegraph's `callees`/`affected` are sparse on **dynamic Python**, and
  JarvanKB is heavily Python (Engine/Service/Skill are Python; only cookie-manager is Node). `query`/
  `callers`/`impact` are the strong commands. Factor this into how strongly you word "prefer codegraph".
- 🔒 **USER-GATED ENVIRONMENT CHANGE:** installing `npm i -g @colbymchenry/codegraph` and adding a
  `codegraph` server to `.mcp.json` touch the user's machine + session config. **Propose, do NOT execute
  without explicit user authorization** (surface it in brainstorming; it becomes a Dashboard user-action if
  approved). Existing `.mcp.json` already holds `tavily` (project-scoped, default-disabled) — codegraph would
  sit beside it. Doc-side wording can land regardless; the install is the gated part.

**#4 Lane Tiering:**
- The **concept is portable and valuable**: JarvanKB has the same fixed per-task doc tax (`temporary-<task>.md`
  + `RepoMem/temp/<slug>/` + `specs/`+`plans/`) on small changes. A `Lane: fast|full` structural axis (default
  `fast`) that governs *which doc artifacts exist* — orthogonal to the existing **procedural** auto-judge skip
  (`CLAUDE.md §3 step 2`) — is a clean fit.
- **But the document-set names are OpenSpec-specific** (`proposal.md`/`tasks.md`/`spec.md`/`design.md`/
  `00-INDEX`). Re-express "fast-lane doc set" in JarvanKB terms (e.g. fast lane = skip `RepoMem/temp/<slug>/`,
  a minimal `temporary-<task>.md`, brainstorming-`specs/` optional; full lane = today's full set). Define the
  selection rule (full if: touches deps / cross-package ≥2 of Engine|Service|Skill / Python↔Node boundary /
  produces a `RepoMem/persist/` asset / net-new public contract surface; else fast).
- `grill-with-docs` (#4 prop 4): **check whether that skill even exists in this environment.** It's tied to
  the ECC recipe's OpenSpec.propose→design.md→writing-plans gap. JarvanKB's analog is
  brainstorming→`specs/`→writing-plans. If the skill isn't available / the gap doesn't exist here, this item
  likely **"does not map — note and skip"**. Don't invent `CONTEXT.md`/`docs/adr/`.
- `00-INDEX` out-of-scope self-attestation table (#4 prop 3a): JarvanKB's no-content-duplication invariant is
  already **HITL-enforced at RepoMem.merge** (`CLAUDE.md §4`), so the "drop the per-task proof table" spirit
  may already hold — verify against current RepoMem temp practice, don't add ceremony.
- Translate the **invariant clauses** carefully into `CLAUDE.md §4`: single-identifier vacuous-satisfaction
  (fast lane → no `temp/<slug>/` → `<task>=<slug>` collapses to `<task>`, still satisfied), "absence-by-lane
  ≠ Skip-Mechanism skip" (no Auto-Skip Log needed), reversibility (`fast→full` mid-flight is cheap).
- **#4's promote-time codegraph de-dup rule** (prop 5) couples to #3 — only meaningful **if codegraph is
  adopted**: don't promote to RepoMem what codegraph can derive (symbol locations / call graphs / impact);
  `persist/architecture/` holds only the why. Land it in the RepoMem.merge promotion standard
  (`CLAUDE.md §3 step 8` + `longterm.md §Pipeline v2 step 8`) — but ONLY if #3 codegraph lands.

## 4. Propagation principle (g3-established — do NOT skip)

**A rule implers must FOLLOW lives in always-loaded `CLAUDE.md`, not only `longterm.md`** (new sessions don't
read longterm by default). So whatever Lane-selection rule + codegraph-preference you adopt MUST be reflected
in `CLAUDE.md` (the always-loaded contract), with full detail in `longterm.md`. Keep the two consistent and
**non-duplicative** (CLAUDE.md = compressed/authoritative-pointer; longterm = full). Cross-check every edit.

## 5. Is this "add-only" or a "Full Rewrite"? (judge + record)

`CLAUDE.md §4`: an active method never deactivates by stealth; recipe upgrades that *remove* require a Full
Rewrite. **Adding** codegraph as a new Harness Enhancement method and **adding** a Lane axis (default fast,
reversible, "NO layer removed" per #4's own invariants) read as **additive amendments**, not a Full Rewrite —
but **you make and record that determination** in your design/decisions, and if any adopted item turns out to
*remove or override* an existing v2 layer/step, STOP and escalate (blocker to root) rather than stealth-deactivate.

## 6. Inputs (minimum — re-fetch the rest as needed)

| Need | Path / command |
|---|---|
| The two proposals | `gh issue view {3,4} --repo JasonJarvan/CodeTeam --json body --jq '.body'` (JSON selector — plain view is broken) |
| Always-loaded contract you'll edit | `CLAUDE.md` (§1 identity/recipe, §2 methods table, §3 pipeline, §4 invariants) |
| Full governance detail you'll edit | `docs/HarnessStack/longterm.md` — **v2 section only** (`§Pipeline v2` ~L34, `§Local sendbox conventions`, `§Hard Invariants (v2)` ~L99, `§Full Rewrite Conditions`). **The block from ~L149 `# longterm.md` onward is the DEPRECATED v1 archive — DO NOT edit it.** |
| Recipe history / why OpenSpec was removed | `longterm.md §Recipe v1→v2 Migration` + `docs/RepoMem/persist/version-plan.md §Recipe version history` |
| Current MCP config | `.mcp.json` (tavily only; codegraph would be added here IF authorized) |
| Module memory (two layers on RepoMem.read) | global `docs/RepoMem/persist/` + (this is a root-level task; the "module" is HarnessStack governance itself) |
| Relationship to prior CodeTeam stream | Dashboard **UN-008** = review of CodeTeam #1/#2 (still open). #3/#4 are the next two; this task is their **local instantiation**. |

## 7. Pipeline / discipline for THIS task

- Run the v2 pipeline, **adapted for a docs/governance task**: `RepoMem.read` → **brainstorming WITH THE USER**
  (this is the key step — settle *which* proposal items to adopt as-is / adapt / defer / reject given §2, and
  *whether* to authorize codegraph install; the adoption decisions are the user's, surfaced by you) →
  writing-plans (a short plan listing each #3/#4 item → adopt/adapt/skip + target file+section) → edit →
  verification.
- **No TDD** (no code, unless codegraph `.mcp.json` is the only "code"). **Verification-before-completion** here
  = the two-pass review #4 itself prescribes: (a) cross-reference integrity (every CLAUDE.md rule has its
  longterm detail and vice-versa; no dangling pointers), (b) no semantic contradiction with existing v2
  invariants / pipeline / sendbox+dashboard layers / Skip Mechanism. `requesting-code-review` = a doc-consistency
  review (ask-first).
- **Step 8 RepoMem.merge** is yours to close (HITL). Most of this task's *output* IS the durable governance doc,
  so promotion is light — but record the design decisions (Dn) and the #3/#4 item-by-item mapping somewhere
  durable (module decisions or a persist note), and prune any temp.

## 8. Worktree / branch / commit discipline

- Worktree off the **local** `feat/agentcrawl-bootstrap` branch (NOT `origin/main` — loses local commits).
  `superpowers:using-git-worktrees`; base = current local branch. **Local commits only — no push / no merge to
  main.**
- **You edit `CLAUDE.md` + `longterm.md` — both shared, always-loaded.** Multiple sessions share the main tree;
  scope commits with explicit pathspec, expect "modified since read" → re-read + retry. **Do NOT touch** other
  sessions' in-flight files (SP-4b/5b/ZhihuArticle implers are active), `gstack`, or the Dashboard SP rows for
  other SPs.

## 9. Out of scope (do NOT do)

- Do NOT reintroduce OpenSpec (translate away from it; Full Rewrite needed to re-add — §2).
- Do NOT install codegraph or edit `.mcp.json` without **explicit user authorization** (§3, propose-first).
- Do NOT edit the upstream `harness-stack` template repo (not in this checkout) — local instantiation only.
- Do NOT edit the DEPRECATED v1 block of `longterm.md` (~L149+).
- Do NOT force-port an item that has no JarvanKB analog — "does not map, noted & skipped" is a valid outcome.
- Do NOT redo anyone else's RepoMem.merge; close only YOUR Step 8.

## 10. Convergence path (you report to ROOT)

- **Parent cwd (absolute):** `/home/shenzhou/Codes/awesome_agent_tools/Tools/JarvanKB/`
- **Done →** `docs/sendbox/toOrchestrator/from-harnessstackimpler-done.md` (milestone-done: per-item
  #3/#4 adopt/adapt/skip table w/ target file+section, the add-only-vs-Full-Rewrite determination, commit
  list, and — if codegraph was authorized — the install + `.mcp.json` state).
- **Blocked / a proposal item removes-or-overrides a v2 layer (§5) / user authorization needed mid-flight →**
  `docs/sendbox/toOrchestrator/from-harnessstackimpler-blocker-<topic>.md` (2–3 options + your pick; stop, wait).

## 11. Day-1 checklist

1. `RepoMem.read` (global persist) + read `CLAUDE.md` + `longterm.md` v2 section in full.
2. Fetch issues #3 + #4 (§1 command). Read §2 mismatch table; build your per-item mapping draft (§3).
3. **Brainstorm with the user** — adoption set + codegraph authorization (§7). This is the gate; don't edit first.
4. writing-plans (item → adopt/adapt/skip + target) → worktree → edit CLAUDE.md + longterm.md (consistent, §4).
5. verification (two-pass cross-ref + no-contradiction, §7) → finish branch (ask-first) → Step 8.
6. Report `from-harnessstackimpler-done.md` to `toOrchestrator/`.

— root orche g4 (2026-06-10)
