# Context Map — JarvanKB

JarvanKB is a personal knowledge-base tooling family: crawl content from sources (Zhihu,
Bilibili), digest it into the user's notes, and keep the supporting long-running services
healthy. Three bounded contexts, one per top-level module group.

## Contexts

- [Engine](./Engine/CONTEXT.md) — pure per-platform fetch/transform libraries
- [Service](./Service/CONTEXT.md) — long-running processes: cookie sync, Collection watchers, ingesters
- [Skill](./Skill/CONTEXT.md) — agent-facing packaged capabilities that wrap engines

## Relationships

- **Skill → Engine**: each crawl Skill wraps its platform Engine (`zhihu-crawl` → `Engine/zhihu`,
  `bilibili-crawl` → `Engine/bilibili`). Skills add agent packaging and config, never new fetch logic.
- **Service (watchers) → Engine**: a Watcher discovers new Collection items and feeds each item's
  reference to the platform Engine for fetching.
- **Service (cookie-manager) → all crawl consumers**: Engines/Watchers/Skills PULL cookies from
  cookie-manager (fetch + client-side decrypt); there is no push delivery.
- **Engine/common → Python consumers**: `LLMClient` is the single shared LLM access library
  (reuse — do not reimplement per module).

## Scope notes

- Glossaries hold **product-domain terms only**. Process/governance vocabulary (SP, orche/impler,
  lane, sendbox, RepoMem, …) is owned by `CLAUDE.md` + `docs/HarnessStack/longterm.md` and is
  deliberately absent here (user decision 2026-06-11, task `grill-with-docs-restore`).
- CONTEXT.md files are glossaries and nothing else — they **complement** RepoMem
  (CONTEXT = what a term means; RepoMem = why decisions were made, gotchas, architecture).
- Maintained by the `grill-with-docs` project skill (community original); decision-worthy outcomes
  from grilling go to RepoMem, not `docs/adr/`.
