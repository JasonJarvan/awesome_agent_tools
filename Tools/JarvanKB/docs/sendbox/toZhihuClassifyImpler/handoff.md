> from: ZhihuCrawl SubOrche (your parent; sub-orchestrator under root orche g4)
> recipient: ZhihuClassifyImpler (a new Claude Code peer session, same cwd = repo root)
> mode: child-handoff (sendbox-protocol Mode A — SubOrche stays alive; you converge back to toZhihuCrawlOrche/)
> purpose: SP-5a v1.2 — add an opt-in default-collection auto-classify mode to the Zhihu Watcher, backed by a
>   shared classifier extracted from SP-3 and a local classification ledger
> lifecycle: burn after you write `from-zhihuclassifyimpler-done.md` and SubOrche reads + converges

# Handoff — ZhihuClassifyImpler (SP-5a v1.2: default-collection auto-classify)

## 0. What you are
Child of the **ZhihuCrawl SubOrche** (NOT root). This is **SP-5a v1.2** — an additive, **opt-in** classify mode
in the existing `Service/crawl/zhihu-watcher/` daemon, plus a shared-classifier extraction. You run the full
v2 8-step pipeline (your own brainstorm → spec → plan → worktree+TDD → verify → finish → your own Step-8).
**Lane: full** (declare in plan frontmatter): it touches **Engine/common + Service/zhihu-watcher + Skill/zhihu-crawl**,
produces a `persist/` asset, and adds public contract surface (the shared classifier API).

## 1. Scope (locked with the user — confirm module-internals in your brainstorm, don't re-litigate these)
Goal: the default collection **`我的收藏`** (a flat inbox) → auto-sort each new item into the user's existing
~33 Obsidian category subfolders, **token-frugally**.

**Per-item flow when classify is ON for a target:**
1. **Fetch full content** (frozen SP-2 engine, like named collections) → **save full markdown into the
   classified subfolder**.
2. **Token-frugal tiered classify** via the shared classifier, on the **already-fetched content** (no extra fetch):
   - **Tier-1**: feed **first ~200 chars** → classifier returns `(folder, vague?)`.
   - if **vague** (≥2 plausible folders): **Tier-2**: feed **first N chars** (larger, capped). **NEVER feed full text.**
3. **专栏-403 degrade** (fetch fails — stale `__zse_ck` / rate-limit): classify from the **list-excerpt** (the
   only text then available) + save an excerpt-stub, OR leave it to the existing failure-store retry. Your call
   which — but a failed item must **NOT** be recorded as done in the ledger (so it retries).

> **Note (corrects the original proposal):** SP-2 v1.2 proved 专栏 full text **IS fetchable** via the primary
> nav-GET path with a fresh `__zse_ck` (12/12 200). So full-content fetch is the primary path; the list-excerpt
> is only the **degrade fallback**, not "the only 专栏 path."

### 1a. Classification ledger — in the SERVICE (zhihu-watcher), NOT the engine
A persistent ledger in `Service/crawl/zhihu-watcher/` (a sibling to the existing seen-id / watermark / failure
stores — **the engine stays frozen/stateless**). Per **successfully**-classified item:
`{item_id, classified_folder, local_path, fav_time, classified_at, sync_status (default "local-only"), sync_attempts}`.
- It is the **authoritative local dedup** → prevents re-hitting the same `我的收藏` items next poll,
  **independent of any Zhihu API**. This is the **fallback-by-design** for the v1.3 sync (§2): even if sync is
  never built or fails, the ledger still prevents re-classification.
- **Record SUCCESSES only.** A failed fetch/classify is not recorded → retries next cycle (failure-store backoff).
- `sync_status` is the **forward-compat hook** for v1.3; v1.2 sets it `local-only` and does nothing else with it.
- You MAY unify this with the existing seen-id store or keep it separate (seen-id already prevents re-hit; the
  ledger enriches it) — your design call.

### 1b. Shared classifier — extract from SP-3 into `jarvankb_common`
- **Extract** SP-3's classifier (`Skill/crawl/zhihu-crawl` `classify` + its `existing_subfolders` reader) into
  **`jarvankb_common`** (beside `LLMClient`); **SP-3 and the watcher both import it** — not a fork, not a copy.
- **Add a `vague`/low-confidence output** to drive the Tier-1→Tier-2 escalation. SP-3 doesn't need it →
  keep SP-3 **non-breaking** and **re-run SP-3's tests** after the move.
- Generic signature, e.g. `classify(title, lead_text, existing_subfolders, client) -> (folder, vague)`. The
  watcher supplies `lead_text` (Tier-1 ~200 / Tier-2 N); SP-3 supplies it from its `content_markdown` lead
  (its current behavior, richer-or-equal).
- Use **codegraph** (`query` / `callers`) to locate SP-3's classify symbol + all callers before moving it (CLAUDE.md §2 code-map).

### 1c. Boundary amendment (add-only invariant)
classify is a **per-target opt-in flag, default OFF** → SP-5a's locked "no-LLM" default behavior is preserved;
LLM runs only when explicitly enabled. **Record the reopening** of SP-5a's no-LLM boundary as an explicit
amendment in the watcher's `docs/superpowers/specs/...design.md §1` + module `decisions.md` (not a stealth add).
**Named collections default OFF** (already user-categorized by folder name); `我的收藏` is the primary use.

