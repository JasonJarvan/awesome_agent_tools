# Ops Doc Maintainer Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a portable `ops-doc-maintainer` skill that collects high-signal Linux ops data and maintains shared docs in `~/.ops-doc-maintainer-docs/`.

**Architecture:** Keep the skill core portable and runtime-neutral in `SKILL.md`, `scripts/`, `references/`, and `assets/`. Use small shell collectors for deterministic host inspection and a Python renderer to normalize outputs, apply noise filters, diff snapshots, update current-state docs, and append meaningful history entries only when something changed.

**Tech Stack:** Markdown skills, Bash, Python 3 standard library, Linux CLI tools (`ss`, `systemctl`, `docker`, `nginx`, `psql`, `apt`, `snap`, `npm`, `pip`, `uv`, `conda`)

---

## Chunk 1: Skill Skeleton And Metadata

### Task 1: Create the portable skill directory layout

**Files:**
- Create: `skills/ops-doc-maintainer/SKILL.md`
- Create: `skills/ops-doc-maintainer/agents/openai.yaml`
- Create: `skills/ops-doc-maintainer/adapters/claude-code.md`
- Create: `skills/ops-doc-maintainer/adapters/openclaw.md`
- Create: `skills/ops-doc-maintainer/references/doc-layout.md`
- Create: `skills/ops-doc-maintainer/references/collection-rules.md`
- Create: `skills/ops-doc-maintainer/references/software-detection-rules.md`
- Create: `skills/ops-doc-maintainer/references/safety-and-boundaries.md`

- [ ] **Step 1: Create the skill folder tree**

Run: `mkdir -p skills/ops-doc-maintainer/{agents,adapters,references,scripts,assets/templates}`
Expected: directories created with no errors

- [ ] **Step 2: Write the core `SKILL.md`**

Include:
- trigger language for inventory refresh and post-install updates
- default docs location via `OPS_DOCS_HOME` fallback to `~/.ops-doc-maintainer-docs`
- portable workflow instructions
- references to bundled scripts and rules

- [ ] **Step 3: Add Codex metadata**

Write `agents/openai.yaml` with:
- `display_name`
- `short_description`
- `default_prompt`

- [ ] **Step 4: Add Claude Code and OpenClaw adapter notes**

Document:
- packaging expectations
- environment variable usage
- shared-docs location
- minimal adaptation notes only

### Task 2: Write the reference docs that constrain scope

**Files:**
- Create: `skills/ops-doc-maintainer/references/doc-layout.md`
- Create: `skills/ops-doc-maintainer/references/collection-rules.md`
- Create: `skills/ops-doc-maintainer/references/software-detection-rules.md`
- Create: `skills/ops-doc-maintainer/references/safety-and-boundaries.md`

- [ ] **Step 1: Document the on-disk doc structure**

Describe:
- host-specific files
- snapshot storage
- watchlist and ignorelist files

- [ ] **Step 2: Document collection boundaries**

Describe:
- hotspot-only collection
- no low-value static system inventory
- meaningful-change-only history behavior

- [ ] **Step 3: Document software detection rules**

Describe:
- `apt`, `snap`, `npm`, `pip`, `uv`, `conda`, `manual-binary`
- global executables only
- ignore dependencies and libraries

- [ ] **Step 4: Document safety rules**

Describe:
- read-only inspection
- redaction of secrets
- graceful degradation when tools or permissions are missing

## Chunk 2: Templates And Collectors

### Task 3: Create Markdown templates for the shared docs

**Files:**
- Create: `skills/ops-doc-maintainer/assets/templates/host-index.md`
- Create: `skills/ops-doc-maintainer/assets/templates/network.md`
- Create: `skills/ops-doc-maintainer/assets/templates/services.md`
- Create: `skills/ops-doc-maintainer/assets/templates/software.md`
- Create: `skills/ops-doc-maintainer/assets/templates/changes.md`

- [ ] **Step 1: Define current-state templates**

Ensure templates cover:
- current network hotspots
- current service hotspots
- current software tools
- current host summary

- [ ] **Step 2: Define the change log template**

Ensure `changes.md` is append-only and reserved for meaningful changes only.

### Task 4: Implement reusable shell collection helpers

