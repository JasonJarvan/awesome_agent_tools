# Awesome Agent Tools

English | [中文](README.zh-CN.md)

An open repository of reusable agent tooling, with a strong focus on portable skills, practical workflows, and clear design.

This repository is built around a simple idea:

> Do not create a new skill too early.
> First search for an existing, trusted solution.
> Only after a workflow succeeds in real use should it be packaged into a reusable skill.

The current flagship artifact is a cross-platform `skill-orchestrator` skill. It helps an agent decide where to search for an existing skill, how to present candidates to the user, and when to stop searching and create a new skill instead.

## Cloning This Repository

Several entries below are git submodules pointing to their own standalone
repos (`Skills/ops-doc-maintainer/` and everything under `Skills/Coding/`).
A plain `git clone` leaves those directories empty — initialise submodules
in the same step:

```bash
git clone --recurse-submodules https://github.com/JasonJarvan/awesome_agent_tools.git
# or, after a plain clone:
git submodule update --init --recursive
```

To pull later upstream changes for the submodule as well:

```bash
git pull --recurse-submodules
```

## What This Repository Contains

- `Skills/skill-orchestrator/`
  A portable orchestration skill for discovering, evaluating, adapting, and eventually creating skills across agent ecosystems such as Codex, Claude Code, and OpenClaw.

- `Skills/barksy_pipeline/`
  A utility-oriented skill for exporting Codex session history to Markdown.

