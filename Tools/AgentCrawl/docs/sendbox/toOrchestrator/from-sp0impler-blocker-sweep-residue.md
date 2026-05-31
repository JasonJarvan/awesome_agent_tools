> from: SP0Impler session (Claude Opus 4.8 1M, 2026-05-31)
> recipient: orchestrator
> mode: blocker (A-12 stop-and-ask)
> purpose: plan Task 11.1/11.2 final grep sweeps hit stale OpenSpec (and pervasive AgentCrawl) matches in files NO SP-0 task scoped and the whitelist doesn't cover → success criterion #1 unachievable without a scope decision
> lifecycle: burn after orche acks (greenlight/decision) and impler resumes Task 11 closure

# BLOCKER — SP-0 final sweep residue (Task 11.1 / 11.2 HITL gate)

## TL;DR

Tasks 1–10 are **done + committed + verified** (10 commits, `8b91d9c`→`bee65f0`). Task 11 structural checks (11.3 dir tree, 11.4 removed paths, 11.5 CLAUDE v2) **pass**. But the **Task 11.1 OpenSpec grep sweep is NOT clean**: four governance/memory files still describe OpenSpec as the *active* spec layer, and **none of them is in any SP-0 task's File-Structure list, nor in the Task 11.1 whitelist**. So plan success-criterion #1 ("zero OpenSpec refs outside the whitelist") cannot pass by executing the plan as written. Per your handoff §3 ("Task 11.1/11.2 unexpected matches → MUST stop and write a blocker letter, even if you think you know the answer"), I stopped before writing the done-letter / burning handoffs / tagging.

I need a **scope decision**, not a mechanical fix. My tentative pick is **D1=A (fix the 4 files now) + D2=A (defer AgentCrawl strings to UN-005)** — details below.

## Timeline

1. Executed Tasks 1–10 verbatim (with documented minor adaptations: bash-via-`bash` for the zsh shell; `rm -f` for the `rm -i` alias; `.claude/` removal is filesystem-only since it's gitignored; commit trailer = Opus 4.8 per harness rule; the two HarnessStack READMEs + top-level README phrased OpenSpec/AgentCrawl-name-free since they're not in the 11.1/11.2 whitelist).
2. Ran Task 11.1 OpenSpec sweep with the plan's 7-file whitelist.
3. Filtered the raw output by (a) benign `pre-openspec-decisions` *filename* references and (b) the two handoff letters slated for deletion in 11.7.
4. Residue remained — in files the plan never touched. → this letter.

## Mismatch core

**The plan's task list under-scoped the migration.** Plan §"Modified" (lines 34–44) lists `config.md`, `version-plan.md`, `runbook.md`, `pre-openspec-decisions.md`, `CLAUDE.md`, the two HarnessStack READMEs, and `Dashboard/index.md`. It does **not** list these, which still carry live OpenSpec semantics:

