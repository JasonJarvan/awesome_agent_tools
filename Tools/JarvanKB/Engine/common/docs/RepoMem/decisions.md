# Module decision log

> Append-only, time-descending (newest at top).
> Each entry: date, slug, decision, rationale, what-changes-when-this-is-revisited.
> When a decision is promoted to global, leave a `[Promoted to global ↗]` marker pointing to `<root>/docs/RepoMem/persist/memory/`.

## 2026-06-05 — sp3-zhihu-skill — LLMClient real impl + packaged as jarvankb-common
Engine/common is now pip-package `jarvankb-common` (import `jarvankb_common`, src-layout), so LLMClient is
genuinely importable like every other module. Real litellm body landed (SP-3 is first consumer); active-order
profile fallthrough; `to_opencode()` still NotImplementedError (v1.x). Import is now
`from jarvankb_common import LLMClient` (was the non-working `from Engine.common.src.llm_client import ...`).
What changes if revisited: provider routing/config schema lives in `config/llm.yaml` + `jarvankb_common.config`.
[Promotion candidate ↗ global persist at SP-3 Step-8 merge — cross-SP reuse by SP-6/SP-4b.]
