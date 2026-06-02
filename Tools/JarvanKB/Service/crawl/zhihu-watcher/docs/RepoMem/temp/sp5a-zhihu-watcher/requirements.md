---
slug: sp5a-zhihu-watcher
status: active
domains:
  - crawl-pipeline
  - credentials
updated_at: 2026-06-02
task_type: feature
---

# SP-5a Zhihu Watcher — task-scoped requirements (working memory)

> Authoritative spec: `../../../superpowers/specs/2026-06-02-SP-5a-zhihu-watcher-design.md`.
> This file is task working-memory only — it does NOT duplicate the design. It holds the acceptance
> bar, the locked-decision checklist, and a running delta log.

## What "done" means (acceptance)

- Daemon polls each configured collection on an interval; new items (not in seen-set) are fetched via
  the frozen SP-2 engine and saved as Markdown under `<output_dir>/<collection>/`.
- A second poll fetches **nothing** (dedup invariant) — the core test.
- Cookie pulled from SP-1, decrypted transiently in memory, never written to disk.
- Unit + integration tests green; lint/typecheck clean; a manual `--once` smoke shown (live smoke may
  be gated on user docker/cookie ops).
- Module `docs/{README,interface,architecture,runbook}` frozen + `RepoMem/{architecture,decisions}` filled.

## Locked-decision checklist (design §1)

- [x] D1 cookie = HTTP GET /get/:uuid + pure-Python decrypt (no Node CLI in image)
- [x] D2 dedup = persistent seen-id set (JSON), key `type:id` — NOT a content-`created` watermark
- [x] D3 APScheduler AsyncIOScheduler (max_instances=1) + docker-compose
- [x] D4 output = reference-repo convention; images = remote URLs (not downloaded)
- [x] D5 filename = `<title>.md` (collision `_<url_id>`), subfolder per collection, `> url` line, no frontmatter

## Delta log (decisions/changes made AFTER the design was approved)

- 2026-06-02: design approved by user; spec committed `1cc8990`. No deltas yet.
