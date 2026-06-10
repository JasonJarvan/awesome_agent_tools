> from: HarnessStackImpler (task `harnessstack-codegraph-lanetiering`)
> recipient: root orchestrator g4
> type: milestone-done
> lifecycle: burn after read (per handoff)
> date: 2026-06-10

# Done — CodeTeam #3 + #4 instantiated into JarvanKB recipe v2

All edits merged to local `feat/agentcrawl-bootstrap` (no push, main untouched). Worktree removed, branch deleted, Step 8 closed (HITL zero-promotion + prune). Full mapping record: `docs/superpowers/specs/2026-06-10-harnessstack-codegraph-lanetiering-design.md`.

## User decisions (brainstorming gate, 2026-06-10)

- **U1** #3 full adoption — install codegraph now + `.mcp.json` entry.
- **U2** #4 Lane Tiering — adopt as translated.
- **U3** `Lane:` declared in **plan-doc frontmatter** (`temporary-<task>.md` has zero instances here and stays an optional recipe patch on both lanes; forcing it would add the tax #4 cuts).
- **U4 (mid-flight user directive)** `grill-with-docs` skill gap must be CLOSED, not skipped → authored as the first project-local skill, overriding my initial does-not-map draft.

## Per-item outcome

| Item | Verdict | Landed at |
|---|---|---|
| #3.1 code-map as Harness Enhancement method | adapt | `CLAUDE.md §2` row + **new** `longterm.md §Harness Enhancement Layer (v2)` |
| #3.2 install + MCP registration | adopt (U1) | codegraph **v0.9.9** installed (`npm i -g`, no sudo); `codegraph init` on main tree OK (**128 files: 99 py / 20 ts / 8 yaml / 1 js**); validated `codegraph query ZhihuFetchError` → exact span `Engine/zhihu/src/zhihu/errors.py:4`; `.mcp.json` += `codegraph` stdio server (**machine-local — `.mcp.json` is gitignored here**, snippet documented in longterm for replication); `.codegraph/` gitignored |
| #3.3 step-1 prefer-codegraph | adapt, weakened for dynamic Python (`query`/`callers`/`impact` strong; `callees`/`affected` sparse; grep fallback) | `CLAUDE.md §3.1` + `longterm.md` Pipeline v2 step 1 |
| #3.4 worktree CLI fallback | adapt | `longterm.md` Pipeline v2 step 5 |
| #4.1 `Lane: fast\|full` axis (default fast) + selection rule | adapt | `CLAUDE.md §3` Lane paragraph + **new** `longterm.md §Lane Tiering (v2)` |
| #4.2 fast-lane doc set | translate (plan doc = proposal/tasks analog; fast skips `temp/<slug>/`, specs optional) | same |
| #4.3a drop `00-INDEX` | does not map — skipped (never existed here; merge-HITL already enforces non-duplication) | recorded in spec + longterm §Not mapped |
| #4.3b collapsible design doc (`### Dn` list) | adapt (light) | `longterm.md §Lane Tiering (v2)` table |
| #4.4 grill-with-docs gate | **adopt-adapted (U4)** | `.claude/skills/grill-with-docs/SKILL.md` (RepoMem replaces ADR/CONTEXT.md as doc context; write-sinks → spec text / `### Dn` / `temp/<slug>/`; full-lane-only auto-judge, window draft-spec→writing-plans). Required `.gitignore` `!.claude/` re-include (repo-root gitignore blocks all `.claude/`); verified loaded — skill appears in session skill list post-merge |
| #4.5 promote-time codegraph de-dup | adapt (lands since #3 landed) | `CLAUDE.md §3.8` + `longterm.md` step-8 promotion standard |
| #4 invariant clauses | adapt (vacuous satisfaction / absence-by-lane ≠ skip / reversibility) | `CLAUDE.md §4` bullet + `longterm.md §Hard Invariants (v2)` |

## Add-only vs Full Rewrite (handoff §5)

**Additive amendment, NOT a Full Rewrite.** New method + new structural axis; default fast, reversible, no layer/step/gate removed or overridden. No escalation was needed.

## Commits (all local, `feat/agentcrawl-bootstrap`)

- `cd003b3` spec + plan + temp decisions
- `d638182` CLAUDE.md + longterm.md + `.gitignore` + grill-with-docs SKILL.md (merged via `ab6a71e`)
- `e39a464` Step-8 prune of `temp/harnessstack-codegraph-lanetiering/`
- (this letter + Dashboard UN-030→archive / UN-031 committed together with this file)

## Verification evidence (two-pass, handoff §7)

- **Pass A:** diff confined to v2 block — last hunk ends new-L190; v1 archive marker now at L197, untouched. All §-pointers resolve bidirectionally (CLAUDE.md×4, SKILL.md×1, spec path).
- **Pass B:** no contradiction with single-verification-gate (grill = optional design-time auto-judge, not a gate replacement), merge ordering, no-duplication, sendbox/dashboard layers, auto-judge skip wording, single identifier.

## Notes for root (for future handoffs)

1. **Stale pointer in your handoff:** "longterm.md §5 Harness Enhancement Layer ~L200" landed in the deprecated v1 archive; the v2 block had NO such section. I created `§Harness Enhancement Layer (v2)`. Future handoffs should cite the new section.
2. CLAUDE.md §2 now lists **5 active methods**; the v1→v2 migration table's "Active methods 5→4" is historical record, intentionally left as-is.
3. `.mcp.json` is gitignored (plaintext key) — codegraph MCP entry is machine-local; replication snippet lives in `§Harness Enhancement Layer (v2)`. User action UN-031 = approve the new MCP server next session (CLI already works regardless).
4. UN-008 (review CodeTeam #1/#2) remains open and untouched; #3/#4 local instantiation does not close it.

— HarnessStackImpler, 2026-06-10
