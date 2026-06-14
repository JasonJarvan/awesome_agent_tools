> from: BilibiliCrawl SubOrche (converging — this is my sign-off)
> recipient: root orche g4 / MainOrc
> type: convergence + re-parent (two live implers handed up; one product decision handed to you)
> lifecycle: burn after you (a) pick up the two implers below and (b) burn `toBilibiliCrawlOrche/handoff.md`
> date: 2026-06-14

# BilibiliCrawl SubOrche — converging; re-parenting 2 live implers to you

Per the user (2026-06-14: "都交给 MainOrc 决定，你将收敛"), I'm winding down. The Bilibili downstream
vertical v1 is **complete** (see `from-bilibilicrawlorche-vertical-done.md`: SP-4b + SP-5b + BN-412 all done,
live-verified). Two implers I spawned are **still live** — they are now **yours** to coordinate:

## 1. UN-046 — BiliRateLimitImpler (GO; just coordinate to done)
- SP-4a Bilibili engine rate-limit hardening (mirror SP-2 v1.2, non-breaking, **preventive**). The user
  greenlit it and authorized me to dispatch (crossing my engine-scope boundary) — but **the engine is your
  natural domain anyway**, so ownership returns to you cleanly.
- Handoff: `docs/sendbox/toBiliRateLimitImpler/handoff.md` (I added a top-note re-pointing its convergence to
  `toOrchestrator/`). It runs the full v2 pipeline + owns its Step-8. **Your job: greenlight its plan, review,
  let it close.** No open question — the design is "SP-2 v1.2 parity for Bilibili."

## 2. UN-047 — WatcherDeployImpler (ON HOLD — needs YOUR product decision)
- Bring up both watcher daemons (SP-5a + SP-5b) + live-verify. Handoff:
  `docs/sendbox/toWatcherDeployImpler/handoff.md` — **enriched** with the ZhihuCrawl SubOrche's deploy
  gotchas (state_dir MUST be a persistent volume = #1 footgun; zhihu-watcher binds no port; clear ALL_PROXY;
  `__zse_ck` staleness = UN-032). Stage-0 asks the user for the vault output root.
- **HELD pending the product decision the user routed to you:** does the user want **autonomous background
  favorites→vault** (the watcher), **on-demand agent crawl** (the MCP), or **both**?

### My analysis for that decision (watcher vs MCP — they are ORTHOGONAL, not substitutes)
- **MCP (UN-043, your scope)** = request/response **tools wrapping the SKILLS** (give MiroThinker/Hermes
  on-demand crawl). Natural MCP fit.
- **Watcher (SP-5a/5b)** = an **autonomous daemon** that polls + writes the vault with no agent present.
  **Not an MCP tool** (a daemon isn't a "call").
- **"Combine Crawl+Engine+Service into one MCP" is NOT best practice**: it mixes interaction models, and the
  engine is already wrapped by the skills (don't re-wrap it). Best decomposition = MCP wraps skills; watcher
  stays a daemon; engine stays a library.
- **Compliance (limit/auth/sourcing) belongs in the ENGINE** (UN-046 is adding it) — **both** the watcher and
  the future MCP inherit it. The engine is the shared chokepoint, NOT the MCP.
- **So neither gates the other.** My recommendation: both can proceed in parallel (watcher = autonomous
  vault-fill; MCP = on-demand). But it's your + the user's product call → hence HELD.

## 3. Already in your inbox (decisions to ratify/action)
- `from-bilibilicrawlorche-port-ratelimit-decisions.md` — **D1** host port convention = formalize **48xxx**
  (45xxx blocked by foreign `node:45397`; zero migration) → ratify + propagate to CLAUDE.md/credentials.md/ops-doc;
  **D2** rate-limit placement = SP-4a engine (= UN-046, now in flight).
- `from-bilibilicrawlorche-vertical-done.md` — milestone + routed observations (SP-1 dead `refresh-zhihu`
  hook = Zhihu vertical's call; engine `trust_env=False` candidate; SP-4b cwd-config note).

## 4. Cleanup
- I burned all SP-4b / SP-5b / BN-412 chains already. **Please burn `toBilibiliCrawlOrche/handoff.md`** (your
  original delegation to me) — my SubOrche role is converged. The two impler handoffs above stay live (now yours).

— BilibiliCrawl SubOrche, signing off
