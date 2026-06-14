> from: ZhihuClassifyImpler (child of ZhihuCrawl SubOrche)
> to: ZhihuCrawl SubOrche
> type: plan-ready
> re: SP-5a v1.2 — default-collection auto-classify
> lifecycle: burn after SubOrche reads
> date: 2026-06-14

# plan-ready — SP-5a v1.2 (default-collection auto-classify)

Brainstorm → spec → plan done (steps 1–4 of the v2 pipeline). Lane: **full**. Ready to enter worktree + TDD.

## Artifacts (all committed to `feat/agentcrawl-bootstrap`)
- Design: `Service/crawl/zhihu-watcher/docs/superpowers/specs/2026-06-14-SP-5a-v1.2-default-collection-classify-design.md` (commit `b050865`)
- Plan: `Service/crawl/zhihu-watcher/docs/superpowers/plans/2026-06-14-SP-5a-v1.2-default-collection-classify-plan.md` (commit `fc45ab6`)
- RepoMem temp: `Service/crawl/zhihu-watcher/docs/RepoMem/temp/sp5a-classify/`

## User-locked module-internals (this brainstorm, beyond the handoff §1 cross-cutting locks)
1. **403 degrade = retry + circuit-break, NOT excerpt-classify.** A failed fetch is not stub-saved and not
   classified from the list excerpt. It retries via FailureStore; after `circuit_break_threshold` (default 10)
   total failures it is permanently skipped + surfaced on a human attention list. (Supersedes handoff §1.3's
   "classify from list-excerpt" degrade option.) The list excerpt is used only to render the attention list.
2. **Failure ledger split confirmed by the user's challenger:** ledger records SUCCESS only; FailureStore
   keeps the failure count + cooldown + the new circuit-break terminal state; attention list = human-read
   surface to judge the real cause (stale `__zse_ck` vs unreachable).
3. **Tier-2 lead cap = 1000 chars** (Tier-1 = 200, aligned to the list excerpt). Never full text.
4. **Watcher classifies into EXISTING folders only** (`allow_new_folders: false`) — an unattended daemon must
   not fractalize the taxonomy. SP-3 keeps propose-new (`allow_new=True`) via the shared `allow_new` flag.
5. **Attention surface = two layers:** authoritative JSON in `state_dir` (FailureStore), human render =
   `output_dir/_zhihu-watcher-attention.md`, integral-overwrite each cycle (never parsed back).

## My design calls (handoff §1 authorized)
- Shared classifier `jarvankb_common.classify(title, lead_text, existing_subfolders, client, *, allow_new) ->
  Classification(folder, is_new, vague)`; **returns the RAW existing folder name on a slug-match** so the
  watcher writes the real Obsidian dir (also fixes a latent SP-3 slug-vs-rawname quirk; SP-3 output unchanged
  because its saver re-slugs). SP-3 → thin adapter; `api.py`/`saver.py` untouched; full SP-3 suite is the
  regression gate.
- Ledger = the dedup backbone for classify targets (NOT the seen-set); non-classify targets unchanged.
- `CollectionItem` already carries `title`/`excerpt`/`favorited_at` → no favorites_client parse change.
- Worktree base verified = local `feat/agentcrawl-bootstrap` (v1.1 already merged at `0489382`).

## No-LLM boundary amendment (add-only, recorded — not stealth)
classify is per-target opt-in, **default OFF** → with no classify target the daemon is byte-for-byte the v1.1
no-LLM behavior (LLMClient never constructed). Recorded in v1 design §1 + will land in module `decisions.md`
at Step 8. Reopening of SP-5a's locked no-LLM boundary is therefore explicit.

## Forward-compat for v1.3 (NOT in scope)
`sync_status="local-only"`/`sync_attempts=0` ledger hook only. **Step-8 promotion to `version-plan.md`:** the
v1.3 【同步知乎收藏夹分类】 roadmap + the `x-zse-96` write-API signing risk (Zhihu collection move is a write
API → likely D1 no-signer wall → ledger stays the authoritative primary). Will request your greenlight /
g4 version registration at Step 8.

## Next
Proceeding to worktree + executing-plans (TDD, subagent-driven) unless you flag a concern. I own merge closure
(Step 8) per the impler-owns-merge invariant.
