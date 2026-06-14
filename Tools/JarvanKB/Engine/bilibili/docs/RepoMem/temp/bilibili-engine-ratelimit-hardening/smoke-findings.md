# Live smoke findings — SP-4a bilibili rate-limit hardening (2026-06-14)

Task-scoped temp capture (full lane). Script: `/tmp/bili_ratelimit_smoke.py` (throwaway, NOT committed).
Run env: proxies cleared + `NO_PROXY=127.0.0.1,localhost`, `PYTHONPATH=src` (worktree code), BN @ `127.0.0.1:3015`.

## A) Pacing observably engages — PASS (deterministic)
`configure(enabled=True, min_interval=0.3, jitter=0.0)`, fresh `_limiter`, 5 `paced(no-op)` calls:
- first-call wait = **0.0 ms** (fresh process: `_last=0` → target in past → no sleep)
- inter-call start gaps = **[0.3, 0.3, 0.3, 0.3] s** (each ≥ min_interval)
⇒ limiter engages exactly as designed; SP-2 parity for "限流可观测生效".

## B) Single-URL ~no added latency — supported (with a measurement caveat)
Real `get_info(BV1GJ411x7h7)`: title=`【官方 MV】Never Gonna Give You Up - Rick Astley`, cid=137649199, dur=213s.
- pacing-ON (fresh-process first call) 666 ms | pacing-OFF 114 ms | delta 553 ms.
- The 553 ms delta is **NOT pacing** — it is cold-session/network variance (bilibili-api-python builds a
  fresh async httpx session per `asyncio.run`, no connection reuse; ON ran cold-first, OFF ran warm-second).
  The first paced call's limiter wait is **provably 0** (see A: first_wait=0.0 ms). The single-URL bar rests on
  that invariant, not on B's noisy wall-time.

## C) Real burst pacing — corroborates
3 rapid real `get_info`, default pacing ON, `_last` reset: gaps **[0.128, 0.39] s**. First gap 0.128 = call-1
unpaced (fresh `_last`) + its network; second gap 0.39 ≥ 0.3 = limiter wait + network. Real calls get spaced.

## D) End-to-end transcribe — BLOCKED by a BN-side issue, UNRELATED to this change
`transcribe(BV1GJ411x7h7)` (ASR path, no cookie) → metadata fetched OK → `_bn.transcribe` → poll → task FAILED:
`BiliNote error: Error code: 401 - Invalid API Key` (the `mimo-v2.5-pro` LLM provider in BN's SQLite).
- This is **downstream of the engine**, at BN's LLM summary stage. Our diff only touches the 3 bilibili-facing
  calls (`get_info`/`get_subtitle`/`subtitle-body`), all upstream and all verified working (metadata fetched
  5+ times across A/B/C). The pacing change cannot cause a BN LLM 401.
- Ops drift: SP-4b confirmed full transcribe+save LIVE on 2026-06-11 (commit `e8039d3`); BN's LLM key has
  expired/rotated since. Fix = refresh the provider key in BN + restart container (BN/ops side — handoff §4
  "do NOT touch the BN container"). Out of scope for this task.
- Verdict: the in-scope path (bilibili-facing calls + active pacing + non-breaking contract) is fully verified;
  the BN LLM 401 is a separate, pre-existing ops blocker on the FULL end-to-end re-run.

## Unit suite
`PYTHONPATH=src python3 -m pytest -q` → **78 passed** (59 baseline + 19 new), ~1s, no real sleeps.
