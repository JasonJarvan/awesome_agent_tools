> from: BilibiliCrawl SubOrche (sub-orchestrator under root g4)
> recipient: root orche g4
> type: milestone-done — Bilibili downstream vertical v1 COMPLETE (roll-up + convergence)
> lifecycle: after you read this, **burn `docs/sendbox/toBilibiliCrawlOrche/handoff.md`** (the root→SubOrche
>   delegation) — my SubOrche role converges. Companion decisions in `from-bilibilicrawlorche-port-ratelimit-decisions.md`.
> date: 2026-06-14

# ⚫ Bilibili downstream vertical — v1 DONE

The whole vertical you delegated (handoff `toBilibiliCrawlOrche/`) is complete + live-verified end-to-end.

## 1. The three pieces — all ⚫ done, all live-verified
| SP | Merge | Tests | Live evidence |
|---|---|---|---|
| **SP-4b** Bilibili Skill | `2334698` | 29 | LLM vague-path (`mimo`) ✓ + **full transcribe→save** ✓ (`BV1GJ411x7h7`: explicit path + vague→`music-videos`; cookie graceful-degrade) |
| **SP-5b** Bilibili Watcher | `51557db` | 44 | `--once` real favorite → engine → **14.7KB md saved**, `fav_time` watermark advanced; 2nd `--once` early-stop `0 new` (dedup invariant) |
| **BN-412** (UN-035/037) | `21c15fa`+`a574ea1` | — | root-caused + fixed + prevention cron; both consumers' full live test re-run ✓ |

## 2. BN-412 — the root cause (closes the "should the engine rate-limit?" question)
**Not a rate-limit / not an IP / not a yt-dlp problem.** bilibili's **playurl API now 412s ANY anonymous
request**; needs SESSDATA. The earlier "cookie push didn't help" was a **false negative** — BN's
`BilibiliDownloader` is an import-time singleton that reads the cookie once at process start, so a pushed
cookie needs a `docker restart` to take. Fixed; prevention = host cron `bn-cookie-sync.py` (`*/10`, pushes +
restarts only on SESSDATA change). So **rate-limiting would not have helped here** — see the decisions letter
for where rate-limiting *does* belong (preventive, SP-4a engine).

## 3. Step-8 promotions (all impler-owned, HITL-approved, already landed)
- `crawl-pipeline.md §B站链路`: NEW favorites-API sub-section (`fav_time`≠`pubtime`, `order=mtime` early-stop,
  `has_more`-not-`media_count` paging) + BN-consumer gotchas (unset `ALL_PROXY`; 412 verified root-cause + fix).
- `memory/empirical-api-first.md`: the "crawl APIs empirically, doc + user-review before implementing" lesson
  (SP-5b's Stage-0 gate vindicated it — `fav_time` is real, closing SP-5a's armchair miss).
- `runbook.md` §5 (412 SOP) + `Engine/bilibili/deploy/bilinote/README.md` (cookie-singleton-needs-restart).

## 4. Routed to you (out of my scope — your / Zhihu-vertical's call)
1. **SP-1 `refresh-zhihu` hook is DEAD config** (BN412Impler found it): points at `/opt/crawl/refresh.sh`,
   which exists neither on host nor in the cookie-manager container (copied from the example). It fires on
   **every** zhihu cookie push and **fails silently**. → Zhihu vertical / SP-1 owner: fix or delete.
2. **Engine `BiliNoteClient` lacks `trust_env=False`** → inherits host SOCKS `ALL_PROXY`, breaks local-BN
   connect (`socksio` ImportError); deploy-rule workaround = unset proxy. Candidate **SP-4a engine fix**
   (already noted in §B站链路; reiterated here for your scheduling).
3. **SP-4b config cwd-resolution** (minor): `config/bilibili-engine.yaml` + llm config resolve relative to
   CWD; running the skill from `Engine/bilibili/` needs `BILIBILI_CRAWL_CONFIG` + `JARVANKB_LLM_CONFIG`.
   Worth an SP-4b usage-doc note someday (not blocking).

## 5. Sendbox convergence (chains I burned)
`from-sp4bimpler-sp4b-done` + `toSP4bImpler/handoff` (last session); `from-sp5bimpler-sp5b-done`,
`from-bn412impler-done` + `toBN412Impler/handoff`, the SP-5b blocker chain. SP-5b/BN412 impler sessions
already burned their own inbound handoffs + my greenlight. **Left for you to burn: `toBilibiliCrawlOrche/handoff.md`** (your delegation to me).

## 6. State
Local `feat/agentcrawl-bootstrap` only, no push, engines frozen/untouched. Bilibili vertical needs nothing
further from me except the two decisions in the companion letter (port convention + rate-limit placement),
which are governance/engine = yours.

— BilibiliCrawl SubOrche, converging
