> from: orchestrator generation 3 (root, Claude Opus 4.8 1M, active 2026-05-31 →)
> recipient: BilibiliCrawlOrche (a Claude Code peer session — a SUB-orchestrator)
> mode: child-handoff (sendbox-protocol Mode A — root orche stays alive; you converge back)
> purpose: delegate the entire Bilibili downstream vertical to you as its sub-orchestrator
> lifecycle: burn after you write `from-bilibilicrawlorche-vertical-done.md` (SP-4b + SP-5b both merged) and root reads it

# Handoff — BilibiliCrawl Sub-Orchestrator

## 0. What you are

You are a **sub-orchestrator** (SubOrche) under root orche (g3), symmetric to the **ZhihuCrawl SubOrche**.
Root stays alive (governance + cross-vertical); you own the **Bilibili downstream vertical** end-to-end.
Hierarchy: `Root Orche → BilibiliCrawlOrche → {SP4bImpler, SP5bImpler}` (longterm.md §Local sendbox conventions).

You do **not** write skill/service code yourself. You **orchestrate**: spawn + coordinate the two implers,
review their plans, greenlight, handle blockers, report vertical completion to root.

## 1. Scope — the Bilibili downstream vertical

Two SPs, both downstream of **SP-4a Bilibili Engine (done, merged 2026-06-02)**:

| SP | Path | What | Status |
|---|---|---|---|
| **SP-4b** Bilibili Skill | `Skill/crawl/bilibili-crawl/` | URL → call SP-4a engine → ask save path + auto-classify (`vague_path`). **Same structure as SP-3 Zhihu Skill.** | ready (dep = SP-4a ✓) |
| **SP-5b** Bilibili Watcher | `Service/crawl/bilibili-watcher/` | favorites polling (default **15–30 min**), high-watermark **`fav_time`**, calls SP-4a engine → BN transcription. **Same structure as SP-5a Zhihu Watcher.** | ready (dep = SP-4a ✓) |

**SP-4b and SP-5b are independent** (neither depends on the other) → run their implers **in parallel**.

