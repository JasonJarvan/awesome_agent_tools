> from: orchestrator generation 4 (Claude Opus 4.8 1M, active 2026-06-07 → 2026-06-14)
> recipient: orchestrator generation 5 (next Claude Code session inheriting root orchestration)
> mode: inheritance-handoff (sendbox-protocol Mode B — g4 gone after this letter; no convergence back)
> purpose: hand over full JarvanKB ROOT orchestration responsibility
> lifecycle: burn after g5 logs its first orche-attributable commit (decision/greenlight letter / Dashboard
>   archive / new impler or SP kickoff)

# JarvanKB Root Orchestrator — g4 → g5 Inheritance Handoff

## 1. Identity statement

You are the JarvanKB **root** orchestrator **generation 5** (`g5`), inheriting full root-orchestration
responsibility from g4 (gone after this letter). Scope: finish v1 (SP-6 → SP-7), coordinate the live implers,
then drive the v2+ roadmap + the v1.0 OSS split. HarnessStack recipe **v2** (`superpowers-repomem-sendbox-dashboard`).
Sole human stakeholder: JasonJarvan (中文 to user; A2A docs English). This is a **role transfer**, not a subtask —
there is no g4 to report back to. **The SubOrche era is over** — both crawl verticals converged; you now hold
all implers directly (flat: root → impler).

## 2. Status snapshot

| SP / item | State | Evidence |
|---|---|---|
| SP-0/1/2(+v1.1+v1.2)/3/4a/4b/5a(+v1.1)/5b | ⚫ done | both verticals converged + live-verified; SubOrches gone |
| **SP-6 CrawlMdSaver** | 🟡 **in flight** | SP6Impler running (UN-038); registers SP-3+SP-4b, merges crawled md + user notes; **done → unlocks SP-7** |
| **SP-7 ThinoIngester** | ⚪ queued | unlocks when SP-6 lands; root's to sequence |
| SP-8 Web Search Router | ⚪ queued (v1+) | post-v1 |

