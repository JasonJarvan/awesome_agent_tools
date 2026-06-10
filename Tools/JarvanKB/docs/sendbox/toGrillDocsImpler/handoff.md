> from: root orchestrator generation 4 (Claude Opus 4.8 1M, active 2026-06-07 →)
> recipient: GrillDocsImpler (a new Claude Code peer session you are about to become)
> mode: child-handoff (sendbox-protocol Mode A — root stays alive; you converge back to `toOrchestrator/`)
> purpose: REPLACE the local adapted `grill-with-docs` skill with the community original (the CONTEXT.md
>   producer), reconcile the governance docs that referenced the adapted version, then RUN it in the project
>   root to produce JarvanKB's project-level `CONTEXT.md`
> lifecycle: burn after root reads your `from-grilldocsimpler-done.md`
> date: 2026-06-10

# Handoff — GrillDocsImpler (restore community grill-with-docs + produce CONTEXT.md)

## 0. What you are

You are a bounded **skill + governance + execution** impler, a **direct child of root orche g4** (skills +
HarnessStack governance are repo-global = root's domain). Root stays alive; you converge back to
`toOrchestrator/`. Task identifier: **`grill-with-docs-restore`**.

## 1. The user's decision (verbatim intent)

The user wants to **install the community/original `grill-with-docs`, REPLACE the current adapted semantics,
then RUN it** to create JarvanKB's project `CONTEXT.md`. This is a deliberate, user-ratified choice that
**partially reverts CodeTeam #4 proposal 4** (see §3). Do not relitigate the choice; do reconcile its
consequences cleanly.

## 2. Starting state — what's on disk right now (I verified this)

- `.claude/skills/grill-with-docs/SKILL.md` (44 lines) is the **ADAPTED** version authored by
  HarnessStackImpler on 2026-06-10 under mid-flight user directive U4. Its semantics are a **full-lane
  per-task DESIGN-REVIEW gate** that uses RepoMem as doc-context and **explicitly forbids creating
  `CONTEXT.md` / `docs/adr/`**. This is the version you are REPLACING.
- **No community grill-with-docs exists anywhere on the machine** — only the adapted one. It is **not** part
  of the installed `superpowers:` plugin (that plugin has brainstorming/executing-plans/… but no grill).
- **No `CONTEXT.md` exists** anywhere in the repo yet.
- `.gitignore` at repo root blocks all `.claude/`; HarnessStackImpler added a `!.claude/` re-include so the
  skill is tracked. Keep that working.

## 3. Governance reconciliation (the catch — handle, don't ignore)

The adapted grill-with-docs is **referenced as a design-review gate** in the always-loaded contract:
- `CLAUDE.md §3` (Lane paragraph / full-lane design-gate mention) and
- `docs/HarnessStack/longterm.md §Lane Tiering (v2)` (CodeTeam #4 prop 4: "full-lane-only auto-judge
  design-gate, window draft-spec→writing-plans").

Replacing the skill's semantics (design-gate → CONTEXT.md producer) makes those references **wrong**. You
must reconcile. **This is a brainstorming decision to settle WITH THE USER** (it changes always-loaded
governance):
- Option (a) **drop** the full-lane design-gate role entirely (grill-with-docs now solely = CONTEXT.md
  bootstrap); remove/rewrite the #4-prop-4 references in CLAUDE.md + longterm accordingly.
- Option (b) **preserve** the design-review function under a **different skill name** (e.g. `design-review`
  / `grill-design`) so #4 prop 4 survives, and free the name `grill-with-docs` for the community CONTEXT.md
  meaning.
- Either way: **a rule/skill must not deactivate by stealth** (`CLAUDE.md §4` add-only invariant). Whatever
  you change in always-loaded CLAUDE.md must stay consistent with longterm detail (propagation principle:
  rules implers follow live in CLAUDE.md, full detail in longterm). Record the decision (a `### Dn`).

## 4. The three deliverables

1. **Obtain the authentic community `grill-with-docs`.** The adapted SKILL.md credits "the community
   grill-with-docs (ADR/CONTEXT.md-based)". **First gate:** locate the genuine upstream source
   (web search / agentskills.io / the skill's origin repo). If you cannot identify the authentic source with
   confidence, **STOP and ask the user** (`from-grilldocsimpler-blocker-source.md` or a chat ask) — the user
   chose "install it", so they likely know the origin. Do **not** fabricate a "community" skill from memory
   and pass it off as the original.
2. **Replace** `.claude/skills/grill-with-docs/SKILL.md` with the community version (keep it tracked via the
   `!.claude/` re-include; if the community skill ships reference files, bring those too). Use
   `superpowers:writing-skills` discipline to install/verify it loads correctly (appears in the session skill
   list). Then do the §3 governance reconciliation.
3. **Run it** in the project root (`/home/shenzhou/Codes/awesome_agent_tools/Tools/JarvanKB/`) to produce
   **`CONTEXT.md`** — JarvanKB's project-level grilled context document. Place it where the community skill
   prescribes (likely repo/project root). Treat it as a **complement to RepoMem**, not a replacement (RepoMem
   stays the durable decision/gotcha memory; CONTEXT.md is the grilled project overview).

## 5. Inputs (minimum — re-fetch as needed)

| Need | Path / source |
|---|---|
| The skill you're replacing | `.claude/skills/grill-with-docs/SKILL.md` (read it to know exactly what semantics + references you're undoing) |
| Where grill-with-docs is referenced in governance | `CLAUDE.md` (§3 Lane paragraph) + `docs/HarnessStack/longterm.md §Lane Tiering (v2)` + the design record `docs/superpowers/specs/2026-06-10-harnessstack-codegraph-lanetiering-design.md` (HarnessStackImpler's mapping; documents the #4-prop-4 adaptation you're partially reverting) |
| Project context to grill against | global `docs/RepoMem/persist/` (architecture/memory/version-plan) + `CLAUDE.md` + `README.md` + module trees (Engine/Service/Skill) — and the user (grilling is interactive) |
| `.gitignore` mechanics | repo-root `.gitignore` blocks `.claude/`; the `!.claude/` re-include must keep the skill tracked |
| Community source | locate upstream (gate 4.1); the user chose "install" so confirm origin with them if unsure |

## 6. Pipeline / discipline

- v2 pipeline, adapted: `RepoMem.read` → **compressed brainstorm WITH THE USER** (settle: the authentic
  community source; the §3 reconciliation choice a-vs-b; where CONTEXT.md lives; whether CONTEXT.md content
  should avoid duplicating RepoMem) → install+replace skill (`writing-skills`) → reconcile governance docs →
  run grill → produce CONTEXT.md.
- **Verification-before-completion:** (a) the new skill loads (in session skill list) with community
  semantics; (b) CLAUDE.md ↔ longterm cross-references are consistent after the §3 edit (no dangling
  "design-gate" pointer if you chose 4.3-a; no stealth-deactivation); (c) `CONTEXT.md` exists and is grounded
  (cites real architecture, not hallucinated).
- **Step 8 RepoMem.merge** is yours (HITL). Record the semantic-replacement decision + the #4-prop-4
  reconciliation as `### Dn`. If CONTEXT.md content overlaps RepoMem, dedupe per the no-duplication invariant.

## 7. Worktree / branch / commit discipline

- Worktree off the **local** `feat/agentcrawl-bootstrap` branch (NOT `origin/main`). `using-git-worktrees`;
  base = current local branch.
- **Push is now ENABLED for `feat/agentcrawl-bootstrap` → origin** (user lifted the no-push invariant
  2026-06-10; see `version-plan.md §Compatibility`). Local commits + merge into local
  `feat/agentcrawl-bootstrap` as usual; **do NOT merge to main / rebase / touch the `gstack` submodule**
  without explicit user say-so. Pushing your branch work is fine but coordinate (the branch tracks origin).
- Multiple sessions share the main tree → scope commits with explicit pathspec; expect "modified since read"
  → re-read+retry. Don't touch other sessions' in-flight files (SP-4b/5b implers active) or `.claire/`.
- ⚠️ **`.mcp.json` is gitignored and holds a plaintext key** — never commit it. The repo is PUBLIC.

## 8. Out of scope (do NOT do)

- Do NOT fabricate a "community" skill from memory — locate the authentic source or ask (§4.1).
- Do NOT stealth-drop the #4-prop-4 design-gate — reconcile it explicitly per §3 (drop-with-record OR
  preserve-renamed), user-confirmed.
- Do NOT reintroduce OpenSpec; do NOT edit the deprecated v1 block of longterm.md.
- Do NOT redo anyone else's RepoMem.merge.

## 9. Convergence path (you report to ROOT)

- **Parent cwd (absolute):** `/home/shenzhou/Codes/awesome_agent_tools/Tools/JarvanKB/`
- **Done →** `docs/sendbox/toOrchestrator/from-grilldocsimpler-done.md` (what landed: community source used,
  skill replaced + loads, §3 reconciliation choice + governance edits, `CONTEXT.md` path + how it was
  grounded, Step-8 decisions, commit list).
- **Blocked (esp. can't identify the authentic community source) →**
  `docs/sendbox/toOrchestrator/from-grilldocsimpler-blocker-<topic>.md` (options + your pick; stop, wait).

## 10. Day-1 checklist

1. `RepoMem.read` (global persist) + read the current `.claude/skills/grill-with-docs/SKILL.md` + the
   CLAUDE.md/longterm references you'll reconcile (§3, §5).
2. Locate the authentic community grill-with-docs (gate 4.1) — confirm origin with the user if unsure.
3. Compressed brainstorm with the user: source + §3 reconciliation (a/b) + CONTEXT.md location/scope.
4. Worktree → install+replace skill (`writing-skills`, verify loads) → reconcile CLAUDE.md+longterm.
5. Run grill → produce `CONTEXT.md`. Verification (§6). Finish branch (ask-first) → Step 8.
6. Report `from-grilldocsimpler-done.md` to `toOrchestrator/`.

— root orche g4 (2026-06-10)
