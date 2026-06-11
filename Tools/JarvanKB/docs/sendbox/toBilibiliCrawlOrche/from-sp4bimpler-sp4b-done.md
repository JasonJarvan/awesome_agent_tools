> from: SP4bImpler (a Claude Code peer session, cwd = repo root)
> recipient: BilibiliCrawlOrche (SubOrche, your parent under root g4)
> type: milestone-done (SP-4b Bilibili Skill v1)
> purpose: SP-4b complete end-to-end (v2 pipeline steps 1–8). Offline-verified + merged locally. Converges back to you.
> lifecycle: this letter + `toSP4bImpler/handoff.md` are a burn-pair (Checkpoint-2) — burn both when you read this.

# SP-4b done — Bilibili Skill v1

## TL;DR
SP-4b shipped: a Bilibili video ref → frozen SP-4a engine transcribe → save Markdown, with vague-path LLM
classification. 10 TDD tasks, **29 unit tests pass**, mirror of SP-3, pure consumer (zero engine/LLMClient
edits). Merged to local `feat/agentcrawl-bootstrap` (`2334698`). **Live smoke is gated** (creds/engine-config)
— offline verification is complete and was the mandatory gate.

## Acceptance
| Item | Evidence |
|---|---|
| Importable API + thin CLI + agentskills.io SKILL.md | `bilibili_crawl.save_bilibili` / `bilibili-crawl --json` / `SKILL.md` + `scripts/sync-skill.sh` |
| Frozen SP-4a engine consumer (no edits) | `git diff --name-only` = `Skill/crawl/bilibili-crawl/` only; engine + `jarvankb_common` untouched |
| cookie active-PULL (`domain=bilibili.com`, no dot) → `BilibiliCredential` | `cookie.py` (SP-3 decrypt reuse) + `build_credential`; 5 tests incl. real-`openssl` legacy round-trip |
| cookie failure NON-FATAL (engine cookie-less-capable) | `api.py` try/except → `credential=None` + warn; `test_cookie_failure_degrades_to_no_credential` |
| vague_path classify (title + summary lead, fallback transcript) | `classify.py`; 5 tests incl. summary→transcript fallback + filesystem-authoritative `is_new` |
| render default single-file, config-overridable to split | `config.RenderConfig` + `api` slug=target.stem wiring; `test_split_transcript_writes_second_file` |
| Full unit suite | **29 passed, 1 warning** (warning = the cookie-degrade test's expected `warnings.warn`) |
| Final whole-impl review (opus) | **Ready to merge**; 3 minor non-blocking nits (inherited from SP-3, kept for parity) |

## Commits (on feat/agentcrawl-bootstrap)
design `b654662` · plan `2cfea0f` · plan-ready/board `beb833a` · code `b4fe48f`→`d3603fa` (10) · merge `2334698`.

## Step-8 RepoMem.merge (closed by impler, HITL with user)
**No global persist promotion** (user-ratified): SP-4b's cross-SP facts were all pre-promoted by SP-3/SP-4a
(cookie domain + engine cookie-less capability in `credentials.md`; LLMClient/SKILL.md in `llm-shared-layer.md`).
Module specifics (graceful-degrade decision, classify-input adaptation) live in
`Skill/crawl/bilibili-crawl/docs/RepoMem/decisions.md`. Temp `temp/sp4b-bilibili-skill/` pruned.

## Live verification (updated 2026-06-11)
- **LLM-provider live smoke ✓ PASSED.** User populated `.env` (`MIMO_API_KEY`). Rewrote `scripts/live_smoke.py`
  to an LLM-only smoke mirroring SP-3 (+ stdlib `.env` auto-load) — it exercises the REAL
  `jarvankb_common.LLMClient` (the one path offline tests mock). Ran it: provider `openai/mimo-v2.5-pro`
  classified the sample video → `机器学习` (existing folder), `LIVE SMOKE OK` (commit `c534d7e`). This confirms
  SP-4b's vague_path uses the real shared LLM layer end-to-end. (`api.py` imports `from jarvankb_common import
  LLMClient`; resolves to `Engine/common/src/jarvankb_common/llm_client.py`.)
- **Full transcribe→save live run** (engine side) is still blocked — not by SP-4b code, but by the B站-vertical
  ops gate **UN-035 (BiliNote yt-dlp `HTTP 412` downloader risk-control)**, which SP-5b hit and explicitly
  flagged as shared with SP-4b. Run `bilibili-crawl <BV> --out <path>` once BN's downloader is fixed. Does NOT
  block SP-6 (SP-4b registered/shipped). Dashboard: UN-033 archived (LLM half done); transcribe half → UN-035.

## Next-step request
Burn this letter + `toSP4bImpler/handoff.md` (burn-pair). SP-4b is registered to SP-6 per the SP Status Board.
