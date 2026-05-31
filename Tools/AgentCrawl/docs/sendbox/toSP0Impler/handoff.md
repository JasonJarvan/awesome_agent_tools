> from: orchestrator session (Claude Opus 4.7, 2026-05-31)
> recipient: SP0Impler (a Claude Code peer session in same cwd)
> mode: child-handoff
> purpose: execute SP-0 implementation plan task-by-task, commit per task, converge with a milestone-done letter
> lifecycle: burn after impler writes `from-sp0impler-sp0-done.md` and orche reads it

# SP-0 Handoff — JarvanKB skeleton + HarnessStack v2 migration

## 0. What this letter is

A **child-handoff** under the sendbox-protocol (see `~/.claude/skills/sendbox-protocol/SKILL.md` §Handoff modes). You are a peer Claude Code session, **not** an in-process subagent — the orchestrator stays alive while you run. When you finish or get stuck, you converge back via the sendbox path defined in §3 below.

## 1. Subtask scope

Execute the **SP-0 implementation plan** end-to-end:

- **Plan file (contract, do not modify)**: `docs/superpowers/plans/2026-05-31-SP-0-jarvankb-skeleton.md`
- 11 tasks, ~10 atomic commits, all on the current branch `feat/agentcrawl-bootstrap`
- Each task has bite-sized steps with exact bash / sed / Write commands — follow them as written; if a command produces unexpected output, STOP at that step and write a blocker letter (see §3)

**Success criteria** (verbatim from plan §Self-Review §1):

1. Zero references to `openspec` / `OpenSpec` / `change-id` / `/opsx:` outside the explicitly whitelisted historical files (plan §Task 11 Step 11.1 gives the whitelist)
2. All 10 sub-project skeleton directories exist with their 5 stub files each + Skill/router/README.md placeholder (plan §Task 1 Step 1.7 expects 51 stub .md files)
3. `Engine/common/src/llm_client.py` loadable (`LLMClient` class instantiable; method bodies correctly raise NotImplementedError)
4. `CLAUDE.md` shows recipe v2 + 8-step pipeline on top
5. `from-sp0impler-sp0-done.md` written to the orchestrator's inbox (path in §3)

## 2. Inputs (minimum set — do NOT load anything else)

| File | Role |
|---|---|
| `docs/superpowers/plans/2026-05-31-SP-0-jarvankb-skeleton.md` | **The plan you execute** — your contract |
| `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` | Reference for *why* — open only if a plan step's intent is unclear |
| `CLAUDE.md` (current state) | Read before Task 5 to see what you are replacing |
| `docs/HarnessStack/longterm.md` (current state) | Read before Task 6 to know the structure you are prepending into |
| `docs/RepoMem/persist/memory/runbook.md` (current state) | Read before Task 8 Step 8.3 to identify §0 block to remove |

**Do NOT** read the rest of `docs/RepoMem/persist/`, `docs/HarnessStack/_toUser/`, or `docs/sendbox/toOrchestrator/handoff.md` (the orche inheritance letter). The plan + design are sufficient context for this subtask.

## 3. Convergence paths

**Parent's (= orchestrator's) cwd (absolute path)**: `/home/shenzhou/Codes/awesome_agent_tools/Tools/AgentCrawl/`
(You are in the same cwd; relative paths work too. Absolute included per cc-sendbox §Cross-cwd write in case you spawn helpers.)

| When | Where you write |
|---|---|
| **Done** (all 11 tasks committed, self-review §11 grep sweeps clean) | `docs/sendbox/toOrchestrator/from-sp0impler-sp0-done.md` |
| **Blocker** (A-12 stop-and-ask — see cc-sendbox §A-12 pattern) | `docs/sendbox/toOrchestrator/from-sp0impler-blocker-<topic>.md` |
| **Plan-ready** (not applicable — plan already exists; do NOT re-plan) | N/A — execute the plan, don't replan |
| **Decisions** (mid-execution decisions you need orche to ack before proceeding) | `docs/sendbox/toOrchestrator/from-sp0impler-decisions.md` (numbered list, options table per decision) |

**HITL gates inside the plan** that you MUST stop at and write a blocker letter for, even if you think you know the answer:

