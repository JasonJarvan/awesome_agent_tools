> from: root orchestrator generation 4 (Claude Opus 4.8 1M, active 2026-06-07 →)
> recipient: SP6Impler (a new Claude Code peer session you are about to become)
> mode: child-handoff (sendbox-protocol Mode A — root stays alive; you converge back to `toOrchestrator/`)
> purpose: build SP-6 CrawlMdSaver — the cross-vertical skill that registers BOTH crawl skills (SP-3 Zhihu +
>   SP-4b Bilibili) and merges crawled markdown with the user's notes into one output doc
> lifecycle: burn after root reads your `from-sp6impler-done.md`
> date: 2026-06-11

# Handoff — SP6Impler (CrawlMdSaver, `Skill/ingester/crawl-md-saver/`)

## 0. What you are

You are the **SP-6 implementer**, a **DIRECT CHILD of root orche g4** — NOT under a crawl SubOrche. SP-6 is
**cross-vertical** (it registers and dispatches to both the Zhihu and Bilibili crawl skills), so it belongs to
root, not to either vertical's SubOrche. Root stays alive; you converge back to `toOrchestrator/`.

Task identifier: **`sp6-crawl-md-saver`**. This unlocked **now** because its two hard-software deps both
landed: **SP-3 Zhihu Skill ⚫ done** + **SP-4b Bilibili Skill ⚫ done** (merge `2334698`). SP-6 is itself the
hard prerequisite for SP-7 (ThinoIngester) — but **SP-7 is OUT OF SCOPE** here (root sequences it after you).

## 1. Scope (from SP-0 skeleton design §7, the authoritative SP map)

`Skill/ingester/crawl-md-saver/` — **CrawlMdSaver**, a skill (the "爬取-笔记整合包装层" / crawl-to-note
integration wrapper). Per SP-0 §243:

> 注册其他 crawl skill，输入=URL+笔记 / 源文档+笔记，输出=合并 md，frontmatter 含用户笔记元数据
> (registers the other crawl skills; input = URL+notes  /  source-doc+notes; output = merged markdown whose
> frontmatter carries the user's note-metadata)

Two input modes:
- **URL + notes** → route to the right crawl skill, crawl → markdown, then merge the user's notes.
- **source-doc + notes** → merge only (no crawl; the source markdown is already in hand).

SP-0 §308 also names an "整理" (organize/refine) step: *合并用户笔记与原文的"整理"步骤* — i.e. there is a
note-with-original reconciliation step, a likely LLM use (see §3).

The skeleton already exists from SP-0 (`Skill/ingester/crawl-md-saver/{src,tests,docs/...}`) — empty scaffolding,
yours to fill.

## 2. The two contracts you integrate (parallel by design — verified)

Both crawl skills expose a near-identical public API and both return `SaveResult`:

| | SP-3 Zhihu (`Skill/crawl/zhihu-crawl`) | SP-4b Bilibili (`Skill/crawl/bilibili-crawl`) |
|---|---|---|
| import | `from zhihu_crawl import save_zhihu` | `from bilibili_crawl import save_bilibili, SaveResult` |
| entry | `save_zhihu(url, save_path=None, *, with_comments, comment_limit, profile, config_path)` | `save_bilibili(ref, save_path=None, *, profile, config_path)` |
| CLI | `zhihu-crawl` (`zhihu_crawl.cli:main`) | `bilibili-crawl` (`bilibili_crawl.cli:main`) |
| ref forms | 知乎 answer/article/question URL | BV id / `bilibili.com` URL / av id |
| save_path | `.md` = explicit write; dir/empty/None = **vague → LLM classify** | same semantics |
| returns | `SaveResult` | `SaveResult` |

Frozen contracts: `Skill/crawl/zhihu-crawl/docs/interface.md` + `Skill/crawl/bilibili-crawl/docs/interface.md`.
Read both — especially the **`SaveResult` shape** (does it carry the markdown *content* + the written path, or
just the path?). That answer drives the §3 merge-vs-write decision.

## 3. Key design decisions — brainstorm WITH THE USER (SP-6 has no prior design; SP-0 §386 defers it to here)

1. **Routing / registration.** URL domain → which crawl skill (`zhihu.com`/`zhuanlan.zhihu.com` → zhihu;
   `bilibili.com`/`b23.tv`/BV → bilibili). Design the registry so a **future crawl skill registers without
   editing SP-6 core** (the "注册其他 crawl skill" charter). Non-URL `source-doc` mode bypasses routing.
2. **The merge-vs-write tension (the crux).** `save_*()` today does fetch→markdown→(classify)→**writes a
   file**. But SP-6 must inject the user's notes into the output. So either (a) call `save_*()` then
   post-process the written file, or (b) obtain the markdown WITHOUT writing, merge, then write once. Pick
   based on what `SaveResult` exposes (§2). Prefer the path that keeps SP-6 a **pure consumer** (no edits to
   SP-3/SP-4b) — if a small read-only addition to a crawl skill's return is unavoidable, that's a
   cross-skill change → flag it (it touches a frozen contract).
3. **Merge layout + frontmatter schema.** Where do user notes sit relative to crawled content? What
   note-metadata lands in frontmatter (source URL, fetched_at, user tags/notes, …)? This is SP-7's input
   contract later — design it deliberately.
4. **The "整理" step (SP-0 §308).** If notes+original need LLM reconciliation, **reuse the shared
   `LLMClient` from `jarvankb_common`** (`from jarvankb_common import LLMClient`) — do NOT reimplement.
   must-read `docs/RepoMem/persist/memory/llm-shared-layer.md`. Provider `mimo-v2.5-pro` already configured.
   Decide whether "整理" is always-on, opt-in, or off-by-default (token cost).
5. **Packaging.** One agentskills.io `SKILL.md` (the SP-3/SP-4b pattern — see `llm-shared-layer.md` §packaging)
   + importable `save_*`-style entry + thin CLI.
6. **Heads-up (concurrent):** SP-5a v1.2 (`ZhihuClassifyImpler`, UN-036) is extracting the shared **classifier**
   into `jarvankb_common`. If SP-6 needs classification, coordinate/reuse rather than duplicate — check its
   state at brainstorm time; don't hard-block on it.

## 4. Inputs (minimum — re-fetch as needed)

| Need | Path |
|---|---|
| Authoritative SP-6 spec | `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` §7 (rows 243/264-269/308) |
| The two contracts to call | `Skill/crawl/{zhihu-crawl,bilibili-crawl}/docs/interface.md` (entries + `SaveResult`) |
| Shared LLM layer (reuse) | `docs/RepoMem/persist/memory/llm-shared-layer.md` + `Engine/common/docs/interface.md` |
| Skeleton to fill | `Skill/ingester/crawl-md-saver/{src,tests,docs/...}` |
| Module + global memory (two layers on RepoMem.read) | global `docs/RepoMem/persist/` + module `Skill/ingester/crawl-md-saver/docs/RepoMem/` |
| Lane Tiering + grill-with-docs (new recipe v2 governance) | `CLAUDE.md §3` + `docs/HarnessStack/longterm.md §Lane Tiering (v2)` — **this is a `Lane: full` task** (cross-vertical, net-new public contract surface) |

## 5. Pipeline / discipline

- **Full v2 pipeline, `Lane: full`** (declare `Lane: full` in your plan-doc frontmatter): `RepoMem.read` →
  **brainstorming WITH THE USER** (settle §3) → design (`specs/`) → **grill-with-docs is eligible** (full-lane
  auto-judge design gate — note: that skill may be mid-replacement, see UN-034; judge availability at the time)
  → writing-plans → worktree + **TDD** → verification → finish branch (ask-first) → Step 8.
- **Verification:** unit tests (mock the two `save_*` boundaries + LLM + network) + an integration/live smoke
  that actually routes one Zhihu URL and one Bilibili ref through to a merged doc (Bilibili full-transcribe may
  hit the BN-412 downloader throttle — a B站-vertical infra issue tracked at UN-035, NOT your skill's bug; the
  LLM/merge/routing path is what you must prove).
- **Step 8 RepoMem.merge** is yours (HITL). Promote only cross-SP-reusable gotchas to global; keep mechanism in
  the module. Most integration facts already live in SP-3/SP-4b — expect light global promotion.

## 6. Worktree / branch / commit discipline

- Worktree off the **local** `feat/agentcrawl-bootstrap` (NOT `origin/main`). `using-git-worktrees`; base =
  current local branch.
- **Push to origin is ENABLED** for `feat/agentcrawl-bootstrap` (no-push invariant lifted 2026-06-10; see
  `version-plan.md §Compatibility`). Merge into local `feat/agentcrawl-bootstrap` as usual; **do NOT merge to
  `main` / rebase / touch the `gstack` submodule** without explicit user say-so.
- Shared main tree → scope commits with explicit pathspec; "modified since read" → re-read+retry. Don't touch
  other sessions' in-flight files (GrillDocsImpler / ZhihuClassifyImpler may be active), `.claire/`, or
  `.mcp.json` (gitignored, holds a key; **repo is PUBLIC**).

## 7. Out of scope (do NOT do)

- Do NOT modify SP-3/SP-4b skills or the engines — SP-6 is a **consumer/wrapper**. A read-only return addition,
  if truly unavoidable (§3.2), is a flagged cross-contract change, not a silent edit.
- Do NOT reimplement `LLMClient` or a classifier — reuse `jarvankb_common`.
- Do NOT start SP-7 (ThinoIngester) — root sequences it after SP-6 lands.
- Do NOT reintroduce OpenSpec; do NOT edit the deprecated v1 longterm block.

## 8. Convergence path (you report to ROOT)

- **Parent cwd (absolute):** `/home/shenzhou/Codes/awesome_agent_tools/Tools/JarvanKB/`
- **Done →** `docs/sendbox/toOrchestrator/from-sp6impler-done.md` (acceptance table w/ evidence: routing both
  verticals, merge+frontmatter, the merge-vs-write decision taken, test count + smoke result, the SP-7-facing
  output contract, Step-8 promotions, commit list). **This unlocks SP-7** — flag it so root sequences SP-7.
- **Blocked →** `docs/sendbox/toOrchestrator/from-sp6impler-blocker-<topic>.md` (2–3 options + your pick; stop,
  wait). A required edit to a frozen SP-3/SP-4b contract (§3.2) is the most likely escalation.

## 9. Day-1 checklist

1. `RepoMem.read` (global persist + module) + read SP-0 §7 + both crawl `interface.md` (esp. `SaveResult`).
2. Brainstorm with the user: routing/registry, merge-vs-write, frontmatter schema, "整理" LLM step, packaging (§3).
3. Design (`specs/`) → grill (if eligible) → writing-plans (`Lane: full`) → worktree + TDD.
4. Build: dispatch/registry → per-skill adapter → merge + frontmatter → CLI + SKILL.md.
5. Verification (unit + routed live smoke, §5) → finish branch (ask-first) → Step 8.
6. Report `from-sp6impler-done.md` to `toOrchestrator/` (note SP-7 now unlocked).

— root orche g4 (2026-06-11)