| File | Stale content (sample) | In any task? | In 11.1 whitelist? |
|---|---|---|---|
| `docs/RepoMem/README.md` | recipe id `openspec-superpowers-...` (L4); "Boundary vs OpenSpec"; "OpenSpec change docs own per-change contracts **going forward**" (L27); merge "after `OpenSpec.archive`" (L37) | ❌ | ❌ |
| `docs/RepoMem/persist/architecture/index.md` | "HarnessStack / RepoMem / **OpenSpec** 自身演进的架构记忆" (L8) | ❌ | ❌ |
| `docs/RepoMem/persist/memory/index.md` | "与 OpenSpec 的边界"; "**未来每个非平凡决策 = 一个 OpenSpec change**，归档在 `docs/openspec/changes/<change-id>/`" (L12–16) | ❌ | ❌ |
| `docs/HarnessStack/hooks/cc-dashboard.md` | OpenSpec proposal/archive HITL write-triggers (L15,71,72); "决定要不要装 OpenSpec CLI" (L56); "`npm install -g @fission-ai/openspec`" (L61,135) | partially (you touched it in `ba30296` for H2A coupling, but not de-OpenSpec'd) | ❌ |

Two more categories that are **NOT genuine problems** (calling them out so we agree they're fine):
- `CLAUDE.md` L11/22/40 — these are the **intended** "removed in v2" crossrefs that plan Task 5.1 *wrote* and Task 5.2 *sanctions* ("Expected: only matches in the 'removed in v2' line"). The whitelist simply omitted CLAUDE.md.
- `config.md` L23 — a benign reference to the filename `pre-openspec-decisions.md` (a whitelisted historical file) inside the grandfather list.

Separately, **Task 11.2 (AgentCrawl)** is dirty across many non-whitelisted files (`RepoMem/README.md`, `architecture/index.md`, `memory/index.md`, `cc-dashboard.md`, `sendbox/toAgent/handoff.md`, `temp/harness-bootstrap/*`, `pre-openspec-decisions.md`). Note: AgentCrawl is **not** one of your §1 success criteria (#1 is OpenSpec-only) — and the physical rename `Tools/AgentCrawl → Tools/JarvanKB` is **UN-005**, still open, in a separate session.

## Options

### Decision 1 — OpenSpec residue in the 4 unscoped files (this is what blocks criterion #1)

| # | Option | Effect | Cost |
|---|---|---|---|
| **A** ⭐ | **Extend SP-0 scope: de-OpenSpec the 4 files to v2 now** (targeted edits: drop v1 recipe id, rewrite "OpenSpec change" boundary → "superpowers writing-plans / RepoMem", drop OpenSpec install/triggers from the hook) **+ add `CLAUDE.md` to the 11.1 whitelist** | criterion #1 passes; v2 docs internally consistent | ~30 min, 4 small edits, 1 extra commit |
| B | Grandfather the 4 files + CLAUDE.md into the whitelist; defer rewrite to a later cleanup | fast close | leaves "OpenSpec is the active spec layer" docs contradicting the v2 recipe — future sessions reading `RepoMem/README.md` / `memory/index.md` get wrong guidance |
| C | Close SP-0 now with a documented known-gap; spin a follow-up task (`sp0-doc-residue`) | unblocks SP-1 Stage 3 fastest | criterion #1 explicitly *not* met at SP-0 close |

### Decision 2 — AgentCrawl strings (secondary; not a §1 criterion)

| # | Option | Effect |
|---|---|---|
| **A** ⭐ | **Defer to UN-005**: do the repo-wide `AgentCrawl → JarvanKB` string sweep atomically *with* the physical dir rename, so paths (`Tools/AgentCrawl/...`) update consistently in one commit | avoids half-renamed string state; rename is one logical change |
| B | Sweep AgentCrawl strings now (SP-0), separately from the dir rename | risk: strings say JarvanKB while the dir is still `Tools/AgentCrawl/` until UN-005 |

## Tentative pick (not neutral)

**D1 = A, D2 = A.** Rationale: (1) The four stale files genuinely contradict the v2 recipe — leaving them is a correctness problem for any future session loading RepoMem/hook docs, and the edits are small and unambiguous (clearly the migration's intent). (2) CLAUDE.md's matches are plan-sanctioned crossrefs; whitelisting it is just fixing the plan's whitelist omission. (3) AgentCrawl is not your stated success criterion and is entangled with UN-005's physical rename — cleanest done atomically there.

If you greenlight D1=A, I will: edit the 4 files to v2, add CLAUDE.md to my effective 11.1 whitelist, re-run both sweeps to confirm only benign `pre-openspec-decisions` filename refs remain, then finish Task 11 (write `from-sp0impler-sp0-done.md`, `git rm` the two handoff letters, closure commit, `sp0-complete` tag).

## Current snapshot

- **Branch**: `feat/agentcrawl-bootstrap`. **gstack** submodule `M` untouched throughout.
- **SP-0 commits (mine)**: `8b91d9c` skeleton · `a1a4f39` LLMClient · `cb1889f` openspec removal · (Task 4 .claude removal = no commit, gitignored) · `836386c` CLAUDE v2 · `2874a53` longterm v2 · `a6c1b72` HarnessStack READMEs v2 · `62b57d6` RepoMem persist · `64ec1ec` Dashboard SP-0-complete · `bee65f0` README v2.
- **Parallel**: you committed `7c428ab` (SP-1 kickoff: `toSP1Impler/handoff.md`, UN-009, SP-1→wip) on top of my work — noted, untouched.
- **Task 11 status**: 11.3 ✅ (18 paths present; plan's "Expected: 22" is an arithmetic typo — actual arg count is 18, all resolve), 11.4 ✅ (openspec/opsx/openspec-* skills all gone), 11.5 ✅ (CLAUDE v2, "v2"×6). 11.1 ❌ (this letter). 11.2 ⚠️ (AgentCrawl pervasive; see D2).
- **Not yet done (waiting on your ack)**: done-letter, burn of the two handoff letters, `sp0-complete` tag.
- **SP-0 board** flipped 🔴 blocked + Dashboard row **UN-010** added pointing here.

— SP0Impler
