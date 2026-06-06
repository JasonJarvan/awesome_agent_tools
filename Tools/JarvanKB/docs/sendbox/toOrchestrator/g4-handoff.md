> from: orchestrator generation 3 (Claude Opus 4.8 1M, active 2026-05-31 → 2026-06-07)
> recipient: orchestrator generation 4 (next Claude Code session inheriting root orchestration)
> mode: inheritance-handoff (sendbox-protocol Mode B — g3 is gone after this letter; no convergence back)
> purpose: hand over full JarvanKB ROOT orchestration responsibility
> lifecycle: burn after g4 logs its first orche-attributable commit (decision/greenlight letter / Dashboard archive / new SubOrche or SP kickoff)

# JarvanKB Root Orchestrator — g3 → g4 Inheritance Handoff

## 1. Identity statement

You are the JarvanKB **root** orchestrator **generation 4** (`g4`). You inherit full root-orchestration
responsibility from g3 (gone after this letter). Scope: deliver the v1 family (SP-0…SP-7) + later the v1.0
OSS split. HarnessStack recipe **v2** active. Sole human stakeholder: JasonJarvan (中文; reply to user in 中文,
A2A docs stay English per `config.md`). This is a **role transfer**, not a subtask — there is no g3 to report back to.

**Your topology** (g3 evolved this — internalize): root orche delegates each crawl *vertical* to a **SubOrche**;
root keeps governance + cross-vertical sequencing.
```
root orche g4 (governance + cross-vertical + SP-6/7 sequencing + v1.0 split)
├─ ZhihuCrawl SubOrche      (ACTIVE)        → SP-3 🟡 + SP-5a 🟡
└─ BilibiliCrawl SubOrche   (handoff written, NOT yet booted = UN-022) → SP-4b + SP-5b
```

## 2. Status snapshot

| SP | State | Evidence / note |
|---|---|---|
| SP-0 skeleton + recipe v2 | ⚫ done | tag `sp0-complete` |
| SP-1 CookieManager | ⚫ done | merge `b84ee0f`; public via frp `https://www.zhaoricheng.fun:48098` |
| SP-2 Zhihu Engine | ⚫ done | merge `f8c14cb`; contract `Engine/zhihu/docs/interface.md` |
| SP-2 v1.1 comment full-tree | ⚫ done | merge `9081cbc` |
| SP-4a Bilibili Engine | ⚫ done | live-BN dual-path smoke; contract `Engine/bilibili/docs/interface.md`; **BN container `jarvankb-bilinote` running at `127.0.0.1:3015`** |
| **SP-3 Zhihu Skill** | 🟡 wip (near done) | under ZhihuCrawl SubOrche; **real `Engine/common` LLMClient landed** (`f8372e4`, pkg `jarvankb-common`); vague_path classify, save orch, CLI, SKILL.md, interface frozen, code-review done (2 fixed/3 deferred). **Committing DIRECTLY on the branch (no worktree)**; uncommitted in-flight files in the tree are SP3Impler's. Final live-LLM smoke is **gated on the user's LLM creds**. No sp3-done yet. |
| **SP-5a Zhihu Watcher** | 🟡 wip | under ZhihuCrawl SubOrche; Stage 1–4 done, `from-sp5aimpler-plan-ready.md` in `toZhihuCrawlOrche/`; into execute (worktree+TDD). seen-id dedup, ref-repo output format, BlockingScheduler. |
| SP-4b Bilibili Skill | 🟢 ready, delegated | BilibiliCrawl SubOrche owns it; **SubOrche not yet booted** (UN-022). Reuses SP-3's LLMClient. |
| SP-5b Bilibili Watcher | 🟢 ready, delegated | same; must read `crawl-pipeline.md §B站链路`. |
| SP-6 CrawlMdSaver | ⚪ queued | **unlocks when SP-3 + SP-4b both land**; it registers BOTH skills → it is **root's direct child** (cross-vertical), NOT under a SubOrche. You sequence it. |
| SP-7 ThinoIngester | ⚪ queued | after SP-6. |
| SP-8 Web Search Router | ⚪ queued (v1+) | post-v1. |

