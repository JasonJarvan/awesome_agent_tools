> from: orchestrator generation 3 (Claude Opus 4.8 1M, active 2026-05-31 →)
> recipient: SP4aImpler (a Claude Code peer session, same cwd as orche)
> mode: child-handoff (sendbox-protocol Mode A — orche stays alive; you converge back)
> purpose: execute the full v2 8-step pipeline for SP-4a (Bilibili Engine), end-to-end
> lifecycle: burn after you write `from-sp4aimpler-sp4a-done.md` and orche reads it

# SP-4a Handoff — Bilibili Engine

## 0. What this letter is

A **child-handoff** under sendbox-protocol. You are a peer Claude Code session; orche (g3) stays alive while
you run. You own SP-4a end-to-end (v2 pipeline 1–8). Runs **in parallel with SP-2** (Zhihu Engine, a sibling
session) — independent, no shared state.

**Staged like SP-1** (design/plan now, execute gated):

| Stage | Scope | Gate |
|---|---|---|
| Stage 1 design | brainstorming → design.md | none — start now |
| Stage 2 plan | writing-plans → plan.md + plan-ready letter | none |
| Stage 3 execute | worktree + TDD → done | **GATED on BiliNote (BN) docker reachable** (see §3.D) |

## 1. Subtask scope

Deliver **SP-4a: Bilibili Engine** — a library (`Engine/bilibili/`) that, given a Bilibili video (BV id / URL),
returns metadata + a transcript (and summary/chapters when available) as Markdown + structured data.

**v1 scope (per SP-0 design §7 — this is authoritative):**
- ✅ **Metadata** via `bilibili-api-python` (title, up, duration, bvid, cid, publish date, …). Needs
  **SESSDATA cookie** for some content — sourced from SP-1 cookie-manager (see cookie note below).
- ✅ **Transcript via a subtitle-first cascade:**
  1. **Subtitle first** — BiliNote's built-in subtitle path / `bilibili-api-python.get_subtitle(cid)`
     (official or AI CC; needs SESSDATA). Zero-cost when present (~30%+ of videos).
  2. **ASR fallback = BiliNote Docker + `TRANSCRIBER_TYPE=bcut`** (B站必剪 free cloud ASR). You are a
     **BiliNote HTTP/Docker client** — BiliNote does the audio extraction + ASR; you call it and parse results.
- ✅ Output Markdown (transcript + summary + chapters if BN returns them) + JSON metadata.
- ✅ Importable Python API (frozen in `Engine/bilibili/docs/interface.md`) + thin CLI for manual testing.

**Out of v1 / NOT yours (critical — avoid the superseded design):**
- ❌ **NO 通义听悟 (Tingwu) / Aliyun OSS / yt-dlp audio-extract pipeline.** That was the **pre-R5 design and
  is SUPERSEDED.** `crawl-pipeline.md`'s Bilibili section still shows it — **ignore that section entirely**;
  R5 switched ASR to **BiliNote + bcut** and dropped Aliyun from v1 (see `version-plan.md` + `credentials.md`).
- ❌ No full-video download / clipping (audio/transcript only — and BN handles extraction, not you).
- ❌ No summarization via LLMClient (BN+bcut provides summary/chapters; engine does not call an LLM).
- ❌ No favorites polling (SP-5b Watcher) and no Skill wiring (SP-4b).

**Cookie note:** Like SP-2, design the engine to **accept SESSDATA / cookies as INPUT** (pure, testable);
the SP-4b Skill / SP-5b Watcher fetches them from SP-1 cookie-manager
(`Service/crawl/cookie-manager/docs/interface.md`, domain `.bilibili.com`). Confirm boundary in brainstorming.

## 2. Inputs (minimum set)

| File / resource | Role |
|---|---|
| `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` §7 (SP-4a row) | **authoritative scope** |
| `CLAUDE.md` §2/§3/§4 | governance — **note §3 step 8 + §4: YOU own RepoMem.merge closure** |
| `Engine/bilibili/docs/{README,interface,architecture}.md` | your module skeleton |
| `Service/crawl/cookie-manager/docs/interface.md` + `docs/RepoMem/persist/architecture/credentials.md` | SESSDATA cookie integration |
| **BiliNote upstream** (research): its Docker image, HTTP API, and `TRANSCRIBER_TYPE=bcut` config | core dependency — research deeply before design (WebSearch/WebFetch) |
| **bilibili-api-python** (research): metadata + `get_subtitle(cid)` | metadata + subtitle path |
| `Engine/common/docs/interface.md` | LLMClient (skeleton; you do NOT implement/call it) |

⚠️ **Do NOT treat `crawl-pipeline.md`'s Bilibili pipeline as current** — it is R5-superseded (Tingwu/OSS/yt-dlp).
Only SP-0 §7 + your own BiliNote research are authoritative.

## 3. Pipeline execution (v2 8-step)

