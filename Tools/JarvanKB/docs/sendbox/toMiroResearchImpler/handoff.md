> mode: inheritance
> from: current Codex session
> recipient: MiroResearchImpler
> purpose: continue the MiroThinker/MiroFlow anti-scraping capability research
> lifecycle: persist until the inheriting agent reports its first milestone or supersedes this handoff

# MiroResearch / MiroThinker Handoff

You are the next agent inheriting the MiroThinker/MiroFlow research thread. The user asked:

> 调研 mirothinker 是怎么实现的；背后是否用 miromind 模型；miroflow 是否是开源 harness；现在 mirothinker 没有反扒能力，不能绕过反扒机制。有哪些办法？一种是本地部署 MiroFlow 然后加反扒机制，另一种是依赖官方能力或给官方提 issue。

## Status Snapshot

| Area | Status | Notes |
|---|---|---|
| Project contract | done | `CLAUDE.md` was read. JarvanKB recipe v2 removed OpenSpec; do not use `openspec-*` skills here. |
| Skill discovery | done | `MiroResearch` is at parent repo path `/home/shenzhou/Codes/awesome_agent_tools/Skills/MiroResearch`, not under JarvanKB `Skill/`. |
| MiroResearch API call | blocked | `MIROMIND_API_KEY` was missing in the environment, so `python3 scripts/miro_research.py run ...` could not be executed. |
| Local/web research | done, preliminary | Official GitHub repos and docs were checked directly. Key evidence below. |
| Main conclusion | preliminary | User's model is mostly right: MiroThinker is the model/agent line; MiroFlow is the open-source harness/framework; public tool layer relies mainly on Serper/Jina/E2B/MCP. No ready-made compliant authenticated browser / CAPTCHA / anti-bot bypass feature was found. |

## Must-Read Files

- `/home/shenzhou/Codes/awesome_agent_tools/Tools/JarvanKB/CLAUDE.md`
- `/home/shenzhou/Codes/awesome_agent_tools/Skills/MiroResearch/SKILL.md`
- `/home/shenzhou/Codes/awesome_agent_tools/Skills/MiroResearch/scripts/miro_research.py`
- Official repos:
  - `https://github.com/MiroMindAI/MiroThinker`
  - `https://github.com/MiroMindAI/MiroFlow`
  - `https://arxiv.org/html/2602.22808v1`

## Evidence Collected

MiroResearch skill behavior:

- The wrapper sends one prompt string into the MiroMind Responses API.
- It expects `MIROMIND_API_KEY`.
- Default model is `mirothinker-1-7-deepresearch-mini`; `--full` uses `mirothinker-1-7-deepresearch`.
- It submits a background job and polls internally; normal usage is one command:

```bash
cd /home/shenzhou/Codes/awesome_agent_tools/Skills/MiroResearch
python3 scripts/miro_research.py run "QUERY" --full --timeout 1800
```

MiroThinker / MiroFlow public architecture:

- `MiroThinker` README describes MiroThinker as a deep research agent optimized for research/prediction.
- MiroThinker 1.7 public README says 256K context and up to 300 tool interactions.
- `MiroFlow` README says it is the official implementation of the MiroMind Research Agent Project and an open-source research agent framework.
- MiroFlow paper says it uses hierarchical architecture, agent graph, robust workflow, optional heavy reasoning, and external tools.
- MiroThinker `apps/miroflow-agent` minimal tool config uses:
  - `tool-python` via E2B
  - `search_and_scrape_webpage` via Serper
  - `jina_scrape_llm_summary` via Jina + summary LLM
- MiroThinker tool docs list optional tools: Google search, Sogou search, vision, audio, reasoning, document reading.

Anti-bot / browsing capability finding:

- Public MiroThinker tools mainly do search and scrape through Serper, Jina, requests, and E2B.
- MiroFlow has `src/tool/mcp_servers/browser_session.py`, a wrapper for a persistent Playwright MCP session.
- However, current MiroFlow main branch has `config/tool/tool-browsing.yaml` referencing `src.tool.mcp_servers.browsing_mcp_server`, but the corresponding `browsing_mcp_server.py` was not present in the cloned main branch.
- MiroFlow `pyproject.toml` did not show Playwright/Selenium/stealth browser dependencies.
- GitHub issue search with terms like `captcha`, `cloudflare`, `playwright`, `browser`, `anti scraping`, `cookie`, `proxy` returned no relevant open issues in MiroFlow/MiroThinker at the time of this session.

Useful commands already run:

```bash
test -n "$MIROMIND_API_KEY" && echo MIROMIND_API_KEY=set || echo MIROMIND_API_KEY=missing
git clone --depth 1 https://github.com/MiroMindAI/MiroFlow.git /tmp/MiroFlow
git clone --depth 1 https://github.com/MiroMindAI/MiroThinker.git /tmp/MiroThinker
rg -n "playwright|selenium|browser|captcha|cloudflare|cookie|proxy|jina|serper|scrape|search|anti|stealth|fingerprint|undetected" /tmp/MiroFlow /tmp/MiroThinker -S
gh issue list --repo MiroMindAI/MiroFlow --search "captcha OR cloudflare OR playwright OR browser OR anti scraping OR scrape OR cookie OR proxy" --limit 20 --json number,title,state,url,createdAt
gh issue list --repo MiroMindAI/MiroThinker --search "captcha OR cloudflare OR playwright OR browser OR anti scraping OR scrape OR cookie OR proxy" --limit 20 --json number,title,state,url,createdAt
```