**Files:**
- Create: `skills/ops-doc-maintainer/scripts/common.sh`
- Create: `skills/ops-doc-maintainer/scripts/collect_network_hotspots.sh`
- Create: `skills/ops-doc-maintainer/scripts/collect_service_hotspots.sh`
- Create: `skills/ops-doc-maintainer/scripts/collect_postgres_hotspots.sh`
- Create: `skills/ops-doc-maintainer/scripts/collect_software_tools.sh`

- [ ] **Step 1: Implement `common.sh`**

Provide:
- command existence checks
- hostname/docs path resolution
- JSON-safe string escaping where needed
- helper functions for line-oriented key-value output

- [ ] **Step 2: Implement network collector**

Collect:
- main IPs
- default route
- DNS
- listening TCP/UDP ports
- firewall summary

- [ ] **Step 3: Implement service collector**

Collect:
- Docker status and running containers
- Nginx status and config summary
- SSH status and config summary

- [ ] **Step 4: Implement PostgreSQL collector**

Collect:
- service state
- listen settings and config paths
- database names
- user names
- active connection summary

- [ ] **Step 5: Implement software collector**

Collect:
- manual `apt` tools
- `snap` apps with commands
- global `npm` CLIs
- global executable tools from `pip`, `uv`, and `conda`
- manual-binary placeholders from config files

## Chunk 3: Rendering, Diffing, And Configuration

### Task 5: Implement the shared-doc writer

**Files:**
- Create: `skills/ops-doc-maintainer/scripts/update_ops_docs.py`

- [ ] **Step 1: Define the normalized data model**

Represent:
- `network`
- `services`
- `software`
- `changes`

- [ ] **Step 2: Load collector outputs and normalize them**

Handle:
- missing collectors
- missing commands
- empty sections

- [ ] **Step 3: Apply noise-reduction rules**

Ignore:
- unchanged content
- ordering-only differences
- low-signal values

- [ ] **Step 4: Render current-state docs**

Write:
- `index.md`
- `network.md`
- `services.md`
- `software.md`

- [ ] **Step 5: Append meaningful history entries**

Update:
- `changes.md` only when meaningful differences exist

### Task 6: Add watchlist and ignorelist support

**Files:**
- Create: `skills/ops-doc-maintainer/assets/templates/watchlist.txt`
- Create: `skills/ops-doc-maintainer/assets/templates/ignorelist.txt`
- Modify: `skills/ops-doc-maintainer/scripts/update_ops_docs.py`

- [ ] **Step 1: Define text file formats**

Support categories such as:
- `service:`
- `software:`
- `port:`
- `container:`

- [ ] **Step 2: Load the lists from the docs home**

Paths:
- `~/.ops-doc-maintainer-docs/watchlist.txt`
- `~/.ops-doc-maintainer-docs/ignorelist.txt`

- [ ] **Step 3: Apply filtering and priority**

Ensure:
- watchlist items are preserved
- ignorelist items are dropped from docs and change detection

## Chunk 4: Verification

### Task 7: Validate the skill on the current machine

**Files:**
- Modify: `skills/ops-doc-maintainer/scripts/*.sh`
- Modify: `skills/ops-doc-maintainer/scripts/update_ops_docs.py`

- [ ] **Step 1: Run the collectors manually**

Run:
- `bash skills/ops-doc-maintainer/scripts/collect_network_hotspots.sh`
- `bash skills/ops-doc-maintainer/scripts/collect_service_hotspots.sh`
- `bash skills/ops-doc-maintainer/scripts/collect_postgres_hotspots.sh`
- `bash skills/ops-doc-maintainer/scripts/collect_software_tools.sh`

Expected: structured output, no crashes, graceful skips where software is absent

- [ ] **Step 2: Run the doc updater**

Run:
- `python3 skills/ops-doc-maintainer/scripts/update_ops_docs.py`

Expected: host docs created under `~/.ops-doc-maintainer-docs/hosts/<hostname>/`

- [ ] **Step 3: Re-run to confirm low-noise behavior**

Run the updater a second time.
Expected: no duplicate meaningful-change entry when nothing changed

- [ ] **Step 4: Summarize any gaps**

Document:
- commands not available on this host
- services not installed
- any heuristics that may need user tuning later
