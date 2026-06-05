# Module internal architecture — Engine/common (jarvankb-common)

> Internal design — module-private decisions, layering, key code paths.
> Distinct from `docs/architecture.md` which is the external summary.

## What this module is

`Engine/common` is the **cross-engine shared layer** (SP-0 §3), not an LLM-only module. Designed to hold:
LLMClient (litellm) + BaseSkill + cookie reader. Packaged as dist `jarvankb-common`, import `jarvankb_common`
(src-layout, editable-installed like every other module).

## Organize-by-concern convention (user guidance, 2026-06-05)

Keep **different functional code separated**; do not mix concerns in one file. Each concern is one module
now; **promote a concern to its own subpackage `jarvankb_common/<concern>/` once its single file grows
beyond one file / gets unwieldy.** Single-file-per-concern is fine while small.

| Concern | Status | Location |
|---|---|---|
| LLM dispatch | landed (SP-3) | `llm_client.py` (`LLMClient`) + `llm_config.py` (`load_llm_config`, `resolve_candidates`, `LLMConfig`) |
| BaseSkill | planned | `base_skill.py` (future; e.g. SP-6) |
| cookie reader | planned | `cookie_reader.py` (future) — NOTE: SP-3 keeps its own module-local cookie pull (handoff §1), this shared one is a later consolidation |

Naming: concern-prefixed module names (e.g. `llm_config.py`, not a generic `config.py`) so future concerns
don't collide and a future generic config stays free.

## LLM concern — key paths

- `LLMClient(profile, config_path=None)` → `resolve_candidates(profile)` builds the available-profile
  fallthrough list ([requested, *active], deduped, only profiles whose `api_key_env` is empty or set).
- `complete()` / `stream()` iterate candidates, calling `litellm.completion(...)`; fall through to the next
  profile on provider error; raise when exhausted. Signatures frozen (v1 contract).
- Config source: repo-root `config/llm.yaml` (or `$JARVANKB_LLM_CONFIG`). Schema: `config/llm.yaml.example`.

## v1 → v2 (see Skill/crawl/zhihu-crawl temp decisions D-SP3-4)

v1 = in-process **library**. v2 = promote to a standalone `Service/.../llm-service` (HTTP, OpenAI-compatible,
runtime-central metering/limit/cache). Non-breaking: the frozen `LLMClient` interface stays; only its
internals swap litellm-direct → service-call. Decide the v2 service with root/SubOrche (platform-level).