## 3. Must-read list (priority order)
1. **`CLAUDE.md`** — always-loaded contract (recipe v2, 8-step pipeline, hard invariants). Already auto-loaded; internalize §3 step 8 + §4 (merge ownership + promotion standard — g3 added these).
2. **`docs/HarnessStack/longterm.md`** §Pipeline v2 (esp. step 8) + §Hard Invariants + §Local sendbox conventions (SubOrche mailbox pattern).
3. **`docs/Dashboard/index.md`** §SP Status Board + §Active — your live to-do projection.
4. **`docs/RepoMem/persist/version-plan.md`** §Orchestrator generations + §Compatibility notes (cookie-pull decision) + §v1.0 OSS plan.
5. **`docs/RepoMem/persist/architecture/{credentials,crawl-pipeline}.md`** — the promoted cross-SP gotchas (cookie PULL + `bilibili.com` domain; Zhihu offset-poison/camelCase; B站 BN/bcut ops). The whole point of the promotion standard.
6. The two active SubOrche handoffs: `docs/sendbox/toZhihuCrawlOrche/handoff.md` + `docs/sendbox/toBilibiliCrawlOrche/handoff.md` — what each vertical owns + how it reports to you.
7. `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` §7 (SP map) + §8 (LLMClient) + §9 (OSS split).

**Skip**: burned letters; impler-internal transcripts; the deprecated v1 longterm.md archival section.

