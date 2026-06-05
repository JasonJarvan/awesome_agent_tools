---
slug: sp3-zhihu-skill
status: active
domains:
  - crawl-pipeline
  - credentials
updated_at: 2026-06-05
task_type: requirement
---

# SP-3 Zhihu Skill — task requirements (working memory)

> Thin pointer doc — the authoritative spec is the design, not restated here (no-duplication invariant).

**Goal:** Zhihu URL → frozen SP-2 engine → save Markdown to a user-chosen path; vague path → LLM
classify into a subfolder under the configured output root. First real `LLMClient` consumer.

**Authoritative scope / design:** `docs/superpowers/specs/2026-06-02-SP-3-zhihu-skill-design.md`
**Plan:** `docs/superpowers/plans/2026-06-02-SP-3-zhihu-skill-plan.md`
**Handoff (parent contract):** `<root>/docs/sendbox/toSP3Impler/handoff.md`

**Success criteria (verification gate, design §10/§11):**
- Unit suite green with engine / `LLMClient` / cookie-service all mocked (no live creds).
- Lint/typecheck clean.
- Offline smoke: explicit-path `url → engine → save`; mocked-LLM vague path.
- Live vague_path classification is the ONLY gated path → Dashboard Type-F + blocker note (creds = user).

**Out of scope:** vault/Obsidian/GBrain/Thino, favorites polling (SP-5a), v1.1 comment-tree, editing the
SP-2 engine, SP-1 push wiring, baking LLM creds, push/merge-to-main/rebase.