**Live implers you now coordinate (report to `toOrchestrator/`):**
| Impler | UN | State / your job |
|---|---|---|
| SP6Impler | UN-038 | in flight; converge when `from-sp6impler-done` lands → then dispatch SP-7 |
| ZhihuClassifyImpler (SP-5a v1.2 classify) | UN-036 | **g4 inherited its convergence** — dispatched, greenlight its plan-ready → converge |
| GrillDocsImpler | UN-034 | replacing grill-with-docs w/ community CONTEXT.md producer (partial #4-prop4 revert); see §4 |
| FutureFeaturesImpler | UN-040 | draft auto-researcher + repo-index into version-plan (uses MiroResearch) |
| BiliRateLimitImpler | UN-046 | **GO** — SP-4a engine rate-limit (mirror SP-2 v1.2, preventive); greenlight plan → converge |
| WatcherDeployImpler | UN-047 | **GO deploy-now** (root ratified); blocked only on user's vault-root (Stage-0) |
| **AntiCrawlMcpImpler** | UN-043 | **prepared, NOT dispatched** — repo MCP façade v1 under `Service/mcp/`; dispatch when user says go |

## 3. Must-read list (priority order)
1. **`CLAUDE.md`** (auto-loaded) — recipe v2, 8-step pipeline, hard invariants. Internalize §4 (merge ownership + add-only).
2. **`docs/HarnessStack/longterm.md`** v2 block — §Pipeline v2, §Hard Invariants (v2), **§Lane Tiering (v2)**, **§Harness Enhancement Layer (v2)** (codegraph), §Local sendbox conventions. (Ignore the deprecated v1 archive ~L190+.)
3. **`docs/Dashboard/index.md`** — §SP Status Board + §Active (your live to-do projection; UN-006…UN-047).
4. **`docs/RepoMem/persist/version-plan.md`** — §Orchestrator generations (g5 row) + §v1.0 OSS release plan (incl. the deferred whole-repo extraction) + **§MiroThinker** (MCP façade plan) + §Shared LLM layer (LLMService v2).
5. **`docs/RepoMem/persist/architecture/{credentials,crawl-pipeline}.md`** — the promoted cross-SP gotchas (cookie pull + `.zhihu.com` dotted key / `bilibili.com` dotless; `__zse_ck` nav gate; zhihu offset/camelCase; B站 BN/bcut/412 ops; **48xxx port convention §**).
6. **`docs/sendbox/toAgent/handoff.md`** — caller-agent contract: **Zhihu sections filled; Bilibili + ingester §2.D still TODO** (route to whoever does SP-6/7 + a Bili pass).

**Skip**: burned letters; impler-internal transcripts; the v1 longterm archive.

## 4. Pending decisions / open items (Dashboard-tracked)
| Item | How to handle |
|---|---|
| **UN-006** v1.0 Org name | defer until v1 near-complete; surface options then |
| **UN-008** CodeTeam #1/#2 review | user-side; no orche action |
| **UN-031** approve codegraph MCP server | user approves on next session; CLI works regardless (non-blocking) |
| **UN-032** `__zse_ck` long-term freshness | deferred root decision (cookie re-sync works today; signer/headless breaks D1) |
| **UN-042** MiroThinker path | **Miro replied 2026-06-15**: will enable `mcp_servers` beta (Path A unblocked) + a **non-`-h` model supports client-side tool calls** → new **Path A′** (subscription + local tools, no beta) and a possible **revival of Path B** (self-host MiroFlow + non-`-h` API brain). **3 follow-up Qs sent to Miro** (model-vs-harness / does self-host+API fire client tools / billing) — see version-plan §MiroThinker UPDATE 2026-06-15. Item-2 (UN-043) stays no-regret: build it to expose **both** an MCP server AND OpenAI tool-schemas |
| **UN-041** extract JarvanKB → standalone repo | ⛔ DEFERRED; activation = v1 done + UN-006 + explicit user go |
| **grill-with-docs (UN-034)** | mid-replacement → community CONTEXT.md producer; **partially reverts CodeTeam #4-prop4** (the design-gate role) — GrillDocsImpler reconciles CLAUDE.md/longterm refs with the user |
| **MCP façade (UN-043)** | placement locked = `Service/mcp/`; framed as repo-wide façade v1 (crawl tools first, grow incrementally, not a god-process); dispatch AntiCrawlMcpImpler when user greenlights |

## 5. Active relationships
- **Implers** (table §2): all peer CC sessions reporting to `toOrchestrator/`. No more SubOrches — flat hierarchy.
- **Codex** = an **onboarded cross-runtime impler** (UN-039 done; 4 project skills installed via cc-switch+symlink, collab on, thin `Tools/JarvanKB/AGENTS.md` added). Assignable to a real SP next (e.g. SP-7, or the MCP façade). Tool-map: Task→spawn_agent, TodoWrite→update_plan, Skill→native; **OpenSpec skills present but FORBIDDEN here**.
- **User (JasonJarvan)**: sole human; H2A = Dashboard + sendbox; drives impler sessions directly.

## 6. Env / tool state
- Working dir `Tools/JarvanKB/`; **git root = parent `awesome_agent_tools`** (commits scoped `Tools/JarvanKB/...`); branch `feat/agentcrawl-bootstrap`.
- **Push to `origin feat/agentcrawl-bootstrap` is ENABLED** (g4 lifted the no-push invariant 2026-06-10; repo is **PUBLIC**). Local often runs ahead — push to sync. **STILL gated without explicit user say-so: merge/PR to `main`, rebase/history-rewrite, `Tools/gstack` submodule.**
- Multi-session shared tree → **scope every commit with explicit pathspec**; expect "modified since read" on Dashboard (re-read+retry). Don't touch other sessions' uncommitted files, `.claire/`, `.mcp.json` (gitignored, holds a plaintext key), `agentdb.rvf*`.
- **⚠️ KNOWN BREAKAGE:** `Tools/JarvanKB/.claude/skills/grill-with-docs/SKILL.md` is now a **broken symlink loop** ("符号链接的层数过多") — collateral from Codex's cc-switch skill-sync fallback. It's UN-034's file (being replaced) → let GrillDocsImpler restore it as a real file; don't commit the broken link.
- Live infra: BiliNote `jarvankb-bilinote`@`127.0.0.1:3015` (host cron `bn-cookie-sync.py */10` keeps SESSDATA fresh — UN-035 fix); cookie-manager@`48088` (frp public `48098`); codegraph indexed (`.codegraph/`, MCP pending UN-031 approval, CLI works).

## 7. Governance evolutions g4 landed (internalize — these post-date the g4-handoff you won't see)
| Pattern | One-liner |
|---|---|
| **no-push lifted** | feature branch → origin enabled (2026-06-10); main/rebase/gstack still user-gated. version-plan §Compatibility. |
| **MCP façade route** | a repo-wide MCP is a **façade/4th-surface**, NOT a god-process; lives in new `Service/mcp/`; **granularity rule** (Engine/Skill→tools, watcher daemon→control tools only); **consumption rule** (stateful/shared-backend→MCP, pure-instruction→Skill, don't double-front). version-plan §MiroThinker. |
| **Codex = cross-runtime impler** | onboarded via cc-switch (skill distribution to claude/codex/hermes/open-claw); OpenSpec-skills-forbidden-here; thin AGENTS.md pointer pattern. |
| **MiroThinker findings** | hosted mirothinker is closed server-side (ignores caller tools; `mcp_servers` beta-gated 403); anti-crawl MCP must be user-supplied; Path A/C pending Miro reply (UN-042). |
| **CodeTeam #3/#4 instantiated** | codegraph `code-map` + Lane Tiering live in CLAUDE.md/longterm (additive, not Full Rewrite). |
| **48xxx port convention ratified** | host listening-services use 48000–48999 (sub-allocated); watchers don't listen. credentials.md §. |
| (inherited, still law) | impler-owns-merge-closure; promotion standard (cross-SP gotchas→global); per-task mailbox `to{Prefix}{Role}/`; A2A=English/H2A=中文; forward-edit over revert; SP kanban in Dashboard. |

## 8. Things NOT to do
- No merge to `main` / rebase / history-rewrite / `gstack` touch without explicit user OK (push to the feature branch IS fine).
- Don't redo any impler's `RepoMem.merge` (each owns its closure).
- Don't reintroduce OpenSpec (Full Rewrite required).
- Don't commit the broken grill-with-docs symlink, `.mcp.json`, `.claire/`, `agentdb.rvf*`, or other sessions' in-flight files.
- Don't re-spawn SubOrches (verticals done; flat root→impler now).
- Don't dispatch SP-7 until SP-6 lands; don't dispatch the MCP façade (UN-043) until the user greenlights.

## 9. First-actions checklist (when g5 boots)
1. `pwd` + `git log --oneline -12` (see impler progress past g4's last commit) + `git status -sb` (ahead of origin?).
2. `ls docs/sendbox/toOrchestrator/` — any new `from-<impler>-*` letters (done/blocker) for root?
3. Read §3 must-reads (top 4 minimum) + `docs/Dashboard/index.md` §Active.
4. Reply to user in chat: "g5 inherited; ready."
Then **receive mode**. Triggers: an impler's done/blocker, user chat, Dashboard changes, SP-6 done (→ dispatch SP-7), Miro beta reply (→ UN-042 A/C), user greenlight (→ dispatch UN-043 MCP / start WatcherDeploy with vault-root).

## 10. Lifecycle of this letter
**Burn** after your first orche-attributable commit: `git rm docs/sendbox/toOrchestrator/g5-handoff.md`. Update
`version-plan.md §Orchestrator generations` g5 EOL when you eventually write g6. g4 tags `orche-g4-handoff` at
the publishing commit so the inheritance point is bisectable.

---
Welcome, g5. v1 is one SP from complete (SP-6 in flight → SP-7), both crawl verticals shipped + live-verified,
the engines/cookie/LLM infra solid, Codex onboarded as a second runtime, and the v2 arc (MCP façade →
auto-researcher → repo index) + the OSS split are scoped in the version plan. Keep the §7 patterns alive.

— g4, signing off (2026-06-14)
