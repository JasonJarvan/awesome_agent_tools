---
slug: sp3-zhihu-skill
status: active
domains:
  - crawl-pipeline
  - credentials
updated_at: 2026-06-05
task_type: requirement
---

# SP-3 — task decision log (append-only, newest at top)

> Task-scoped. At Step-8 HITL merge, promote the cross-SP-reusable ones to module
> `decisions.md` / global `persist/` and leave a `[Promoted ↗]` marker.

## D-SP3-3 (2026-06-05) — Promotion candidates flagged for Step-8 merge
- **Global (cross-SP-reusable):** (a) the SP-1 cookie active-pull + client-side decrypt pattern (legacy
  CryptoJS `Salted__`/EVP + `aes-128-cbc-fixed`) — SP-5a/SP-4b reuse; (b) `LLMClient` real litellm body
  landed in `Engine/common` (made importable via new pyproject) — SP-6 reuse; (c) agentskills.io
  single-`SKILL.md`-across-four-runtimes packaging — SP-4b reuse (also in cross-session memory).
- **Module-local (stays here):** vague_path classification mechanism, path-resolution rules, slug rules.
- Rationale (CLAUDE.md §3 step 8): promote cross-SP root-causes/patterns, NOT mechanism that lives in code;
  a downstream SP in another module's cwd does not read this module's decisions.

## D-SP3-2 (2026-06-05) — Skip the plan-ready letter; go directly to execution
- **User decision** (chat, 2026-06-05): proceed straight from spec approval into writing-plans → execute
  without writing `from-sp3impler-plan-ready.md` to `toZhihuCrawlOrche/`.
- **Overrides** handoff §3.C (Stage-2 convergence letter). The done-letter / burn lifecycle (§8) is
  unaffected unless the user says otherwise.

## D-SP3-1 (2026-06-02) — Brainstorming-confirmed design decisions
- See design §2 (packaging = pkg+CLI+single SKILL.md; taxonomy = infer-existing+propose-new; save_path
  param + rule-based vagueness; cookie = HTTP GET+decrypt; llm config = `<root>/config/llm.yaml`;
  Engine/common gets a pyproject so LLMClient is importable). Not restated here (no-duplication).
