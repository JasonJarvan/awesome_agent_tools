# Module internal architecture — zhihu-watcher

> Internal design notes (module-private). External summary lives in `docs/architecture.md`.
> Authoritative design: `docs/superpowers/specs/2026-06-02-SP-5a-zhihu-watcher-design.md`.

## Layering & package layout (`src/` layout, mirrors `Engine/zhihu`)

```
src/zhihu_watcher/
  config.py            # WatcherConfig / CookieSource / CollectionConfig + load_config (yaml + validate)
  cookie_provider.py   # CookieProvider.get_cookies(): SP-1 GET -> in-memory decrypt -> .zhihu.com dict
  favorites_client.py  # FavoritesClient.list_items(): collections API offset paging -> [CollectionItem]
  watermark_store.py   # WatermarkStore.load/save(): per-collection seen-id JSON, atomic write
  fetcher.py           # fetch(): wraps frozen SP-2 zhihu.fetch -> FetchedDoc | None
  saver.py             # save(): reference-repo markdown format
  watcher.py           # Watcher.run_cycle() orchestration + build_watcher() DI wiring
  __main__.py          # CLI (--once / --config) + BlockingScheduler daemon
```

## Key design choices (the non-obvious bits)

- **Dependency injection in `Watcher`.** `Watcher(config, cookie_provider, favorites_client, fetcher_fn,
  watermark_store, saver_fn=...)` takes every collaborator as a constructor arg; `build_watcher(config)`
  wires the real ones. This is what makes the whole cycle (incl. the second-cycle-no-op dedup invariant)
  testable with fakes and no network — see `tests/test_watcher_integration.py`.

- **Dedup = persistent seen-id set, not a timestamp watermark.** Key = `"{content_type}:{content_id}"`.
  The collections API does not reliably expose a *favorited* time, and `content.created` is the content's
  creation time (≠ favorite time), so a created-watermark would miss newly-favorited-but-old items. The
  seen-set is reloaded from disk at the top of each `_poll_collection` (no in-memory caching across cycles)
  and persisted via `store.save` immediately after each successful item (1-item crash window).

- **Cookie decryption mirrors CookieCloud (pure Python, `cryptography`).**
  `the_key = md5(uuid+"-"+password).hex[:16]`. `legacy` = OpenSSL `Salted__` envelope + `EVP_BytesToKey(MD5)`
  + AES-256-CBC + PKCS7; `aes-128-cbc-fixed` = 16-byte key + zero IV + AES-128-CBC + PKCS7. `crypto_type`
  comes from the SP-1 response, not config. Plaintext cookies are never written to disk — only returned as a
  transient dict and logged by count only.

- **Paging follows `paging` rather than self-constructing offsets.** `list_items` loops
  `GET .../collections/{id}/items?offset=&limit=20`, stops on `paging.is_end is True`, else advances offset
  and stops once `len(items) >= paging.totals`, with an empty-data safety break. NOTE: the stop guard is
  `len(items) >= totals` (NOT `offset >= totals`) — the offset form breaks early when the API splits fewer
  items than `totals` across pages with a late `is_end`. No `x-zse-96` signing (verified against the
  reference repo; consistent with `crawl-pipeline.md §知乎链路`). `trust_env=False` (direct connect).

- **Output format = reference repo, NOT SP-2 `.to_markdown()`.** We call `zhihu.fetch()` for the content but
  serialize `FetchResult.content_markdown` ourselves as `"> <url>\n" + body` (no YAML frontmatter), to match
  `github.com/JasonJarvan/Zhihu-Collections-MCP`. Images keep remote URLs (no download, no Obsidian wikilinks).

- **Synchronous, `BlockingScheduler`.** All collaborators are sync (httpx sync client + sync SP-2 engine), so
  a blocking scheduler with a sync job is the correct fit. The job uses `max_instances=1` + `coalesce=True`;
  the daemon also runs one cycle immediately at startup, then on the interval. (Do NOT pass
  `next_run_time=None` to `add_job` — that pauses the job; omit it so APScheduler schedules the first fire at
  now+interval.)

## Daemon-never-crashes guards (every external failure caught)

1. `cookie_provider.get_cookies()` in `run_cycle` → except → log + skip cycle.
2. `favorites_client.list_items()` in `_poll_collection` → except → log + skip that collection.
3. `watermark_store.load()` in `_poll_collection` → except → log + skip that collection (corrupt state file).
4. per-item `fetcher.fetch()` + `saver.save()` → broad except → log + continue, item NOT marked seen.

## Tests

`tests/` has one file per module (unit) + `test_watcher_integration.py` (full cycle, second-cycle-no-op
dedup invariant, fetch-fail-no-mark, cookie-fail-skip, unexpected-exception-no-crash, corrupt-state-skip,
CLI `--once`, scheduler wiring/unpaused-job). 31 tests, all green. Cookie decryption tested against real
round-trip vectors for both crypto modes. No network in any test (httpx MockTransport / monkeypatched
`zhihu.fetch`).