- **Task 3 Step 3.1**: if `find docs/openspec -type f` returns any files. Plan says STOP, escalate. Honor it.
- **Task 7 Step 7.2 / 7.3**: if `sed` substitutions leave orphan OpenSpec paragraphs that the plan's "fix with Edit" guidance doesn't cleanly handle and you can't determine the intended replacement.
- **Task 11 Step 11.1 / 11.2**: if grep sweep finds unexpected matches not covered by the whitelist.

For each blocker letter follow cc-sendbox §A-12 structure: TL;DR / Timeline / Mismatch core / Options table / Tentative pick / Current snapshot. **Don't be neutral** — state your tentative pick.

## 4. Out-of-scope (forbidden actions)

You MUST NOT:

- **Modify `design.md` or `plan.md`** — they are the contract. If either is wrong, write a blocker letter instead of editing.
- Touch anything for SP-1 through SP-7 beyond the stub README files Task 1 generates. **Do not** implement CookieManager, Zhihu engine, BiliNote client, etc. The plan's Task 1 stubs are intentionally placeholder-only.
- `git merge` to `main` or any other branch. Stay on `feat/agentcrawl-bootstrap`.
- Run `git push` to remote. Local commits only.
- `git rebase` or rewrite committed history.
- Run `npm uninstall -g @fission-ai/openspec` — design §6.5 marks that as a user-decision, plan says "suggest to user; not in plan".
- Run `mv Tools/AgentCrawl Tools/JarvanKB` — that physical rename is **UN-005** on the dashboard, executed by user in a separate session.
- Implement the LLMClient body (Task 2 stubs `raise NotImplementedError` — keep them as such).
- Spawn your own subagents via the Agent tool unless a blocker letter explicitly returns a subagent-driven instruction from orche.
- Edit `docs/sendbox/toOrchestrator/handoff.md` (the inheritance letter from bootstrap). Plan Task 11 Step 11.7 handles its removal correctly via `git rm`.

You MAY:

- Run `git status`, `git log`, `git diff`, `ls`, `find`, `grep` freely as reconnaissance
- Skip explanation steps (the plan documents *why*; you just execute)
- Use TaskCreate / TaskUpdate to track your own progress through the 11 tasks if helpful (your task list is independent from orche's)

## 5. Branch + worktree state at handoff

- Branch: `feat/agentcrawl-bootstrap` of the parent repo `awesome_agent_tools`
- HEAD: `97d760b docs(SP-0): implementation plan` (the commit that landed the plan you are executing)
- Above that: `2d2ef3d docs(SP-0): JarvanKB skeleton + HarnessStack v2 design`
- Submodule `gstack` shows `M` in `git status` — **pre-existing, unrelated, do NOT touch**
- Working tree otherwise clean

## 6. Reporting cadence

This is a single-handoff letter. **You do not need to send progress letters** while executing — orche will see the commits stream in via `git log`. Only write to the orchestrator inbox if:

- You hit a blocker (§3)
- You need a decision (§3 "Decisions" path)
- You finish (§3 "Done" path)

User-facing surface: if you genuinely need the user's eyeballs (e.g. ambiguous sed orphan you can't reasonably resolve), prefer a sendbox blocker letter so orche routes it. Direct chat with user is fine for clarifying questions about the plan's intent that don't require an orche decision.

## 7. Lifecycle of this letter

`burn` after you write `from-sp0impler-sp0-done.md` and orchestrator reads it. The plan's Task 11 Step 11.7–11.8 handle:
- Writing `from-orche-sp0-done.md` (note: rename appropriately to `from-sp0impler-sp0-done.md` since YOU are the author, not orche — minor correction to the plan text, take it)
- `git rm`-ing the old inheritance handoff (`docs/sendbox/toOrchestrator/handoff.md`)
- This handoff letter (`docs/sendbox/toSP0Impler/handoff.md`) — also `git rm` it as part of Task 11.7 alongside the inheritance letter (the plan didn't mention this letter because it didn't exist when the plan was written; **take this addition as authorized**)

After your commit chain ends with the burn of both letters, orche will be re-invoked by the user (or you ping in chat) to start SP-1 brainstorming.

---

**Begin execution at plan §Task 1 Step 1.1.**
