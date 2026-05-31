> from: orchestrator generation 3 (Claude Opus 4.8 1M, active 2026-05-31 →)
> recipient: SP2Impler (a Claude Code peer session, same cwd as orche)
> mode: child-handoff (sendbox-protocol Mode A — orche stays alive; you converge back)
> purpose: execute the full v2 8-step pipeline for SP-2 (Zhihu Engine), end-to-end
> lifecycle: burn after you write `from-sp2impler-sp2-done.md` and orche reads it

# SP-2 Handoff — Zhihu Engine

## 0. What this letter is

A **child-handoff** under sendbox-protocol. You are a peer Claude Code session; the orchestrator (g3)
stays alive while you run. You own SP-2 end-to-end through the v2 pipeline (steps 1–8). Runs **in parallel
with SP-4a** (Bilibili Engine, a sibling session) — fully independent, no shared state.

**No execute gate.** Unlike SP-1, all entry conditions are already met (SP-0 done ✓, SP-1 cookie protocol
frozen ✓). You may run Stage 1 (design) → Stage 2 (plan) → Stage 3 (execute) straight through.

## 1. Subtask scope

Deliver **SP-2: Zhihu Engine** — a library (`Engine/zhihu/`) that fetches a single Zhihu page
(answer / article / question) and returns clean Markdown + structured metadata.

**v1 scope:**
- ✅ Fetch one Zhihu URL → Markdown body + metadata (title, author, vote/comment counts, url, fetched_at).
- ✅ **zse-96 signature** handling — Zhihu's API requires a `x-zse-96` signature computed in a **browser
  context** (JS engine), NOT pure HTTP. The design must account for this (see §3.B options).
- ✅ **Cookie injection** — Zhihu needs `d_c0` / `z_c0` cookies. SP-1 cookie-manager is the source of truth
  (`Service/crawl/cookie-manager/docs/interface.md`). **Design the engine to accept cookies as INPUT**
  (a cookie string / dict parameter), keeping the engine pure + unit-testable. *Who fetches cookies from
  cookie-manager* (pull `show domain=.zhihu.com` / `GET /get/:uuid` + decrypt, or a push hook writing a
  file) is the **SP-3 Skill / SP-5a Watcher's** job — the engine just consumes injected cookies. Confirm
  this boundary in brainstorming.
- ✅ **Comments**: two-layer **flat** schema (top-level comments + their direct child replies as a flat
  list with a `parent_id` field). **Do NOT build a custom comment tree.** Comments are optional per-call.
- ✅ Importable Python API (frozen in `Engine/zhihu/docs/interface.md`) + a thin CLI for manual testing.

**Out of v1 (defer / not yours):**
- ❌ No summarization / translation / classification — that is the SP-3 Skill's job (uses `Engine/common`
  LLMClient). The engine is **pure fetch**; it does NOT call an LLM.
- ❌ No favorites-folder polling — that is SP-5a Watcher.
- ❌ No multi-page crawl / search / feed — single URL in, one page out.

