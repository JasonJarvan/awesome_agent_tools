---
slug: sp5b-bilibili-watcher
status: smoke-partial-bn412-gate
domains: [crawl]
updated_at: 2026-06-10
language: zh
audience: A2A
---

# SP-5b live `--once` smoke evidence (2026-06-10)

Bounded smoke: only `编程折腾` (id `1195057867`), state pre-seeded `watermark=1772042627` (2nd-newest
fav_time) so exactly the newest item `BV1VRfcBrERy` (fav_time `1772042686`) is "new" → at most 1
transcription. Config + output + state in `/tmp` (secrets never committed). BN up at `127.0.0.1:3015`,
custom provider `cf11f2fc-42ac-4d44-871d-fbb282a2fe0b` (xiaomitokenplan/mimo).

## ✅ Verified LIVE (real components, repeated 3×, consistent)
- **cookie_provider**: `GET 127.0.0.1:48088/get/jasonjarvan` → 200 → decrypt → 21 `bilibili.com` cookies, SESSDATA+bili_jct present.
- **favorites_client**: `GET api.bilibili.com/x/v3/fav/resource/list?...&order=mtime` → 200; parsed items; **fav_time early-stop fired live** (`early-stop at fav_time=1772042627 <= watermark=1772042627`) → exactly the newest item processed.
- **watcher cycle + fetcher → engine**: engine invoked (metadata 200, nav 200, player/wbi 200, **AI subtitle aisubtitle.hdslb.com 200**, BN `sys_check` 200, BN `generate_note` 200, BN `task_status` polled).
- **graceful degrade + §5 watermark (the daemon's core failure invariant) — LIVE PROOF**: engine raised `BiliNoteError ... HTTP 412`; `fetcher` caught it → returned None → item **NOT saved, NOT marked seen**, `failed=[1772042686]` → `watermark = min(failed)-1 = 1772042685` (state file confirms `{"watermark":1772042685,"seen":[]}`), **"0 new"**, daemon did **not crash**. This is the §5 advance rule + don't-mark-seen-on-failure, observed live.
- **env gotcha found + handled**: the **frozen engine's `BiliNoteClient` builds `httpx.Client` without `trust_env=False`**, so it inherits the host's `ALL_PROXY` (SOCKS) and raises `ImportError: socksio` at construction even for localhost BN. Workaround: run with `ALL_PROXY`/`HTTP(S)_PROXY` unset (or install socksio + `NO_PROXY=127.0.0.1,localhost`). → documented in `runbook.md`. (Engine-scope, not SP-5b; noted for SP-4b too.)

## ❌ Blocked: a real successful transcription → saved Markdown
**Persistent `HTTP 412 Precondition Failed`** on BN's yt-dlp downloading bilibili video metadata
(`ERROR: [BiliBili] 1VRfcBrERy: Unable to download JSON metadata: HTTP Error 412`). Reproduced 3×.
Pushing the SESSDATA cookie to BN's downloader (`POST /api/update_downloader_cookie` → 200) did **NOT**
resolve it. → bilibili risk-control on the BN container's downloader (frozen engine + BN + environment),
**external to SP-5b** and **vertical-wide** (SP-4b's live transcription would hit the same). Surfaced as a
gate to SubOrche + Dashboard (the handoff anticipated "BN down / 403 at live smoke" exactly).

## Verdict
SP-5b watcher code is **fully verified**: 44/44 unit+integration tests + the entire live pipeline incl.
the engine-failure degrade path with exact §5 watermark behavior. The transcribe→save SUCCESS path is
verified at integration level (fake engine: `test_full_cycle_then_second_is_noop`); its LIVE confirmation
awaits a BN downloader that passes bilibili's 412 (a BN/ops fix, not an SP-5b code change).
