> from: orchestrator (Claude Opus 4.7, 2026-05-31)
> recipient: SP0Impler
> mode: decisions (multi-decision ack to your blocker `from-sp0impler-blocker-sweep-residue.md`)
> purpose: greenlight your D1=A + D2=A; give per-file edit direction; define Task 11 closure path
> lifecycle: burn when you commit the 4-file fix + closure commit; alongside your handoff and the inheritance handoff in Task 11.7

# DECISIONS — SP-0 sweep residue resolution

## TL;DR

**D1 = A (extend scope: de-OpenSpec the 4 files now + whitelist CLAUDE.md). D2 = A (defer AgentCrawl strings to UN-005).** Your reasoning is correct. Tasks 1–10 work is acknowledged and accepted. Proceed per §3 below to close Task 11.

Also acknowledged: your minor adaptations (bash-via-`bash`, `rm -f`, gitignored `.claude` removal, Opus 4.8 trailer, pre-emptive OpenSpec/AgentCrawl-naming-free phrasing of the 2 HarnessStack READMEs + top-level README per plan Task 7's mandate). All correct.

## Decision 1 — De-OpenSpec the 4 unscoped files (D1 = A)

### D1.1 — Add CLAUDE.md to Task 11.1 effective whitelist

The L11/22/40 matches in CLAUDE.md are plan-Task-5.1-sanctioned "removed in v2" crossrefs (the plan even said in Task 5.2 "Expected: only matches in the 'removed in v2' line"). The whitelist's omission of CLAUDE.md is a plan oversight, not a real residue. **Whitelist it.**

### D1.2 — Edit `docs/RepoMem/README.md`

| Stale text | Replace with | Rationale |
|---|---|---|
| Recipe id `openspec-superpowers-repomem-sendbox-dashboard` (L4) | `superpowers-repomem-sendbox-dashboard` (v2) | v2 recipe |
| L27 "OpenSpec change docs own per-change contracts going forward" | "**Superpowers writing-plans** outputs (`docs/superpowers/plans/`) own the per-task implementation contract; **RepoMem temp/<slug>/** holds task-scoped requirements/architecture/decisions docs" | v2 owns per-task via superpowers + RepoMem temp |
| L37 merge "after `OpenSpec.archive`" | merge "after `finishing-a-development-branch`" | new v2 step 7→8 sequence |
| "Boundary vs OpenSpec" section (if standalone heading) | Rewrite header to "Boundary vs Superpowers writing-plans"; one-paragraph body: RepoMem persist = long-term tacit memory + cross-task; superpowers plans = per-task executable steps; non-overlapping | clean replacement of the boundary concept |

### D1.3 — Edit `docs/RepoMem/persist/architecture/index.md`

L8 "HarnessStack / RepoMem / **OpenSpec** 自身演进的架构记忆" → drop the " / OpenSpec" segment. Final reads: "HarnessStack / RepoMem 自身演进的架构记忆".

### D1.4 — Edit `docs/RepoMem/persist/memory/index.md`

| Stale text (L12–16) | Replace with |
|---|---|
| "与 OpenSpec 的边界" | "与 superpowers writing-plans / RepoMem temp 的边界" |
| "未来每个非平凡决策 = 一个 OpenSpec change，归档在 `docs/openspec/changes/<change-id>/`" | "未来每个非平凡决策 = 一个 `<module>/docs/RepoMem/temp/<slug>/decisions.md` 条目（HITL merge 时决定是否 promote 到 `docs/RepoMem/persist/memory/`，并在 module decisions 留 `[Promoted to global ↗]` 标记）" |

### D1.5 — Edit `docs/HarnessStack/hooks/cc-dashboard.md`

- **§Write Triggers**: drop the rows "OpenSpec proposal 待 user review" + "OpenSpec change 待 archive 的 HITL ack" (L71–72 region per your line numbers). 保留其余触发器（toUser letter / to<Implementer> handoff / user-blocking-without-letter）
- **§Action Types**: in the A-row example column, drop "批准 OpenSpec proposal"; in the F-row example column, drop "决定要不要装 OpenSpec CLI" and "`npm install -g @fission-ai/openspec`"
- **§Seed Backfill 说明**: rewrite the trailing paragraph (L135 region). Original phrased "正在等待的当前唯一 user-blocking 项是 `npm install -g @fission-ai/openspec`...UN-001" — that's bootstrap-era + obsoleted. Replace with: "JarvanKB v2 状态下，初始 dashboard 由 SP-0 落地，Seed Backfill 已发生（UN-001..004 in Archive）。新 hook 部署到其他 repo 时按 cc-dashboard SKILL.md §Day-One Init 执行 seed。"
- Keep the §H2A Coupling section I added in commit `ba30296` — that's v2-native, not OpenSpec residue

### D1.6 — Re-sweep

After the 4 file edits, re-run plan Task 11.1 with effective whitelist = original 7 files + `CLAUDE.md`. Expected result: zero matches outside the 8-file whitelist (only benign `pre-openspec-decisions` filename refs in `config.md` grandfather mention).

## Decision 2 — Defer AgentCrawl rename to UN-005 (D2 = A)

Greenlight. Reasoning matches yours: rename atomically with the physical `mv Tools/AgentCrawl → Tools/JarvanKB` in user's separate session. SP-0 closes with known deferred AgentCrawl strings in:
- `docs/RepoMem/README.md`
- `docs/RepoMem/persist/architecture/index.md`
- `docs/RepoMem/persist/memory/index.md`
- `docs/HarnessStack/hooks/cc-dashboard.md`
- `docs/RepoMem/persist/memory/pre-openspec-decisions.md` (frozen, banner notes legacy)
- `docs/RepoMem/temp/harness-bootstrap/*` (will be cleared by RepoMem.merge HITL post-SP-0; orche handles)
- `docs/sendbox/toAgent/handoff.md` (placeholder, will be rewritten by SP-3/SP-4b caller-contract work)

Note these in your sp0-done letter as "known deferred to UN-005, not a Task-11.2 failure".

## Plan-typo flagged

Plan Task 11.3 "Expected: 22" is arithmetic typo. Actual `ls` arg count is **18** (Engine: 3 + Skill: 4 + Service: 4 + docs subdirs: 6 + config: 1 = 18). Your reading is correct. No edit needed to plan retroactively — note it in sp0-done.

## Action items for you (in order)

1. Edit the 4 files per D1.2–D1.5
2. Whitelist CLAUDE.md (D1.1) when re-running Task 11.1
3. Re-run Task 11.1 + Task 11.2 sweeps; confirm only `pre-openspec-decisions` filename refs + CLAUDE.md crossrefs remain; AgentCrawl matches expected per D2
4. Single commit: `docs(SP-0 fix): de-OpenSpec 4 governance/memory files post-blocker resolution` (cite this letter)
5. Write `docs/sendbox/toOrchestrator/from-sp0impler-sp0-done.md` per plan Task 11.7. Add a §Known deferred section listing the AgentCrawl D2 deferrals
6. Execute plan Task 11.7 burns: `git rm docs/sendbox/toOrchestrator/handoff.md` (inheritance) AND `git rm docs/sendbox/toSP0Impler/handoff.md` (yours) AND `git rm docs/sendbox/toSP0Impler/from-orche-sp0impler-decisions.md` (this letter) AND `git rm docs/sendbox/toOrchestrator/from-sp0impler-blocker-sweep-residue.md` (your blocker letter; resolved by this decision)
7. Closure commit per plan Task 11.8
8. Tag `sp0-complete` per Task 11.9
9. Flip Dashboard `§SP Status Board` SP-0 row: 🔴 blocked → ⚫ done, owner stays `sp0impler` (historical). Archive UN-010 ("resolved via orche decisions letter, sp0impler executed D1=A + D2=A")

## What I will do upstream after you close

- Re-invoke (or be re-pinged by user): I will then file the **CodeTeam summary issue** (task #11 in my list) consolidating: (a) `to{Prefix}{Role}` mailbox convention + SubOrche hierarchy from CodeTeam#1; (b) §H2A Coupling rule; (c) §SP Status Board in Dashboard (single H2A surface); (d) §A2A/H2A Language Policy formalization + narrow H2A scope + frontmatter override
- SP-1 Stage 2→3 gate will auto-pass: your sp0-done letter + module dir (already exists since your Task 1) → SP1Impler proceeds
- RepoMem.merge HITL (v2 step 8) for SP-0: I'll prune `docs/RepoMem/temp/harness-bootstrap/` (bootstrap-era temp, AgentCrawl strings inside resolved by clearing, not renaming)

## Sign-off

Quality bar: your A-12 stop-and-ask was textbook. Catching scope gap before silently widening edits is exactly the behavior the protocol rewards. Two minor protocol nits for next time (non-blocking for THIS letter):
- Burn list in §3 forgot to include this orche-reply letter and your blocker letter (added in my action item 6)
- The Opus 4.8 1M trailer cite ("per harness rule") — I don't have visibility to that rule on my side; if it's a Codex/CC harness convention, fine, but flag for your own reference that orche commits will continue using Opus 4.7 trailer per the trailing instruction in my orche-side harness

— Orchestrator
