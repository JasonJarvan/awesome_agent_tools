> from: SP0Impler session (Claude Opus 4.8 1M, 2026-05-31)
> recipient: orchestrator (and any future orchestrator)
> mode: milestone-done
> purpose: confirm SP-0 completion (skeleton + recipe v2 migration); close the SP-0 handoff chain
> lifecycle: persist until next milestone, then archive

# SP-0 milestone-done — JarvanKB skeleton + HarnessStack v2

## What was delivered

- **10 sub-project directories** seeded under Engine/Skill/Service, each with `docs/{README,interface,architecture}.md` + `docs/RepoMem/{architecture,decisions}.md` + `src/` + `tests/` (51 stub .md files); `Skill/router/README.md` placeholds SP-8 (v1+).
- **LLMClient skeleton** in `Engine/common/src/` (litellm-backed; constructor instantiable; `complete` / `stream` / `to_opencode` raise `NotImplementedError` per the v1 frozen contract) + `config/llm.yaml.example`.
- **Spec layer fully removed**: its workspace directory + the root symlink + the per-repo `.claude/` command/skill artifacts (the `.claude/` ones were gitignored → filesystem-only removal, no commit). See `docs/HarnessStack/longterm.md §Recipe v1→v2 Migration` for the layer name, the exact removed paths, and rationale.
- **Recipe v1 → v2 Full Rewrite** recorded in `longterm.md` (8-step pipeline, single verification gate, layered RepoMem, `to{Prefix}{Role}` mailbox convention); v1 content archived as DEPRECATED.
- **v2 migration of all governance/memory docs**: `CLAUDE.md`, both HarnessStack READMEs, RepoMem persist (`runbook §0` removed + pre-v2 banner), RepoMem governance docs (`README` / `architecture/index` / `memory/index`), `hooks/cc-dashboard.md`, `Dashboard/index.md`, and top-level `README.md`.
- **Mid-execution blocker** (Task 11 sweep residue in 4 unscoped files) raised + resolved via your decisions letter (D1=A, D2=A); those 4 files cleaned of Spec-layer references in commit `de4af04`.

## Verification (single gate, v2)

- 51 stub `.md` present (Task 1.7) ✅
- `LLMClient` instantiable + 3 methods raise `NotImplementedError` (Task 2.6) ✅
- Spec-layer workspace / root symlink / `.claude` artifacts all gone (Task 11.4) ✅
- `CLAUDE.md` recipe v2, "v2" ×6 (Task 11.5) ✅
- Final Spec-layer-name grep sweep clean outside the 8-file whitelist (7 original + `CLAUDE.md`) and the benign `pre-openspec-decisions.md` filename references (Task 11.1, re-run post-fix) ✅
- Required directory tree: 18 paths present (plan's "Expected: 22" is an arithmetic typo — actual `ls` arg count is 18) ✅

## Known deferred (intentional, NOT failures)

- **`AgentCrawl` → `JarvanKB` string rename** deferred to **UN-005** (physical `mv Tools/AgentCrawl Tools/JarvanKB`, separate user session) per D2=A — done atomically with the directory rename so paths update consistently. Strings remain in: `docs/RepoMem/README.md`, `persist/architecture/index.md`, `persist/memory/index.md`, `HarnessStack/hooks/cc-dashboard.md`, `persist/memory/pre-openspec-decisions.md` (frozen), `temp/harness-bootstrap/*` (your RepoMem.merge prunes), `sendbox/toAgent/handoff.md` (SP-3/SP-4b caller-contract work rewrites). This is **not** a Task-11.2 failure.
- RepoMem.merge HITL (v2 step 8) for SP-0 temp docs: you handle upstream.

## Commit chain (branch `feat/agentcrawl-bootstrap`)

`8b91d9c` skeleton · `a1a4f39` LLMClient · `cb1889f` Spec-layer removal · `836386c` CLAUDE v2 · `2874a53` longterm v2 · `a6c1b72` HarnessStack READMEs · `62b57d6` RepoMem persist · `64ec1ec` Dashboard SP-0-complete · `bee65f0` README v2 · `862c147` blocker + UN-010 · `de4af04` 4-file Spec-layer cleanup · (closure commit + `sp0-complete` tag follow). Task 4 produced no commit (gitignored).

## Disposition of the SP-0 handoff chain (git rm'd in the closure commit)

- `docs/sendbox/toOrchestrator/handoff.md` (bootstrap inheritance letter)
- `docs/sendbox/toSP0Impler/handoff.md` (your handoff to me)
- `docs/sendbox/toSP0Impler/from-orche-sp0impler-decisions.md` (your decisions reply)
- `docs/sendbox/toOrchestrator/from-sp0impler-blocker-sweep-residue.md` (my blocker, resolved)

## Next

- SP-1 Stage 2→3 gate auto-passes (this letter + the Engine/Service module dirs from Task 1 exist).
- UN-005 (repo rename) + UN-006 (GitHub org name) remain open for the user.
- Dashboard SP-0 row flipped 🔴 blocked → ⚫ done; UN-010 archived (resolved via your decisions letter).

— SP0Impler
