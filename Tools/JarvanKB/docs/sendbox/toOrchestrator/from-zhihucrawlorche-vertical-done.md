> from: ZhihuCrawl SubOrche (UN-019, active 2026-06-02 → 2026-06-14)
> recipient: root orchestrator / MainOrche (g4)
> mode: milestone-done (vertical roll-up + convergence — ends my SubOrche role)
> lifecycle: burn this + my entry handoff `toZhihuCrawlOrche/handoff.md` after you read

# Vertical done — Zhihu downstream (SP-3 + SP-5a)

The Zhihu downstream vertical delegated to me (g3-handoff, UN-019) is complete. Closing my SubOrche role and
handing the residuals below to you.

## 1. Delivered + converged (all merged, Step-8 closed, sendbox chains burned)
| SP | What | Evidence |
|---|---|---|
| **SP-3 Zhihu Skill** | URL → cookie(SP-1) → frozen SP-2 engine → save md; vague-path LLM classify | merged; 40 tests + live vague_path (`mimo-v2.5-pro`); landed the real `jarvankb_common.LLMClient` + agentskills.io `SKILL.md`; contract frozen |
| **SP-5a Watcher v1** | favorites poll → engine → save; seen-id dedup | merged `7acacb2`; 32 tests + 真站 smoke |
| **SP-5a Watcher v1.1** | `targets` (collection/user), watermark = top-level `created`, 403 backoff | merged `0489382`; 58 tests + 真站 smoke; §知乎链路 promotion A/B/C verified `5f7fd5a` |

**Routing contributions** (not my code): cookie = active **pull**, SP-1 push path permanently cancelled
(your version-plan record); article-403 **misdiagnosis corrected** → became **SP-2 v1.2 rate-limit hardening**
(your ZhihuArticleImpler) — 专栏 full text is fetchable via the primary nav-GET with fresh `__zse_ck`; only
the `/api/v4/articles` API is signature-gated (no signer, D1).

## 2. Gap I filled this turn (Goal A — "Hermes uses the skills")
Rewrote the **caller-agent contract** `docs/sendbox/toAgent/handoff.md` (was a stale placeholder referencing
the dead Tingwu/Playwright design): established the framework (trigger / tool-catalog / pre-flight creds /
fallback / output-format) and **filled the Zhihu sections** (SP-3 skill, SP-5a watcher, SP-1 cookie pre-flight
incl. dotted `.zhihu.com` key + `__zse_ck` freshness, LLM creds). With this, a calling agent (Hermes) can use
the **Zhihu** tools end-to-end.
- **Bilibili sections** marked TODO → **BiliOrc** (SP-4b/5b).
- **Ingester section (§2.D)** marked TODO → **you/SP-6/SP-7**.
- (`toAgent/` is persist-lifecycle/HITL — this edit was user-instructed = HITL satisfied.)

## 3. Handed to you (MainOrche) — residuals I am NOT closing
- **SP-5a v1.2 default-collection auto-classify**: **dispatched but NOT started** — handoff at
  `docs/sendbox/toZhihuClassifyImpler/handoff.md`, Dashboard **UN-036** (still open; no impler run yet). Since
  I'm converging, **you inherit its convergence** (greenlight its plan-ready → converge). It's thematically
  adjacent to the SP-6/7 ingester layer you now own (writes classified content into Obsidian subfolders).
  Full locked scope in the handoff: opt-in classify mode (default OFF, add-only boundary amendment), tiered
  token-frugal classify (excerpt → vague? → first-N, never full text), shared classifier extracted SP-3 →
  `jarvankb_common`, **classification ledger in the SERVICE** (authoritative local dedup, engine stays frozen),
  Lane: full.
- **SP-5a v1.3 sync-categorization-to-Zhihu**: roadmap (post-v1.2-smoke). ⚠️ Zhihu **write** API likely
  `x-zse-96`-gated (cf. articles) → may hit the D1 no-signer wall; the local ledger is the fallback-by-design.
  To be promoted to version-plan at v1.2's Step-8.
- **UN-032** (`__zse_ck` long-term freshness for watchers): deferred, root decision.
- **Caller contract**: Bili sections → BiliOrc; ingester §2.D → you/SP-6.

## 4. Lifecycle
Burn this letter + `docs/sendbox/toZhihuCrawlOrche/handoff.md` after you read. My SubOrche role ends here.

— ZhihuCrawl SubOrche (g4-era), 2026-06-14
