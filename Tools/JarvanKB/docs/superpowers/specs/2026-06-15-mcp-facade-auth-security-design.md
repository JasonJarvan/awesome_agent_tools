# MCP Façade — Auth & Security Design (for AntiCrawlMcpImpler / Item-2 / UN-043)

> Cross-module design input for the `Service/mcp/` anti-crawl MCP façade. Authored by root orche g4,
> 2026-06-15, after the user chose **Path A** (Miro hosted workflow + `mcp_servers` calling our **public** MCP).
> Status: **binding security contract** — the impler implements these; they are not optional.
> Context: `version-plan.md §MiroThinker (RESOLVED 2026-06-15)`; user-facing: `toUser/mirothinker-path-aprime-client-side-explainer.md §2`.

## 1. Threat model (why this is strict)

In Path A the MCP is reachable from the **public internet** (Miro's server calls it; **Miro provides no URL
whitelist during beta**), and it performs **authenticated, logged-in crawling using the user's cookies**
(zhihu `.zhihu.com`, bilibili `SESSDATA`). Threat: anyone who discovers the endpoint could drive the user's
identity to scrape/abuse → account ban, data exfiltration, cookie theft. The design must make a leaked
endpoint/token **low-blast-radius** and make cookie theft **structurally impossible via the interface**.

## 2. Design principles (in priority order)

1. **Capability minimization (the core protection).** The MCP exposes ONLY `fetch(url) → markdown` style
   tools, scoped to allowed domains. It MUST NOT expose: a "return the cookie" tool, a "make an arbitrary
   authenticated request" tool, or a generic HTTP proxy. → A leaked token can only retrieve crawled content
   from allowed domains; it can never obtain the cookie or aim the identity at an arbitrary site.
2. **Cookie never crosses the interface.** The cookie is pulled in-memory from the **localhost** cookie-manager
   (`127.0.0.1:48088`) at call time, used only on the outbound crawl, and discarded. It is **never** a tool
   input, **never** in a tool result, **never** logged, **never** written to disk in plaintext (extends the
   repo's existing "active-pull + in-memory decrypt" rule). cookie-manager itself is **not** exposed through
   the public MCP — only the fetch tools are.
3. **Strong per-request auth** (compensates for Miro's missing URL whitelist). Endpoint is **HTTPS only**.
   Every request carries a strong random **bearer token / OAuth** (wired via the `mcp_servers` config
   `access_token` / `headers` / `oauth`). The token is **rotatable** and **revocable**. Reject anything
   without a valid token.
4. **Network reachability narrowed on our side.** Front the MCP with **Nginx + TLS** (reuse the cookie-manager
   frp/Nginx pattern — do NOT expose a raw port). If Miro's **egress IP range** is obtainable (open question
   to Miro), **IP-allowlist** it at the reverse proxy/firewall — we can do IP-allowlisting even though Miro
   does not do URL-whitelisting.
5. **Domain allowlist + rate-limit + audit.** Tools accept only `zhihu.com` / `bilibili.com` targets (the
   cookie cannot be pointed elsewhere). Per-token + per-IP rate-limit (layered on top of the engine's v1.2
   outbound rate-limiter). **Audit-log** every call (caller, tool, args-summary, target, timestamp, outcome)
   so abuse is bounded and detectable.
6. **Defense in depth (optional).** Consider a dedicated/limited crawl account so a compromise doesn't endanger
   the primary identity.

## 3. Compliance boundary (unchanged, restated)

Authorized sessions/cookies only; rate-limit + cache + provenance; **manual handoff** on CAPTCHA / access
walls. **NO** CAPTCHA bypass, **NO** access-control evasion, **NO** identity rotation. The MCP's structured
output fields are: `content, source_url, fetch_method, auth_context, failure_reason, needs_human_action` —
note `auth_context` reports *whether* an authed session was used, **never the cookie itself**.

## 4. Placement & dual-surface (from the locked decisions)

- Lives in the new **`Service/mcp/`** subcategory (user decision: option 2). It is a long-running server
  (like cookie-manager) that **wraps `Skill/crawl/*` + `Engine/*` as libraries**; it does not reimplement
  crawl/anti-crawl logic.
- Build the crawl logic so the **same core both exposes an MCP server (Path A) AND can export OpenAI
  tool-schemas / run as a local MCP** (the B′/C fallbacks). One capability, two surfaces — see
  `docs/sendbox/archive/mirothinker-fallback-paths.md`.
- Granularity: Engine `fetch`/`transcribe` + Skill/crawl → request/response MCP tools; watcher daemons →
  control tools only (out of Item-2 scope).

## 5. Acceptance (what the impler must demonstrate)

- A request **without** a valid token is rejected; **with** the token, `fetch(zhihu/bili url)` returns
  markdown.
- A request targeting a **non-allowlisted domain** is refused.
- **No cookie** appears in any tool input, output, log line, or on disk (assert in tests + inspect a live run).
- HTTPS + auth verified end-to-end; rate-limit + audit log observable.
- (When Miro confirms) the MCP is reachable by Miro's server and a real workflow run actually invokes a tool
  (not internal-search fallback).

## 6. Open dependencies (confirm before/at dispatch — UN-042)

Exact model id (`apodex-1-0-deepresearch` vs docs' `mirothinker-1-7`); both account whitelists enabled;
`mcp_servers` precise schema (transport http/SSE for a public server, auth field); Miro egress IPs (for §2.4
IP-allowlist); confirmation that an attached MCP tool actually fires.

— root orche g4
