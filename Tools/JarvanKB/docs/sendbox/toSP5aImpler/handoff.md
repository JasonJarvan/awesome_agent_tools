> from: ZhihuCrawl SubOrche (a Claude Code peer session — sub-orchestrator under root orche g3)
> recipient: SP5aImpler (a Claude Code peer session, same cwd as SubOrche = repo root)
> mode: child-handoff (sendbox-protocol Mode A — SubOrche stays alive; you converge back to it)
> purpose: execute the full v2 8-step pipeline for SP-5a (Zhihu Watcher), end-to-end
> lifecycle: burn after you write `from-sp5aimpler-sp5a-done.md` and SubOrche reads it

# SP-5a Handoff — Zhihu Watcher

## 0. What this letter is

A **child-handoff** under sendbox-protocol. You are a peer Claude Code session; your parent is the
**ZhihuCrawl SubOrche** (NOT root orche — root delegated the whole Zhihu vertical to SubOrche). SubOrche
stays alive while you run; you converge back to it. You own SP-5a end-to-end (v2 pipeline steps 1–8).

Runs **in parallel with SP-3** (Zhihu Skill, a sibling session under the same SubOrche) — independent,
no shared state. Do not wait on SP-3; do not touch its module.

## 1. Subtask scope

Deliver **SP-5a: Zhihu Watcher** (`Service/crawl/zhihu-watcher/`, type=service): a standalone service that
polls the user's Zhihu favorites on a schedule, keeps a high-watermark, and on new items fetches them via the
frozen SP-2 engine and saves Markdown — no user interaction (it's a daemon).

> ⚠️ **READ FIRST — `docs/RepoMem/persist/architecture/crawl-pipeline.md` §知乎链路.** It holds the SP-2
> root-causes/gotchas **promoted globally specifically so you (running in `Service/crawl/zhihu-watcher/` cwd)
> see them** — the layered-read promotion standard exists for exactly this. Key gotchas you MUST respect:
> `comment_v5` **offset is poison → use cursor paging** (first call `order_by`+`limit`, follow `paging.next`
> to `is_end`); **`js-initialData` camelCase vs `/api/v4` snake_case** (dual-key fallback); **no `x-zse-96`
> signing needed** (2026-06 confirmed); **Zhihu direct-connect `trust_env=False`** (host has `HTTP_PROXY`/
> `ALL_PROXY` for overseas sites; Zhihu is a mainland site — proxying it is slow + risk-flagged). These were
> learned on the answer/comment path; the favorites-list API is a different endpoint but the same idioms apply.

**v1 scope (per SP-0 design §7 SP-5a row + the SubOrche brainstorm decisions below — authoritative):**
- ✅ **Standalone service with its OWN scheduler** (asyncio loop / APScheduler), default poll **30–60 min**
  (configurable). **User decision: standalone + own scheduler, NOT SP-1's cron hook.** This becomes the
  isomorphic precedent for SP-5b (Bilibili Watcher).
- ✅ Poll the user's Zhihu **favorites / collection folder(s)** (config-specified collection id/url).
- ✅ **High-watermark on `created`** — persist the watermark; on each poll, fetch only items newer than it,
  advance it, and dedup so an item is never re-fetched.
- ✅ On a new item → fetch cookie from SP-1 (active pull, §3.B-cookie) → call **frozen SP-2 engine contract**
  `Engine/zhihu/docs/interface.md`: `fetch(url, cookies, ...) -> FetchResult` then `.to_markdown()`.
- ✅ Save Markdown to the **configured output dir** (no interactive prompt, no LLM classification — it's a
  daemon; nobody is present to answer).
- ✅ Produce deployment artifacts (docker-compose / config / runbook). **Bringing the service UP is a USER
  operation** (per SP-1/SP-4a precedent: "起 Docker 容器是 user 操作").

**SubOrche brainstorm decisions you MUST honor (cross-SP boundaries — locked with the user 2026-06-02):**
- **Cookie = active PULL, never push.** SP-1's push path (write_file hook → "SP-1b") is **permanently
  cancelled** (cross-vertical decision, escalated to root). Pull cookies from SP-1 each poll cycle (or cache +
  refresh) and inject into `fetch(cookies=...)`. See §3.B-cookie. Always uses the latest stored cookie;
  decrypt only transiently in memory — never persist plaintext cookies to disk.
- **Output = configurable output dir, vault-agnostic.** Save under a `config`-specified output dir (the user
  MAY point it at an Obsidian vault subdir, but you do NOT bake vault semantics). **No GBrain frontmatter /
  no Obsidian taxonomy / no Thino** — SP-6/SP-7 own that.
- **No LLM / no classification.** Unlike SP-3, the watcher does NOT use LLMClient and does NOT auto-classify —
  it saves new items to the configured dir (you decide the per-item filename/subfolder convention in design).
- **Self-contained, parallel-independent.** Do NOT build shared `Engine/common` helpers competitively with
  SP-3. Minor cookie-fetch/save duplication vs SP-3 is accepted for v1; consolidation is deferred.

**Out of v1 / NOT yours:**
- ❌ The v1.1 comment full-tree (handoff drafted at `toZhihuCommentImpler/` — **do NOT start**, user greenlight pending).
- ❌ SP-3's interactive skill / vague_path classification / LLMClient.
- ❌ Editing the SP-2 engine — frozen, pure consumer.
- ❌ SP-1 push wiring (cancelled — pull only); SP-1's cron-hook scheduling (you run your own scheduler).
- ❌ Vault/Obsidian/GBrain/Thino integration.

**Design-time decisions left to YOU (your own compressed brainstorm with the user):**
- **Favorites-list API mechanism** (which Zhihu endpoint lists a collection's items, paging — respect the
  §知乎链路 cursor-paging idiom) and **which collection(s)** to watch (config: id/url list — it's the user's account).
- **Watermark store** format/location (json/sqlite file under a state dir? what survives restart).
- **Scheduler** choice (asyncio loop vs APScheduler) + **deployment shape** (docker-compose vs systemd).
- Per-item **filename/subfolder convention** under the output dir.

## 2. Inputs (minimum set — re-fetch others as needed; do NOT expect a context dump)

| File / resource | Role |
|---|---|
| `docs/RepoMem/persist/architecture/crawl-pipeline.md` §知乎链路 | **MUST-READ** promoted Zhihu gotchas (above) |
| `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` §7 (SP-5a row) | **authoritative scope** |
| `CLAUDE.md` §2/§3/§4 | governance — **note §3 step 8 + §4: YOU own RepoMem.merge closure** |
| `Engine/zhihu/docs/interface.md` | **frozen SP-2 engine contract** you program against |
| `Service/crawl/zhihu-watcher/docs/{README,interface,architecture}.md` + `docs/RepoMem/{architecture,decisions}.md` | your module skeleton (interface.md is a placeholder — you freeze it; service ⇒ also write `runbook.md`) |
| `Service/crawl/cookie-manager/docs/interface.md` | SP-1 cookie integration — §7 active-pull path + §3 decrypt protocol + §4 CLI |
| `~/.claude/skills/{superpowers/*,repo-mem,sendbox-protocol,cc-dashboard}` | the protocols you operate under |

## 3. Pipeline execution (v2 8-step)

### 3.A Step 1 RepoMem.read
Read two layers: global persist (esp. `crawl-pipeline.md §知乎链路`) + module
(`Service/crawl/zhihu-watcher/docs/RepoMem/{architecture,decisions}.md`).

### 3.B Step 2 brainstorming (compressed — invoke `superpowers:brainstorming`, confirm via direct chat)
Confirm the YOU-owned design decisions above (favorites API + collection selection, watermark store,
scheduler/deployment shape, filename convention). The cross-SP boundaries in §1 are already locked — do NOT
re-litigate them.
- design.md → `Service/crawl/zhihu-watcher/docs/superpowers/specs/2026-06-02-SP-5a-zhihu-watcher-design.md`.

**§3.B-cookie — active pull mechanism (pick one in brainstorm):**
- (a) **HTTP `GET /get/:uuid` + decrypt** per `interface.md §3` (legacy AES / aes-128-cbc-fixed) — clean for a
  dockerized Python service (no Node CLI in the image).
- (b) **CLI shell-out** `cookie-manager show domain=.zhihu.com` — if the CLI is reachable in the service runtime.
Config needs the SP-1 connection (base URL / uuid / password, or CLI+config path).

### 3.C Step 3-4 RepoMem.capture + writing-plans
- temp → `Service/crawl/zhihu-watcher/docs/RepoMem/temp/sp5a-zhihu-watcher/`.
- plan → `Service/crawl/zhihu-watcher/docs/superpowers/plans/2026-06-02-SP-5a-zhihu-watcher-plan.md`.
- Stage-2 done → `from-sp5aimpler-plan-ready.md` to `toZhihuCrawlOrche/` (NOT toOrchestrator — your parent is SubOrche).

### 3.D Step 5-7 execute + verification + finishing
- worktree (`.worktrees/sp5a-zhihu-watcher/`) + TDD + **subagent-driven** (user's standing preference).
- `verification-before-completion`: tests + lint/typecheck + a manual smoke — poll a real (small) collection,
  show watermark advance + a new item fetched → saved Markdown; show that a second poll re-fetches nothing
  (dedup/watermark works). If bringing the service up for the live smoke needs the user (docker), surface it
  like a gate (Dashboard row + note to SubOrche) — do NOT block design/plan on it.
- `requesting-code-review` + `finishing-a-development-branch` — both **ask-first**.

### 3.E Step 8 RepoMem.merge — **YOU OWN THIS** (recipe v2)
Per `CLAUDE.md` §3 step 8 + §4: the implementer closes merge within its OWN lifecycle (HITL with user).
Promote **cross-SP-reusable** lessons (e.g. a reusable favorites-poll/high-watermark pattern, any new Zhihu
favorites-API gotcha worth adding to `crawl-pipeline.md §知乎链路`) to global persist; keep module specifics
in `Service/crawl/zhihu-watcher/docs/RepoMem/decisions.md`. May delegate *execution* to SubOrche but track to
completion before reporting done — **never fire-and-forget**.

## 4. Convergence paths
Parent = ZhihuCrawl SubOrche, cwd = repo root (same as yours). Inbound replies: `docs/sendbox/toSP5aImpler/from-zhihucrawlorche-*.md`.

| Event | Write to |
|---|---|
| plan-ready | `docs/sendbox/toZhihuCrawlOrche/from-sp5aimpler-plan-ready.md` |
| blocker (incl. live-smoke docker gate) | `docs/sendbox/toZhihuCrawlOrche/from-sp5aimpler-blocker-<topic>.md` |
| done | `docs/sendbox/toZhihuCrawlOrche/from-sp5aimpler-sp5a-done.md` |

## 5. Out-of-scope (forbidden)
- Touching SP-3 (`Skill/crawl/zhihu-crawl/`), the SP-2 engine, or any other SP.
- LLMClient / classification / interactive prompts; SP-1 push wiring or SP-1 cron-hook scheduling.
- Vault/Obsidian/GBrain/Thino semantics; v1.1 comment-tree.
- Editing `CLAUDE.md` / `docs/HarnessStack/` / `docs/RepoMem/persist/` directly — EXCEPT a `crawl-pipeline.md
  §知乎链路` gotcha addition goes through YOUR Step 8 HITL merge (module decisions only otherwise).
- `git push` / merge-to-main / rebase — **local commits only** on `feat/agentcrawl-bootstrap`.

You MAY: read-only git/ls/grep; WebSearch/WebFetch for Zhihu favorites-API / scheduler research; create your
worktree; read-only pkg queries; TaskCreate/Update.

## 6. Branch / worktree / env state
Branch `feat/agentcrawl-bootstrap`; at Stage 3 create your own worktree (isolate from sibling SP-3 +
the live SP4aImpler). Commit with prefix `docs(SP-5a):` / `feat(SP-5a):` to limit shared-index races.
`gstack` submodule shows `M` — **never touch**.

## 7. Status board responsibility
The SubOrche flipped §SP Status Board SP-5a → 🟡 wip (owner sp5aimpler) at spawn. Update that row per stage
(🟡 wip → ⚫ done; 🔴 blocked only if a gate stalls), same-row, `docs(SP-5a):` commits.

## 8. Lifecycle
`burn` after you write `from-sp5aimpler-sp5a-done.md` and SubOrche reads it.

---
**Begin at Step 1 (READ `crawl-pipeline.md §知乎链路` FIRST), then Step 2 (brainstorming).** Greet the user,
ask "ready to start SP-5a brainstorming?" — the cross-SP boundaries are locked; your brainstorm is only the
YOU-owned design decisions in §1.
