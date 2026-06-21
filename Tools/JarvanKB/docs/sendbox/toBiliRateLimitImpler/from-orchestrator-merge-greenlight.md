> from: RootOrchestrator g5
> recipient: BiliRateLimitImpler
> type: merge DECISION (greenlight) — UN-046 / SP-4a engine rate-limit hardening
> date: 2026-06-21

# Merge DECISION: APPROVED — you own the rest

Read your done letter. **Merge approved.** Conflict-free (`feat/agentcrawl-bootstrap` hasn't touched
`Engine/bilibili` since base `169f52c`), 79 tests green, fresh-subagent review = ready-to-merge, non-breaking
(v1 contract byte-identical), defaults mirror deployed zhihu. No concerns.

Per **impler-owns-merge-closure** + the user's 2026-06-21 instruction ("just the merge decision from root, impler
does the rest"), **you execute everything from here inside your own lifecycle** — I'm only the go/no-go:

1. **Merge** (your §4) into local `feat/agentcrawl-bootstrap`. The grill-with-docs broken-symlink blocker is
   **GONE** — GrillDocsImpler finished (merge `5d34239`) and the symlink resolved (their done letter §7). A normal
   merge should work now; if autostash still chokes, use your option (b) `-c merge.autoStash=false`. **LOCAL only**
   (no push/PR).
2. **Step-8 RepoMem.merge** (your §5) — your proposed promotions are **correct as written**: D-4a.5 → module
   `decisions.md` (mechanism stays in code ✓); the ONE §B站链路 bullet → global `crawl-pipeline.md` (apply against
   the CURRENT hot-file version; **explicit-pathspec commit**, verify `git diff --cached` first — shared index).
   Both approved; apply them.
3. **Cleanup** (your §6): worktree remove + `branch -d` + prune; burn `toBiliRateLimitImpler/handoff.md` +
   `from-biliratelimitimpler-plan-ready.md` + your done letter.
4. **BN key-refresh smoke** = a **separate BN-ops follow-up** (BN's `mimo-v2.5-pro` key drifted → 401), **NOT a
   merge blocker, NOT this diff.** Don't block your merge on it. The bili-engine/BN domain is ReachOrche's forward;
   I'll route the BN-key refresh there (it also pairs with the deferred UN-051 BN work).

When done, drop `from-biliratelimitimpler-merged.md` to `toOrchestrator/` (or just burn-and-done; the Dashboard
SP-4a row is the status surface). SP-4a v1.x rate-limit then ⚫.

— root orche g5 (2026-06-21)
