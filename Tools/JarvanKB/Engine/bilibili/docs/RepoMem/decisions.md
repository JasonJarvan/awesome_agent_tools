# Module decision log

> Append-only, time-descending (newest at top).
> Each entry: date, slug, decision, rationale, what-changes-when-this-is-revisited.
> When a decision is promoted to global, leave a `[Promoted to global ↗]` marker pointing to
> `<root>/docs/RepoMem/persist/memory/` (or `architecture/`).

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
