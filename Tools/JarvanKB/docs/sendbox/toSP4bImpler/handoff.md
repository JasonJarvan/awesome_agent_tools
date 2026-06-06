> from: BilibiliCrawl SubOrche (a Claude Code peer session — sub-orchestrator under root orche g4)
> recipient: SP4bImpler (a Claude Code peer session, same cwd as SubOrche = repo root)
> mode: child-handoff (sendbox-protocol Mode A — SubOrche stays alive; you converge back to it)
> purpose: execute the full v2 8-step pipeline for SP-4b (Bilibili Skill), end-to-end
> lifecycle: burn after you write `from-sp4bimpler-sp4b-done.md` and SubOrche reads it

# SP-4b Handoff — Bilibili Skill

## 0. What this letter is

A **child-handoff** under sendbox-protocol. You are a peer Claude Code session; your parent is the
**BilibiliCrawl SubOrche** (NOT root orche — root delegated the whole Bilibili downstream vertical to
SubOrche). SubOrche stays alive while you run; you converge back to it. You own SP-4b end-to-end (v2
pipeline steps 1–8).

Runs **in parallel with SP-5b** (Bilibili Watcher, a sibling session under the same SubOrche) —
independent, no shared state. Do not wait on SP-5b; do not touch its module.

**Your closest structural template = the just-shipped SP-3 (Zhihu Skill, ⚫ done + merged 2026-06-07).**
SP-4b is the Bilibili analogue: same shape (URL → cookie pull → frozen engine → save + vague_path classify),
same packaging. Reuse, don't reinvent.

## 1. Subtask scope

Deliver **SP-4b: Bilibili Skill** (`Skill/crawl/bilibili-crawl/`, type=skill): given a Bilibili video
reference, transcribe it via the frozen SP-4a engine and save it as Markdown to a user-chosen location;
when the chosen path is vague, auto-classify into a subfolder.

**v1 scope (per SP-0 design §7 SP-4b row + §8 LLMClient + the boundaries below — authoritative):**
- ✅ Video ref (BV id / `bilibili.com` URL / av id) → fetch cookie from SP-1 (active pull, §3.B-cookie) →
  build a `BilibiliCredential(sessdata, bili_jct?, buvid3?)` → call the **frozen SP-4a engine contract**
  `Engine/bilibili/docs/interface.md`: `engine.transcribe(ref, credential=cred) -> BilibiliResult`, then
  `result.render(RenderOptions(...))` → save `rendered.main_markdown` (and the split transcript file if you
  enable `split_transcript`).
- ✅ Ask the user a **save path**; write the Markdown there. **vague_path auto-classify**: when the path is
  vague (root folder / "put it in my KB"), use **LLMClient** to classify into a subfolder under the
  configured output root.
- ✅ **REUSE the real `Engine/common` LLMClient** that **SP-3 already landed** — it is a packaged dist
  `jarvankb-common` (`Engine/common/src/jarvankb_common/llm_client.py`, litellm body, supports custom
  OpenAI-compatible providers). **DO NOT reimplement it** (CLAUDE.md / handoff forbid it; must-read
  `docs/RepoMem/persist/memory/llm-shared-layer.md`). The provider is **already configured** = `mimo-v2.5-pro`
  (xiaomi token-plan, OpenAI protocol) in gitignored `config/llm.yaml` (+ `.env`); **reuse the same profile** —
  so unlike SP-3 at its start, **you have no LLM-creds gate** (creds already exist in the tree).
- ✅ Importable Python API + thin CLI + **one agentskills.io `SKILL.md`** (Claude Code/Codex/OpenClaw/Hermes) —
  mirror SP-3's packaging (`scripts/sync-skill.sh` precedent). Freeze your contract in
  `Skill/crawl/bilibili-crawl/docs/interface.md`.

**Cross-SP boundaries you MUST honor (locked, symmetric to the Zhihu vertical — do NOT re-litigate):**
- **Cookie = active PULL, never push.** SP-1's push path is permanently cancelled. Pull SESSDATA from SP-1
  on demand, decrypt transiently in memory (never persist plaintext), build the `BilibiliCredential`, inject.
- **⚠️ Cookie domain = `bilibili.com` (NO leading dot).** Verified 2026-06-02 (`credentials.md §Bilibili`).
  The box holds `SESSDATA` + `bili_jct` (no `buvid3`). **`.bilibili.com` returns nothing.** NOTE the engine's
  `interface.md §5` still says `.bilibili.com` — that line is **stale**; `credentials.md` is authoritative.
- **Engine is cookie-less-capable on public videos** (metadata + bcut ASR work without SESSDATA); SESSDATA
  only engages the subtitle-first path. So a missing/expired cookie degrades gracefully, not fatally.
- **Output = configurable output root, vault-agnostic.** Write under a `config`-specified output root (user
  MAY point it at an Obsidian vault subdir, but you bake NO vault semantics). vague_path classifies into
  subfolders under that root. **No GBrain frontmatter / no Obsidian taxonomy / no Thino** (SP-6/SP-7 own that).
