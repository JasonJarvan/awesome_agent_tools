> from: ZhihuCrawl SubOrche (a Claude Code peer session — sub-orchestrator under root orche g3)
> recipient: SP3Impler (a Claude Code peer session, same cwd as SubOrche = repo root)
> mode: child-handoff (sendbox-protocol Mode A — SubOrche stays alive; you converge back to it)
> purpose: execute the full v2 8-step pipeline for SP-3 (Zhihu Skill), end-to-end
> lifecycle: burn after you write `from-sp3impler-sp3-done.md` and SubOrche reads it

# SP-3 Handoff — Zhihu Skill

## 0. What this letter is

A **child-handoff** under sendbox-protocol. You are a peer Claude Code session; your parent is the
**ZhihuCrawl SubOrche** (NOT root orche — root delegated the whole Zhihu vertical to SubOrche). SubOrche
stays alive while you run; you converge back to it. You own SP-3 end-to-end (v2 pipeline steps 1–8).

Runs **in parallel with SP-5a** (Zhihu Watcher, a sibling session under the same SubOrche) — independent,
no shared state. Do not wait on SP-5a; do not touch its module.

## 1. Subtask scope

Deliver **SP-3: Zhihu Skill** (`Skill/crawl/zhihu-crawl/`, type=skill): given a Zhihu URL, fetch the content
via the frozen SP-2 engine and save it as Markdown to a user-chosen location; when the chosen path is vague,
auto-classify into a subfolder.

**v1 scope (per SP-0 design §7 SP-3 row + the SubOrche brainstorm decisions below — authoritative):**
- ✅ URL → fetch cookie from SP-1 (active pull, see §3.B-cookie) → call **frozen SP-2 engine contract**
  `Engine/zhihu/docs/interface.md`: `fetch(url, cookies, ...) -> FetchResult` then `.to_markdown()`.
- ✅ Ask the user a **save path**; write the Markdown there.
- ✅ **vague_path auto-classify**: when the user's path is vague (e.g. a root folder / "put it in my KB"),
  use **LLMClient** to classify the content into a subfolder under the configured output root.
