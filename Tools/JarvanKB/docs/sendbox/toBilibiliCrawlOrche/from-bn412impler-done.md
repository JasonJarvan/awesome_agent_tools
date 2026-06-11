> from: BN412Impler (child of BilibiliCrawl SubOrche)
> recipient: BilibiliCrawl SubOrche
> type: done (UN-035 / UN-037 — BN-412 downloader remediation)
> date: 2026-06-11
> lifecycle: after you read this, burn `toBN412Impler/handoff.md` per its §8

# DONE — BN-412 fixed, real video transcribed end-to-end, prevention automated

## 1. Definition-of-done evidence (live, 2026-06-11)

`bilibili-crawl BV1GJ411x7h7 --out <path> --json` produced real saved Markdown on BOTH paths:

| Path | transcript_source | Evidence |
|---|---|---|
| subtitle (engine prefetch → BN LLM-only) | `subtitle` | `/tmp/bn412-smoke/never-gonna-give-you-up.md` (3.4 KB, frontmatter + mimo summary + transcript) |
| **asr (the previously-412-blocked hop: BN yt-dlp download → bcut → LLM)** | `asr` | `/tmp/bn412-smoke/ngu-asr-path.md` (3.5 KB), forced by running credential-less (skill's graceful degrade), mirroring the 2026-06-02 SP-4a ASR baseline on the same BV |

SP-5b watcher needs no action: 412-failed videos were never marked seen (runbook §5 degrade), so the next cycle auto-retries and lands them.

## 2. Root cause (verified, single-variable matrix in the BN container)

| yt-dlp | cookie | playurl result |
|---|---|---|
| 2025.03.31 (image) | none | **412** |
| 2026.06.09 (latest) | none | **412** |
| 2025.03.31 | SESSDATA | 200 |
| 2026.06.09 | SESSDATA | 200 |

Plus: same container/egress IP with browser-UA hit `view`/`zone` APIs → 200. So:

- **bilibili's playurl API now rejects ANONYMOUS requests with 412** — independent of egress IP and yt-dlp version. Handoff candidates #1 (egress IP, "most likely") and #2 (yt-dlp upgrade) are both REFUTED; #3 (anti-detect headers) unnecessary.
- **"Cookie push didn't resolve" (2026-06-10) was a FALSE NEGATIVE**: BN's `BilibiliDownloader` is an import-time singleton (`app/services/constant.py`) that reads the cookie store once at process start. The container started 06-03; the cookie was pushed 06-10 → it sat in `/app/backend/config/downloader.json` but never reached the live yt-dlp. Fix = push cookie + `docker restart jarvankb-bilinote`.
- The engine's own `bilibili-api-python` calls were always 200 because they hit view/subtitle endpoints, not playurl — consistent with the handoff's observation, now explained.
- Container left at image-original yt-dlp 2025.03.31 (upgrade tested, then reverted — minimal diff; upgrade documented as a future lever only).

## 3. Prevention (user-approved in-session, option B)

Residual failure mode = SESSDATA rotation (engine best-effort re-pushes the fresh cookie into BN's store on every ASR run — `engine.py:52` — but the live process won't re-read it). Automated:

- `Engine/bilibili/deploy/bilinote/bn-cookie-sync.py` + host cron (`*/10`): pulls bilibili cookies from SP-1 (reuses `bilibili_crawl.cookie` decrypt, plaintext in memory only), compares **SESSDATA value only** against BN's store (full-string compare would flap against engine re-pushes), and only on change pushes + restarts + health-polls. Log: `~/.local/state/jarvankb/bn-cookie-sync.log` (never logs cookie values). Verified: no-op path (silent exit 0) and `--force` full path (push + restart + healthy in 8 s) + positive/negative yt-dlp cookie controls.
- **Why not an SP-1 exec hook**: the cookie-manager container has no docker.sock and its bridge netns cannot reach BN's host-loopback-only port — structurally impossible from inside; host cron is the correct seam.

## 4. Step-8 closure (HITL approved by user in-session)

- `Service/crawl/bilibili-watcher/docs/runbook.md` §5 412 row → verified root cause + 4-step SOP + automation pointer.
- `Engine/bilibili/deploy/bilinote/README.md` → cookie-singleton-needs-restart gotcha + bn-cookie-sync section.
- `docs/RepoMem/persist/architecture/crawl-pipeline.md §B站链路` → 412 bullet rewritten from "known hazard, candidates" to verified root cause + fix; stale escalation framing removed.
- Commits (local `feat/agentcrawl-bootstrap`, pathspec'd): `21c15fa` (root-cause + promotions), `a574ea1` (automation), + dashboard/letter commit.
- Lane: fast (no `temp/<slug>/`, evidence in this letter + saved notes).

## 5. Observations for you to route (NOT acted on — out of my scope)

1. **SP-1 `refresh-zhihu` hook is dead config**: it points at `/opt/crawl/refresh.sh`, which exists neither on host nor in the cookie-manager container (copied from the example). It fires on every zhihu cookie push and fails silently. Zhihu vertical's call whether to fix or delete.
2. The engine `BiliNoteClient trust_env=False` candidate fix (already routed to root per §B站链路) is unchanged by this task — deploy-level `ALL_PROXY` clearing remains the rule.
3. SP-4b's gitignored `Skill/crawl/bilibili-crawl/config.yaml` now exists (created for the DoD smoke: cookie-manager box `jasonjarvan`, llm profile `mimo`). Note the engine resolves `config/bilibili-engine.yaml` relative to **cwd** — the smoke ran from `Engine/bilibili/` with `BILIBILI_CRAWL_CONFIG` pointing at the skill config; may be worth a usage note in SP-4b docs someday.

## 6. Dashboard

UN-035 + UN-037 moved to Archive (done 2026-06-11, by bn412impler).
