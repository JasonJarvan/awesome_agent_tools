# version-plan.md

> Long-term version / roadmap notes for AgentCrawl.
> Explicitly named in `docs/HarnessStack/longterm.md` §Related Documents.

## Current version

- Phase 1 (current): documentation skeleton only. No code.
  - Deliverables: `README.md`, `CLAUDE.md`, `docs/HarnessStack/`, `docs/RepoMem/persist/{architecture,decisions,runbook}.md`, empty `docs/toAgent/`.
  - Effective from: 2026-05-26.

## Planned phases (non-binding sketch — confirm at planning time)

| Phase | Scope | Gate to enter |
|---|---|---|
| Phase 2 — minimum viable pipeline | `scripts/bilibili_audio.py` + `oss_upload.py` + `tingwu_transcribe.py` + `save_local.py`; manual cookie loading | Aliyun credentials acquired; `docs/sendbox/toAgent/handoff.md` filled by maintainer |
| Phase 3 — Zhihu path | `scripts/zhihu_fetch.py` (Playwright CDP) + Jina fallback | Phase 2 verified end-to-end on a real BV id |
| Phase 4 — cookie management | `cookies/manager.py`, `cookies/refresh_chrome_cdp.py` | Phase 2 + 3 exposed real cookie-rotation pain |
| Phase 5 — CLI surface | `cli.py` (`python -m agentcrawl ...`) | Phase 2–4 stable as importable modules |

## Compatibility / upgrade notes

- HarnessStack recipe currently `superpowers-repomem`. Extending to `openspec-superpowers-repomem` is an **add-only** upgrade per `longterm.md` §Full Rewrite Conditions — update `Recipe Reference` in place; not a full rewrite.
- ASR service choice (currently 通义听悟新版 API) is reviewed in `decisions.md` §D3. Re-evaluate annually or when pricing/API changes.

## How this doc is updated

Append-most. Major changes (phase scope reshuffle, recipe upgrade) go through `RepoMem.merge` HITL review.