- `Skills/ops-doc-maintainer/` *(git submodule → [JasonJarvan/ops-doc-maintainer](https://github.com/JasonJarvan/ops-doc-maintainer))*
  A cross-platform ops documentation skill (Linux and Windows). Auto-detects the host on every invocation and maintains low-noise shared docs for network hotspots, listening ports, Docker, Nginx/IIS, SSH/WinRM, VPN/proxy state, PostgreSQL connection guidance (Linux only), and manually installed global CLI tools. Designed to be written once and installed into Codex, Claude Code, and OpenClaw while sharing one docs directory.

- `Skills/web-search.md`
  A lightweight skill note related to web search behavior.

- `Skills/Coding/` — curated skills for coding agents, each a git submodule:

  - `Skills/Coding/RepoMem/` *(git submodule → [JasonJarvan/RepoMem](https://github.com/JasonJarvan/RepoMem))*
    A persistent memory layer for code repositories and coding agents.

  - `Skills/Coding/HarnessFactory/` *(git submodule → [JasonJarvan/HarnessFactory](https://github.com/JasonJarvan/HarnessFactory))*
    A harness system for coding agents — long-term and temporary contractor templates plus skill packaging, designed to be embedded into target development repos. *(formerly `HarnessStack`)*

  - `Skills/Coding/cc-sendbox/` *(git submodule → [JasonJarvan/cc-sendbox](https://github.com/JasonJarvan/cc-sendbox))*
    Multi-agent coordination via versioned letters — packaged as a Claude Code skill.

- `Tools/cursor_history_viewer/`
  Existing project material related to browsing and exporting agent or editor history.

## Why This Project Exists

Teams using AI coding agents quickly run into the same problem:

- Sometimes the right answer is a `skill`
- Sometimes it is an `MCP server`
- Sometimes it is just a `CLI tool`
- Sometimes the best move is to build nothing and reuse what already works

Most projects jump straight into creation. This repository takes the opposite approach. It treats creation as the last step, not the first.

That leads to three design principles:

1. Search before build.
2. Ask for confirmation before adapting or generating new tooling.
3. Keep the reusable logic platform-neutral, and isolate platform-specific behavior in thin adapters.

## The `skill-orchestrator`

The `skill-orchestrator` is intentionally scoped to skills first. It does not yet absorb MCP orchestration. That is a deliberate design choice.

The planned layering is:

1. `skill-orchestrator`
2. `mcp-orchestrator`
3. A higher-level capability orchestrator that can route between skills, MCP, and possibly CLI tools

This keeps the first version focused and makes evaluation simpler.

### What The Skill Does

Given a user request, the skill should:

1. Analyze the request and decide which source type is most appropriate for skill discovery.
2. Search the highest-priority registered markets first.
3. Search those markets in parallel when the runtime supports parallel or delegated work.
4. Return a small number of high-signal candidates rather than a long dump of links.
5. Ask the user whether to adopt one of the discovered options, continue searching, or create a new skill.
6. If a discovered skill targets another ecosystem, ask whether adaptation should happen before use.

### Why The Skill Is Cross-Platform

The skill is designed around a portable core:

- search policy
- source registry
- scoring rules
- candidate presentation format
- adaptation rules

Platform-specific behavior is intentionally separated:

- Codex-specific metadata
- Claude Code-specific frontmatter or tool constraints
- OpenClaw-specific runtime fields
- differences in sub-agent spawning, parallel search, and user confirmation flows

This means the content is reusable even when the packaging is not identical.

## Repository Layout

```text
awesome_agent_tools/
├── README.md
├── AGENT.md
├── Skills/
│   ├── Coding/                               # curated skills for coding agents (all submodules)
│   │   ├── RepoMem/                          # submodule → JasonJarvan/RepoMem
│   │   ├── HarnessFactory/                   # submodule → JasonJarvan/HarnessFactory
│   │   └── cc-sendbox/                       # submodule → JasonJarvan/cc-sendbox
│   ├── barksy_pipeline/
│   ├── ops-doc-maintainer/                   # submodule → JasonJarvan/ops-doc-maintainer (cross-platform)
│   │   ├── SKILL.md
│   │   ├── README.md
│   │   ├── adapters/
│   │   │   ├── linux/{claude-code.md, openclaw.md}
│   │   │   └── windows/claude-code.md
│   │   ├── agents/
│   │   │   ├── linux/openai.yaml
│   │   │   └── windows/openai.yaml
│   │   ├── assets/
│   │   │   ├── linux/templates/
│   │   │   └── windows/templates/
│   │   ├── references/
│   │   │   ├── linux/{collection-rules.md, doc-layout.md, safety-and-boundaries.md, software-detection-rules.md}
│   │   │   └── windows/{collection-rules.md, doc-layout.md, safety-and-boundaries.md, software-detection-rules.md}
│   │   └── scripts/
│   │       ├── update_ops_docs.py            # dispatcher: detects OS, delegates
│   │       ├── linux/{collect_*.sh, ops_doc_lib.py, update_ops_docs.py}
│   │       └── windows/{win_ops_doc_lib.py, update_ops_docs.py}
│   ├── skill-orchestrator/
│   │   ├── SKILL.md
│   │   ├── agents/
│   │   │   └── openai.yaml
│   │   ├── scripts/
│   │   │   ├── requirements.txt
│   │   │   └── search_skills.py
│   │   ├── references/
│   │   │   ├── adaptation-matrix.md
│   │   │   ├── decision-rules.md
│   │   │   ├── result-schema.md
│   │   │   ├── search-playbook.md
│   │   │   └── sources.yaml
│   │   └── assets/
│   │       └── templates/
│   │           ├── candidate-summary.md
│   │           └── creation-brief.md
│   │   └── output/ (generated, gitignored)
│   └── web-search.md
└── Tools/
    └── cursor_history_viewer/
```

## How To Use The Skill

The skill is intended for agent runtimes that support skill folders with a `SKILL.md` entry point.

Typical usage pattern:

1. Put the skill folder where your agent runtime can discover it.
2. Ask for a tool or reusable workflow.
3. Let the skill choose the best source type to search first.
4. Review the candidate summary.
5. Confirm whether to adopt, adapt, continue searching, or create a new skill.

If you want a repeatable, half-automated search outside the agent runtime, use the included script:

```bash
cd Skills/skill-orchestrator/scripts
python -m pip install -r requirements.txt
python search_skills.py "documentation co-authoring skill for Claude Code" --ecosystem claude_code
```

The script writes both Markdown and JSON outputs into `Skills/skill-orchestrator/output/`.
When no strong candidate exists, or when you may still prefer a custom solution, the output also includes a structured creation brief that can seed a new skill.
For web-based source lookups, the script uses retries and fallback providers so occasional search-engine failures degrade gracefully into source notes instead of breaking the whole run.

Example requests:

- "Find a community skill for structured code review in Claude Code."
- "Search for a Codex-compatible skill for repository archaeology."
- "I need a cross-platform skill for issue triage. Reuse something existing if possible."
- "Search skill markets first, then GitHub, then help me create one if nothing is strong enough."

## The `ops-doc-maintainer`

The `ops-doc-maintainer` skill focuses on hotspot-only host documentation rather than full machine inventory. Its default shared docs home is `~/.ops-doc-maintainer-docs/`, with `OPS_DOCS_HOME` available as an override.

### What The Skill Does

Given a Linux host, the skill should:

1. Track only high-signal network and port information.
2. Summarize Docker, Nginx, and SSH state without dumping raw configs.
3. Record PostgreSQL connection guidance and config path references rather than database internals.
4. Record manually installed global executable tools from `apt`, `snap`, `npm`, `pip`, `uv`, `conda`, and a manual-binary list.
5. Update current-state docs and append only meaningful changes to history.

### Why The Skill Is Cross-Platform

Like `skill-orchestrator`, `ops-doc-maintainer` keeps its core portable:

- runtime-neutral `SKILL.md`
- reusable scripts
- references and templates
- thin adapter notes for Claude Code and OpenClaw

That makes it practical to validate in this repository first and then copy into each assistant's local skill directory without changing the shared docs model.

## How Discovery Works

The core search strategy is intentionally conservative.

### Source Types

The first version focuses on skill discovery, not MCP orchestration. The main source types are:

- agent-specific skill markets
- GitHub
- other skill directories or ecosystem-specific registries

All registered sources live in [`Skills/skill-orchestrator/references/sources.yaml`](Skills/skill-orchestrator/references/sources.yaml), which is designed to be easy to edit as the ecosystem changes.

### Priority Model

For agent-specific markets, sources are grouped into two tiers:

- `tier_1`: preferred and trusted first-pass sources
- `tier_2`: broader or more experimental fallback sources

The orchestrator searches all `tier_1` sources in parallel where possible. Only if no sufficiently strong result is found does it move to `tier_2`.

### Candidate Count

The orchestrator does not dump every hit.

Its default presentation rule is:

- return `Top 3` by default
- never return more than `5`
- do not pad with weak candidates just to hit a number
- if one result is clearly best, return it with a backup option

This keeps decision-making fast and humane.

## Design Files

The skill is documented as a small system rather than a single prompt file.

- [`SKILL.md`](Skills/skill-orchestrator/SKILL.md)
  The portable operating manual for the orchestrator.

- [`sources.yaml`](Skills/skill-orchestrator/references/sources.yaml)
  Editable registry of search sources, grouped by source type, agent ecosystem, and priority tier.

- [`decision-rules.md`](Skills/skill-orchestrator/references/decision-rules.md)
  Routing, scoring, stopping rules, and candidate-count logic.

- [`result-schema.md`](Skills/skill-orchestrator/references/result-schema.md)
  Defines exactly what information should be returned to help a user choose.

- [`adaptation-matrix.md`](Skills/skill-orchestrator/references/adaptation-matrix.md)
  Describes how skills can be adapted between Codex, Claude Code, and OpenClaw.

- [`search-playbook.md`](Skills/skill-orchestrator/references/search-playbook.md)
  Concrete execution guidance for searching well and escalating carefully.

## Why The README Is Detailed

This project is intended to be useful both to humans and to agents.

That creates a tension:

- humans need clear architecture and rationale
- agents need compact, structured operating instructions

The solution here is to separate concerns:

- the root `README.md` explains the system to humans
- the skill folder contains the compact operational material for agent runtimes

## Current Scope And Future Work

Current scope:

- skill discovery
- candidate evaluation
- user confirmation
- cross-platform adaptation planning
- creation fallback after search exhaustion

Planned future work:

- a dedicated `mcp-orchestrator`
- a unified top-level capability orchestrator
- richer search scripts for repeatable marketplace queries
- automated source freshness checks

## Contributing

Contributions are most helpful when they improve one of these areas:

- better registered sources in `sources.yaml`
- clearer decision rules
- stronger cross-platform adaptation guidance
- real-world examples of successful skill reuse

When proposing changes, prefer improvements that make the orchestrator more legible and more trustworthy, not just more complex.

## Philosophy In One Sentence

The best skill is often the one you do not have to create, and the best custom skill is one distilled from a workflow that has already proven itself in practice.