### 3.A Step 1 RepoMem.read — global persist + `Engine/bilibili/docs/RepoMem/{architecture,decisions}.md`.

### 3.B Step 2 brainstorming (compressed — invoke `superpowers:brainstorming`, confirm via direct chat)
Confirm: (a) BiliNote deployment shape (self-host Docker; who runs it — see §3.D); (b) subtitle-vs-ASR
cascade + how bcut is configured in BN; (c) cookie-injection boundary; (d) output Markdown shape; (e) BN
API surface (submit job → poll → parse transcript/summary/chapters).
- design.md → `Engine/bilibili/docs/superpowers/specs/2026-05-31-SP-4a-bilibili-engine-design.md`.

### 3.C Step 3-4 RepoMem.capture + writing-plans
- temp → `Engine/bilibili/docs/RepoMem/temp/sp4a-bilibili-engine/`; plan → `.../plans/2026-05-31-SP-4a-bilibili-engine-plan.md`.
- Stage-2 done → `from-sp4aimpler-plan-ready.md` to `toOrchestrator/`.

### 3.D Stage 2 → Stage 3 gate: **BiliNote docker reachable**
BiliNote is a third-party self-hosted Docker tool you consume as a client. To run Stage 3 (execute + the
mandatory manual smoke), a BN instance must be reachable. **Deploying/running BN docker is a USER action**
(per SP-1 precedent: "起 Docker 容器是 user 操作"). When you reach the gate:
- Produce the BN `docker-compose` / config + the env (`TRANSCRIBER_TYPE=bcut`) as part of your plan, then
- write `from-sp4aimpler-blocker-bn-docker.md` (or ask the user in chat) requesting the user bring BN up and
  confirm its endpoint. Track Dashboard **UN-018**. Do NOT block Stage 1/2 on this.

### 3.E Step 5-7 execute + verification + finishing
- worktree (`.worktrees/sp4a-bilibili-engine/`) + TDD + **subagent-driven** (user's standing preference).
- `verification-before-completion`: tests + lint/typecheck + **mandatory manual smoke** against a live BN
  (one BV with subtitle → subtitle path; one without → bcut ASR path; show resulting Markdown).
- `requesting-code-review` + `finishing-a-development-branch` — both **ask-first**.

### 3.F Step 8 RepoMem.merge — **YOU OWN THIS** (recipe v2, updated)
Per `CLAUDE.md` §3 step 8 + §4: **the implementer closes merge within its OWN lifecycle** (HITL with user).
Promote global-scope lessons (e.g. a reusable BiliNote-client / subtitle-cascade pattern) to
`docs/RepoMem/persist/`; keep module specifics in `Engine/bilibili/docs/RepoMem/decisions.md`. May delegate
*execution* to orche but track to completion before reporting done — **never fire-and-forget**.

## 4. Convergence paths
Parent cwd = repo root (same as yours). Inbound replies: `docs/sendbox/toSP4aImpler/from-orche-*.md`.

| Event | Write to |
|---|---|
| plan-ready | `docs/sendbox/toOrchestrator/from-sp4aimpler-plan-ready.md` |
| blocker (incl. BN-docker gate) | `docs/sendbox/toOrchestrator/from-sp4aimpler-blocker-<topic>.md` |
| done | `docs/sendbox/toOrchestrator/from-sp4aimpler-sp4a-done.md` |

## 5. Out-of-scope (forbidden)
- Touching SP-2 (`Engine/zhihu/`) or any other SP — sibling SP2Impler owns Zhihu.
- The superseded Tingwu/OSS/Aliyun path (out of v1).
- Editing `CLAUDE.md`/`docs/HarnessStack/`/`docs/RepoMem/persist/` directly (module decisions only; global via YOUR Step 8 merge).
- `git push`/merge-to-main/rebase — **local commits only**.
- Implementing/calling LLMClient.

You MAY: read-only git/ls/grep; WebSearch/WebFetch for BiliNote/bilibili-api research; create your worktree;
read-only pkg queries; TaskCreate/Update.

## 6. Branch / worktree state
Branch `feat/agentcrawl-bootstrap`; at Stage 3 create your own worktree (isolate from sibling SP-2). `gstack` submodule `M` — never touch.

## 7. Status board responsibility
Update §SP Status Board SP-4a row per stage (🟡 wip → 🔴 blocked at BN gate → 🟡 wip → ⚫ done), same-row, `docs(SP-4a):` commits.

## 8. Lifecycle
`burn` after you write `from-sp4aimpler-sp4a-done.md` and orche reads it. (Multi-stage: persists across stage transitions, burns at convergence.)

---
**Begin at Step 1, then Step 2 (brainstorming).** Greet the user, ask "ready to start SP-4a brainstorming?" —
research BiliNote's API + bcut first; it drives the design. Remember: BiliNote+bcut, NOT Tingwu.