## 2. v1.3 roadmap (forward-compat ONLY — NOT your scope, but shape v1.2 for it)
The user's next version (starts AFTER v1.2 smoke passes): **【同步知乎收藏夹分类】** — use the classify result
to call the Zhihu **write API** to move `我的收藏` items into the matching categorized Zhihu collection.
- You **only** provide the `sync_status` ledger hook in v1.2 (default `local-only`). **Do NOT implement the sync.**
- ⚠️ **Feasibility risk to record**: Zhihu collection add/move is a **write** API → very likely **`x-zse-96`-gated**
  (cf. `/api/v4/articles` 403 `code 10003`). If so it hits the **D1 no-signer** wall (root's call). This is
  exactly why the **local ledger is the authoritative primary** and sync is best-effort on top.
- **Promote this v1.3 roadmap + the signing risk to `version-plan.md` in your Step-8** (precedent: SP-3 promoted
  "LLMService v2"). Knowe g4 for formal version registration.

## 3. Out of scope
- The actual v1.3 Zhihu-sync (write API) — forward-compat hook only.
- vault GBrain / Obsidian-taxonomy / Thino semantics (SP-6/7).
- Auto-classifying named collections by default (opt-in only).
- The `__zse_ck` solver (UN-032); editing the frozen SP-2 engine; introducing ANY signer (D1).

## 4. Inputs (minimum; re-fetch the rest)
| Need | Path |
|---|---|
| SP-3 classifier to extract (+ its tests) | `Skill/crawl/zhihu-crawl/` (`classify`, `existing_subfolders`, lead-text) — use codegraph |
| Shared-layer home + LLMClient | `Engine/common/` (`jarvankb_common`) + `docs/RepoMem/persist/memory/llm-shared-layer.md` |
| The watcher you extend (+ its stores) | `Service/crawl/zhihu-watcher/` (seen-id / watermark / failure stores; resolver; saver; favorites_client) |
| Excerpt fields (list carries excerpt) + watermark facts | `Service/crawl/zhihu-watcher/docs/RepoMem/temp/...api-fields-empirical.md`; `docs/RepoMem/persist/architecture/crawl-pipeline.md §知乎链路` |
| Frozen engine contract | `Engine/zhihu/docs/interface.md` |
| Governance (Lane:full, codegraph, grill-with-docs, impler-owns-Step-8) | `CLAUDE.md` §2/§3/§4 + `docs/HarnessStack/longterm.md` §Lane Tiering / §Harness Enhancement |
| LLM provider (reuse) | `mimo-v2.5-pro` already configured (`config/llm.yaml`) |

## 5. Pipeline (v2 8-step, Lane: full)
1. RepoMem.read (two layers).
2. brainstorming (compressed — §1 scope is LOCKED; confirm module-internals only: classifier signature +
   vagueness threshold, ledger schema + unify-with-seen-id?, Tier-N size, classified-subfolder file naming,
   the 专栏-403 degrade choice). Full-lane: MAY `grill-with-docs` the draft spec before writing-plans (auto-judge).
3-4. RepoMem.capture (temp) + writing-plans (`Lane: full` in frontmatter).
5. worktree (base = **local** `feat/agentcrawl-bootstrap`, NOT origin/main) + TDD + subagent-driven.
6. verification-before-completion: tests (incl. **SP-3 regression** after extraction) + **live smoke** on the
   real default collection (`我的收藏`, id `721323262`): classify + save into subfolders + ledger written +
   **re-run → 0 re-hit** (dedup via ledger) + a vague item escalating Tier-1→Tier-2. Use the mimo creds.
7. requesting-code-review + finishing-a-development-branch (both **ask-first**).
8. **your own RepoMem.merge closure**: promote v1.3 roadmap + signing risk to `version-plan.md`; record the
   no-LLM boundary amendment; module `decisions.md`; prune temp.

## 6. Convergence (report to ZhihuCrawl SubOrche — your parent, cwd = repo root)
| Event | Write to |
|---|---|
| plan-ready | `docs/sendbox/toZhihuCrawlOrche/from-zhihuclassifyimpler-plan-ready.md` |
| blocker | `docs/sendbox/toZhihuCrawlOrche/from-zhihuclassifyimpler-blocker-<topic>.md` |
| done | `docs/sendbox/toZhihuCrawlOrche/from-zhihuclassifyimpler-done.md` |
Inbound replies: `docs/sendbox/toZhihuClassifyImpler/from-zhihucrawlorche-*.md`.

## 7. Discipline
Local commits only on `feat/agentcrawl-bootstrap`; own worktree `.worktrees/sp5a-classify/`; **commit with
explicit pathspec** (shared main-tree index — a bare commit once swept another session's staged changes);
prefix `feat(SP-5a v1.2):` / `docs(SP-5a v1.2):`. `gstack` submodule — never touch. Uncommitted files outside
your modules belong to other sessions — don't touch.

## 8. Lifecycle
burn after you write `from-zhihuclassifyimpler-done.md` and SubOrche converges.

---
**Begin at Step 1, then Step 2 (brainstorming).** The §1 cross-cutting scope is locked — your brainstorm is the
module-internals. Greet the user, ask "ready to start SP-5a v1.2 brainstorming?"
