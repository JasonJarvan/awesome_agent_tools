---
slug: sp5a-zhihu-watcher
status: active
domains:
  - crawl-pipeline
  - credentials
updated_at: 2026-06-02
task_type: feature
---

# SP-5a Zhihu Watcher — implementation working notes

> Spec: `../../../superpowers/specs/2026-06-02-SP-5a-zhihu-watcher-design.md` (§3 has the component table).
> This file accumulates things learned WHILE building — quirks, test-vector sources, risks tracked —
> that are not (yet) in the design. Promote the durable ones at Step 8 merge.

## Risks / things to verify during implementation

- **R1 (residual x-zse-96):** collections endpoint "no signing" is from the reference repo's code, not
  our own 2026-06 live run. Live smoke must confirm a 200 with plain cookie. 403 ⇒ blocker (design §2).
- **R2 (legacy decrypt fidelity):** the OpenSSL `Salted__` + EVP_BytesToKey path is the fiddly bit.
  Unit-test against known vectors; cross-check the live SP-1 box / `cookie-manager show` CLI as oracle.
- **R3 (collection name source):** v1 takes `name` from config (defaults to id). Auto-discovery of
  collection names via `https://www.zhihu.com/collections/mine` is NOT in v1 (reference repo does it via
  HTML scrape; out of scope unless trivial).

## Worktree / branch gotcha (from global memory + handoff §6)

- Create the worktree branched from the **local** `feat/agentcrawl-bootstrap`, NOT `origin/main`
  (`EnterWorktree` default `fresh=origin/main` would drop local commits). Worktree path
  `.worktrees/sp5a-zhihu-watcher/`. Isolate from sibling SP-3 + the live SP4aImpler.
- Commit prefixes: `docs(SP-5a):` / `feat(SP-5a):`. Local commits only; no push/merge-to-main.

## Build order (TDD, filled as we go)

- (to be tracked during Step 5 against the plan's task list)
