---
language: en
audience: A2A
status: research finding (informs deferred task Dashboard UN-050)
created: 2026-06-18
---

# LLM Model-Router Survey & Recommendation — JarvanKB

> Research finding (subagent, 2026-06-18) backing the **tiered model router** design in
> `version-plan.md §Shared LLM layer` and the deferred task **Dashboard UN-050**. Bottom line:
> **roll a thin custom tier-map over litellm now; defer dedicated routers (RouteLLM / semantic-router) to the
> later intra-customer learned/semantic phase.**

**Scope:** tiered routing (heavy/medium/light) now, learned/semantic intra-customer routing later, on top of
existing `jarvankb_common.LLMClient` (in-process litellm over `config/llm.yaml`), with an in-process → standalone
HTTP `LLMService` roadmap.

## (1) Comparison table

| Option | What it does | Routing mechanism | Self-host / OSS | Fit with litellm + in-proc→service path | Integration cost | Maturity |
|---|---|---|---|---|---|---|
| **litellm `Router`** (in-proc, already shipped) | LB + fallback across deployments of a model_group; `model_group_alias`, tag-based routing, `CustomRoutingStrategy` hook | static-shuffle / least-busy / usage / latency / cost; custom code for anything else | OSS, Apache-2.0; pure Python lib | **Native** — same package; no new dep; survives proxy migration (Router *is* the proxy core) | Very low — config + thin wrapper | Mature, very active |
| **litellm Proxy / Gateway** | Router exposed as OpenAI-compatible HTTP server + keys/teams/spend | same strategies, server-side | OSS, self-hostable (Docker) | This **is** the v2 `LLMService` target — frozen OpenAI interface for free | Low later (deploy), N/A now | Mature, very active |
| **RouteLLM** (LMSYS) | Learned strong↔weak router from preference data; OpenAI-compatible server; uses litellm under the hood | **learned quality** (win-prediction); threshold-calibrated | OSS, ~5k★, active | Built on litellm; OpenAI-compat drop-in | Medium — **strictly binary** (2 models), threshold calibration, embedding key | Research-grade, maintained |
| **semantic-router** (Aurelio) | Embedding-similarity decision layer; route = example utterances → target | **semantic embedding** (no LLM call, ~100ms) | OSS, MIT, active | Library; sits *above* LLMClient as a tier-classifier feeding a model name | Medium — author utterances per route, embedder dep + vector store | Mature, active |
| **NotDiamond** | Hosted router; auto-picks best LLM, custom router training | learned quality + cost, hosted | **No** (SaaS) | External hop; against frozen-interface/solo goals | Low API, vendor lock | Commercial |
| **Martian** | Hosted router+gateway, OpenAI-compatible, max-cost | learned quality + cost + reliability, hosted | **No** (SaaS) | External hop | Low API, vendor lock | Commercial |
| **OpenRouter** | Hosted multi-provider gateway; `openrouter/auto` routes per query | learned/meta + provider cost/latency/uptime fallback | **No** (SaaS), OpenAI-compatible | Fine as *one provider* behind litellm; not a self-host router | Trivial API | Mature commercial |
| **GPTRouter** (Writesonic) | Self-host gateway, uptime/latency fallback across 30+ models | latency/uptime fallback | OSS, self-host | Overlaps litellm proxy; less active | Medium (deploy a service) | OSS, lower activity |
| **LLMRouter** (ulab-uiuc) | Academic library of routing algorithms/benchmarks | research routers (learned) | OSS | Research toolkit, not production glue | High | Academic |

Sources: litellm routing (docs.litellm.ai/docs/routing), model_alias, proxy/load_balancing; RouteLLM
(github.com/lm-sys/RouteLLM, lmsys.org/blog/2024-07-01-routellm); semantic-router
(github.com/aurelio-labs/semantic-router); NotDiamond; Martian; OpenRouter (openrouter.ai/openrouter/auto);
GPTRouter (github.com/Writesonic/GPTRouter); LLMRouter (github.com/ulab-uiuc/LLMRouter).

## (2) Recommendation

**Roll a thin custom tier-map over litellm now. Do NOT adopt a dedicated router yet.**

- The static tier-map is a **config artifact, not a routing engine** — heavy/medium/light is three named profiles
  the repo already models; the "decision" = the caller names a tier (a dict lookup). Pulling in
  RouteLLM/semantic-router/a gateway to do a dict lookup is overkill for a solo KB.
- litellm's own `Router` is the right **substrate** (LB+fallback) but has no built-in complexity-tier concept —
  you write the thin tier layer either way, so keep it in `LLMClient`; `Router`/proxy is the engine underneath
  (no migration: Router *is* the v2 proxy core).
- Hosted routers (NotDiamond/Martian/OpenRouter-as-router) are **out** (external hop, vendor lock vs self-hosted
  `LLMService` goal). OpenRouter is acceptable only *as one upstream provider* behind litellm.
- **RouteLLM** (binary strong-vs-weak only, needs threshold calibration) and **semantic-router** (needs curated
  per-route utterances + embedder) are the **right LATER** tools for the intra-customer learned/semantic phase —
  adopt then, scoped to the one customer that needs it, behind the same frozen interface.

## (3) Migration sketch

Additive, back-compatible — add a tier layer alongside existing named profiles:

```yaml
tiers:                 # NEW: static complexity map; values reference existing profile/model
  heavy:  mimo-v2.5-pro
  medium: mimo-v2.5
  light:  mimo-v2.5            # collapse until a cheaper light profile exists
profiles:              # unchanged — named profiles + active-fallthrough as today
defaults:
  tier: medium
```

Router sits **inside `LLMClient`**, between the consumer call and litellm:

```
customer → LLMClient.complete(tier=…) → [tier→profile resolve] → litellm (Router: LB+fallback) → provider
                    ▲ frozen interface                              ▲ engine, swappable
```

- **NOW:** resolve = dict lookup; litellm in-process. Customers default to `medium`; long-transcript summary →
  `heavy`, vague-path classify → `light`.
- **v2 (HTTP LLMService):** `LLMClient` becomes a thin OpenAI-compatible client; tier→profile map + litellm
  `Router` move server-side into the litellm proxy; `tier=` maps to a `model_group_alias` on the wire — consumer
  code unchanged.
- **LATER (intra-customer learned/semantic):** keep `tier=` as the explicit override; add an optional
  `tier="auto"` classifier per sub-task — plug semantic-router or RouteLLM *behind* the same seam, scoped to the
  customer that needs it. No interface change.

> **JarvanKB-design note (root g5):** keep the user's declarative **`customers:` block** (customer→default tier)
> on top of this — `LLMClient(customer="bili-watcher")` resolves customer→tier→model, so tier assignments live in
> config (not scattered at call sites), while `.complete(tier=/task=)` stays the override for intra-customer
> routing. That marries the research's additive tier layer with the user's "customer=service/skill" binding.