## 4. Pending decisions / open items
| Item | How to handle |
|---|---|
| **UN-022**: BilibiliCrawl SubOrche not yet booted | When the user opens it, it self-drives (spawns SP-4b/5b). No action until it reports `from-bilibilicrawlorche-*`. |
| **SP-3 LLM-creds gate** | SP-3's final live smoke needs the user's LLM API key. Watch for SP3Impler/ZhihuCrawl SubOrche to surface it (likely a blocker or chat ask). When SP-3 done lands (via ZhihuCrawl SubOrche's vertical roll-up, or directly), it half-unlocks SP-6. |
| **SP-6 sequencing** | When **SP-3 AND SP-4b** are both done, spawn SP-6 as your **direct child** (it registers both crawl skills — cross-vertical, not a SubOrche's). Then SP-7 after SP-6. |
| **UN-006**: v1.0 Org name | Defer until v1 nears completion; surface options then. |
| **UN-008**: CodeTeam #1/#2 review | User-side; no orche action. |
| ZhihuCrawl/BilibiliCrawl `from-<suborche>-vertical-done.md` | When a SubOrche reports its vertical done: verify, archive/burn its handoff chain, update Dashboard, check SP-6 unlock. Each SubOrche/impler **owns its own Step 8 merge — do NOT redo**. |

## 5. Active relationships
- **ZhihuCrawl SubOrche** (peer CC session): owns SP-3 + SP-5a; reports to `toOrchestrator/` as `from-zhihucrawlorche-*`. Already escalated one decision (cookie-pull, resolved + recorded by g3).
- **BilibiliCrawl SubOrche** (peer CC session, pending boot): owns SP-4b + SP-5b.
- **SP3Impler, SP5aImpler** (peer CC sessions under ZhihuCrawl SubOrche): currently live in the **main tree** (SP-3 commits directly to branch). Their uncommitted files are theirs — don't touch.
- **User (JasonJarvan)**: sole human; H2A surface = Dashboard + sendbox; drives impler sessions directly.
- **gstack submodule**: shows `M` — pre-existing, **never touch**.

## 6. Env / tool state
- Working dir `/home/shenzhou/Codes/awesome_agent_tools/Tools/JarvanKB/`; branch `feat/agentcrawl-bootstrap`; **local commits only — no push / no merge to main**.
- **BiliNote** container `jarvankb-bilinote` @ `127.0.0.1:3015` (bcut, provider mimo-v2.5-pro) — for the Bilibili vertical.
- **SP-1 cookie-manager** running; consumers fetch cookies by **active PULL** (push path cancelled — see §7).
- Tavily MCP = project-scoped + default-disabled (built-in WebSearch/WebFetch fine).
- **Multiple sessions share the main tree** → shared git index. Scope every commit with explicit pathspec; expect "modified since read" on Dashboard (re-read + retry). Uncommitted in-flight files (e.g. `Engine/common/.../llm_config.py`, SP-3 test/zh-design) belong to other sessions.

## 7. Governance evolutions g3 landed (internalize — these post-date the g3-handoff you won't see)
| Pattern | One-liner |
|---|---|
| **Impler owns merge closure** (UN-015) | Step 8 `RepoMem.merge` closes within the impler's OWN lifecycle (HITL; may delegate exec to orche but tracks to done). NEVER "NOT YOUR JOB". Codified in CLAUDE.md §3 step8 + §4 + longterm. |
| **RepoMem.merge promotion standard** | Promote to global persist ONLY non-code-derivable rationale/gotchas; **cross-SP-reusable gotchas MUST go global** because layered-read means a downstream SP in another cwd never reads the origin module's `decisions.md`. longterm §Pipeline v2 step8 + CLAUDE.md §3 step8. |
| **Cookie = active PULL; SP-1 push path permanently cancelled** | User-ratified 2026-06-02 (hook engine retained, latent). All crawl consumers. `credentials.md` §Integration contract + version-plan. |
| **SubOrche for multi-impler verticals** | Two *independent* engines (SP-2/SP-4a) = direct children of root. A vertical with ≥2 same-domain implers (Zhihu SP-3+5a, Bilibili SP-4b+5b) = a SubOrche (`toZhihuCrawlOrche/`, `toBilibiliCrawlOrche/`). Root → SubOrche → Impler. |
| **Propagation principle** | A rule implers must FOLLOW must live in always-loaded `CLAUDE.md`, not only `longterm.md` (new sessions don't read longterm by default). This is why UN-015 + the promotion standard were inlined into CLAUDE.md. |
| (inherited, still in docs) | per-task mailbox `to{Prefix}{Role}/`; H2A coupling; A2A=English/H2A=中文; forward-edit over revert; SP kanban lives in Dashboard. |

## 8. Things NOT to do
- No `git push` / merge to `main` / rebase / history rewrite — local commits only on `feat/agentcrawl-bootstrap`.
- Don't touch `gstack` (parent-repo submodule) or any other session's uncommitted in-flight files.
- Don't **redo** any impler/SubOrche `RepoMem.merge` (each owns its own closure, HITL-confirmed).
- Don't reintroduce OpenSpec (Full Rewrite required per `longterm.md §Full Rewrite Conditions`).
- Don't move the SP kanban out of Dashboard; don't churn grandfathered 中文 persist files.
- Don't collapse the SubOrche hierarchy (implers report to their SubOrche's mailbox, not directly to you).
- Don't spawn SP-6 until BOTH SP-3 and SP-4b are done.

## 9. First-actions checklist (when g4 boots)
1. `pwd` (confirm repo root) + `git log --oneline -10` (see SubOrche/impler progress past g3's last commit).
2. `ls docs/sendbox/toOrchestrator/` — any new `from-<suborche>-*` / `from-<impler>-*` letters for root?
3. Read §3 must-reads (top 5 minimum).
4. Glance `toZhihuCrawlOrche/` + `toBilibiliCrawlOrche/` inboxes for vertical-internal state (context only).
5. Reply to user in chat: "g4 inherited; ready."
Then sit in **receive mode**. Triggers: a SubOrche's `vertical-done`/blocker, an impler escalation to root, user chat, Dashboard state changes, SP-6 unlock (SP-3 + SP-4b done).

## 10. Lifecycle of this letter
**Burn** after your first orche-attributable commit lands (decision/greenlight letter / Dashboard archive / new SubOrche or SP kickoff): `git rm docs/sendbox/toOrchestrator/g4-handoff.md`. Update `version-plan.md §Orchestrator generations` g4 EOL when you eventually write g5. g3 tags `orche-g3-handoff` at the publishing commit so the inheritance point is bisectable.

---
Welcome, g4. Two verticals are fanned out under SubOrches, four SPs done, the engines + cookie infra solid.
Your near-term arc: SP-3 finishing (LLM-creds gate) → BilibiliCrawl boot → both verticals converge → SP-6
(cross-vertical, your direct child) → SP-7 → v1.0 OSS split. Keep the governance patterns in §7 alive.

— g3, signing off (2026-06-07)
