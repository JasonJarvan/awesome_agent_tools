> ARCHIVED fallback reference — MiroThinker integration alternatives to Path A
> Why archived: user chose **Path A** (hosted non-`-h` workflow + `mcp_servers`) on 2026-06-15. These are the
>   non-A paths, kept ONLY for "Path A broke, need a fallback" (Miro revokes the beta / mcp tools don't fire /
>   public-endpoint exposure becomes unacceptable). Active plan + the chosen path live in
>   `version-plan.md §MiroThinker`. Full empirical detail: `docs/sendbox/toMiroResearchImpler/miromind-repos-and-anticrawl.zh.md`.
> date: 2026-06-15

# MiroThinker — fallback paths (if Path A breaks)

**Path A (chosen)** = MiroMind hosted non-`-h` workflow (`apodex-1-0-deepresearch`) + `mcp_servers` (Miro's
server calls our public anti-crawl MCP, server-side). Uses the subscription. Needs: workflow-toolcall
whitelist + mcp_servers beta + our MCP public-with-strong-auth.

If A becomes unavailable/unacceptable, fall back to **B′** or **C** (both: self-hosted harness, tools run
**locally → zero public exposure → cookie never leaves the box**, which also sidesteps Path A's public-MCP
security burden):

| | Brain | Harness | Tools | Subscription | Cost |
|---|---|---|---|---|---|
| **B′** (preferred fallback) | **self-hosted MiroThinker open weights** (sglang/vLLM, ~1×RTX 4090) | self-host MiroFlow OR custom loop | local, client-side tool-call works | ❌ no | **GPU** |
| **C** | third-party (Claude / GPT / Gemini via OpenRouter) | self-host MiroFlow (`agent_quickstart_search.yaml`) | local anti-crawl MCP | ❌ no | per-token LLM cost |

**Path B is DEAD — do NOT revisit:** "self-host MiroFlow, point its brain at the hosted MiroMind API." The
hosted models (both `/v1/chat/completions` and `/v1/responses`, all `apodex-1-0-deepresearch*` variants) run
their own **server-side** search loop and **ignore caller `tools` / never return `tool_calls`** — confirmed
by live test (2026-06-12) AND by Miro (2026-06-15: "API 平台目前不提供裸模 API"). So tools attached in a
local harness **never fire** when the brain is the hosted API. The only way to use a MiroMind model with
local client-side tools is to **self-host the weights** (= B′), because there is no bare-model API.

**Reusable across all paths:** the `Service/mcp/` anti-crawl façade (Item-2) — in A it's attached via
`mcp_servers` (public); in B′/C it's a local MCP the self-hosted MiroFlow/custom-loop calls (no public
surface). Build it once. Engine-side anti-crawl (SP-2 v1.2 rate-limit, cookie pull) is inherited by all.

— root orche g4 (archived 2026-06-15)
