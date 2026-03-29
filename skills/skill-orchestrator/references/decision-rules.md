# Decision Rules

Use this document to decide where to search, when to stop, how to score candidates, and how many results to return.

## 1. Route To A Source Type

Use this routing table first.

- Ask for an existing skill in a named ecosystem: start with that ecosystem's `skill_market`.
- Ask for a cross-platform skill: start with `skill_market`, then search `github` if no strong result appears.
- Ask for something niche, experimental, or likely to live in a repository rather than a curated market: start with `github`.
- Ask vaguely for "a tool" but describe a reusable agent workflow: interpret that as a skill-discovery request unless the user explicitly asks for MCP or CLI tooling.

## 2. Search Tiered Markets Conservatively

For a chosen agent ecosystem:

1. Search all `tier_1` markets first.
2. Deduplicate and score the results.
3. If there is at least one strong candidate, stop and return results.
4. Only if there is no strong candidate should you search `tier_2`.

Do not skip directly to low-signal sources just because they are broad.

## 3. Score Candidates

Use a 100-point score with these dimensions:

- `need_fit` up to 30
  How well the candidate matches the user's requested workflow or problem.

- `platform_fit` up to 20
  How directly it fits the current runtime or target ecosystem.

- `community_trust` up to 20
  Use stars, forks, discussion quality, references, and evidence of real usage.

- `maintenance_health` up to 15
  Use recency, signs of maintenance, and compatibility indicators.

- `clarity_and_packaging` up to 10
  Prefer a clear `SKILL.md`, concrete resources, and understandable setup.

- `risk_penalty` subtract up to 15
  Subtract for unclear licensing, unsafe scripts, stale dependencies, or vague ownership.

## 4. Interpret Scores

- `85-100`: strong candidate
- `70-84`: usable candidate
- `50-69`: weak candidate, show only if better options do not exist
- `0-49`: do not present unless the user explicitly asks for exhaustive results

## 4A. Community Threshold Heuristic

For GitHub-discovered candidates, treat `100+ stars` as a strong positive signal, not an automatic acceptance rule.

Use this as a practical heuristic:

- `100+ stars`: strong community signal when paired with decent maintenance
- `30-99 stars`: moderate signal, often worth considering for niche workflows
- `< 30 stars`: weak signal unless there is another strong trust factor such as official backing or unusually strong documentation

Do not reject a candidate only because it is below 100 stars when:

- the domain is niche
- the source is official
- or the packaging and maintenance quality are unusually strong

## 5. Decide How Many Candidates To Return

Default return count is `3`.

Apply these rules:

- Return `3` by default when at least three good candidates exist.
- Return `2` when only two are genuinely decision-worthy.
- Return `1 primary + 1 backup` when one candidate clearly dominates.
- Return up to `5` only when the additional candidates represent meaningfully different strategies or tradeoffs.
- Return `0` when nothing clears the minimum threshold and recommend continued search or creation instead.

Never pad the list with low-quality candidates just to hit a target number.

## 6. Define "Clearly Dominates"

A candidate clearly dominates when all of the following are true:

- it is at least 10 points ahead of the next candidate
- it has no major adaptation or safety penalty
- it is directly compatible with the target ecosystem or requires only light adaptation

When this happens, present it first and add exactly one backup candidate.

## 7. Deduplicate Before Ranking

Treat these as duplicates unless there is a meaningful difference:

- mirrors of the same project
- forks with no substantial divergence
- repositories that simply repackage the same skill

Keep the strongest representative and mention notable alternatives only if they differ in maintenance status or platform support.

## 8. Ask For Confirmation At Decision Boundaries

Ask the user before:

- adopting a found candidate
- adapting a candidate from another ecosystem
- broadening the search to lower-priority sources after reasonable high-priority search
- creating a new skill

## 9. Stop Conditions

Stop searching and present results when:

- a strong candidate exists
- or several usable candidates create a real decision set

Stop searching and recommend creation when:

- all relevant registered sources have been searched
- and no candidate meets the minimum quality bar
- and the user still wants a reusable solution
