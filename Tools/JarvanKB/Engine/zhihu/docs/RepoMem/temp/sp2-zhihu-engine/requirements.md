---
slug: sp2-zhihu-engine
status: in-progress
task_type: feature
domains: [crawl, zhihu]
updated_at: 2026-06-01
---

# SP-2 Zhihu Engine — task working state

> Task-scoped scratch. The authoritative design is
> `../../superpowers/specs/2026-05-31-SP-2-zhihu-engine-design.md` — **do not duplicate it here**.
> This file tracks only working state, open empirical questions, and the smoke checklist.

## Pipeline position
- Step 1 RepoMem.read ✓ · Step 2 brainstorming ✓ (design landed `d9d28f8`) · Step 3 capture (this) ·
  Step 4 writing-plans (next).

## Settled decisions (full rationale in design.md / will promote to decisions.md at Step 8)
- zse-96: **pure cookie + HTTP, no browser, no signer** (aligns user's Zhihu-Collections-MCP).
- Body: initialData JSON primary → CSS-selector → unsigned /api/v4 fallback.
- Image: engine emits remote URLs only (localization is SP-6).
- Question URL: return question + embedded answers in **full fidelity** (design tenet — engine
  maximizes extraction, consumers filter; request-boundary not value-judgment).
- Reimplement, do NOT lift reference code (reference unlicensed; JarvanKB → MIT).

## OPEN — settle empirically at smoke (verification gate)
1. **Does `/api/v4/comment_v5/...` hard-enforce x-zse-96?**
   - If unsigned + cookies works → ship comments signer-free. ✅ preferred.
   - If real 403 → branch: (a) port RSSHub MIT `x-zse-96` scoped to comments, or (b) document
     bodies-only limitation. Decide WITH user at smoke.
2. Confirm question-page initialData actually carries embedded-answer FULL content (vs preview only)
   on a live page — adjust `EmbeddedAnswer.content_markdown` population accordingly.
3. Confirm unsigned `/api/v4/answers/{id}?include=content` still works as 403 fallback in 2026.

## Smoke checklist (live cookies required)
- [ ] one public answer URL → markdown + metadata
- [ ] one article (zhuanlan) URL → markdown + metadata
- [ ] one question URL → title + detail + embedded answers (full content)
- [ ] comments path on the answer (settles OPEN-1)

## Cookies for smoke
Pull from SP-1 cookie-manager `show domain=.zhihu.com` (or `GET /get/:uuid` + decrypt). Meaningful:
`z_c0`, `d_c0`, `__zse_ck`. Engine takes them as injected input; sourcing is the consumer's job.
