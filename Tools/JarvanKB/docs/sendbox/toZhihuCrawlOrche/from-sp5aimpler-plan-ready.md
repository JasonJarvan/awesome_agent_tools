> from: SP5aImpler session (Claude Opus 4.8 1M, 2026-06-02)
> recipient: ZhihuCrawl SubOrche (my parent; Mode A — you stayed alive, I converge back to you)
> mode: plan-ready
> purpose: notify Stage-2 (design + plan) done for SP-5a; record the design deltas vs your handoff; signal I am proceeding to execution under the user's live direction
> lifecycle: persist until I send `from-sp5aimpler-sp5a-done.md`, then archive with the handoff chain

# plan-ready — SP-5a Zhihu Watcher

Task slug `sp5a-zhihu-watcher`. Pipeline steps 1–4 (RepoMem.read → brainstorm → capture → writing-plans) are done.

## Artifacts

- design: `Service/crawl/zhihu-watcher/docs/superpowers/specs/2026-06-02-SP-5a-zhihu-watcher-design.md` (user-approved)
- plan:   `Service/crawl/zhihu-watcher/docs/superpowers/plans/2026-06-02-SP-5a-zhihu-watcher-plan.md` (11 tasks, TDD, complete code)
- temp:   `Service/crawl/zhihu-watcher/docs/RepoMem/temp/sp5a-zhihu-watcher/{requirements,architecture}.md`
- commits on `feat/agentcrawl-bootstrap`: `1cc8990` (design), `6a3934f` (plan + design refinements + temp)

## Design decisions (the YOU-left-to-me set, locked with the user 2026-06-02)

- D1 cookie pull = **HTTP `GET /get/:uuid` + decrypt in pure Python** (`cryptography`; legacy OpenSSL `Salted__`/EVP_BytesToKey + aes-128-cbc-fixed). No Node CLI in the image. Transient, never persisted.
- D2 dedup = **persistent seen-id set** (JSON per collection), key `type:id`.
- D3 scheduler = **APScheduler `BlockingScheduler`** (interval, `max_instances=1`, coalesce) + **docker-compose**.
- D4/D5 output = **Zhihu-Collections-MCP reference-repo convention** (user designated it as authoritative): subfolder per collection, `<sanitized_title>.md` (collision `_<url_id>`), first line `> <url>`, **no frontmatter**, images = **remote URLs (not downloaded)**.

## ⚠️ Deltas vs your handoff (please note — none re-open a locked cross-SP boundary)

1. **"High-watermark on `created`" → seen-id set.** Verified against the reference repo: the collections
   API does not reliably expose a *favorited* timestamp, and `content.created` is the content's creation
   time (≠ favorite time) — a created-watermark would miss newly-favorited-but-old items. A persistent
   seen-id set achieves the same goal ("never re-fetch, only new") more robustly. User approved.
2. **Output format = reference repo, not SP-2 `.to_markdown()`.** User pointed me at
   `github.com/JasonJarvan/Zhihu-Collections-MCP` and said "output format same as it". So I fetch via the
   frozen SP-2 `fetch()` (engine path honored) but serialize `FetchResult.content_markdown` as
   `> url\n<body>` with **no frontmatter** (the reference has none), keeping remote image URLs. This means
   we deliberately do NOT call `.to_markdown()`. No Obsidian `![[]]` wikilinks / no image download → stays
   vault-agnostic per your "no Obsidian taxonomy" boundary.
3. **Scheduler class = `BlockingScheduler`** (not `AsyncIOScheduler`): the components are synchronous, so a
   blocking scheduler with a sync job is correct. Same library, same interval/no-overlap behavior.

## Good news (resolves the §知乎链路 residual risk you flagged)

The reference repo lists collection items with **plain cookies + browser headers, NO `x-zse-96`** — the
D5 "no signing" finding extends to the collections endpoint. I still treat a live-smoke 403 as a blocker
(v1 adds no signer); see below.

## What's next (I own SP-5a end-to-end; not blocking on a greenlight since the user is live)

Step 5–7: create worktree `.worktrees/sp5a-zhihu-watcher/` (branched from **local** `feat/agentcrawl-bootstrap`),
subagent-driven TDD per the plan, then verification + ask-first code-review + finishing. Step 8 RepoMem.merge
I close within my own lifecycle (promotion candidate: "collections endpoint needs no x-zse-96, 2026-06" →
`crawl-pipeline.md §知乎链路`).

## Gate you should be aware of (will surface at verification, not now)

Live smoke needs the user to: ensure a fresh `.zhihu.com` cookie is stored in SP-1, and `docker compose up`
the watcher. Per SP-1/SP-4a precedent ("起 Docker 容器 = user 操作") this is a USER op — I'll surface it as
a Dashboard gate + a note here when I reach Step 6. It does NOT block design/plan/code+unit+integration.
