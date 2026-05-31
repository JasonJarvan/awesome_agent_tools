# Skill/router/ — Meta-Skill layer (v1+ placeholder)

Sub-projects classified as "routers" (skills that dispatch to other skills) live here.

## Pending sub-projects

- **SP-8 web-search/** — aggregator skill for Zhihu official Skills (`zhihu_search_skills.zip`, `global_search_skills.zip`, `hot_list_skills.zip`) + Tavily MCP + Exa.
  Status: v1+ candidate, not in v1 scope.
  Reference: `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` §7

## Convention

- Routers do not vendor third-party Skill packs into this repo (avoids drift). README in each router subdir documents external download instructions.
- Routers depend on Skills only via Claude Code's `Skill` tool dispatch — no direct imports.
