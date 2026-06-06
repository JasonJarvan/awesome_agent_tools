> from: BilibiliCrawl SubOrche (a Claude Code peer session — sub-orchestrator under root orche g4)
> recipient: SP5bImpler (a Claude Code peer session, same cwd as SubOrche = repo root)
> mode: child-handoff (sendbox-protocol Mode A — SubOrche stays alive; you converge back to it)
> purpose: execute the full v2 8-step pipeline for SP-5b (Bilibili Watcher), end-to-end
> lifecycle: burn after you write `from-sp5bimpler-sp5b-done.md` and SubOrche reads it

# SP-5b Handoff — Bilibili Watcher

## 0. What this letter is

A **child-handoff** under sendbox-protocol. You are a peer Claude Code session; your parent is the
**BilibiliCrawl SubOrche** (NOT root orche — root delegated the whole Bilibili downstream vertical to
SubOrche). SubOrche stays alive while you run; you converge back to it. You own SP-5b end-to-end (v2
pipeline steps 1–8).

Runs **in parallel with SP-4b** (Bilibili Skill, a sibling session under the same SubOrche) — independent,
no shared state. Do not wait on SP-4b; do not touch its module.

> ⚠️ **READ FIRST — `docs/RepoMem/persist/architecture/crawl-pipeline.md` §B站链路.** It holds the SP-4a
> root-causes/gotchas **promoted globally specifically so you (running in `Service/crawl/bilibili-watcher/`
> cwd) see them** — the layered-read promotion standard exists for exactly this. Key gotchas you MUST
> respect when calling the engine → BN: **BN `latest` image nginx is broken → host maps backend `:8483`**
> (container `jarvankb-bilinote` already up at `127.0.0.1:3015`); **set `TRANSCRIBER_TYPE=bcut` via
> `POST /api/transcriber_config`, not env**; **bcut + public-video audio download need NO cookie**
> (membership/paid only); **BN has no auth → bind `127.0.0.1` only**; response wrapper `{code,msg,data}`,
> submit→poll `GET /api/task_status/{id}`. The engine already abstracts all this — you call the engine, not
> BN — but you must understand it for the live smoke and deployment.

**Your closest structural template = the just-shipped SP-5a (Zhihu Watcher, ⚫ done + merged 2026-06-07).**
SP-5a is a 7-component resident daemon: `config` / `cookie_provider` / `favorites_client` / `watermark_store`
/ `fetcher` / `saver` / `watcher`, with **APScheduler `BlockingScheduler`** (sync components ⇒ blocking
scheduler + sync job, `max_instances=1`) + **docker-compose** + a **`--once`** smoke mode. Read its
`docs/superpowers/specs/2026-06-02-SP-5a-zhihu-watcher-design.md` — SP-5b mirrors it almost 1:1 EXCEPT the
two B站 deltas below (engine + watermark).

## 1. Subtask scope

