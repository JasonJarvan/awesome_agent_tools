---
name: skill-orchestrator
description: Discover, evaluate, and adapt reusable skills before creating new ones. Use when the user asks for a skill, a reusable agent workflow, a cross-platform skill, or help deciding whether to reuse an existing skill or create a new one for Codex, Claude Code, or OpenClaw. Prefer searching trusted skill markets and GitHub first, ask for user confirmation before adaptation or creation, and only propose creating a new skill after available sources have been exhausted or clearly fail to meet the need.
---

# Skill Orchestrator

Treat skill creation as the fallback, not the default.

Follow this workflow:

1. Analyze the user's request.
2. Choose the best source type to search first.
3. Search high-priority sources before lower-priority sources.
4. Return a small, decision-friendly candidate set.
5. Ask the user whether to adopt, continue searching, adapt, or create.
6. Only create a new skill after search exhaustion or explicit user preference.

## Load These References

- Read `references/sources.yaml` to discover source types, agent-specific markets, and source priorities.
- Read `references/decision-rules.md` before searching or recommending a creation path.
- Read `references/result-schema.md` before presenting candidates to the user.
- Read `references/adaptation-matrix.md` when a discovered skill targets a different agent ecosystem from the current runtime.
- Read `references/search-playbook.md` when deciding how broad to search, when to parallelize, and when to stop.
- Use `scripts/search_skills.py` when a repeatable, half-automated search pass would help. The script reads `sources.yaml`, searches registered sources, scores candidates, writes Markdown and JSON summaries to `output/`, and generates a creation brief when a custom skill path is likely.
- When web lookups fail or return no results, treat that as a search note rather than a hard stop. The script already retries and falls back across providers.

## Core Rules

- Prefer reuse over creation.
- Prefer trusted markets before broad web discovery.
- Search `tier_1` sources before `tier_2` sources within the same source type.
- Use parallel or delegated search when the runtime supports it and the searches are independent.
- Do not overwhelm the user with raw search output.
- Do not return weak candidates only to fill a quota.
- Do not adapt a cross-platform candidate without asking the user first.
- Do not create a new skill until the user confirms creation or all suitable registered sources are exhausted.

## Source Selection

Choose the initial source type using this default routing:

- If the request clearly asks for an existing skill in a named ecosystem, start with `skill_market`.
- If the request asks for a broad community solution and no ecosystem is specified, start with `skill_market`, then `github`.
- If the request is highly niche or likely to live in repositories rather than curated markets, start with `github`.
- If the request is ambiguous, start with `skill_market` and `github` as the first search wave if the runtime can support parallel work.

Do not route to MCP-specific discovery here. This skill is intentionally scoped to skill discovery and creation. A separate orchestrator should handle MCP discovery.

## Search Execution

When searching agent-specific skill markets:

1. Identify the relevant agent ecosystem from the request.
2. Search every `tier_1` market for that ecosystem in parallel when possible.
3. Score and deduplicate results.
4. If a strong enough candidate exists, stop and present results.
5. Otherwise search `tier_2` markets.

When searching global sources such as GitHub:

1. Search the preferred global sources in parallel when possible.
2. Use platform and skill-specific terms in the search query.
3. Favor repositories with strong signs of community trust and recent maintenance.

## Candidate Return Policy

Use the rules in `references/decision-rules.md`.

Default display behavior:

- Return `Top 3` candidates.
- Return at most `5`.
- Return fewer when only one or two are truly worth considering.
- If one candidate clearly dominates, return it as the primary recommendation and include one backup.

## User Confirmation

Before moving forward, explicitly ask the user to choose one of these paths:

- adopt a discovered candidate
- continue searching
- adapt a cross-platform candidate
- create a new skill

If the user declines all discovered candidates, continue searching until all suitable registered sources are exhausted. Then say that the registered sources have been exhausted and creation is now the recommended path.

## Adaptation

When a discovered skill belongs to a different ecosystem:

1. Identify the source ecosystem and target ecosystem.
2. Read `references/adaptation-matrix.md`.
3. Explain the expected adaptation work in plain language.
4. Ask whether the user wants to proceed with adaptation.

If the user says no, return to search or creation options.

## Creation Fallback

Only create a new skill when one of these is true:

- all relevant registered sources have been searched and no suitable candidate was found
- the user explicitly prefers creating a new skill
- discovered candidates are too weak, unsafe, stale, or incompatible, and the user agrees that creation is the better path

When creating a new skill:

1. Summarize why creation is justified.
2. Convert the user's need into a concise skill brief.
3. Capture intended platforms, triggers, workflows, and reusable resources.
4. Structure the new skill around portable content first, then add platform-specific adapters only where necessary.

Use `assets/templates/creation-brief.md` as the output shape when helpful.