The `/tmp` clones are not durable project artifacts. Re-clone if needed.

## If MIROMIND_API_KEY Becomes Available

Use this prompt with `MiroResearch`:

```text
Research task: Investigate how MiroThinker is implemented, how it relates to MiroMind models and the MiroFlow open-source harness, and what options exist for handling websites that block automated scraping.

Context:
- User believes MiroThinker uses MiroMind models and MiroFlow is the open-source harness.
- Current problem: MiroThinker/MiroResearch appears unable to handle anti-bot protected sites and should not bypass anti-scraping mechanisms unlawfully.
- We need practical product/engineering options:
  1. Self-host MiroFlow and add a compliant browsing/fetching layer.
  2. Depend on official MiroMind/MiroThinker capabilities, or file an upstream issue if missing.
- Current date: 2026-06-12. Prioritize official sources and current repo state.

Questions to answer:
1. What are MiroThinker, MiroMind model, and MiroFlow respectively? How do they fit together?
2. What web search, browsing, scraping, browser, and code-execution tools are present in the official public repos?
3. Does official MiroThinker/MiroFlow support authenticated browsing, user-supplied cookies, proxy/session configuration, JS-heavy page rendering, CAPTCHA/manual handoff, or anti-bot challenge handling?
4. If official support is missing, what is the safest compliant extension design for self-hosted MiroFlow?
5. What exactly should be requested in a GitHub issue or upstream feature request?

Safety and legal boundary:
- Do not recommend bypassing CAPTCHA, evading access controls, rotating identities to defeat bans, or violating website terms.
- Prefer compliant approaches: official APIs, user-authorized sessions, rate limits, robots/ToS checks, cached retrieval, provenance, and manual challenge handoff.

Output format:
- Executive summary
- Architecture map
- Evidence table with source links
- Official capability gap analysis
- Option A: self-hosted extension design
- Option B: official feature request path
- Recommended issue title and body
- Risks and open questions
```

Command:

```bash
cd /home/shenzhou/Codes/awesome_agent_tools/Skills/MiroResearch
python3 scripts/miro_research.py run "$(cat /path/to/prompt.txt)" --full --timeout 1800
```

If storing the prompt in a temp file is inconvenient, pass it directly as one shell-quoted string.

## Preliminary Recommendation

Short term:

- Use self-hosted MiroFlow only if you need custom retrieval against sites that require user authorization.
- Add a new MCP server/tool rather than modifying the model. Candidate tool names:
  - `authenticated_browser_fetch`
  - `managed_browser_reader`
  - `authorized_site_connector`

Medium term:

- File an upstream feature request asking for pluggable compliant browsing connectors.
- Do not frame it as "anti-scraping bypass"; frame it as "authenticated / JS-heavy / manually approved browsing support."

Long term:

- Split retrieval policy from research reasoning:
  - official APIs first
  - user-authorized session connector
  - Jina/Serper fallback
  - plain requests fallback
  - manual handoff when a challenge or access boundary appears

## Suggested Upstream Issue

Title:

```text
Feature request: support user-provided compliant browsing connectors for authenticated / JS-heavy pages
```

Body:

```text
MiroThinker/MiroFlow currently works well for many research tasks through search and page extraction tools such as Serper/Jina/E2B. Some legitimate research workflows require access to pages that are JS-heavy, require user-authenticated sessions, or return anti-bot/CAPTCHA challenges to generic fetchers.

Request:
- Add a pluggable browsing/fetch connector interface that can be configured by users in self-hosted MiroFlow.
- Support user-provided authorized sessions/cookies where the user has access rights.
- Support rate limiting, cache, provenance, robots/ToS guardrails, and explicit failure reasons.
- Support manual challenge handoff instead of attempting to bypass CAPTCHA or access controls.
- Return structured output such as content, source_url, fetch_method, auth_context, failure_reason, needs_human_action.

Non-goal:
- This is not a request to bypass CAPTCHA, defeat access controls, rotate identities to evade blocking, or violate website terms.

Use case:
- Deep research agents need reliable retrieval from user-authorized sources while preserving compliance, auditability, and source citation.
```

## Open Questions For Next Agent

- Confirm whether MiroMind official hosted API has a private/undocumented connector feature. Public docs checked so far did not show one.
- Confirm whether `tool-browsing` is intentionally incomplete on main, exists on a branch/tag, or depends on external MCP Playwright setup.
- Decide whether this research should be turned into a JarvanKB future-feature draft, and if so place it under the appropriate `version-plan.md` section rather than leaving only this transient letter.
- If user provides `MIROMIND_API_KEY`, run the MiroResearch prompt above and reconcile its report against the local findings.
