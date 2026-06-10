---
slug: sp4b-bilibili-skill
status: active
domains:
  - crawl-pipeline
  - credentials
updated_at: 2026-06-07
---

# SP-4b Bilibili Skill — working memory

> Task-scoped scratchpad (no-duplication: design lives in
> `docs/superpowers/specs/2026-06-07-SP-4b-bilibili-skill-design.md`; plan in `docs/superpowers/plans/`).
> Holds only in-flight notes, gotchas discovered during implementation, and Step-8 merge candidates.

## Pointers (don't duplicate — link)
- Design: `../../superpowers/specs/2026-06-07-SP-4b-bilibili-skill-design.md`
- Structural mirror: `Skill/crawl/zhihu-crawl/` (SP-3, ⚫ done) — packaging, classify, cookie, saver.
- Frozen upstreams: `Engine/bilibili/docs/interface.md` (§3 API, §4 render, §5 cred) +
  `Engine/common/docs/interface.md` (LLMClient) + `docs/RepoMem/persist/architecture/credentials.md`.

## Step-8 merge candidates (cross-SP-reusable lessons — evaluate at closure, do NOT promote code)
- **cookie domain mapping**: Bilibili box key = `bilibili.com` (NO dot); holds `SESSDATA` + `bili_jct`
  (no `buvid3`). Already in global `credentials.md §Bilibili` → likely no new promotion, just confirm.
- **SESSDATA→BilibiliCredential mapping + graceful degrade**: cookie failure is NON-FATAL for an engine that
  is cookie-less-capable (degrade to `credential=None`, warn, continue). This *contrasts* SP-3's fail-loud —
  candidate lesson "credential-fatality depends on engine's anonymous capability, decided per-vertical."
- **classify-input shape for non-article media**: title + AI-summary lead (fallback transcript lead) vs
  SP-3's article body lead. Candidate "media-vs-article classify-input" note IF it generalizes to SP-7.

## In-flight gotchas (append as discovered)
- Engine `interface.md §5` says `.bilibili.com` — STALE; use `bilibili.com` (no dot). credentials.md wins.
- `transcribe(ref, credential=cred)` convenience builds default engine via `BilibiliEngine.from_config()`
  → depends on repo-root `config/bilibili-engine.yaml` being set up (provider mimo-v2.5-pro). BN must be up
  at live smoke (`jarvankb-bilinote` @ 127.0.0.1:3015).
- Shared index w/ SP-5b: commit with `-- pathspec` (memory: shared-index-commit-pathspec).
