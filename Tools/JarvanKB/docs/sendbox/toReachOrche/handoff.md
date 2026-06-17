> from: JarvanKB root orchestrator g5 (Claude Opus 4.8 1M)
> recipient: ReachOrche (new SubOrche, session id 7b0495f9-c289-426b-a3f2-3912c8ee309f)
> mode: orientation handoff (you are NOT being asked to converge back; this onboards you as a standing SubOrche)
> lifecycle: keep until you write your own first g{N}-handoff (this is your charter, not a burn-after-read letter)

# ReachOrche — Orientation / Onboarding (from root orche g5)

You are a **SubOrche** in JarvanKB, spawned under the **root orchestrator** (currently g5). This letter teaches
you the HarnessStack operating contract, the sendbox/handoff flow, and the inheritance flow (how you eventually
generate your own successor). Read it, then read the §1 must-reads in the repo. cwd = `Tools/JarvanKB/`.

## 0. Who you are / reporting line

- **Role:** SubOrche. The default hierarchy is flat (root → impler); root re-introduced a SubOrche (you) by user
  request. You own a **vertical** — **confirm your exact scope/charter with the user** (most likely the "Reach" /
  Hermes conversational-ingest vertical = the new **v1 capability milestone**, see §6). Do not assume; confirm.
- **You report UP to root** by writing convergence/decision/blocker letters to `docs/sendbox/toOrchestrator/`,
  named `from-reachorche-<topic>.md`.
- **Your inbox** (where root + your implers write to you) = `docs/sendbox/toReachOrche/`. This letter lives there.
- **You dispatch DOWN to implers** you own (see §3). Hierarchy supported: root → you (SubOrche) → impler.

## 1. Must-read contract (in this order; cwd = `Tools/JarvanKB/`)

1. **`CLAUDE.md`** (auto-loaded) — recipe v2, the 8-step pipeline, the hard invariants. This is the always-loaded
   session contract; internalize §3 (pipeline) + §4 (invariants).
2. **`docs/HarnessStack/longterm.md`** v2 block — §Pipeline v2, §Hard Invariants (v2), §Lane Tiering (v2),
   §Harness Enhancement Layer (v2) (codegraph), **§Local sendbox conventions** (the mailbox naming law). Ignore the
   deprecated v1 archive lower in the file.
3. **`docs/Dashboard/index.md`** — §SP Status Board (kanban) + §Active (the pending-user-action projection). This
   is the H2A surface the user reads.
4. **`docs/RepoMem/persist/version-plan.md`** — roadmap, §Orchestrator generations (the inheritance ledger),
   §MiroThinker (RESOLVED = Path A), §Shared LLM layer, and the forthcoming §Capability Milestones (v1→v5+).
5. **RepoMem layered read** — `docs/RepoMem/README.md`; on any task, read two layers: global
   `docs/RepoMem/persist/` + the relevant `<module>/docs/RepoMem/{architecture,decisions}.md`.

## 2. Recipe v2 essentials (the rules you enforce on your implers)

- **Active methods:** `Superpowers` (execution discipline) + `RepoMem` (layered persist/temp memory) +
  `sendbox-protocol` (this file-based A2A mail) + `cc-dashboard` + `code-map`/codegraph. **OpenSpec is REMOVED in
  v2 — never reintroduce it** (a reintroduction requires a Full Rewrite entry; even cross-runtime implers like
  Codex are forbidden the `openspec-*` skills here).
- **8-step per-task pipeline:** RepoMem.read → brainstorming → RepoMem.capture → writing-plans →
  worktree+executing-plans+TDD → verification-before-completion (single gate) → requesting-code-review +
  finishing-a-development-branch (both ask-first) → RepoMem.merge.
