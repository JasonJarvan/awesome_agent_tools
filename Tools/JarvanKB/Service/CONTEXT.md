# Service

Long-running processes with their own deploy units: cookie sync, Collection watchers, and
ingesters. A Service polls or listens; it delegates fetching to Engines.

## Language

**Watcher**:
A polling Service that watches a user's Collections on one platform and feeds newly collected
items to that platform's Engine.
_Avoid_: poller, monitor, listener

**Collection**:
A user-curated favorites list on a platform — the unit a Watcher watches. Canonical
cross-platform term (user decision 2026-06-11): Zhihu "collection / 收藏夹", Bilibili
"fav folder / media_id" are platform aliases.
_Avoid_: favorites folder, fav folder, 收藏夹 (in English prose)

**fav-time**:
The moment an item was added to a Collection (Bilibili item `fav_time`; Zhihu item top-level
`created`). Distinct from the content's publish time.
_Avoid_: pubtime, ctime, created_time (those are publish-side fields)

**Watermark**:
A Collection's incremental-progress marker: the fav-time boundary below which items count as
already processed. Platform semantics differ — Bilibili listings are fav-time-ordered, so the
Watermark may early-stop pagination; Zhihu listings are unordered, so the Watermark only
filters and must never early-stop.
_Avoid_: checkpoint, cursor, high-water mark (use the one term)

**seen-id**:
The set of item ids already processed; the dedupe mechanism that complements (not replaces)
the Watermark.
_Avoid_: dedupe cache

**CookieManager**:
The CookieCloud-protocol-compatible sync Service — the single cookie source for every crawl
consumer. The unmodified official CookieCloud browser extension is its uploader.
_Avoid_: cookie store, cookie service (use the name)

**PULL contract**:
How consumers obtain cookies: fetch the encrypted blob from CookieManager and decrypt
client-side. The push delivery path is permanently cancelled.
_Avoid_: push, webhook delivery

**domain-key**:
The lookup key for cookies of a site: the dotted registrable domain (`.zhihu.com`,
`.bilibili.com`). Undotted keys may exist but be empty.
_Avoid_: hostname, bare domain

**Hook engine**:
CookieManager's retained-but-latent event machinery; adding a future non-decrypting consumer
is a config entry, not new code.
_Avoid_: plugin system

**Ingester**:
A Service that digests crawled content into the user's note system (v1 target: Thino-style
notes; `thino-ingester` is the first instance).
_Avoid_: importer, syncer
