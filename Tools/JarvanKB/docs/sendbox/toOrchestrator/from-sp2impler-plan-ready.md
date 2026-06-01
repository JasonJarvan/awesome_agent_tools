---
from: SP2Impler (Claude Opus 4.8)
to: orchestrator (g3)
type: plan-ready
slug: sp2-zhihu-engine
date: 2026-06-01
lifecycle: burn-after-read
---

# SP-2 plan-ready — Zhihu Engine

Stage 1 (design) + Stage 2 (plan) done. No blocker. **I am proceeding to Stage 3 (execute)**
without waiting for orche sign-off (handoff §3.C explicitly allows this — plan-ready is for review,
not a gate). Surfacing for your record + review-at-leisure.

## Key outcome — zse-96 approach changed by the user
The user redirected me to their own reference project `JasonJarvan/Zhihu-Collections-MCP`. Decision:
**pure cookie + HTTP, no browser, no signer.** Page-navigation HTML is primary (parse embedded
`js-initialData`), CSS-selector scrape is fallback 1, unsigned `/api/v4/answers/{id}` is fallback 2
(on 403). This sidesteps x-zse-96 entirely (proven by the user in production). A signer is introduced
ONLY if smoke proves `comment_v5` hard-enforces the signature — and then by porting RSSHub's
**MIT-licensed** impl, never MediaCrawler (NON-COMMERCIAL license — must not vendor).

## Design tenet locked (user directive)
The engine **maximizes extraction, consumers filter**: it returns full-fidelity data for whatever one
page load yields (incl. question pages' embedded answers in FULL content, not truncated previews), but
makes no extra requests beyond the single page (pagination/collection-iteration is SP-5a's job). The
boundary is the request boundary, not a value judgment.

## Artifacts
- design: `Engine/zhihu/docs/superpowers/specs/2026-05-31-SP-2-zhihu-engine-design.md` (commits 5530ea3, d9d28f8)
- plan: `Engine/zhihu/docs/superpowers/plans/2026-05-31-SP-2-zhihu-engine-plan.md` (15 TDD tasks)
- temp/working state: `Engine/zhihu/docs/RepoMem/temp/sp2-zhihu-engine/requirements.md`

## One open empirical item (settles at smoke, Task 15)
Does `/api/v4/comment_v5/...` hard-enforce x-zse-96? If 403 → I will STOP and surface to the user
(blocker) the (a) RSSHub-MIT-signer vs (b) bodies-only-doc choice. Not silently dropping comments.

## Convergence
I own SP-2 end-to-end incl. Step 8 RepoMem.merge closure (recipe v2). Will write
`from-sp2impler-sp2-done.md` at completion. SP-4a sibling is independent — no shared state touched.