**Architecture decision to settle in brainstorming:** how to get the browser context for zse-96 —
(a) **MediaCrawler pattern** (the SP-0 design's named approach), or (b) **Playwright CDP** against an
already-logged-in local Chrome (`crawl-pipeline.md` Zhihu fallback chain: CDP `Chrome:9222` → Jina Reader
`r.jina.ai` forwarding `d_c0/z_c0`). Both are on the table; weigh maintenance + reliability + headless-server
viability with the user.

## 2. Inputs (minimum set — do NOT load more unless design needs it)

| File / resource | Role |
|---|---|
| `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` §7 (SP-2 row) + §8 (LLMClient) | **authoritative scope** + shared-LLM layer (you won't implement it, just know it exists) |
| `CLAUDE.md` §2/§3/§4 (recipe v2) | governance + invariants — **note §3 step 8 + §4: YOU own RepoMem.merge closure** |
| `Engine/zhihu/docs/{README,interface,architecture}.md` | your module skeleton (placeholders to fill) |
| `Service/crawl/cookie-manager/docs/interface.md` | cookie integration contract (the "SP-1 协议敲定" you depend on) |
| `docs/RepoMem/persist/architecture/credentials.md` | how cookies flow from SP-1 to consumers |
| `docs/RepoMem/persist/architecture/crawl-pipeline.md` | **research context for the Zhihu chain only** (CDP → Jina fallback). ⚠️ its **Bilibili** section is R5-superseded — ignore it. |
| `Engine/common/docs/interface.md` | LLMClient contract (skeleton; you do NOT implement or call it in SP-2) |
| **MediaCrawler upstream** (research) + **zse-96 references** (community write-ups on Zhihu's `x-zse-96`) | approach research for the signature problem — use WebSearch/WebFetch (Tavily MCP is project-scoped + default-disabled; built-in WebSearch/WebFetch are fine) |

**Do NOT read** unless design needs: other SPs' docs, SP-1 internal source, `pre-openspec-decisions.md`
(mostly R5-superseded), the Bilibili module.

## 3. Pipeline execution (v2 8-step)

### 3.A Step 1 RepoMem.read
- Global persist (read-only): `config.md` (language policy), `architecture/{credentials,crawl-pipeline,index}.md`, `version-plan.md`.
- Module: `Engine/zhihu/docs/RepoMem/{architecture,decisions}.md` (skeleton; you'll grow them).

### 3.B Step 2 brainstorming (compressed — auto-judge skip likely, but still invoke `superpowers:brainstorming`)
Confirm with the **user via direct chat** (not sendbox): (a) zse-96 approach A (MediaCrawler) vs B
(Playwright-CDP + Jina fallback); (b) comment scope (fetch comments by default? depth = flat two-layer);
(c) cookie-injection boundary (engine takes cookies as input; skill/watcher fetches from cookie-manager);
(d) output Markdown shape (frontmatter fields).
- design.md → `Engine/zhihu/docs/superpowers/specs/2026-05-31-SP-2-zhihu-engine-design.md` (module dir
  already exists — no temporary root location needed, unlike SP-1).

### 3.C Step 3-4 RepoMem.capture + writing-plans
- temp docs → `Engine/zhihu/docs/RepoMem/temp/sp2-zhihu-engine/`.
- plan.md → `Engine/zhihu/docs/superpowers/plans/2026-05-31-SP-2-zhihu-engine-plan.md`.
- Stage-2 done = plan + self-review → write `from-sp2impler-plan-ready.md` to `toOrchestrator/`.
  **(There is no hard execute gate; plan-ready is for orche review, not a blocker. You MAY proceed to
  Stage 3 after writing it unless you want orche sign-off first — your call, state which in the letter.)**

### 3.D Step 5-7 execute + verification + finishing
- `using-git-worktrees` (e.g. `.worktrees/sp2-zhihu-engine/`) + `executing-plans` + **TDD** + **subagent-driven**
  (the user's standing preference, per SP-1).
- `verification-before-completion` = single gate: tests + lint/typecheck + **mandatory manual smoke**
  (fetch a real public Zhihu answer with live cookies; show the Markdown + metadata; exercise the comment path).
- `requesting-code-review` + `finishing-a-development-branch` — both **ask-first** (write a letter / ask user).

### 3.E Step 8 RepoMem.merge — **YOU OWN THIS** (recipe v2, updated)
Per `CLAUDE.md` §3 step 8 + §4 "Merge ordering & ownership": **the implementer closes merge within its OWN
lifecycle.** After `finishing-a-development-branch`, run `RepoMem.merge` (HITL with the user): promote any
global-scope lessons (e.g. a reusable zse-96 / browser-context pattern, if it generalizes) to
`docs/RepoMem/persist/`; keep module-specific decisions in `Engine/zhihu/docs/RepoMem/decisions.md`. You may
delegate *execution* to orche but must track it to completion before reporting done — **never fire-and-forget**.
(This supersedes SP-1's old "Step 8 = NOT YOUR JOB" framing.)

## 4. Convergence paths

**Parent cwd** = this repo root (same as yours): `/home/shenzhou/Codes/awesome_agent_tools/Tools/JarvanKB/`.

| Event | Write to |
|---|---|
| Stage 2 plan-ready | `docs/sendbox/toOrchestrator/from-sp2impler-plan-ready.md` |
| Blocker (A-12 stop-and-ask) | `docs/sendbox/toOrchestrator/from-sp2impler-blocker-<topic>.md` |
| Done | `docs/sendbox/toOrchestrator/from-sp2impler-sp2-done.md` |
| Orche → you | `docs/sendbox/toSP2Impler/from-orche-*.md` |

User talks to you directly in chat for brainstorming / review / greenlight; sendbox is for async + cross-session record.

## 5. Out-of-scope (forbidden)

- Touching SP-4a (`Engine/bilibili/`) or any other SP's files — your sibling SP4aImpler owns Bilibili.
- Editing `CLAUDE.md` / `docs/HarnessStack/` (governance) or `docs/RepoMem/persist/` directly — module
  decisions go in `Engine/zhihu/docs/RepoMem/decisions.md`; global promotion happens via YOUR Step 8 merge (HITL).
- `git push` / merge to `main` / rebase / history rewrite — **local commits only** on `feat/agentcrawl-bootstrap`.
- Implementing or calling `Engine/common` LLMClient (SP-2 is pure fetch).
- Editing another session's mailbox (`toSP4aImpler/`, `toOrchestrator/handoff` slots, etc.).

You MAY: read-only git/ls/grep; WebSearch/WebFetch for MediaCrawler/zse-96 research; create your worktree;
`pip`/`npm` read-only queries; TaskCreate/Update for your own progress.

## 6. Branch / worktree state at handoff
- Branch `feat/agentcrawl-bootstrap`; HEAD = orche's SP-2/4a kickoff commit. Tree clean (only the `gstack`
  submodule shows `M` — pre-existing, **never touch**).
- At Stage 3, create your own worktree to isolate from the sibling SP-4a session (avoid shared-index races).

## 7. Status board responsibility
Update `docs/Dashboard/index.md` §SP Status Board SP-2 row on each stage transition
(🟡 wip → ⚫ done), same-row edit, one commit per transition with `docs(SP-2):` prefix.

## 8. Lifecycle of this letter
`burn` after you write `from-sp2impler-sp2-done.md` and orche reads it.

---
**Begin at Step 1 (RepoMem.read), then Step 2 (brainstorming — likely compressed).** Say hi to the user and
ask "ready to start SP-2 brainstorming?" — confirm the zse-96 approach first; it drives the whole design.
