# [shared] LLM layer + multi-runtime Skill packaging

> Durable cross-SP knowledge promoted by `RepoMem.merge` of `sp3-zhihu-skill` (2026-06-07). Audience: A2A
> (English). SP-4b/SP-6/SP-7 work in other module cwds and do NOT read SP-3's module decisions — the
> reusable bits live here. Concise pointers only (no-duplication: module/code holds the detail).

## LLMClient — shared LLM layer, real impl landed in SP-3

- Lives in `Engine/common`; dist `jarvankb-common`; import `from jarvankb_common import LLMClient`.
- litellm backend. `complete(messages, **kw) -> str`, `stream(...) -> Iterator[str]`, `to_opencode()`
  (NotImplemented, v1.x). **Signatures are the frozen v1 contract.**
- Config: repo-root `config/llm.yaml` — `profiles{model, api_key_env, api_base?|api_base_env}` + `active:[...]`
  fallthrough. Keys in env / `.env` (gitignored), **never in the repo**. Template: `config/llm.yaml.example`.
- A profile is "available" iff `api_key_env` is empty OR its env var is set; `LLMClient(profile)` tries the
  requested profile then the `active` order, falling through on provider error.
- **Custom OpenAI-compatible providers:** `model: openai/<id>` + literal `api_base: https://…/v1` + `api_key_env`.
  Verified live with `mimo-v2.5-pro` (xiaomi token-plan endpoint).
- **Consumers (SP-4b vague_path, SP-6 note-merge, SP-7 formatting): reuse as-is, do NOT reimplement.**
  Full contract + examples: `Engine/common/docs/interface.md`.
- v1 = in-process **library**. **v2 = standalone `Service/.../llm-service`** (HTTP, OpenAI-compatible,
  runtime-central config/metering/rate-limit/cache); non-breaking (frozen interface). See `version-plan.md`.

## Multi-runtime Skill packaging (agentskills.io)

- Claude Code / OpenAI Codex CLI / OpenClaw / Hermes Agent share **one** open `SKILL.md` standard
  (agentskills.io). Write ONE compliant file; reuse across all four — **no per-runtime format fork.**
- Frontmatter: `name` / `description` (use "Use when …" for trigger matching) / `version` / `license` /
  `tags` (lowercase-hyphenated). Runtime-private fields go in `metadata.<runtime>` namespaces
  (`metadata.hermes`, `metadata.openclaw`); other runtimes ignore them.
- Deploy-path differences (`~/.claude/skills`, `~/.codex/skills`, `~/.openclaw/skills`, `~/.hermes/skills`)
  are a **sync concern, not a format concern** — a small sync script symlinks one source to many targets.
- The importable Python package + thin CLI (`--json` structured output) is the universal substrate every
  agent can call. Reference implementation: `Skill/crawl/zhihu-crawl/` (SP-3).
