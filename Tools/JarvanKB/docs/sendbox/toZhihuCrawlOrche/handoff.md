> from: orchestrator generation 3 (root, Claude Opus 4.8 1M, active 2026-05-31 →)
> recipient: ZhihuCrawlOrche (a Claude Code peer session — a SUB-orchestrator)
> mode: child-handoff (sendbox-protocol Mode A — root orche stays alive; you converge back)
> purpose: delegate the entire Zhihu downstream vertical to you as its sub-orchestrator
> lifecycle: burn after you write `from-zhihucrawlorche-vertical-done.md` (SP-3 + SP-5a both merged) and root reads it

# Handoff — ZhihuCrawl Sub-Orchestrator

## 0. What you are

You are a **sub-orchestrator** (SubOrche) under the root orchestrator (g3). Root stays alive and runs the
**Bilibili vertical + governance**; you own the **Zhihu downstream vertical** end-to-end. This is the
`Root Orche → SubOrche → Impler` hierarchy from `longterm.md` §Local sendbox conventions (you are the
`toZhihuCrawlOrche` example made real).

You do **not** write engine/skill code yourself. You **orchestrate**: spawn + coordinate the implers below
you, review their plans, greenlight, handle blockers, and report vertical completion back to root.

## 1. Scope — the Zhihu downstream vertical

Three SPs, all downstream of **SP-2 Zhihu Engine (done, merged `f8c14cb`)**:

| SP | Path | What | Status / gate |
|---|---|---|---|
| **SP-3** Zhihu Skill | `Skill/crawl/zhihu-crawl/` | URL → call SP-2 engine → ask save path + auto-classify (`vague_path`) | ready now (only dep = SP-2 ✓) |
| **SP-5a** Zhihu Watcher | `Service/crawl/zhihu-watcher/` | favorites polling (default 30–60 min), high-watermark `created` stamp, calls SP-2 engine | ready now (only dep = SP-2 ✓) |
| **v1.1** Comment full-tree | (extends `Engine/zhihu/`) | exhaustive child-reply pagination; handoff already drafted at `docs/sendbox/toZhihuCommentImpler/handoff.md` | **do NOT start** until the user greenlights it (per their priority it ranks above image-dedup, but timing is the user's) |

**SP-3 and SP-5a are independent** (neither depends on the other) → run their implers **in parallel**.

## 2. How you orchestrate (the SubOrche playbook)

Per the v2 pipeline + sendbox-protocol (invoke the `sendbox-protocol` skill):

1. **Spawn each impler** by writing a Mode-A child-handoff: `docs/sendbox/toSP3Impler/handoff.md` and
   `docs/sendbox/toSP5aImpler/handoff.md`. Model them on the structure of *this* letter and on the engine
   handoffs in git history (`toSP2Impler/`, `toSP4aImpler/` — the latter is still live, read it as a template).
   Each impler runs the full v2 8-step pipeline (brainstorming compressed/auto-judge → design → plan →
   worktree+TDD+subagent-driven → verify → finish → **its own Step 8 merge**).
2. **Mailboxes** (per-task, hard invariant): implers report to **YOUR** inbox `docs/sendbox/toZhihuCrawlOrche/`
   as `from-sp3impler-*.md` / `from-sp5aimpler-*.md` (plan-ready / blocker / done). You reply into
   `toSP3Impler/` / `toSP5aImpler/`.
3. **Review their plan-ready** against SP-0 §7 (rows below) + the engine contract; greenlight.
4. **Each impler OWNS its own `RepoMem.merge` closure** (CLAUDE.md §3 step 8 + §4 — the v2 rule; do NOT
   tell them "merge is the orche's job"). Apply the **promotion standard** (`longterm.md` §Pipeline v2 step 8):
   cross-SP-reusable gotchas go to global persist; mechanism stays in code.
5. **Add Dashboard rows** for the impler sessions the user must open (Type B), and update the SP Status
   Board SP-3 / SP-5a rows (owner → sp3impler / sp5aimpler; status per stage).
6. **Converge to root**: when SP-3 **and** SP-5a are both merged + their sendbox chains cleaned, write
   `docs/sendbox/toOrchestrator/from-zhihucrawlorche-vertical-done.md` (a milestone-done roll-up). That
   ends your role; root burns this handoff.
7. **Escalate to root** (`from-zhihucrawlorche-blocker-<topic>.md` → `toOrchestrator/`) only for
   cross-vertical / governance issues you can't resolve within the Zhihu vertical.

## 3. Per-SP scope (from SP-0 design §7 — authoritative)

**SP-3 Zhihu Skill** (`Skill/crawl/zhihu-crawl/`, type=skill):
- URL → calls the **frozen SP-2 engine contract** `Engine/zhihu/docs/interface.md` (`fetch(url, cookies, ...)`
  → `FetchResult` / `.to_markdown()`) → asks the user a save path + **auto-classifies** when the path is
  vague (`vague_path`).
- **First real `Engine/common` LLMClient implementation likely lands here** (SP-0 §8: "first real impl with
  SP-3 or SP-6"). The skill uses LLMClient for the vague-path classification. Confirm in brainstorming
  whether SP-3 implements the LLMClient body or stubs remain — coordinate so SP-6 doesn't redo it.
- Cookie: the skill **fetches** Zhihu cookies from SP-1 cookie-manager
  (`Service/crawl/cookie-manager/docs/interface.md`, domain `.zhihu.com`) and **injects** them into the
  engine's `fetch(cookies=...)`. (The engine is a pure consumer — it never fetches cookies.)

**SP-5a Zhihu Watcher** (`Service/crawl/zhihu-watcher/`, type=service):
- Polls the user's Zhihu favorites folder on a schedule (default 30–60 min), keeps a **high-watermark on
  `created`**, and on new items calls the SP-2 engine (cookies injected from SP-1).
- ⚠️ **SP-5a MUST read `docs/RepoMem/persist/architecture/crawl-pipeline.md` §知乎链路 first** — it holds
  the SP-2 root-causes/gotchas promoted globally *specifically so SP-5a (running in `Service/crawl/
  zhihu-watcher/` cwd) sees them*: `comment_v5` offset-poison (use cursor paging), `js-initialData`
  camelCase vs `/api/v4` snake_case, no zse-96 signing needed, Zhihu direct-connect (`trust_env=False`).
  This is the whole point of the layered-read promotion standard — make the watcher impler read it.

## 4. Inputs you (and your implers) need

| Resource | Role |
|---|---|
| `CLAUDE.md` §2/§3/§4 | governance + invariants (note §3 step 8 + §4: **impler owns merge closure**; promotion standard) |
| `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` §7 (SP-3/SP-5a rows) + §8 (LLMClient) | authoritative scope |
| `Engine/zhihu/docs/interface.md` | **frozen SP-2 engine contract** both implers program against |
| `docs/RepoMem/persist/architecture/crawl-pipeline.md` §知乎链路 | promoted Zhihu gotchas (SP-5a must-read) |
| `Service/crawl/cookie-manager/docs/interface.md` + `architecture/credentials.md` | Zhihu cookie integration (`.zhihu.com`) |
| `Engine/common/docs/interface.md` | LLMClient contract (SP-3 may implement its body) |
| `~/.claude/skills/{sendbox-protocol,repo-mem,superpowers/*}` | the protocols you operate under |
| git history `toSP2Impler/` (burned) + live `toSP4aImpler/handoff.md` | impler-handoff templates |

## 5. Out-of-scope (forbidden)
- The Bilibili vertical (SP-4a/4b/5b) and any other SP outside Zhihu downstream — root owns those.
- Editing `CLAUDE.md` / `docs/HarnessStack/` / `docs/RepoMem/persist/` directly (governance is root's;
  module decisions + impler Step-8 merges handle persist promotion via HITL).
- Starting the v1.1 comment-tree before the user greenlights it.
- `git push` / merge to `main` / rebase — **local commits only** on `feat/agentcrawl-bootstrap`.
- Writing engine/skill code yourself — you orchestrate; implers implement.

## 6. Env / state at handoff
- Branch `feat/agentcrawl-bootstrap`; tree clean (only `gstack` submodule `M` — **never touch**).
- Concurrent sessions sharing the main tree: **root orche**, **SP4aImpler** (Bilibili, active), and the
  implers you'll spawn. Tell each impler to create its **own worktree** at Stage 3, and commit with its
  own prefix (`docs(SP-3):` / `feat(SP-3):`, `docs(SP-5a):` / `feat(SP-5a):`) to limit shared-index races.

## 7. Lifecycle of this letter
`burn` after you write `from-zhihucrawlorche-vertical-done.md` (SP-3 + SP-5a both merged) and root reads it.

## 8. First actions when you boot
1. `pwd` (confirm repo root) + `git log --oneline -5`.
2. Read §3/§4 inputs (top: CLAUDE.md §3/§4, SP-0 §7 SP-3/SP-5a, `Engine/zhihu/docs/interface.md`, crawl-pipeline.md §知乎链路).
3. Brainstorm scope with the user (compressed) per SP, then write `toSP3Impler/handoff.md` + `toSP5aImpler/handoff.md`.
4. Add Dashboard Type-B rows (open SP3Impler + SP5aImpler sessions) + flip SP Status Board SP-3/SP-5a → wip.
5. Reply to the user in chat: "ZhihuCrawl SubOrche ready; spawning SP-3 + SP-5a."

— root orche g3
