# BN internal concurrency / rate-limit investigation (2026-06-21)

> User-prompted follow-up: "calling BN's API isn't rate-limited by us — can rapid/concurrent API calls BYPASS
> BN's own throttle and burst bilibili?" Subagent inspected the RUNNING container (read-only, no tasks fired),
> verified byte-identical to upstream `JefferyHCool/BiliNote@master`. Decision (user): **record + defer the fix.**

## Findings (Q1–Q5)
1. **BN has a GLOBAL concurrency cap, not unbounded.** `/api/generate_note` returns `task_id` immediately, then
   `run_note_task` is submitted to a **process-level singleton `ThreadPoolExecutor(max_workers=3)`**
   (`/app/backend/app/services/task_serial_executor.py`, misleading alias `SerialTaskExecutor`; container
   `TASK_MAX_WORKERS` UNSET → default **3**). Single uvicorn worker (`main.py:112`, no `workers=`). No
   celery/RQ/Semaphore/asyncio.Queue elsewhere.
2. **Global, NOT per-request → NOT bypassable from the API layer.** N concurrent `generate_note` → still ≤3
   concurrent yt-dlp downloads, the rest queue in the one shared pool. So you canNOT hammer the API into
   unbounded fan-out. (Worst case = 3× serial, not N×.)
3. **BN applies ZERO rate-limit to bilibili.** `bilibili_downloader.py` yt-dlp opts have NO `limit-rate /
   sleep_interval / max_sleep_interval / sleep_interval_requests / retries / concurrent_fragment_downloads /
   throttledratelimit`. Full-speed, back-to-back, no 412/429 backoff. No proxy (direct egress).
4. **Shared egress IP.** BN container is bridge NAT (`NetworkMode=bilinote_default`, `172.22.0.2`) → SNAT to the
   **host public IP = the same IP the engine's direct get_info/get_subtitle/subtitle-CDN calls use.** A BN-side
   burst risk-controls the shared IP, which also endangers the engine's direct calls.

## Verdict (Q5)
BN's protection is a **non-bypassable global concurrency cap of 3** — good. BUT it is ONLY a concurrency cap
(no rate-limit at all) running full-speed on the shared host IP. So a CONCURRENT bulk consumer (a watcher
firing many parallel `transcribe()` — requires explicit threading, since `transcribe()` is synchronous/blocking)
has a **bounded** residual exposure: ≤3 concurrent, full-speed playurl downloads on the engine's egress IP.
Severity: **bounded + modest** (transcribe is minutes-long/BN-bound; the playurl download is a brief few
requests ×3, far below typical risk-control thresholds; reaching 3 needs deliberate consumer concurrency).

## My earlier BN-exclusion call, updated
The core was right (BN can't be bypassed into unbounded fan-out → the engine's direct-call rate-limit is the
main lever). The refinement: BN has zero rate-limit + shares the engine's IP, so the exclusion isn't *fully*
risk-free for concurrent consumers — there's a small, bounded hole.

## Recommended fix — DEFERRED (user 2026-06-21: record + revisit)
Engine-side, BN untouched. In `bilinote_client.py`:
- a configurable `threading.BoundedSemaphore(n)` (n ≤ 3, default ~2) held across `generate_note`/`transcribe`
  so the engine never has more than n BN tasks in flight (caps fan-out at the source, headroom under BN's pool);
- optionally a min-interval on `generate_note` submissions (reuse the engine's existing `ratelimit` limiter
  discipline — BN has no rate-limit of its own).
Hook: `BiliNoteClient.__init__` (params from `bilibili-engine.yaml`) wrapping `generate_note` (the single
chokepoint every consumer passes through). **Revisit when:** SP-5b watcher runs `transcribe()` concurrently.

## Evidence (subagent, container `4bc0fe75829f` / `jarvankb-bilinote`)
- pool: `/app/backend/app/services/task_serial_executor.py` (cap=3 singleton) + `note.py:143` `task_serial_executor.run(...)`
- route/bg-task: `/app/backend/app/routers/note.py` (`generate_note`, `run_note_task`)
- yt-dlp opts (no throttle): `/app/backend/app/downloaders/bilibili_downloader.py`
- single worker: `/app/backend/main.py:112`; supervisord `[program:backend]` (no `TASK_MAX_WORKERS`)
- net: `docker inspect` → `NetworkMode=bilinote_default`, `172.22.0.2` (bridge → host-IP SNAT)
- engine client (no gating today): `Engine/bilibili/src/bilibili/bilinote_client.py` (`generate_note` L45, `transcribe` L77)
