# Module decision log

> Append-only, time-descending (newest at top).
> Each entry: date, slug, decision, rationale, what-changes-when-this-is-revisited.
> When a decision is promoted to global, leave a `[Promoted to global ↗]` marker pointing to
> `<root>/docs/RepoMem/persist/memory/` (or `architecture/`).

## 2026-06-21 — bilibili-engine-ratelimit-hardening (v1.x, verified)

### D-4a.5 — engine has built-in proactive rate-limit + reactive throttle backoff on its bilibili-facing calls (mirror SP-2 D8)
The 3 bilibili.com-facing calls (`metadata._get_info_raw` get_info, `subtitle._get_tracks_raw` get_subtitle,
`subtitle._get_body_raw` subtitle-CDN GET) route through `ratelimit.paced()`: a process-shared `_RateLimiter`
(min-interval + jitter, so bulk consumers self-pace while a single transcribe's first call is ~unaffected) +
retry on throttle with exponential backoff honoring `Retry-After`. Throttle = HTTP 429 + bilibili business
codes -509/-799; **412 is NOT throttle** (anonymous-playurl auth / BN-internal, BN-412) and **-101** (no login)
— both pass through unchanged → existing ASR-fallback / `CredentialError` paths intact. Unlike SP-2's
`_request()->Response`, the wrapper takes a callable because bilibili calls RAISE on throttle
(`ResponseCodeException.code` / `NetworkException.status` / httpx `HTTPStatusError`); classifier duck-types
`.status`/`.code` (no hard `bilibili_api` import). **BN-local calls (`bilinote_client.py`, 127.0.0.1) are NOT
paced** — not bilibili calls; BN's internal yt-dlp bilibili downloads are below the engine (see §B站链路 BN-412).
Conservative defaults mirror deployed zhihu (min_interval=0.3, jitter=0.2, max_retries=3, backoff_base=0.5);
tunable via module-level `bilibili.configure(...)`; non-breaking (v1 frozen contract byte-identical). Mechanism
in `src/bilibili/ratelimit.py`; contract note `docs/interface.md §8`. **Revisit when:** a consumer needs a
per-call rate override, or bilibili changes which codes signal throttling, **or a concurrent bulk consumer
saturates BN's download cap-of-3** (BN has no rate-limit + shares the engine egress IP) → then add a BN-client
concurrency/min-interval cap (deferred 2026-06-21; see §B站链路 + `temp/bilibili-engine-ratelimit-hardening/bn-concurrency-investigation.md`).

> D-4a.5 mechanism stays in code — NOT promoted. The cross-SP root-cause rides along under the §B站链路
> promotion — promoted 2026-06-21 (HITL: root orche greenlight + user-delegated closure).

## 2026-06-02 — sp4a-bilibili-engine (initial implementation, verified)

### D-4a.1 — BiliNote is a hard v1 dependency; both cascade paths produce a summary
Engine routes BOTH the subtitle path (via `prefetched_transcript` → BN runs LLM summary only) and the
ASR path (BN downloads audio + bcut) through BN. **Rationale:** the user's progressive-disclosure render
(`split_transcript` → summary-as-index + separate transcript file) needs a *consistent* summary for every
video; a subtitle video that skipped BN would have no index. **Revisit when:** a BN-less / `summarize=False`
offline mode is wanted (deferred to v2+) — then subtitle-only videos could skip BN entirely.

### D-4a.2 — Engine-driven subtitle-first cascade (not BN-driven)
The engine fetches metadata + subtitle itself (`bilibili-api-python`) and decides the path, rather than
letting BN's internal cascade run blind. **Rationale:** the path taken (`transcript.source`) is observable
+ unit-testable, and the mandatory smoke must prove which path ran. **Revisit when:** never, unless BN
exposes a raw-ASR endpoint that removes the need for engine-side subtitle handling.

### D-4a.3 — Manual LLM-provider config; engine is a read-side BN consumer
Engine reads `provider_id`/`model_name` from `config/bilibili-engine.yaml`; it never writes BN's provider
DB. **Rationale:** decoupling — provider setup is user/ops territory; auto-register would couple the engine
to BN's provider API + make it hold the LLM key. **Revisit when:** a one-command bootstrap is wanted.

### D-4a.4 — Render: deterministic prose-merge, no LLM; switches with module-local config
`include_timestamps=False` (default) merges segments into readable paragraphs by a deterministic heuristic
(gap/char-budget breaks; CJK joined without spaces) — NO LLM (handoff invariant). Switches:
`include_transcript=True` / `include_timestamps=False` / `split_transcript=False`. Config is **module-local**
(`Engine/bilibili/config/`, mirroring SP-1's actual layout), not repo-root, for fractal-split. **Revisit when:**
v2+ "smart switches" (auto-split on length, auto-timestamps by content type).

### Smoke-driven fixes (2026-06-02, all verified against live BN + real bilibili)
- `bilibili-api-python.get_subtitle` **raises** `CredentialNoSessdataException` without SESSDATA (not empty);
  `fetch_subtitle` now returns None on missing-cred / ANY subtitle-fetch error → cascade falls to ASR (engine
  runs cookie-less on public videos). [Promoted to global ↗ `architecture/credentials.md`]
- BN `latest` image nginx broken → deploy maps host port to backend `:8483`; `TRANSCRIBER_TYPE` set via
  `POST /api/transcriber_config` (env doesn't pass through supervisord).
  [Promoted to global ↗ `architecture/crawl-pipeline.md` §B站链路]
- Cookies in cookie-manager under `bilibili.com` (no leading dot), not `.bilibili.com`.
  [Promoted to global ↗ `architecture/credentials.md`]
- ASR branch raises `TranscriptionFailed` if BN returns SUCCESS with no transcript (defensive).

**Smoke evidence:** `docs/RepoMem/temp/sp4a-bilibili-engine/smoke.md` (ASR `BV1GJ411x7h7` + subtitle
`BV1BXQABNE4y`, both paths + prose-merge verified). 59 unit tests green.
