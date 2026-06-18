# Skill

Agent-facing capabilities packaged per the agentskills.io `SKILL.md` standard, runnable from any
compliant agent runtime (Claude Code, Codex, OpenClaw, Hermes). A crawl Skill wraps its platform
Engine; it adds packaging, config and agent ergonomics — never new fetch logic.

## Language

**Skill**:
In this context: a product deliverable — an agent-invocable capability shipped as an
agentskills.io-compliant `SKILL.md` package (e.g. `zhihu-crawl`, `bilibili-crawl`). Not to be
confused with the development-process skills this repo's agents use to build it (those are
governance, out of CONTEXT scope).
_Avoid_: plugin, command, tool (in the agent-packaging sense)

**Router**:
The planned entry Skill that dispatches a content reference to the right crawl Skill by domain
(v1+ placeholder, `Skill/router/`).
_Avoid_: dispatcher, gateway

**crawl-md-saver**:
The ingester-side wrapper Skill (SP-6) that registers the crawl Skills and merges user notes
with crawled source content into one Markdown deliverable.
_Avoid_: DocSaver (early codename, same thing)
