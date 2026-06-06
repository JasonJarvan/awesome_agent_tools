# Module decision log

> Append-only, time-descending (newest at top).
> Each entry: date, slug, decision, rationale, what-changes-when-this-is-revisited.
> When a decision is promoted to global, leave a `[Promoted to global ↗]` marker pointing to `<root>/docs/RepoMem/persist/memory/`.

## 2026-06-07 — sp3-zhihu-skill — v1 done (live-verified), merged to feat/agentcrawl-bootstrap

SP-3 Zhihu Skill landed: `URL → SP-1 cookie pull+decrypt (in-memory) → frozen SP-2 engine fetch →
to_markdown → explicit-.md-path verbatim write OR vague-path LLM classification into an output_root
subfolder`. Surfaces: importable `zhihu_crawl.save_zhihu` + thin `zhihu-crawl` CLI (`--json`) + one
agentskills.io `SKILL.md`. 40 unit tests + offline integration smoke + **live** vague-path smoke
(`mimo-v2.5-pro` over the OpenAI protocol → classified into `机器学习`).

Durable decisions (cross-SP-reusable ones promoted — see markers; mechanism that lives in code is NOT promoted):
- **Cookie = active PULL only** (SP-1 push permanently cancelled); decrypt transiently in memory, never persist
  plaintext. HTTP `GET /get/:uuid` + client-side AES (`legacy` CryptoJS Salted__/EVP + `aes-128-cbc-fixed`).
  `[Promoted to global ↗ persist/architecture/credentials.md]`
- **LLMClient real impl landed in `Engine/common` (`jarvankb_common`)** — litellm backend, active-order
  fallthrough, importable as a package; honors literal `api_base` for custom OpenAI-compatible providers
  (e.g. `mimo`). v1 = in-process library; LLMService = v2 (new platform SP).
  `[Promoted to global ↗ persist/memory/llm-shared-layer.md + version-plan.md]`
- **Packaging** = one agentskills.io `SKILL.md` across Claude Code/Codex/OpenClaw/Hermes; importable pkg +
  thin CLI is the universal substrate. `[Promoted to global ↗ persist/memory/llm-shared-layer.md]`
- **vague_path** (module-local): classify only when `save_path` is vague (not a `.md` file); infer existing
  subfolders + propose a new one; `is_new` is filesystem-authoritative (not the model's flag); classification
  input = title + type + a markdown-cleaned plain-text lead capped at `classify_snippet_chars` (default 240)
  to save tokens. **URL→markdown is LLM-free**; the LLM is only the vague-path classifier.
- **Robustness** (module-local): `_parse` tolerates prose-wrapped LLM JSON (prefers the last object, else
  `ValueError`); `resolve_target` slugs `category` (path-traversal defense); `LLMClient.stream` does not
  replay tokens after a mid-stream error.

Module contract: `docs/interface.md` (frozen, 中文). Internal design: `docs/RepoMem/architecture.md`.
**v1.1 candidate:** have the frozen SP-2 engine expose Zhihu 话题/topics in `FetchResult.metadata` so
classification could prefer them (cheaper, more accurate — could even skip the LLM by mapping topic→folder).
