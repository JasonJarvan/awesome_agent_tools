---
recipients:
  - role: SP1Impler
    purpose: be aware that the working directory rename UN-005 has happened; refresh any cached cwd / path assumptions; do NOT treat surviving AgentCrawl strings in historical narrative docs as bugs
    lifecycle: until SP1Impler logs its next stage-transition commit (it will have implicitly accepted by then)
  - role: FutureOrche
    purpose: post-rename audit trail
    lifecycle: until next major migration (eg. v1.0 OSS split)
on_lifecycle_end: archive
created: 2026-05-31
created_in: orche-2026-05-31-post-sp0
---

# Broadcast — Directory rename `Tools/AgentCrawl/` → `Tools/JarvanKB/` is done

## What changed (physical)

- Filesystem: `/home/shenzhou/Codes/awesome_agent_tools/Tools/AgentCrawl/` no longer exists
- Filesystem: `/home/shenzhou/Codes/awesome_agent_tools/Tools/JarvanKB/` is the live project root
- Same git history; tag `sp0-complete` (5c28447) still resolvable
- Branch unchanged: `feat/agentcrawl-bootstrap`

This was Dashboard **UN-005**, executed by the user in a separate session. It is now archived as done.

## What changed (string-sweep follow-through, this orche commit)

Per the D2=A deferral in `from-orche-sp0impler-decisions.md` (already burned), orche has just swept `AgentCrawl` → `JarvanKB` in **active-reference** files. **Historical-narrative** files keep `AgentCrawl` intact — that is correct and not a residue:

| Kept (intentional narrative) | Why |
|---|---|
| `docs/RepoMem/persist/version-plan.md` §Project rename | Records the rename event itself |
| `docs/RepoMem/persist/memory/pre-openspec-decisions.md` D5–D7 | FROZEN LEGACY banner already explains |
| `docs/HarnessStack/longterm.md` §Recipe v1→v2 Migration Trigger | Quotes the migration trigger verbatim |
| `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` §Background / §2 | Discusses the rename |
| `docs/superpowers/plans/2026-05-31-SP-0-jarvankb-skeleton.md` | Contains sed commands and historical execution record |
| `docs/Dashboard/index.md` Archive rows UN-002 / UN-010 | Historical action descriptions |
| `docs/sendbox/toOrchestrator/from-sp0impler-sp0-done.md` §Known deferred | done-letter snapshot |

If you grep for `AgentCrawl` across the repo, hits in the above files are **expected**, not bugs.

## Action required from SP1Impler

1. **Refresh your cwd assumption**: if you held `/home/shenzhou/Codes/awesome_agent_tools/Tools/AgentCrawl/` in any cached state, replace with `Tools/JarvanKB/`. `pwd` once at next turn to confirm.
2. **Re-check your handoff letter**: `docs/sendbox/toSP1Impler/handoff.md` was swept (§4 "Parent's cwd (absolute path)" now reads `Tools/JarvanKB/`). Your understanding of paths inside it should remain consistent.
3. **Stage 2→3 gate**: independent of this rename, the gate auto-passed earlier:
   - `docs/sendbox/toOrchestrator/from-sp0impler-sp0-done.md` exists ✓
   - `Service/crawl/cookie-manager/` exists (under `Tools/JarvanKB/` now) ✓
   You may have already transitioned; if not, this is the reminder. Continue per your handoff §3.D.

## Action required from future orchestrator(s)

None — this letter is informational. When you load RepoMem.read, you'll find:
- `version-plan.md` records rename as 2026-05-31
- `Dashboard/index.md` Archive shows UN-005 done
- `longterm.md` v2 Full Rewrite section narrates trigger as "scope expansion of `AgentCrawl` → `JarvanKB`"

These are consistent and reflect the post-rename state.

## Supersession

This letter is superseded by:
- SP1Impler's next stage-transition commit (its first explicit post-rename action implicitly acknowledges)
- OR explicit `archive` after 7 days idle (per `on_lifecycle_end` frontmatter)

Whichever comes first.

— Orchestrator (2026-05-31, post-SP-0)
