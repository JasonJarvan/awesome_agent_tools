# Module decision log

> Append-only, time-descending (newest at top).
> Each entry: date, slug, decision, rationale, what-changes-when-this-is-revisited.
> When a decision is promoted to global, leave a `[Promoted to global ↗]` marker pointing to `<root>/docs/RepoMem/persist/memory/`.

## 2026-06-07 — sp4b-bilibili-skill — Bilibili Skill v1 (mirror SP-3)
Decisions: packaging mirrors SP-3 (importable `save_bilibili` + thin CLI + one agentskills.io SKILL.md);
cookie via SP-3 pull+decrypt reuse with `domain="bilibili.com"` (no dot) → `BilibiliCredential`; vague_path
= rule-based (`.md`=explicit) + infer-existing/propose-new; classify input = title + summary lead (fallback
transcript lead, cap `classify_snippet_chars` default 240); render default = single file (summary + readable
transcript), config-overridable to split.
Divergence from SP-3 worth noting: **cookie failure is NON-FATAL here** (engine is cookie-less-capable on
public videos) — contrast SP-3's fail-loud. What changes if revisited: if the engine ever requires SESSDATA
for all videos, restore fail-loud.
[Step-8 merge promotion candidates ↗ global persist: "credential-fatality depends on the engine's anonymous
capability (decide per-vertical)"; confirm `domain=bilibili.com` already in credentials.md.]