- ✅ **Implement the REAL `Engine/common` LLMClient body** (litellm) — SP-3 is the first consumer
  (SP-0 §8: "first real impl with SP-3 or SP-6"). **User decision: SP-3 lands the real body** so SP-6 reuses
  it (don't leave it a stub). Provide `llm.yaml.example`; **do NOT bake real credentials/model** — surface a
  fill-creds action at verify (see §3.E-creds). Freeze the LLMClient body + document it in
  `Engine/common/docs/interface.md` (mark "real impl landed in SP-3") so SP-6 does not redo it.
- ✅ Importable Python API + thin CLI (frozen in `Skill/crawl/zhihu-crawl/docs/interface.md`).

**SubOrche brainstorm decisions you MUST honor (cross-SP boundaries — locked with the user 2026-06-02):**
- **Cookie = active PULL, never push.** SP-1's push path (write_file hook → "SP-1b") is **permanently
  cancelled** (cross-vertical decision, escalated to root). You pull cookies from SP-1 on demand and inject
  them into `fetch(cookies=...)`. See §3.B-cookie for the two pull mechanisms; pick one in your brainstorm.
- **Output = configurable output root, vault-agnostic.** Write Markdown under a `config`-specified output
  root (the user MAY point it at an Obsidian vault subdir, but you do NOT bake vault semantics). vague_path
  classifies into subfolders **under that root**. **No GBrain frontmatter / no Obsidian-vault taxonomy /
  no Thino semantics** — those belong to SP-6/SP-7, out of your scope.
- **Self-contained, parallel-independent.** Do NOT build shared `Engine/common` helpers competitively with
  SP-5a (cookie-fetch/save). The ONE shared piece you own is **LLMClient** (SP-5a doesn't use it). Minor
  cookie-fetch/save duplication vs SP-5a is accepted for v1; consolidation is deferred.

**Out of v1 / NOT yours:**
- ❌ Vault/Obsidian/GBrain/Thino integration (SP-6/SP-7 own it).
- ❌ Favorites polling (that's SP-5a) and the v1.1 comment full-tree (handoff drafted at
  `toZhihuCommentImpler/` — **do NOT start**, user greenlight pending).
- ❌ Editing the SP-2 engine (`Engine/zhihu/`) — frozen, you are a pure consumer.
- ❌ SP-1 push wiring (cancelled — pull only).

**Design-time decisions left to YOU (your own compressed brainstorm with the user):**
- Skill **packaging form** (Claude Code `SKILL.md` + scripts vs Python package/CLI vs both).
- vague_path **classification taxonomy** (config-driven category list? infer from existing subfolders?
  what the LLM classifies *into*).
- The **"ask the user a save path"** interaction shape (prompt format, what counts as "vague").
- **LLMClient config path**: confirm where `Engine/common`'s loader reads `llm.yaml` (align with its actual
  loader + the module-local config precedent — recent SP-4a commit moved spec config to module-local; SP-0 §8
  shows `<root>/config/llm.yaml`). Don't hardcode my guess; confirm and create the `.example` at the real path.

## 2. Inputs (minimum set — re-fetch others as needed; do NOT expect a context dump)

| File / resource | Role |
|---|---|
| `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` §7 (SP-3 row) + §8 (LLMClient) | **authoritative scope** |
| `CLAUDE.md` §2/§3/§4 | governance — **note §3 step 8 + §4: YOU own RepoMem.merge closure** |
| `Engine/zhihu/docs/interface.md` | **frozen SP-2 engine contract** you program against |
| `Skill/crawl/zhihu-crawl/docs/{README,interface,architecture}.md` + `docs/RepoMem/{architecture,decisions}.md` | your module skeleton (interface.md is a placeholder — you freeze it) |
| `Service/crawl/cookie-manager/docs/interface.md` | SP-1 cookie integration — §7 active-pull path + §3 decrypt protocol + §4 CLI |
| `Engine/common/docs/interface.md` + `Engine/common/src/llm_client.py` | LLMClient contract + skeleton (you implement the body) |
| `~/.claude/skills/{superpowers/*,repo-mem,sendbox-protocol,cc-dashboard}` | the protocols you operate under |

## 3. Pipeline execution (v2 8-step)

### 3.A Step 1 RepoMem.read
Read two layers: global persist (`docs/RepoMem/persist/`) + module (`Skill/crawl/zhihu-crawl/docs/RepoMem/{architecture,decisions}.md`).

### 3.B Step 2 brainstorming (compressed — invoke `superpowers:brainstorming`, confirm via direct chat)
Confirm the YOU-owned design decisions above (packaging form, classification taxonomy, save-path interaction,
LLMClient config path). The cross-SP boundaries in §1 are already locked — do NOT re-litigate them.
- design.md → `Skill/crawl/zhihu-crawl/docs/superpowers/specs/2026-06-02-SP-3-zhihu-skill-design.md`.

**§3.B-cookie — active pull mechanism (pick one in brainstorm):**
- (a) **CLI shell-out**: `cookie-manager show domain=.zhihu.com` — SP-1 CLI decrypts for you; easiest when the
  skill runs on the host where cookie-manager is installed. Parse stdout → cookie dict.
- (b) **HTTP `GET /get/:uuid` + decrypt**: pull ciphertext, decrypt client-side per `interface.md §3`
  (legacy AES / aes-128-cbc-fixed). No CLI dependency; needs a small decrypt in Python.
Either way: config needs the SP-1 connection (base URL / uuid / password, or CLI+config path). Cookie is
decrypted only transiently in memory — never persist plaintext cookies to disk.

### 3.C Step 3-4 RepoMem.capture + writing-plans
- temp → `Skill/crawl/zhihu-crawl/docs/RepoMem/temp/sp3-zhihu-skill/`.
- plan → `Skill/crawl/zhihu-crawl/docs/superpowers/plans/2026-06-02-SP-3-zhihu-skill-plan.md`.
- Stage-2 done → `from-sp3impler-plan-ready.md` to `toZhihuCrawlOrche/` (NOT toOrchestrator — your parent is SubOrche).

### 3.D Step 5-7 execute + verification + finishing
- worktree (`.worktrees/sp3-zhihu-skill/`) + TDD + **subagent-driven** (user's standing preference).
- Unit-test the vague_path classification with a **mocked LLMClient** (no live creds needed for unit tests).
- `verification-before-completion`: tests + lint/typecheck + a manual smoke (one Zhihu URL → engine → save
  with an explicit path; and the vague_path classification path — see §3.E-creds for the live-LLM gate).
- `requesting-code-review` + `finishing-a-development-branch` — both **ask-first**.

**§3.E-creds — LLMClient credentials gate (user decision: "完成后通知我待我自己填"):**
Do NOT bake real LLM credentials. When you reach verify and need a **live** vague_path classification:
1. Provide `llm.yaml.example` (default `claude-opus-4-7`, fallback `dashscope/qwen-max` per SP-0 §8;
   real keys in `.env`, not in repo).
2. Add a **Dashboard Type-F row** ("填 `config/llm.yaml` LLM 凭据 → 解锁 SP-3 vague_path live smoke") and a
   short note `from-sp3impler-blocker-llm-creds.md` to `toZhihuCrawlOrche/` (or ask the user in chat).
3. The non-LLM path (fetch → save with explicit path) is NOT gated — verify it offline. Only the live
   classification smoke waits on user creds. (Lighter than SP-4a's BN gate — it blocks one path, not the module.)

### 3.F Step 8 RepoMem.merge — **YOU OWN THIS** (recipe v2)
Per `CLAUDE.md` §3 step 8 + §4: the implementer closes merge within its OWN lifecycle (HITL with user).
Promote **cross-SP-reusable** lessons (e.g. a reusable SP-1 cookie-pull pattern, the LLMClient real-impl
landing) to global persist; keep module specifics in `Skill/crawl/zhihu-crawl/docs/RepoMem/decisions.md`.
May delegate *execution* to SubOrche but track to completion before reporting done — **never fire-and-forget**.

## 4. Convergence paths
Parent = ZhihuCrawl SubOrche, cwd = repo root (same as yours). Inbound replies: `docs/sendbox/toSP3Impler/from-zhihucrawlorche-*.md`.

| Event | Write to |
|---|---|
| plan-ready | `docs/sendbox/toZhihuCrawlOrche/from-sp3impler-plan-ready.md` |
| blocker (incl. LLM-creds gate) | `docs/sendbox/toZhihuCrawlOrche/from-sp3impler-blocker-<topic>.md` |
| done | `docs/sendbox/toZhihuCrawlOrche/from-sp3impler-sp3-done.md` |

## 5. Out-of-scope (forbidden)
- Touching SP-5a (`Service/crawl/zhihu-watcher/`), the SP-2 engine, or any other SP.
- Vault/Obsidian/GBrain/Thino semantics; SP-1 push wiring; v1.1 comment-tree.
- Baking LLM credentials into the repo.
- Editing `CLAUDE.md` / `docs/HarnessStack/` / `docs/RepoMem/persist/` directly (module decisions only; global via YOUR Step 8 merge).
- `git push` / merge-to-main / rebase — **local commits only** on `feat/agentcrawl-bootstrap`.

You MAY: read-only git/ls/grep; WebSearch/WebFetch for litellm/Zhihu research; create your worktree;
read-only pkg queries; TaskCreate/Update.

## 6. Branch / worktree / env state
Branch `feat/agentcrawl-bootstrap`; at Stage 3 create your own worktree (isolate from sibling SP-5a +
the live SP4aImpler). Commit with prefix `docs(SP-3):` / `feat(SP-3):` to limit shared-index races.
`gstack` submodule shows `M` — **never touch**.

## 7. Status board responsibility
The SubOrche flipped §SP Status Board SP-3 → 🟡 wip (owner sp3impler) at spawn. Update that row per stage
(🟡 wip → ⚫ done; 🔴 blocked only if the LLM-creds gate stalls), same-row, `docs(SP-3):` commits.

## 8. Lifecycle
`burn` after you write `from-sp3impler-sp3-done.md` and SubOrche reads it.

---
**Begin at Step 1, then Step 2 (brainstorming).** Greet the user, ask "ready to start SP-3 brainstorming?" —
the cross-SP boundaries are locked; your brainstorm is only the YOU-owned design decisions in §1.
