> from: SP5bImpler (Claude Code peer session, child of BilibiliCrawl SubOrche; cwd = repo root; active 2026-06-10)
> recipient: BilibiliCrawl SubOrche (my parent) — **and a heads-up that this is VERTICAL-WIDE (affects SP-4b too)**
> purpose: surface a BN-side HTTP 412 that blocks LIVE transcription at smoke; SP-5b code is done + verified.
>   This is the handoff-anticipated "BN down / 403 at live smoke" gate — it does NOT block SP-5b code/merge.
> lifecycle: burn after SubOrche acks (or folds into vertical tracking); the underlying BN-412 is an ops fix.
> date: 2026-06-10

# Gate (not a code defect) — BN yt-dlp HTTP 412 blocks live transcription (vertical-wide)

## 1. TL;DR
SP-5b watcher is **fully implemented + verified** (44/44 tests + the entire LIVE pipeline incl. the §5
failure-degrade path). The ONLY thing not shown live is a successful transcription → saved Markdown,
because **BN's yt-dlp consistently fails with `HTTP 412 Precondition Failed` ("Unable to download JSON
metadata")** — bilibili risk-control on the BN container's downloader. Reproduced 3×; **pushing the
SESSDATA cookie to BN (`POST /api/update_downloader_cookie` → 200) did NOT resolve it.** This is a
**frozen-engine + BN + environment** issue, external to SP-5b, and **vertical-wide: SP-4b's live smoke
will hit the same** (same engine, same BN).

## 2. What IS verified (live, real components, 3× consistent)
- cookie_provider: 21 `bilibili.com` cookies pulled+decrypted from SP-1; SESSDATA+bili_jct present.
- favorites_client: `order=mtime` listing 200; **fav_time early-stop fired live** (only the newest item processed).
- watcher cycle → fetcher → engine: engine invoked (metadata/nav/player-wbi/**AI-subtitle 200**, BN generate_note + task_status polled).
- **§5 failure-degrade, LIVE PROOF**: engine raised on the 412 → fetcher returned None → item NOT saved, NOT marked seen → `watermark = min(failed)-1 = 1772042685` (state file confirms) → "0 new", **daemon did not crash**.
- Bonus env gotcha (documented in runbook): the frozen engine's `BiliNoteClient` builds httpx without `trust_env=False` → inherits host `ALL_PROXY` (SOCKS) → `ImportError: socksio` even for localhost BN. Workaround: unset `ALL_PROXY`/`HTTP(S)_PROXY` (or `httpx[socks]` + `NO_PROXY=127.0.0.1,localhost`). Relevant to SP-4b + the docker deploy.

## 3. The 412 (the gate)
```
BiliNote error: ERROR: [BiliBili] 1VRfcBrERy: Unable to download JSON metadata:
HTTP Error 412: Precondition Failed (caused by <HTTPError 412: Precondition Failed>)
```
BN is UP + healthy (`/docs` 200, providers 200, generate_note/task_status 200). The 412 is bilibili
blocking BN's yt-dlp metadata fetch. Likely fixes (BN/ops side, NOT SP-5b code): update BN's yt-dlp,
change the BN container's egress IP, or add wbi/anti-detection headers to BN's downloader. SP-4a's
smoke succeeded 2026-06-02 on specific BVs — risk-control conditions appear to have tightened since.

## 4. Ask / impact
- **No action needed on SP-5b code** — it's done, verified, and degrades correctly on exactly this failure.
- **Heads-up for SP-4b**: its live smoke will hit the same BN-412; coordinate one BN/ops fix for the vertical.
- The user can merge SP-5b now (code complete) and treat the BN-412 as a separate vertical ops item, or
  hold the merge until BN transcribes. Surfaced as Dashboard ops row.

## 5. State
14 commits on isolated branch `sp5b-bilibili-watcher` (off local `feat/agentcrawl-bootstrap`). Engine
untouched (frozen). No push. Awaiting the user's finishing-a-development-branch decision (ask-first).
