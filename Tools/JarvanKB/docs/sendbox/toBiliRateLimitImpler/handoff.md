> from: BilibiliCrawl SubOrche (sub-orchestrator under root g4)
> recipient: BiliRateLimitImpler (a Claude Code peer session, cwd = repo root)
> mode: child-handoff (sendbox-protocol Mode A — SubOrche stays alive; you converge back)
> purpose: harden Engine/bilibili (SP-4a) with active rate-limiting + throttle backoff — mirror SP-2 Zhihu v1.2
> lifecycle: burn after you write `from-biliratelimitimpler-done.md` and SubOrche reads it

# Handoff — SP-4a Bilibili Engine rate-limit hardening (v1.x)

> ⚠️ **Parent re-pointed to root g4 / MainOrc** (BilibiliCrawl SubOrche converged 2026-06-14). Report
> plan-ready / blocker / done to **`docs/sendbox/toOrchestrator/from-biliratelimitimpler-*.md`** (NOT
> `toBilibiliCrawlOrche/`). Everything else in this handoff stands. Greenlight comes from root.

## 0. What you are + a scope note
An **engine-hardening impler**, child of BilibiliCrawl SubOrche. **Normally `Engine/bilibili` (SP-4a) is
root-owned + frozen and out of the SubOrche's scope** — but the **user explicitly authorized this dispatch
(2026-06-14)**, so it runs as my child this once. You change ONLY the engine's internals, **non-breaking**.

This is **preventive**, not a fix for anything broken. **The recent BN-412 was NOT a rate problem** (it was
playurl rejecting anonymous requests + a BN cookie singleton — already fixed). Rate-limiting protects the
engine's own bilibili calls from *future* risk-control, exactly as SP-2 did for Zhihu.

## 1. The task — mirror SP-2 Zhihu v1.2 for Bilibili
Add **active rate-limiting + throttle backoff** at the Bilibili engine's HTTP chokepoint(s), so both SP-4b
(skill) and SP-5b (watcher) — which call the platform *through the engine* — are covered without duplication.

- **Active rate-limit**: min-interval + jitter, **process-shared** (mirror SP-2's mechanism in
  `Engine/zhihu/src/zhihu/fetcher.py`).
- **Backoff on throttle signals**: HTTP 429 (+ bilibili rate codes like `-509`/`-799` if you find them),
  honoring `Retry-After`. **Leave 412 alone** — that's the anonymous-playurl auth signal the engine already
  surfaces; do NOT treat it as a rate signal.
- **Config knob**: expose like SP-2's `zhihu.configure(...)` → a `bilibili.configure(...)` (or engine-config
  field) for min-interval/jitter/backoff. **Sensible defaults on; a single URL must see no added latency**
  (SP-2's acceptance bar: "限流可观测生效 + 单 URL 无延迟").
- **NON-BREAKING**: the v1 frozen public contract — `BilibiliEngine`, `transcribe()`, `BilibiliCredential`,
  `EngineConfig`, `RenderOptions`, `result.render()`, dataclass field names (`Engine/bilibili/docs/interface.md`
  §3) — stays byte-identical. You ADD a knob; you don't change signatures.

**Where it hooks** (confirm by reading — don't trust me blindly): the bilibili-api-python calls in
`Engine/bilibili/src/bilibili/{metadata.py,subtitle.py}` (`get_info`/`get_subtitle`/playurl) and the BN HTTP
calls in `bilinote_client.py`. Decide the single chokepoint shape in your brainstorm (a shared limiter the
modules route through, mirroring how SP-2 centralized in `fetcher.py`).

## 2. Inputs (minimum)
| Resource | Role |
|---|---|
| `Engine/zhihu/src/zhihu/fetcher.py` + `__init__.py` (`configure`) + `Engine/zhihu/docs/superpowers/plans/2026-06-09-zhihu-ratelimit-hardening-plan.md` | **THE TEMPLATE** — SP-2 v1.2; mirror its mechanism, config knob, tests |
| `docs/RepoMem/persist/architecture/crawl-pipeline.md` §知乎链路 (rate-limit bullets) + §B站链路 | precedent + the verified note "engine-side rate-limit ≠ BN-412" |
| `Engine/bilibili/src/bilibili/{metadata.py,subtitle.py,bilinote_client.py,engine.py,config.py}` | where you add the limiter |
| `Engine/bilibili/docs/interface.md` | the frozen contract you must NOT break |
| `Engine/zhihu/docs/RepoMem/decisions.md` (D8/D9) | SP-2's rate-limit decisions (mechanism stays in code) |
| `CLAUDE.md` §3/§4 | governance — you own Step-8 closure |

## 3. Pipeline (v2)
- **Step 2 brainstorm (compressed)**: the design is "mirror SP-2 v1.2 for Bilibili" — confirm only the
  chokepoint shape + config-knob surface + defaults. Don't re-litigate whether to do it.
- **TDD** (it's a feature; SP-2 shipped 67 tests): unit-test the limiter (min-interval, jitter bounds,
  process-shared), the backoff (429 + `Retry-After`, exponential), and that the frozen contract is unchanged.
- **Lane**: judge per CLAUDE.md — likely **full** (engine module change; may add a §B站链路 note). Declare in plan frontmatter.
- **verification-before-completion**: tests green + a **real-call smoke** showing rate-limit observably active
  (e.g. N rapid calls spaced by min-interval) AND a single `transcribe()` sees no added latency. Engine still
  transcribes end-to-end (BN is up at `127.0.0.1:3015`).
- **worktree** `.worktrees/bili-ratelimit/` off local `feat/agentcrawl-bootstrap`; `requesting-code-review` +
  `finishing-a-development-branch` both ask-first.

## 4. Scope / boundaries
- ONLY `Engine/bilibili` rate-limit hardening, **non-breaking**.
- Do NOT touch SP-4b / SP-5b (they inherit the limiter automatically through the engine).
- Do NOT touch the BN container / BN-412 (separate, done — UN-035).
- `git push` / merge-to-main / rebase — **local only**. Commit prefix `feat(bili-ratelimit):` /
  `docs(bili-ratelimit):`. **Commit with explicit pathspec** (`git commit -- <paths>`) + verify
  `git diff --cached` first — index is **shared with concurrent sessions**.

## 5. Step-8 (you own closure)
Promote only **cross-SP-reusable** Bilibili throttle root-causes/gotchas to `crawl-pipeline.md §B站链路`
(e.g. which bilibili codes mean "throttled", real Retry-After behavior) — **mechanism stays in code**, like
SP-2's D8. Module specifics → `Engine/bilibili/docs/RepoMem/decisions.md`. HITL with user.

## 6. Convergence
Parent = BilibiliCrawl SubOrche. Inbound: `docs/sendbox/toBiliRateLimitImpler/from-bilibilicrawlorche-*.md`.
| Event | Write to |
|---|---|
| plan-ready | `docs/sendbox/toBilibiliCrawlOrche/from-biliratelimitimpler-plan-ready.md` |
| blocker | `docs/sendbox/toBilibiliCrawlOrche/from-biliratelimitimpler-blocker-<topic>.md` |
| done | `docs/sendbox/toBilibiliCrawlOrche/from-biliratelimitimpler-done.md` |

## 7. Lifecycle
`burn` after `from-biliratelimitimpler-done.md` + SubOrche reads.

---
**Begin at Step 1 (read SP-2 `fetcher.py` + its plan as your template), then Step 2 (compressed brainstorm:
confirm the chokepoint + knob).** The bar is SP-2 parity for Bilibili, non-breaking.