Deliver **SP-5b: Bilibili Watcher** (`Service/crawl/bilibili-watcher/`, type=service): a standalone daemon
that polls the user's Bilibili favorites on a schedule, keeps a high-watermark, and on newly-favorited items
transcribes them via the frozen SP-4a engine and saves Markdown — no user interaction (it's a daemon).

**v1 scope (per SP-0 design §7 SP-5b row + the boundaries below — authoritative):**
- ✅ **Standalone service with its OWN scheduler** (`BlockingScheduler`, `max_instances=1`, per the SP-5a
  precedent), default poll **15–30 min** (configurable). NOT SP-1's cron hook.
- ✅ Poll the user's Bilibili **favorites folder(s)** (config-specified favorite-list id/url).
- ✅ On a new item → fetch cookie from SP-1 (active pull, §3.B-cookie) → build `BilibiliCredential` → call the
  **frozen SP-4a engine** `Engine/bilibili/docs/interface.md`: `engine.transcribe(ref, credential=cred)` →
  save `result.render(...).main_markdown` to the configured output dir. (Engine → BN → bcut/字幕 → markdown.)
- ✅ Produce deployment artifacts (Dockerfile / docker-compose / config / `runbook.md`). **Bringing the
  service UP is a USER operation** (per SP-1/SP-4a/SP-5a precedent: "起 Docker 容器是 user 操作").

### ⚠️ WATERMARK — special instruction from the user (2026-06-07), the ONE big SP-5b delta

SP-0 §7 specs the high-watermark on **`fav_time`**. The sister SP-5a (Zhihu) instead shipped a **seen-id
set**, on the reasoning that "Zhihu exposes no reliable favorited-time field" — **the user has flagged that
conclusion as a likely BUG**: SP-5a read `content.created` (the *content's* authoring time) and missed the
**top-level `created`** (sibling to `content`) which the user's own collection-List API response shows is the
**favorite/collected time**. The user's directive, verbatim intent: **do NOT armchair the API the way SP-5a
did.** So SP-5b runs a mandatory empirical-first sub-step BEFORE you design the watermark:

> **Stage 0 (before your design — §3.0): empirically investigate the REAL Bilibili favorites API.**
> Actually call it (`bilibili-api-python` favorite-list, and/or the raw `api.bilibili.com/x/v3/fav/resource/list`
> endpoint) with the user's real cookie, capture a real response, and **document every returned attribute and
> its true meaning** — especially: **is there a per-item favorite-time field (`fav_time`)? distinct from the
> video's publish/`ctime`?** plus the paging model, ordering, and public/private scope. Produce an
> **API-fields research doc**. → **USER REVIEWS + EDITS that doc (HITL gate).** → **THEN** design + implement
> the watermark against the *user-reviewed* doc.

Default toward a **`fav_time` high-watermark** (SP-0 §7 + the user's strong prior that B站 favorites DO carry
`fav_time`); fall back to a seen-id set **only if** the user-reviewed doc shows `fav_time` is unreliable. Note
the paging gotcha SP-5a learned (promoted to §知乎链路): **follow `is_end` / collected-count, never compute a
stop from `offset >= totals`** — an early-stop on a watermark must not skip items spread across pages. Bake
whatever the user-reviewed doc concludes; do not silently pick.

**Cross-SP boundaries you MUST honor (locked, symmetric to the Zhihu vertical — do NOT re-litigate):**
- **Cookie = active PULL, never push.** Pull SESSDATA from SP-1 each cycle (or cache + refresh), decrypt
  transiently in memory (never persist plaintext), build `BilibiliCredential`, inject into the engine.
- **⚠️ Cookie domain = `bilibili.com` (NO leading dot).** Verified 2026-06-02 (`credentials.md §Bilibili`);
  box holds `SESSDATA` + `bili_jct`. `.bilibili.com` returns nothing. (Engine `interface.md §5`'s `.bilibili.com`
  is **stale** — `credentials.md` is authoritative.) Engine is **cookie-less-capable on public videos**
  (metadata + bcut ASR); SESSDATA only engages the subtitle-first path — so a missing cookie degrades, not fatal.
- **Output = configurable output dir, vault-agnostic.** No GBrain frontmatter / no Obsidian taxonomy / no
  Thino (SP-6/SP-7 own that). You decide the per-item filename/subfolder convention (mirror SP-5a's
  subfolder-per-collection + sanitized-title scheme).
- **No LLM / no classification.** Unlike SP-4b, the watcher does NOT use LLMClient and does NOT auto-classify —
  it's a daemon; nobody is present to answer.
- **Self-contained, parallel-independent.** No shared helpers built competitively with SP-4b; minor
  cookie-fetch/save duplication vs SP-4b accepted for v1.
- **Frozen SP-4a engine** — pure consumer, never edit `Engine/bilibili/`.

**Design-time decisions left to YOU (your own compressed brainstorm with the user — §3.B), informed by the
Stage-0 doc:**
- **Watermark store** format/location (json/sqlite under a state dir; survives restart) — its *shape* depends
  on the Stage-0 outcome (`fav_time` cursor vs seen-id set).
- **Which favorite folder(s)** to watch (config: id/url list — it's the user's account) + how to derive the
  fav-list id from a URL.
- **Cookie-pull mechanism** (HTTP GET + Python decrypt, reusing the `credentials.md` reference — cleanest for a
  dockerized Python service; vs CLI shell-out).
- Per-item **filename/subfolder convention** under the output dir; **RenderOptions** for the saved file.
- **Deployment shape** (docker-compose per SP-5a).

**Out of v1 / NOT yours:**
- ❌ SP-4b's interactive skill / vague_path classification / LLMClient.
- ❌ Editing the SP-4a engine — frozen, pure consumer.
- ❌ SP-1 push wiring (cancelled — pull only) / SP-1's cron-hook scheduling (you run your own scheduler).
- ❌ Vault/Obsidian/GBrain/Thino integration; the Zhihu vertical or any non-Bilibili SP.

## 2. Inputs (minimum set — re-fetch others as needed; do NOT expect a context dump)

| File / resource | Role |
|---|---|
| `docs/RepoMem/persist/architecture/crawl-pipeline.md` §B站链路 | **MUST-READ** promoted BN/bcut gotchas (above) |
| `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` §7 (SP-5b row) | **authoritative scope** |
| `CLAUDE.md` §2/§3/§4 | governance — **note §3 step 8 + §4: YOU own RepoMem.merge closure** |
| `Engine/bilibili/docs/interface.md` | **frozen SP-4a engine contract** you program against |
| `Service/crawl/zhihu-watcher/` (SP-5a, ⚫ done) — its `docs/superpowers/specs/2026-06-02-SP-5a-zhihu-watcher-design.md`, frozen `docs/{interface,runbook}.md`, `src/` | **structural template** (7-component daemon, BlockingScheduler, compose, cookie decrypt §3.2, `--once`, error-handling matrix). Mirror it EXCEPT engine + watermark. |
| `docs/RepoMem/persist/architecture/credentials.md` (§Integration contract + §Bilibili) | cookie active-PULL + verified Python decrypt reference + `domain=bilibili.com` |
| `bilibili-api-python` favorites API (WebSearch/WebFetch + actually call it in Stage 0) | the real attribute shapes — **empirically, not from memory** |
| `Service/crawl/bilibili-watcher/docs/{README,interface,architecture}.md` + `docs/RepoMem/{architecture,decisions}.md` | your module skeleton (interface.md placeholder — you freeze it; service ⇒ also write `runbook.md`) |
| `~/.claude/skills/{superpowers/*,repo-mem,sendbox-protocol,cc-dashboard}` | the protocols you operate under |

## 3. Pipeline execution (v2 8-step)

### 3.0 Stage 0 — empirical favorites-API investigation + USER-REVIEW gate (do this FIRST)
Before brainstorming the design: actually call the real Bilibili favorites API with the user's cookie,
capture a real response, and write an **API-fields research doc** →
`Service/crawl/bilibili-watcher/docs/RepoMem/temp/sp5b-bilibili-watcher/favorites-api-fields.md`. Document
each attribute's meaning (confirm `fav_time` exists + is the collected time, distinct from video publish time;
paging model; ordering; public/private). **Stop and ask the user to review + edit that doc** — write a short
`from-sp5bimpler-blocker-fav-api-review.md` to `toBilibiliCrawlOrche/` (or ask in chat) + a Dashboard row. Only
after the user ratifies the doc do you proceed to design the watermark. (If calling the API live needs the
user — fresh cookie / network — surface it as a gate; do not armchair past it.)

### 3.A Step 1 RepoMem.read
Read two layers: global persist (esp. `crawl-pipeline.md §B站链路` + `credentials.md §Bilibili`) + module
(`Service/crawl/bilibili-watcher/docs/RepoMem/{architecture,decisions}.md`).

### 3.B Step 2 brainstorming (compressed — invoke `superpowers:brainstorming`, confirm via direct chat)
Confirm the YOU-owned decisions above (watermark store shaped by the Stage-0 doc, which fav folders, cookie-pull
mechanism, filename convention, deployment shape). Cross-SP boundaries in §1 are locked — do NOT re-litigate.
- design.md → `Service/crawl/bilibili-watcher/docs/superpowers/specs/2026-06-07-SP-5b-bilibili-watcher-design.md`.

**§3.B-cookie — active pull mechanism (pick one in brainstorm):**
- (a) **HTTP `GET /get/:uuid` + decrypt in pure Python** (`cryptography`), reusing the verified reference in
  `credentials.md` (SP-5a `cookie_provider` precedent: `legacy` Salted__ AES-256-CBC + `aes-128-cbc-fixed`).
  Pick the **`bilibili.com`** (no dot) entry. Cleanest for a dockerized Python service (no Node CLI in image).
- (b) **CLI shell-out** `cookie-manager show domain=bilibili.com` — if the CLI is reachable in the runtime.

### 3.C Step 3-4 RepoMem.capture + writing-plans
- temp → `Service/crawl/bilibili-watcher/docs/RepoMem/temp/sp5b-bilibili-watcher/` (the Stage-0 doc lives here too).
- plan → `Service/crawl/bilibili-watcher/docs/superpowers/plans/2026-06-07-SP-5b-bilibili-watcher-plan.md`.
- Stage-2 done → `from-sp5bimpler-plan-ready.md` to `toBilibiliCrawlOrche/` (your parent is SubOrche, NOT root).

### 3.D Step 5-7 execute + verification + finishing
- worktree (`.worktrees/sp5b-bilibili-watcher/`) + TDD + **subagent-driven** (user's standing preference).
- Unit: cookie decrypt (both modes, `bilibili.com` extraction), favorites_client paging (mock HTTP, assert it
  pages to completion + stops on `is_end`/count, parses fields), watermark_store (load/mark/advance, persist
  across reload, atomic write), fetcher (wraps engine; graceful degrade → don't advance watermark on failure),
  saver (filename/subfolder/no-frontmatter convention).
- `verification-before-completion` — live smoke: a real fav folder → `--once` → a new item transcribed via the
  engine (BN at `127.0.0.1:3015`) → saved Markdown; run `--once` again → no new file (watermark/dedup works);
  show the watermark state. **BN must be up** (it already is); bringing it up / `docker compose up` / fresh
  cookie are **USER ops** → surface as a gate (Dashboard row + note to SubOrche). The gate does NOT block
  design/plan/code+unit.
- `requesting-code-review` + `finishing-a-development-branch` — both **ask-first**.

### 3.E Step 8 RepoMem.merge — **YOU OWN THIS** (recipe v2)
Per `CLAUDE.md` §3 step 8 + §4: close merge within your OWN lifecycle (HITL with user). Promote
**cross-SP-reusable** lessons — esp. the **user-reviewed Bilibili favorites-API field semantics** (`fav_time`
truth, paging, ordering) → add to `crawl-pipeline.md §B站链路`, since SP-5b is the first to crawl that endpoint
and a future consumer running in another cwd won't read your module docs. Keep module specifics in
`Service/crawl/bilibili-watcher/docs/RepoMem/decisions.md`. **Mechanism in code does NOT get promoted.** May
delegate *execution* to SubOrche but track to completion before reporting done — **never fire-and-forget**.

## 4. Convergence paths
Parent = BilibiliCrawl SubOrche, cwd = repo root (same as yours). Inbound replies:
`docs/sendbox/toSP5bImpler/from-bilibilicrawlorche-*.md`.

| Event | Write to |
|---|---|
| Stage-0 fav-API doc review | `docs/sendbox/toBilibiliCrawlOrche/from-sp5bimpler-blocker-fav-api-review.md` |
| plan-ready | `docs/sendbox/toBilibiliCrawlOrche/from-sp5bimpler-plan-ready.md` |
| blocker (e.g. BN down / 403 at live smoke) | `docs/sendbox/toBilibiliCrawlOrche/from-sp5bimpler-blocker-<topic>.md` |
| done | `docs/sendbox/toBilibiliCrawlOrche/from-sp5bimpler-sp5b-done.md` |

## 5. Out-of-scope (forbidden)
- Touching SP-4b (`Skill/crawl/bilibili-crawl/`), the SP-4a engine, or any other SP / the Zhihu vertical.
- LLMClient / classification / interactive prompts; SP-1 push wiring or SP-1 cron-hook scheduling.
- Vault/Obsidian/GBrain/Thino semantics.
- Editing `CLAUDE.md` / `docs/HarnessStack/` / `docs/RepoMem/persist/` directly — EXCEPT a `crawl-pipeline.md
  §B站链路` favorites-API addition goes through YOUR Step 8 HITL merge (module decisions only otherwise).
- `git push` / merge-to-main / rebase — **local commits only** on `feat/agentcrawl-bootstrap`.

You MAY: read-only git/ls/grep; WebSearch/WebFetch for bilibili-api-python / scheduler research; **call the
real favorites API in Stage 0**; create your worktree; read-only pkg queries; TaskCreate/Update.

## 6. Branch / worktree / env state
Branch `feat/agentcrawl-bootstrap`; at Stage 3 create your own worktree (isolate from sibling SP-4b). Commit
with prefix `docs(SP-5b):` / `feat(SP-5b):` to limit shared-index races. `gstack` submodule shows `M` —
**never touch**.

## 7. Status board responsibility
The SubOrche flipped §SP Status Board SP-5b → 🟡 wip (owner sp5bimpler) at spawn. Update that row per stage
(🟡 wip → ⚫ done; 🔴 blocked only if a gate stalls), same-row, `docs(SP-5b):` commits.

## 8. Lifecycle
`burn` after you write `from-sp5bimpler-sp5b-done.md` and SubOrche reads it.

---
**Begin at Stage 0 (empirically crawl the favorites API → fields doc → USER REVIEW), then Step 1, then Step 2
(brainstorming).** Greet the user, ask "ready to start SP-5b — beginning with the live favorites-API
investigation?" SP-5a is your mirror for everything EXCEPT the watermark, where the user wants the API
investigated and the doc ratified before you commit a mechanism.