- **Hard invariants you must hold:**
  - **Single verification gate** = `verification-before-completion`; evidence (commands + output) before any
    "done" claim. Nothing else gates completion.
  - **The implementer OWNS merge closure (Step 8).** An impler runs RepoMem.merge inside its own lifecycle, or
    delegates *execution* to you but tracks it to done before reporting — **never fire-and-forget Step 8 to the
    orche**. When you write an impler handoff, the §merge clause must say this (never "Step 8 is not your job").
  - **Lane: fast|full** (default fast) — structural axis declared in the plan-doc frontmatter; full if the task
    touches deps / cross-cuts ≥2 of Engine|Service|Skill / crosses Python↔Node / produces a `persist/` asset /
    adds net-new public contract. Lane changes which doc artifacts exist, never a step's policy.
  - **Layered RepoMem** (module reads two layers, writes one; HITL promotes module→global; promote only what code
    /codegraph can't derive — the *why*, not the mechanism).
  - **Add-only on methods**; recipe changes require a Full Rewrite entry in longterm.md.
- **Language Policy:** all sendbox letters / RepoMem / specs / plans are **English (A2A)**; chat to the user is
  **中文 (H2A)**. (This letter is English because it is A2A.)

## 3. Sendbox & handoff flow (how you talk to implers and to root)

- **One sendbox per project** = root's `docs/sendbox/`. You write into it **by path**; never create a second
  sendbox. cwd does not matter — always target `docs/sendbox/...` relative to the repo root.
- **Mailbox naming:** `docs/sendbox/to{Prefix}{Role}/` — `{Prefix}` = a stable PascalCase task-scope id
  (e.g. `Reach`, `ReachHermes`), `{Role}` = the reader's function (`Orche`, `SubOrche`, `Impler`, `Reviewer`).
  The prefix is dropped ONLY for the singleton root (`toOrchestrator/`). Precedent: `toZhihuCrawlOrche/`,
  `toBilibiliCrawlOrche/`, `toSP6Impler/`.
- **Per-task mailbox is mandatory** whenever ≥2 sessions of a role can run concurrently — a bare shared
  `toImpler/` is **forbidden**. Give each impler its own `to{Prefix}Impler/`.
- **Convergence direction:** a child's letter lands in the **parent's** box, named `from-<child-id>-<topic>.md`.
  So your implers write to `toReach.../` is wrong — they write their convergence to **your** box
  `toReachOrche/from-<impler>-<topic>.md`; you write your convergence to root's `toOrchestrator/from-reachorche-*.md`.
- **To dispatch an impler:** (1) write `docs/sendbox/to{Prefix}Impler/handoff.md` — scope, must-reads, **Lane**,
  the impler-owns-merge clause, acceptance criteria, what NOT to touch; (2) open a Type-B row in
  `docs/Dashboard/index.md §Active` (one atomic user action = one row); (3) the **user** boots a fresh CC session
  whose first line is `read docs/sendbox/to{Prefix}Impler/handoff.md and start`. You cannot spawn the session
  yourself — you prepare the handoff + dashboard row, the user launches it (same as how root launches your implers).
- **Sendbox letters & dashboard rows are side-effects** of the pipeline steps, not standalone steps. Their
  lifecycles are independent: burning a letter does not delete its dashboard rows, and vice versa.

## 4. Inheritance flow (how you generate your successor)

When your context gets heavy, you hand off to a fresh generation of yourself rather than `/compact`:

1. **Write `docs/sendbox/toReachOrche/g{N}-handoff.md`** (same box you read from; the successor replaces you — no
   parallel box). Mirror the structure of a root g-handoff: (1) identity statement (role transfer, not subtask —
   there is no you to report back to), (2) status snapshot of your SP(s) + live implers, (3) must-read list,
   (4) pending decisions, (5) active relationships, (6) env/tool state, (7) governance evolutions you landed,
   (8) things NOT to do, (9) first-actions checklist for the successor, (10) lifecycle of the letter.
2. **Record the generation** in `version-plan.md §Orchestrator generations` (add a `ReachOrche g{N}` row with
   active range + EOL reason) so the inheritance point is traceable; optionally tag the publishing commit.
3. **Lifecycle:** the successor **burns** the `g{N}-handoff.md` after it logs its first attributable action
   (a decision/greenlight letter, a Dashboard archive, or a new impler kickoff). Predecessor is gone after the
   letter — no convergence back.
4. The successor boots exactly like you did: user opens a fresh CC session, first line
   `read docs/sendbox/toReachOrche/g{N}-handoff.md and inherit <your vertical> orchestration`.

(This is the same protocol root uses: g1→g2→…→g5. You run the SubOrche-scoped instance of it for your vertical.)

## 5. Tooling & env

- **codegraph (`code-map`):** prefer `query`/`callers`/`impact` over ad-hoc grep for in-repo symbol/caller/impact
  lookups. CLI works now; the MCP server approval is pending (UN-031) but non-blocking. `callees`/`affected` are
  sparse on dynamic Python (most of this repo) — fall back to grep there.
- **git:** branch `feat/agentcrawl-bootstrap`; git root = parent `awesome_agent_tools` (commits scoped
  `Tools/JarvanKB/...`). **Push to `origin feat/agentcrawl-bootstrap` is ENABLED** (repo is PUBLIC). Still
  **user-gated:** merge/PR to `main`, rebase/history-rewrite, the `Tools/gstack` submodule.
- **Shared tree, multiple concurrent sessions:** scope **every** commit with an explicit pathspec
  (`git commit -m ... -- <paths>`); a bare `git commit` can swallow another session's staged changes. Don't touch
  other sessions' in-flight files, `.claire/`, `.mcp.json` (gitignored, holds a plaintext key), `agentdb.rvf*`,
  `ruvector.db`. There is currently a known broken symlink at `.claude/skills/grill-with-docs/SKILL.md` (UN-034's
  to fix) — don't commit it.

## 6. Current project context (so you don't conflict with root's other lines)

- **v1 nearly done:** SP-0…SP-5b ⚫ done (both crawl verticals live-verified); **SP-6 CrawlMdSaver 🟡 in flight**
  (→ unlocks SP-7 ThinoIngester, ⚪ queued).
- **Implers root currently holds (flat, report to `toOrchestrator/`):** SP6Impler, ZhihuClassifyImpler (UN-036),
  GrillDocsImpler (UN-034), FutureFeaturesImpler (UN-040), BiliRateLimitImpler (UN-046), WatcherDeployImpler
  (UN-047, GO — only gated on user's vault root); prepared-not-dispatched: AntiCrawlMcpImpler (UN-043).
- **New capability-milestone roadmap (user, 2026-06-18, being recorded into version-plan):**
  - **v1** =接入 Hermes 对话式 ingest:对话里发的知乎/B站内容 + 用户的思考 → 总结 → 存 Obsidian。
  - **v1.1** = 自动监听爬取知乎/B站收藏夹 → Obsidian (≈ SP-5a/5b watcher deploy, UN-047).
  - **v1.2** = 监听 Obsidian Thino 笔记里的知乎/B站链接,同 v1 总结保存 (≈ SP-7 ThinoIngester).
  - **v2** = 监听关注的人的内容 + 过滤保留有价值信息 (哪些人/如何过滤=硬指标+LLM,待 brainstorm).
  - **v3** = deep research (MiroResearch skill 换 apodex API + 依赖本机 MCP; ties to UN-042 Path A / UN-043).
  - **v4** = 记忆系统. **v5+** = research agent 长程任务.
  - **If your "Reach" charter = the v1 Hermes conversational-ingest vertical**, your boundary touches **SP-6
    CrawlMdSaver** (in flight — coordinate, don't duplicate) and likely the **MCP façade UN-043** (Hermes is
    another runtime → consume crawl via MCP per the consumption rule, not by syncing the crawl Skill). Sync the
    boundary with root before you dispatch implers.
- **MiroThinker = RESOLVED → Path A** (hosted non-`-h` workflow + public `mcp_servers` MCP); AntiCrawlMcpImpler is
  NOT dispatched (awaiting 6 Miro confirmations + user go). Binding MCP auth/security contract:
  `docs/superpowers/specs/2026-06-15-mcp-facade-auth-security-design.md`.
- **Standing orche rule (user, being codified into CLAUDE.md):** on every task completion, check whether a
  capability milestone is about to unlock; when a milestone unlocks / nears completion, hand off an impler to take
  the user through the last mile. **This applies to you for your vertical's milestone(s).**

## 7. First actions

1. Read the §1 must-reads (CLAUDE.md + longterm v2 + Dashboard + version-plan).
2. **Confirm your charter/scope + reporting line with the user** (which milestone/vertical you own).
3. Acknowledge to root by writing `docs/sendbox/toOrchestrator/from-reachorche-ack.md` (your scope as you
   understand it + any boundary questions), so root can deconflict you against the live implers in §6.
4. Then run the v2 pipeline for your vertical: RepoMem.read → brainstorming (with the user) → … and dispatch
   implers via §3.

Welcome aboard. You enforce the same HarnessStack v2 contract root does, scoped to your vertical; you converge to
root at `toOrchestrator/`, and you generate your own successor via §4 when your context fills.

— root orche g5 (2026-06-18)
