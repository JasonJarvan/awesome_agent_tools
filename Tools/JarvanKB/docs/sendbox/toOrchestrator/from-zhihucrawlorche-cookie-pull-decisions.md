> from: ZhihuCrawl SubOrche (sub-orchestrator under root orche g3)
> recipient: root orche (Orchestrator)
> purpose: relay a USER-ratified, cross-vertical cookie-integration decision for root to (a) record in
>          version-plan.md and (b) propagate to the Bilibili vertical (SP-4b/5b)
> lifecycle: burn after root records it in `version-plan.md` and reflects it in SP-4b/5b scope

# Decision relay — cookie integration = active PULL; SP-1 push path permanently cancelled

## TL;DR
The user ratified (chat, 2026-06-02): **all crawl consumers fetch SP-1 cookies by active PULL.** The
SP-1 **push** delivery path (a `write_file`/`cookie-update` hook landing plaintext cookies for consumers to
read — the "SP-1b" wiring) is **permanently cancelled**. This spans verticals (SP-3/SP-5a now, SP-4b/5b
later), so it needs a `version-plan.md` record + propagation to the Bilibili vertical — **root's lane**
(SubOrche cannot edit `docs/RepoMem/persist/`).

## The decision (with rationale)
- **PULL** chosen over push. Push's only net win (pure-consumer, no client-side decrypt) is outweighed by:
  (1) push leaves **plaintext cookies persistently on disk**; pull decrypts only transiently in-memory;
  (2) push adds a standing cross-module **config** dependency consumers must maintain; pull keeps each
  consumer self-contained (matches the parallel-independence stance for the implers);
  (3) freshness: pull-on-demand is always ≥ a pushed file for Zhihu's long-lived cookies.
- Pull mechanism is left to each impler (SP-1 `interface.md §7` active path): HTTP `GET /get/:uuid` + client
  decrypt (`§3`), or CLI `cookie-manager show domain=<site>`. Shared decrypt, if extracted, belongs in
  `Engine/common` cookie-reader (SP-0 §3) — deferred for v1 parallel independence.
- **"Cancelled" = the dedicated push *delivery path* for crawl consumers is not built.** SP-1's general hook
  engine (`cookie-update`/`cron` + `exec`/`write_file`) **stays as-is, latent** — if a future non-decrypting
  consumer ever needs push, it is a config entry, not new code. Nothing is removed from SP-1.

## Action items for root
1. **Record** in `docs/RepoMem/persist/version-plan.md`: "cookie delivery for all crawl consumers = active
   pull; SP-1 push delivery path permanently cancelled (SP-1 hook engine retained, latent). User-ratified
   2026-06-02." (Optionally cross-note in SP-0 design §7 / a decisions entry.)
2. **Propagate to the Bilibili vertical**: SP-4b (Bilibili Skill) and SP-5b (Bilibili Watcher) pull SESSDATA
   from SP-1 (domain `.bilibili.com`) by the same pull contract — fold into their future handoffs/scope.
3. No user action needed (the user already decided in chat) — this is an A2A relay to a detached session.

## Already done by SubOrche (Zhihu vertical)
- Encoded "active pull, push cancelled" into `toSP3Impler/handoff.md` + `toSP5aImpler/handoff.md`.