**Lean on the just-built Zhihu vertical as a structural template** — SP-4b mirrors SP-3 (skill), SP-5b
mirrors SP-5a (watcher). When SP-3/SP-5a land (they're `wip` now under ZhihuCrawl SubOrche), their
design/plan + the patterns they settle (save-path UX, vague_path classification, scheduler shape) are the
closest reference for your implers. Reuse, don't reinvent.

## 2. How you orchestrate (SubOrche playbook)

Identical to the ZhihuCrawl SubOrche pattern (invoke the `sendbox-protocol` skill):

1. **Spawn each impler** via a Mode-A child-handoff: `docs/sendbox/toSP4bImpler/handoff.md` +
   `docs/sendbox/toSP5bImpler/handoff.md`. Template: the live `toSP3Impler/` + `toSP5aImpler/` handoffs
   (the ZhihuCrawl SubOrche wrote those — read them as your model). Each impler runs the full v2 8-step
   pipeline (compressed brainstorm → design → plan → worktree+TDD+subagent-driven → verify → finish →
   **its own Step 8 merge**).
2. **Mailboxes** (per-task, hard invariant): implers report to **YOUR** inbox
   `docs/sendbox/toBilibiliCrawlOrche/` as `from-sp4bimpler-*.md` / `from-sp5bimpler-*.md`; you reply into
   `toSP4bImpler/` / `toSP5bImpler/`.
3. **Review plan-ready** against SP-0 §7 (rows below) + the engine contract; greenlight.
4. **Each impler OWNS its own `RepoMem.merge` closure** (CLAUDE.md §3 step 8 + §4 — do NOT frame Step 8 as
   "orche's job"). Apply the **promotion standard** (`longterm.md` §Pipeline v2 step 8): cross-SP-reusable
   gotchas → global persist; mechanism stays in code.
5. **Dashboard**: add Type-B rows for the impler sessions the user opens; update SP Status Board SP-4b/SP-5b
   (owner → sp4bimpler / sp5bimpler; status per stage).
6. **Converge to root**: when SP-4b **and** SP-5b are both merged + sendbox chains cleaned, write
   `docs/sendbox/toOrchestrator/from-bilibilicrawlorche-vertical-done.md` (milestone-done roll-up). Root burns this handoff.
7. **Escalate to root** (`from-bilibilicrawlorche-blocker-<topic>.md` → `toOrchestrator/`) only for
   cross-vertical / governance issues.

## 3. Per-SP scope (SP-0 design §7 — authoritative)

**SP-4b Bilibili Skill** (`Skill/crawl/bilibili-crawl/`, type=skill):
- URL → calls the **frozen SP-4a engine contract** `Engine/bilibili/docs/interface.md` (structured
  `BilibiliCredential` input, render switches) → asks save path + **auto-classifies** vague paths.
- Uses `Engine/common` LLMClient for classification. ⚠️ **SP-3 (Zhihu Skill) is landing the FIRST real
  `Engine/common` LLMClient implementation** (per its scope). **SP-4b must REUSE that LLMClient, not
  reimplement it** — coordinate timing with root/ZhihuCrawl SubOrche if SP-3's LLMClient hasn't merged yet
  (a cross-vertical dependency; escalate if it blocks you).
- Cookie: skill **PULLs** from SP-1 cookie-manager (see §4 — `domain=bilibili.com`, SESSDATA) and injects
  the `BilibiliCredential` into the engine.

**SP-5b Bilibili Watcher** (`Service/crawl/bilibili-watcher/`, type=service):
- Polls the user's Bilibili favorites on a schedule (default **15–30 min**), high-watermark on **`fav_time`**,
  calls the SP-4a engine on new items (→ BN transcription).
- ⚠️ **SP-5b MUST read `docs/RepoMem/persist/architecture/crawl-pipeline.md` §B站链路 first** — it holds the
  SP-4a-promoted reusable gotchas (real BN+bcut pipeline; `latest` image nginx broken → map host→backend
  `:8483`; set `TRANSCRIBER_TYPE` via API; bcut needs no cookie; `bilibili-api-python` field shapes).

## 4. Cookie integration (decided — user-ratified 2026-06-02)

**Active PULL only; SP-1 push path is permanently cancelled** (`architecture/credentials.md` §Integration
contract). Both implers fetch SESSDATA from SP-1 cookie-manager via `GET /get/:uuid` + client decrypt (or
`cookie-manager show domain=bilibili.com`), then build a `BilibiliCredential` to inject.
**Critical gotcha (SP-4a-verified):** Bilibili cookies live under **`domain=bilibili.com` (NO leading dot)**,
not `.bilibili.com`. The box holds `SESSDATA` + `bili_jct`. Engine is cookie-less-capable on public videos
(metadata + bcut ASR); SESSDATA only needed for the subtitle-first path.

## 5. Live env state (from SP-4a, ready to use)
- **BiliNote running**: container `jarvankb-bilinote` at `127.0.0.1:3015` (compose maps host→backend `:8483`;
  `TRANSCRIBER_TYPE=bcut`; provider `xiaomitokenplan` = xiaomi mimo `mimo-v2.5-pro`).
- Engine config `Engine/bilibili/config/bilibili-engine.yaml` (gitignored); deploy artifacts `Engine/bilibili/deploy/bilinote/`.

## 6. Inputs you (and your implers) need

| Resource | Role |
|---|---|
| `CLAUDE.md` §2/§3/§4 | governance (impler owns merge closure; promotion standard) |
| `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` §7 (SP-4b/SP-5b) + §8 (LLMClient) | authoritative scope |
| `Engine/bilibili/docs/interface.md` | **frozen SP-4a engine contract** both implers program against |
| `docs/RepoMem/persist/architecture/crawl-pipeline.md` §B站链路 | promoted BN/bcut gotchas (SP-5b must-read) |
| `docs/RepoMem/persist/architecture/credentials.md` (§Integration contract + Bilibili section) | cookie PULL + `bilibili.com` domain |
| `Engine/common/docs/interface.md` | LLMClient contract (SP-4b consumes SP-3's impl) |
| live `toSP3Impler/` + `toSP5aImpler/` handoffs | structural templates for your two implers |
| `~/.claude/skills/{sendbox-protocol,repo-mem,superpowers/*}` | the protocols you operate under |

## 7. Out-of-scope (forbidden)
- The Zhihu vertical (SP-2/3/5a + comment-tree) and any non-Bilibili-downstream SP — root / ZhihuCrawl own those.
- Editing `CLAUDE.md` / `docs/HarnessStack/` / `docs/RepoMem/persist/` directly (governance is root's;
  persist promotion happens via impler Step-8 merges, HITL).
- Re-implementing `Engine/common` LLMClient (SP-3 owns the first impl; SP-4b reuses).
- `git push` / merge to `main` / rebase — **local commits only** on `feat/agentcrawl-bootstrap`.
- Writing skill/service code yourself — you orchestrate; implers implement.

## 8. Env / concurrency at handoff
- Branch `feat/agentcrawl-bootstrap`; tree has `gstack` submodule `M` — **never touch**.
- Concurrent sessions sharing the main tree: root orche, ZhihuCrawl SubOrche + SP3Impler + SP5aImpler, and
  the two implers you'll spawn. Tell each impler to create its **own worktree** at Stage 3 and commit with
  its own prefix (`docs(SP-4b):`/`feat(SP-4b):`, `docs(SP-5b):`/`feat(SP-5b):`) to limit shared-index races.

## 9. Lifecycle
`burn` after you write `from-bilibilicrawlorche-vertical-done.md` (SP-4b + SP-5b both merged) and root reads it.

## 10. First actions when you boot
1. `pwd` + `git log --oneline -5`.
2. Read §6 inputs (top: CLAUDE.md §3/§4, SP-0 §7 SP-4b/SP-5b, `Engine/bilibili/docs/interface.md`,
   crawl-pipeline.md §B站链路, credentials.md cookie sections).
3. Compressed brainstorm scope per SP with the user, then write `toSP4bImpler/handoff.md` + `toSP5bImpler/handoff.md`.
4. Add Dashboard Type-B rows (open SP4bImpler + SP5bImpler sessions) + flip SP Status Board SP-4b/SP-5b → wip.
5. Reply to the user: "BilibiliCrawl SubOrche ready; spawning SP-4b + SP-5b."

— root orche g3
