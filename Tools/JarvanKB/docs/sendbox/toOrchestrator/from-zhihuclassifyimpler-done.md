> from: ZhihuClassifyImpler (SP-5a v1.2)
> to: root orchestrator (g5) — ZhihuCrawl SubOrche has converged (v1.2 re-parented to root/MainOrche per
>   Dashboard SP-5a row); this supersedes the handoff §6 `toZhihuCrawlOrche` done-routing.
> type: milestone-done + global-promotion-request (HITL — global persist is root's call, user 2026-06-18)
> re: SP-5a v1.2 — default-collection auto-classify
> lifecycle: burn after root ratifies the two promotions (§2) and logs them

# SP-5a v1.2 — DONE + two global-persist promotions for your ratification

## 1. What landed
Opt-in, **default-OFF** auto-classify for the Zhihu Watcher. `classify: true` target → fetch (frozen SP-2) →
classify into an **existing** Obsidian subfolder via a shared classifier extracted from SP-3 into
`jarvankb_common` → save → record in a **success-only ledger** (the dedup backbone for classify targets).
Failures escalate cooldown → circuit-break → a regenerated Markdown attention surface. No classify target ⇒
byte-for-byte the v1.1 no-LLM daemon (`LLMClient` never constructed).

- **Merged** `c426131` into `feat/agentcrawl-bootstrap` (`--no-ff`; worktree + branch cleaned up).
- **127 offline tests** (jarvankb_common 22 + SP-3 regression 27 + watcher 78) + **live smoke** (real
  `我的收藏` 721323262 + real `mimo`): classify+save into `赚钱-*` + ledger + re-run `0 re-hit` + a vague item
  escalated Tier-1→Tier-2; a bad-key run validated the graceful-degrade path. Module memory: full v1.2 entry
  in `Service/crawl/zhihu-watcher/docs/RepoMem/decisions.md`.
- Module-scope closure already done by me: decisions.md entry, `.gitignore` for real/smoke config (public-repo
  secret hygiene), temp pruned, Dashboard updated.

## 2. Global-persist promotions — PROPOSED, awaiting your ratification (user routed this to you)
I did NOT write global persist (governance-gated). Proposed verbatim text to apply:

### 2a. `docs/RepoMem/persist/version-plan.md` — append a section
> ## SP-5a v1.3 roadmap — 【同步知乎收藏夹分类】 (Zhihu collection-sync) + signing risk
> Use the v1.2 classify result to call the Zhihu **write** API to move `我的收藏` items into the matching
> categorized Zhihu collection. v1.2 ships ONLY the `sync_status` ledger hook (default `local-only`); the sync
> itself is NOT built. **Feasibility risk:** Zhihu collection add/move is a **write** API → very likely
> `x-zse-96`-gated (cf. `/api/v4/articles` 403 `code 10003`) → hits the **D1 no-signer** wall (root's call).
> This is exactly why the **local ledger is the authoritative primary** and sync is best-effort on top.
> (Precedent: SP-3 promoted "LLMService v2".)

### 2b. `docs/RepoMem/persist/memory/llm-shared-layer.md` — add a sibling-API section
> ## Shared classifier — `jarvankb_common.classify` (landed SP-5a v1.2)
> Beside `LLMClient`: `classify(title, text, subfolders, client, *, allow_new=True) -> Classification(folder,
> is_new, vague)` + `lead_text(markdown, max_chars)` + `existing_subfolders(output_root)`. Self-contained
> (own slug / JSON-parse / prompt). `vague` = model-reported ambiguity (caller MAY escalate to a longer lead —
> the watcher does Tier-1 200ch → Tier-2 1000ch; SP-3 ignores it). `allow_new` = **prompt-only** flag;
> `is_new` is always filesystem-authoritative. On a slug-match `folder` returns the **RAW existing folder
> name** (so a watcher writes the real dir). **Consumers (SP-3 already via a thin adapter; SP-4b vague_path;
> SP-6/7) reuse as-is — do NOT reimplement.** SP-3's `classify.py` is now an adapter; `api.py`/`saver.py`
> source unchanged.

If you'd rather I apply these after your OK, say so and I'll write them (still HITL).

## 3. Milestone gate (your new standing rule, CLAUDE.md §3 / 2026-06-18)
SP-5a v1.2 unlocks a user-facing capability: **auto-sorted Zhihu default-collection → categorized vault**.
The "last mile" beyond this SP's technical done = **deploying the watcher daemon** against the real vault +
running the full-inbox first back-fill. That is already tracked as **Dashboard UN-047 (WatcherDeployImpler)** —
recommend it picks up classify-mode for `我的收藏` (config block + `classify:true` target are in the example
yaml). Suggest you update `Dashboard §里程碑` accordingly.

## 4. Heads-up: environmental fix I made (NOT SP-5a scope — grill-restore / UN-034 domain)
The merge surfaced a **working-tree self-loop symlink** at `Tools/JarvanKB/.claude/skills/grill-with-docs`
(`→ itself`, ELOOP) in the MAIN checkout — it had been aborting **every session's** pre-commit/merge (the
repeated "符号链接的层数过多" failures). The committed tree is a proper directory + `SKILL.md`; the loop was
**uncommitted working-tree corruption**. I repaired it (`rm` loop + `git checkout HEAD -- <path>`, zero
git-content change). GrillDocsImpler (UN-034) should know their working tree had this; the commit was fine.

## 5. Deploy creds note
The service stores no creds in-repo by design. Live smoke used a `/tmp` config with the cookie-manager box
uuid/password (user-provided) + a fresh `MIMO_API_KEY` (the old token-plan key had expired — credential, not
code). Deploy (UN-047) needs a fresh `MIMO_API_KEY` + the box creds in a gitignored `config/zhihu-watcher.yaml`.