- **Self-contained, parallel-independent.** Do NOT build shared helpers competitively with SP-5b. The shared
  piece (LLMClient) already exists — you consume it. Minor cookie-fetch/save duplication vs SP-5b is accepted.
- **Frozen SP-4a engine** — pure consumer, never edit `Engine/bilibili/`.

**Design-time decisions left to YOU (your own compressed brainstorm with the user — §3.B):**
- Skill **packaging form** (mirror SP-3: importable `bilibili_crawl.save_bilibili` + thin CLI + agentskills.io
  `SKILL.md` — confirm this is what the user wants for SP-4b too).
- **What content the LLM classifies on.** A video is not an article: you have `result.metadata.title` + BN's
  `result.summary_markdown` + the transcript. Decide the classification input (likely title + summary, with a
  token-saving snippet cap — SP-3's precedent is `classify_snippet_chars` default 240; reuse the idea).
- **RenderOptions defaults** (`include_transcript` / `include_timestamps` / `split_transcript`) for the saved
  file — decide what a B站 note should look like by default (e.g. summary + progressive-disclosure transcript).
- vague_path **classification taxonomy** + the **save-path interaction shape** (what counts as "vague") —
  mirror whatever SP-3 settled (read its design + frozen interface).

**Out of v1 / NOT yours:**
- ❌ Favorites polling (that's SP-5b) and any watcher/daemon behavior.
- ❌ Editing the SP-4a engine (`Engine/bilibili/`) — frozen, pure consumer.
- ❌ Reimplementing `Engine/common` LLMClient (SP-3 landed it; you reuse `jarvankb-common`).
- ❌ Vault/Obsidian/GBrain/Thino integration (SP-6/SP-7). SP-1 push wiring (cancelled).
- ❌ The Zhihu vertical or any non-Bilibili SP.

## 2. Inputs (minimum set — re-fetch others as needed; do NOT expect a context dump)

| File / resource | Role |
|---|---|
| `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` §7 (SP-4b row) + §8 (LLMClient) | **authoritative scope** |
| `CLAUDE.md` §2/§3/§4 | governance — **note §3 step 8 + §4: YOU own RepoMem.merge closure** |
| `Engine/bilibili/docs/interface.md` | **frozen SP-4a engine contract** you program against (v1 frozen API §3, render switches §4, credential boundary §5) |
| `docs/RepoMem/persist/memory/llm-shared-layer.md` | **MUST-READ** — LLMClient real-impl (import/config/custom-provider) + agentskills.io single-`SKILL.md` packaging. **Reuse, do NOT reimplement.** |
| `docs/RepoMem/persist/architecture/credentials.md` (§Integration contract + §Bilibili) | cookie active-PULL + verified Python decrypt reference + `domain=bilibili.com` |
| `Engine/common/docs/interface.md` + `Engine/common/src/jarvankb_common/llm_client.py` | LLMClient frozen contract + real body you consume |
| `Skill/crawl/zhihu-crawl/` (SP-3, ⚫ done) — its `docs/superpowers/specs/2026-06-02-SP-3-zhihu-skill-design.md`, frozen `docs/interface.md`, `SKILL.md`, `src/` | **structural template** (packaging, classify-input, save-path UX, vague_path taxonomy) |
| `Skill/crawl/bilibili-crawl/docs/{README,interface,architecture}.md` + `docs/RepoMem/{architecture,decisions}.md` | your module skeleton (interface.md is a placeholder — you freeze it) |
| `~/.claude/skills/{superpowers/*,repo-mem,sendbox-protocol,cc-dashboard}` | the protocols you operate under |

## 3. Pipeline execution (v2 8-step)

### 3.A Step 1 RepoMem.read
Read two layers: global persist (`docs/RepoMem/persist/`, esp. `memory/llm-shared-layer.md` +
`architecture/credentials.md`) + module (`Skill/crawl/bilibili-crawl/docs/RepoMem/{architecture,decisions}.md`).

### 3.B Step 2 brainstorming (compressed — invoke `superpowers:brainstorming`, confirm via direct chat)
Confirm the YOU-owned design decisions above (packaging form, classify input for a video, RenderOptions
defaults, vague_path taxonomy + save-path interaction). The cross-SP boundaries in §1 are already locked —
do NOT re-litigate them.
- design.md → `Skill/crawl/bilibili-crawl/docs/superpowers/specs/2026-06-07-SP-4b-bilibili-skill-design.md`.

**§3.B-cookie — active pull mechanism (pick one in brainstorm):**
- (a) **HTTP `GET /get/:uuid` + decrypt in pure Python** — reuse the **verified decrypt reference** in
  `credentials.md` (the SP-3 `cookie.py` / SP-5a `cookie_provider` precedent: `legacy` Salted__ AES-256-CBC
  and `aes-128-cbc-fixed`). Pick the **`bilibili.com`** (no dot) entry from the inner `cookie_data`.
- (b) **CLI shell-out** `cookie-manager show domain=bilibili.com` — if the CLI is reachable on the host.
Either way: config needs the SP-1 connection (base URL / uuid / password). Decrypt transiently in memory only.

### 3.C Step 3-4 RepoMem.capture + writing-plans
- temp → `Skill/crawl/bilibili-crawl/docs/RepoMem/temp/sp4b-bilibili-skill/`.
- plan → `Skill/crawl/bilibili-crawl/docs/superpowers/plans/2026-06-07-SP-4b-bilibili-skill-plan.md`.
- Stage-2 done → `from-sp4bimpler-plan-ready.md` to `toBilibiliCrawlOrche/` (your parent is SubOrche, NOT root).

### 3.D Step 5-7 execute + verification + finishing
- worktree (`.worktrees/sp4b-bilibili-skill/`) + TDD + **subagent-driven** (user's standing preference).
- Unit-test the vague_path classification with a **mocked LLMClient**; mock the engine + cookie boundaries.
- `verification-before-completion` — both paths:
  - **Offline / ungated:** explicit-`.md`-path write through a mocked-or-real engine seam; vague_path
    classification unit path.
  - **Live smoke:** a real Bilibili video → engine `transcribe` → save (explicit path) **and** the vague_path
    classification via the real `mimo-v2.5-pro` profile. The engine needs **BiliNote up** — it already is:
    container `jarvankb-bilinote` at `127.0.0.1:3015` (compose maps host→backend `:8483`; `TRANSCRIBER_TYPE=bcut`;
    provider `mimo-v2.5-pro`). If BN is down at smoke time, that's a **gate** (Dashboard row + note to SubOrche),
    not a design blocker. **No LLM-creds gate** (mimo already configured — reuse it).
- `requesting-code-review` + `finishing-a-development-branch` — both **ask-first**.

### 3.E Step 8 RepoMem.merge — **YOU OWN THIS** (recipe v2)
Per `CLAUDE.md` §3 step 8 + §4: close merge within your OWN lifecycle (HITL with user). Promote
**cross-SP-reusable** lessons (e.g. a reusable BilibiliCredential-build pattern, any new B站 engine-consumer
gotcha) to global persist; keep module specifics in `Skill/crawl/bilibili-crawl/docs/RepoMem/decisions.md`.
**Mechanism that lives in code does NOT get promoted.** May delegate *execution* to SubOrche but track to
completion before reporting done — **never fire-and-forget**.

## 4. Convergence paths
Parent = BilibiliCrawl SubOrche, cwd = repo root (same as yours). Inbound replies:
`docs/sendbox/toSP4bImpler/from-bilibilicrawlorche-*.md`.

| Event | Write to |
|---|---|
| plan-ready | `docs/sendbox/toBilibiliCrawlOrche/from-sp4bimpler-plan-ready.md` |
| blocker (e.g. BN down at live smoke) | `docs/sendbox/toBilibiliCrawlOrche/from-sp4bimpler-blocker-<topic>.md` |
| done | `docs/sendbox/toBilibiliCrawlOrche/from-sp4bimpler-sp4b-done.md` |

## 5. Out-of-scope (forbidden)
- Touching SP-5b (`Service/crawl/bilibili-watcher/`), the SP-4a engine, or any other SP / the Zhihu vertical.
- Reimplementing `Engine/common` LLMClient; baking LLM credentials into the repo.
- Vault/Obsidian/GBrain/Thino semantics; SP-1 push wiring.
- Editing `CLAUDE.md` / `docs/HarnessStack/` / `docs/RepoMem/persist/` directly (module decisions only;
  global promotion via YOUR Step 8 HITL merge).
- `git push` / merge-to-main / rebase — **local commits only** on `feat/agentcrawl-bootstrap`.

You MAY: read-only git/ls/grep; WebSearch/WebFetch for litellm / bilibili-api-python research; create your
worktree; read-only pkg queries; TaskCreate/Update.

## 6. Branch / worktree / env state
Branch `feat/agentcrawl-bootstrap`; at Stage 3 create your own worktree (isolate from sibling SP-5b). Commit
with prefix `docs(SP-4b):` / `feat(SP-4b):` to limit shared-index races. `gstack` submodule shows `M` —
**never touch**.

## 7. Status board responsibility
The SubOrche flipped §SP Status Board SP-4b → 🟡 wip (owner sp4bimpler) at spawn. Update that row per stage
(🟡 wip → ⚫ done; 🔴 blocked only if the BN gate stalls), same-row, `docs(SP-4b):` commits.

## 8. Lifecycle
`burn` after you write `from-sp4bimpler-sp4b-done.md` and SubOrche reads it.

---
**Begin at Step 1, then Step 2 (brainstorming).** Greet the user, ask "ready to start SP-4b brainstorming?" —
the cross-SP boundaries are locked; your brainstorm is only the YOU-owned design decisions in §1. SP-3 is your
mirror: read its design + frozen interface first so you reuse rather than reinvent.
