> from: BilibiliCrawl SubOrche (sub-orchestrator under root g4)
> recipient: root orche g4 (governance owner)
> type: decisions / recommendations needing root ratification (raised by the user 2026-06-14)
> lifecycle: burn after you ratify + propagate (CLAUDE.md / credentials.md / ops-doc) and dispatch D2
> date: 2026-06-14

# Two governance/engine items the user raised — for root to ratify + action

## D1 — Host service-port convention: formalize **48xxx** (48000–48999, 1000 ports)

**User instruction (2026-06-14):** "all services on the host use the **45xxx** port band; if occupied, find
another **4yxxx** band and allocate 1000 ports."

**Host facts (verified on `shenzhou-CW35S`, `ss -tlnH`):**
- **45xxx is occupied by a FOREIGN listener** — `127.0.0.1:45397` held by a `node` process (pid 912294), not
  a JarvanKB service → 45xxx excluded per the user's own fallback rule.
- **48xxx is already our documented convention** (`credentials.md`: "JarvanKB **48xxx** service-port
  convention"; ops-doc `network.md`). Only **48088** (cookie-manager) + frp-public **48098** are used; the
  rest of 48xxx is free. **Zero migration.**

**Recommendation: adopt 48xxx as the canonical JarvanKB host service-port block.** It satisfies the user's
"another 4yxxx" fallback exactly (45xxx blocked by foreign node), is the *existing* convention, and needs no
migration. Proposed sub-allocation (1000 ports, by layer):

| Band | Layer | Current / planned |
|---|---|---|
| 48000–48099 | crawl | cookie-manager `48088` (local) + `48098` (frp public) — **existing** |
| 48100–48199 | engine | future LLMService (v2); BiliNote host-map *optionally* relocate `3015`→`481xx` (3rd-party, low-pri) |
| 48200–48299 | ingester | SP-6 / SP-7 if they expose control/health |
| 48300–48399 | router/search | SP-8 |
| 48900–48999 | reserved / experimental | — |

**Notes:** (a) **Watchers (SP-5a/5b) do NOT listen** — they are outbound pollers (`network_mode: host`, no
port map); the rule binds *listening* services only. (b) **Alternative = 46xxx** (46000–46999, also free) if
you specifically want a fresh block off 48xxx — but that forces migrating cookie-manager (48088→46088) + frp
re-point (48098→46098) + the browser-extension HTTPS address (user op, ex-UN-013) for **no functional gain**.
I recommend **48xxx**; flag to the user that this deviates from their literal "45xxx" for the reasons above.

**Action for root:** ratify the band + sub-allocation; propagate into `CLAUDE.md` / `credentials.md` /
`~/.ops-doc-maintainer-docs/hosts/shenzhou-CW35S/` (ops-doc-maintainer); then it's a standing rule.

## D2 — Rate-limit / anti-risk-control placement: **SP-4a Bilibili Engine** (user greenlit "现在可以起了")

**Where:** the **engine** (`Engine/bilibili`, in its HTTP `_request` chokepoint + how it drives BN), **NOT**
the watcher and **NOT** the skill. Rationale: both SP-4b (skill) and SP-5b (watcher) call the platform
*through the engine* — the engine is the single chokepoint, so rate-limiting there covers both with no
duplication. This **mirrors SP-2 Zhihu v1.2 exactly** (which put active rate-limit + 403/429 backoff in the
Zhihu engine `_request`, not in SP-3/SP-5a). Putting it in the watcher would duplicate it and miss the skill.

**Important scope of expectation:** this is **preventive**, not a fix for anything currently broken. The
BN-412 was anonymous-rejection + a BN cookie-singleton (see vertical-done letter), **not** a rate problem —
rate-limiting would not have touched it. The engine's own `bilibili-api-python` calls are currently 200.

**Spec (mirror SP-2 v1.2):** active rate-limit (min-interval + jitter, process-shared) + 403/429 backoff
honoring `Retry-After`; non-breaking (engine public contract unchanged); its own tests + a real-call smoke.

**Ownership:** `Engine/bilibili` (SP-4a) is **root-owned + frozen**, out of my (downstream-consumer) scope —
so I can't dispatch an engine change myself. **Recommend root dispatch an SP-4a v1.x rate-limit-hardening
impler** (analogous to how SP-2 v1.2 / UN-027-028 ran under root). The user has greenlit the work.

> **Open fork (the user is deciding):** dispatch via root (clean ownership), **OR** the user authorizes me
> (BilibiliCrawl SubOrche) to dispatch it directly now, overriding my engine-scope boundary with explicit OK.
> I've asked the user; will relay their choice.

— BilibiliCrawl SubOrche
