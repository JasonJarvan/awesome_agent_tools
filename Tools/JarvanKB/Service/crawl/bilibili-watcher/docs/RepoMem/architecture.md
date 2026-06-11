# Module internal architecture — bilibili-watcher

> Internal design notes (module-private). External summary lives in `docs/architecture.md`.
> Authoritative design: `docs/superpowers/specs/2026-06-07-SP-5b-bilibili-watcher-design.md`.
> This is a near-verbatim mirror of the SP-5a zhihu-watcher architecture, with two deltas:
> (Δ1) SP-4a engine instead of SP-2; (Δ2) fav_time watermark + has_more paging instead of
> seen-set-only + offset/totals paging.

## Layering & package layout (`src/` layout, mirrors SP-5a)

```
src/bilibili_watcher/
  config.py            # WatcherConfig / CookieSource / EngineConfig / RenderConfig / FolderConfig
                       # + load_config (yaml + validate)
  cookie_provider.py   # CookieProvider.get_cookies(): SP-1 GET -> in-memory decrypt -> bilibili.com dict
  favorites_client.py  # FavoritesClient.list_items(): /x/v3/fav/resource/list order=mtime paging
                       # -> [BiliFavItem]; fav_time early-stop; has_more paging; type==2 filter
  watermark_store.py   # WatermarkStore.load/save(): per-folder {watermark, seen} JSON, atomic write
                       # + next_watermark(): §5 conservative advance rule
  fetcher.py           # make_fetcher(): wraps frozen SP-4a engine -> FetchedDoc | None
                       # + build_credential(): cookies dict -> BilibiliCredential
  saver.py             # save(): bilibili-url first-line + engine markdown, sanitized filename
  watcher.py           # Watcher.run_cycle() orchestration + build_watcher() DI wiring
  __main__.py          # CLI (--once / --config) + BlockingScheduler daemon
```

## Key design choices (the non-obvious bits)

- **Dependency injection in `Watcher`.** `Watcher(config, cookie_provider, favorites_client,
  fetcher_fn, watermark_store, saver_fn=...)` takes every collaborator as a constructor arg;
  `build_watcher(config)` wires the real ones. This makes the full cycle testable with fakes and no
  network — see `tests/test_watcher_integration.py` (dedup invariant, fetch-fail-hold-watermark,
  cookie-fail-skip, corrupt-state-skip all covered unit-level).

- **Dual dedup: fav_time watermark (Δ2) + bvid seen-set.** Two cooperating layers per folder:
  - *seen-set (keyed `bvid`)*: correctness/idempotency. A video is saved **at most once**, regardless
    of equal fav_time, re-favorites, or retries. Persisted immediately after each successful save
    (≤1-item crash window, mirroring SP-5a's posture).
  - *`fav_time` high-watermark W*: early-stop optimization. Invariant: every item with `fav_time > W`
    has been saved. Each cycle pages with `order=mtime` (fav_time DESC) and stops as soon as it sees
    an item with `fav_time <= W`.

- **§5 watermark advance rule (conservative, retry-safe).**
  `next_watermark(prev, listed, failed)` where `listed` = all fav_times returned this cycle and
  `failed` = fav_times of items that failed to transcribe or save:
  - No failures: `W ← max(W, max(listed))` — advance to the newest.
  - Any failure: `W ← min(failed) − 1` — keep every failed item (and only those) re-listable next
    cycle. Successes are skipped via the seen-set (not double-fetched).
  - No new items: `W` unchanged.
  1-second granularity (`fav_time` is unix seconds) is sufficient.

- **Paging stops on `has_more == False`, never on `media_count` (B站 gotcha).** Stage-0 empirical
  finding: a folder reported `media_count=4` but returned 3 items in `medias[]` (one deleted/invalid).
  `media_count` counts items not returned — **never use it as a paging termination condition**.
  See `docs/RepoMem/temp/sp5b-bilibili-watcher/favorites-api-fields.md`.

- **Early-stop evaluated before type-filter.** A non-video item (type!=2) at the fav_time boundary
  still triggers the watermark stop, because `order=mtime` sorts ALL item types together. Checking
  `fav_time <= watermark` happens before the `type==2` filter in `favorites_client.list_items()`.

- **Cookie domain = `bilibili.com` (NO leading dot).** `credentials.md §Bilibili` is authoritative.
  `engine/docs/interface.md §5` lists `.bilibili.com` (stale) — the watcher follows `credentials.md`,
  not the stale engine doc. `extract_bilibili_cookies()` matches `str(domain) == "bilibili.com"` exactly.

- **Cookie decryption mirrors CookieCloud (pure Python, `cryptography`).** Identical to SP-5a:
  `the_key = md5(uuid+"-"+password).hex[:16]`. `legacy` = OpenSSL `Salted__` + `EVP_BytesToKey(MD5)`
  + AES-256-CBC + PKCS7; `aes-128-cbc-fixed` = 16-byte key + zero IV + AES-128-CBC + PKCS7.
  `crypto_type` comes from the SP-1 response, not config. Cookies are never written to disk.

- **Cookie → credential path.** `cookie_provider.get_cookies()` returns the `bilibili.com` cookie dict.
  `favorites_client` uses it directly as `cookies=` on the httpx request (SESSDATA authenticates).
  `fetcher.build_credential(cookies)` builds `BilibiliCredential(sessdata=cookies.get("SESSDATA"),
  bili_jct=cookies.get("bili_jct"))` — `buvid3=None` is acceptable (engine degrades gracefully).

- **Engine wiring (Δ1).** `make_fetcher(engine, render)` binds a `BilibiliEngine` instance +
  `RenderOptions` into a `(bvid, credential) -> FetchedDoc | None` closure. On any `BilibiliEngineError`
  (incl. `BiliNoteUnavailable`, `TranscriptionFailed`, timeout) the fetcher logs + returns `None`
  so the daemon degrades gracefully: item NOT marked seen + fav_time recorded in `failed` → retried.

- **Synchronous, `BlockingScheduler`.** All collaborators are sync (httpx sync + sync SP-4a engine),
  so a blocking scheduler with a sync job is the correct fit. `max_instances=1` + `coalesce=True`.
  The daemon also runs one cycle immediately at startup. Do NOT pass `next_run_time=None` to `add_job`
  — that pauses the job (APScheduler 3.x verified gotcha, see SP-5a decisions.md).

## Daemon-never-crashes guards (every external failure caught)

1. `cookie_provider.get_cookies()` in `run_cycle` → except → log + skip cycle.
2. No SESSDATA in cookies → log + skip cycle.
3. `watermark_store.load()` in `_poll_folder` → except → log + skip that folder (corrupt state file).
4. `favorites_client.list_items()` in `_poll_folder` → except → log + skip that folder.
5. per-item `fetcher.fetch()` + `saver.save()` → broad except → log + append fav_time to `failed` +
   continue; item NOT marked seen, watermark held below the failure.

## Tests

`tests/` has one file per module (unit) + `test_watcher_integration.py` (full cycle, second-cycle-noop
dedup invariant, fetch-fail-hold-watermark-§5, cookie-fail-skip, no-SESSDATA-skip,
listing-error-skip, unexpected-exception-no-crash, corrupt-state-skip, CLI `--once`, scheduler
wiring). 44 tests, all green. No network in any test (httpx MockTransport / injected fakes).
