# SP-0 JarvanKB Skeleton + HarnessStack v2 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the JarvanKB monorepo directory skeleton, remove OpenSpec from the active recipe (recipe v1→v2 Full Rewrite), update governance docs (CLAUDE.md / HarnessStack / RepoMem / Dashboard), and seed sub-project stubs for the 10 v1 sub-projects.

**Architecture:** Pure file-system + documentation refactor. No application code, no tests-per-se — verification is filesystem checks + content greps. Each task commits independently so progress is bisectable.

**Tech Stack:** Bash, Markdown. No build or test runner needed. Optional: `tree` command for verification.

---

## Preconditions

- **CWD throughout this plan**: `~/Codes/awesome_agent_tools/Tools/AgentCrawl/`
- **If user has already renamed `Tools/AgentCrawl/` → `Tools/JarvanKB/`** in a separate session: substitute `Tools/JarvanKB/` for every `Tools/AgentCrawl/` path below. The rename is **independent** of this plan; this plan works either way.
- **Branch**: stay on the current `feat/agentcrawl-bootstrap` branch. Do NOT branch again. Do NOT merge to `main` (the parent repo's default) until SP-0 + a few sub-projects are done.
- **Design reference**: `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` is the source of truth — open it in a second window while executing.

---

## File Structure (what this plan creates / modifies)

### Created
- `Engine/{common,zhihu,bilibili}/` — engine modules with `docs/` substructure
- `Skill/crawl/{zhihu-crawl,bilibili-crawl}/` — crawl skills
- `Skill/ingester/crawl-md-saver/` — ingester skill
- `Skill/router/README.md` — SP-8 placeholder (v1+)
- `Service/crawl/{cookie-manager,zhihu-watcher,bilibili-watcher}/` — crawl services
- `Service/ingester/thino-ingester/` — ingester service
- `README.md` (top-level) — replaces or significantly extends current
- Per sub-project skeleton files: `docs/{README.md,interface.md,architecture.md}` + `docs/RepoMem/{architecture.md,decisions.md}`

### Modified
- `CLAUDE.md` — recipe ID v2, pipeline 13→8 steps, Where-to-Look updated
- `docs/HarnessStack/README.md` — recipe identity v2
- `docs/HarnessStack/longterm.md` — v1 deprecated + v2 active + Full Rewrite record
- `docs/HarnessStack/_toUser/README.md` — pipeline 8-step + OpenSpec section removed
- `docs/RepoMem/persist/config.md` — recipe reference v2
- `docs/RepoMem/persist/version-plan.md` — v1→v2 migration entry + new 10-sub-project phase plan
- `docs/RepoMem/persist/memory/runbook.md` — §0 OpenSpec symlink section removed
- `docs/RepoMem/persist/memory/pre-openspec-decisions.md` — add banner about post-v2 status
- `docs/Dashboard/index.md` — clean OpenSpec-related rows

### Deleted
- `openspec` (root symlink → `docs/openspec`)
- `docs/openspec/` (empty workspace: `changes/`, `specs/`)
- `.claude/commands/opsx/` (4 md files)
- `.claude/skills/openspec-{apply-change,archive-change,explore,propose}/` (4 skill dirs)

### Out of scope for this plan
- The repo physical rename `Tools/AgentCrawl/` → `Tools/JarvanKB/` (user does in another session)
- Implementing LLMClient body (only stub the file in `Engine/common/`)
- Any sub-project (SP-1..SP-7) actual implementation
- Migrating the 14 existing RepoMem persist docs to a new location (they already live in `docs/RepoMem/persist/` which is the v2 location)
- Global `npm uninstall -g @fission-ai/openspec` (suggest to user; not in plan)

---

## Self-Review note before starting

After all tasks complete, the repo should:
1. Have zero references to `openspec` / `OpenSpec` / `change-id` outside of `pre-openspec-decisions.md` (which retains historical name) and the SP-0 design.md (which describes the migration)
2. Have a complete sub-project skeleton — every cell in §7 of the design.md has a corresponding directory
3. Pass: `grep -r "openspec" --include="*.md" . | wc -l` returns only design.md + pre-openspec-decisions.md + version-plan.md (which records the migration)

---

## Task 1 — Create new directory skeleton with stub docs

**Files:**
- Create: `Engine/common/`, `Engine/zhihu/`, `Engine/bilibili/`
- Create: `Skill/crawl/zhihu-crawl/`, `Skill/crawl/bilibili-crawl/`
- Create: `Skill/ingester/crawl-md-saver/`
- Create: `Skill/router/README.md`
- Create: `Service/crawl/cookie-manager/`, `Service/crawl/zhihu-watcher/`, `Service/crawl/bilibili-watcher/`
- Create: `Service/ingester/thino-ingester/`
- Plus per-sub-project: `docs/README.md`, `docs/interface.md`, `docs/architecture.md`, `docs/RepoMem/architecture.md`, `docs/RepoMem/decisions.md`

- [ ] **Step 1.1: Create the 10 sub-project directories + nested docs/RepoMem**

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/

for d in \
  Engine/common Engine/zhihu Engine/bilibili \
  Skill/crawl/zhihu-crawl Skill/crawl/bilibili-crawl \
  Skill/ingester/crawl-md-saver \
  Service/crawl/cookie-manager Service/crawl/zhihu-watcher Service/crawl/bilibili-watcher \
  Service/ingester/thino-ingester
do
  mkdir -p "$d/docs/RepoMem/temp" "$d/src" "$d/tests"
done

mkdir -p Skill/router
```

- [ ] **Step 1.2: Verify directory tree**

```bash
find Engine Skill Service -type d | sort
```

Expected output: all 10 sub-project paths plus their `docs/`, `docs/RepoMem/`, `docs/RepoMem/temp/`, `src/`, `tests/` (Skill/router has only itself).

- [ ] **Step 1.3: Seed stub `docs/README.md` for each sub-project**

Each sub-project gets a 5-line stub README. Run this single loop:

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/

declare -A SP=(
  ["Engine/common"]="SP-0 shared layer|LLMClient (litellm backend) + BaseSkill + cookie reader|library"
  ["Engine/zhihu"]="SP-2 Zhihu engine|cookie + zse-96 signature scraping via MediaCrawler pattern|library"
  ["Engine/bilibili"]="SP-4a Bilibili engine|BiliNote HTTP client + bilibili-api-python metadata|library"
  ["Skill/crawl/zhihu-crawl"]="SP-3 Zhihu Skill|URL → engine → ask user → save md (vague + decided paths)|skill"
  ["Skill/crawl/bilibili-crawl"]="SP-4b Bilibili Skill|URL → engine → ask user → save md|skill"
  ["Skill/ingester/crawl-md-saver"]="SP-6 CrawlMdSaver Skill|wrapper that registers crawl skills, merges user notes + source|skill"
  ["Service/crawl/cookie-manager"]="SP-1 CookieManager|fork CookieCloud + hook mechanism + CLI list/show|service"
  ["Service/crawl/zhihu-watcher"]="SP-5a Zhihu favorites watcher|polling watcher, high-watermark on 'created'|service"
  ["Service/crawl/bilibili-watcher"]="SP-5b Bilibili favorites watcher|polling watcher, high-watermark on 'fav_time'|service"
  ["Service/ingester/thino-ingester"]="SP-7 Thino Ingester|watch Thino_path, parse blocks, dispatch to crawl-md-saver|service"
)

for path in "${!SP[@]}"; do
  IFS='|' read -r title desc kind <<< "${SP[$path]}"
  cat > "$path/docs/README.md" <<EOF
# ${path##*/}

> **${title}**
> Status: placeholder — implementation pending its own brainstorming + plan.

## What this does

${desc}

## Kind

${kind}

## See also

- Top-level design: \`docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md\` §7
- Module contract (TBD): \`docs/interface.md\`
- Internal architecture (TBD): \`docs/RepoMem/architecture.md\`
EOF
done
```

- [ ] **Step 1.4: Seed stub `docs/interface.md` and `docs/architecture.md`**

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/

for path in \
  Engine/common Engine/zhihu Engine/bilibili \
  Skill/crawl/zhihu-crawl Skill/crawl/bilibili-crawl \
  Skill/ingester/crawl-md-saver \
  Service/crawl/cookie-manager Service/crawl/zhihu-watcher Service/crawl/bilibili-watcher \
  Service/ingester/thino-ingester
do
  cat > "$path/docs/interface.md" <<'EOF'
# Interface (placeholder)

> Will be filled during this module's brainstorming → design → writing-plans cycle.
> Holds the stable public contract: function signatures / CLI args / HTTP endpoints.

(TBD — do not implement against this until populated)
EOF

  cat > "$path/docs/architecture.md" <<'EOF'
# Architecture (placeholder)

> External-facing architecture summary; will be filled during this module's design phase.
> For internal design notes, see `docs/RepoMem/architecture.md`.

(TBD)
EOF
done
```

- [ ] **Step 1.5: Seed stub `docs/RepoMem/{architecture,decisions}.md`**

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/

for path in \
  Engine/common Engine/zhihu Engine/bilibili \
  Skill/crawl/zhihu-crawl Skill/crawl/bilibili-crawl \
  Skill/ingester/crawl-md-saver \
  Service/crawl/cookie-manager Service/crawl/zhihu-watcher Service/crawl/bilibili-watcher \
  Service/ingester/thino-ingester
do
  cat > "$path/docs/RepoMem/architecture.md" <<'EOF'
# Module internal architecture (placeholder)

> Internal design — module-private decisions, layering, key code paths.
> Distinct from `docs/architecture.md` which is the external summary.

(TBD — populate during this module's brainstorming/writing-plans)
EOF

  cat > "$path/docs/RepoMem/decisions.md" <<'EOF'
# Module decision log

> Append-only, time-descending (newest at top).
> Each entry: date, slug, decision, rationale, what-changes-when-this-is-revisited.
> When a decision is promoted to global, leave a `[Promoted to global ↗]` marker pointing to `<root>/docs/RepoMem/persist/memory/`.

(empty — no decisions yet)
EOF
done
```

- [ ] **Step 1.6: Seed `Skill/router/README.md` (SP-8 placeholder)**

```bash
cat > Skill/router/README.md <<'EOF'
# Skill/router/ — Meta-Skill layer (v1+ placeholder)

Sub-projects classified as "routers" (skills that dispatch to other skills) live here.

## Pending sub-projects

- **SP-8 web-search/** — aggregator skill for Zhihu official Skills (`zhihu_search_skills.zip`, `global_search_skills.zip`, `hot_list_skills.zip`) + Tavily MCP + Exa.
  Status: v1+ candidate, not in v1 scope.
  Reference: `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` §7

## Convention

- Routers do not vendor third-party Skill packs into this repo (avoids drift). README in each router subdir documents external download instructions.
- Routers depend on Skills only via Claude Code's `Skill` tool dispatch — no direct imports.
EOF
```

- [ ] **Step 1.7: Verify all stubs exist**

```bash
find Engine Skill Service -name "*.md" -type f | sort | wc -l
```

Expected: **51** files (10 sub-projects × 5 stub files [README/interface/architecture/RepoMem-architecture/RepoMem-decisions] + 1 Skill/router/README.md).

If count differs, list missing:
```bash
for path in Engine/common Engine/zhihu Engine/bilibili Skill/crawl/zhihu-crawl Skill/crawl/bilibili-crawl Skill/ingester/crawl-md-saver Service/crawl/cookie-manager Service/crawl/zhihu-watcher Service/crawl/bilibili-watcher Service/ingester/thino-ingester; do
  for f in docs/README.md docs/interface.md docs/architecture.md docs/RepoMem/architecture.md docs/RepoMem/decisions.md; do
    [ -f "$path/$f" ] || echo "MISSING: $path/$f"
  done
done
```

- [ ] **Step 1.8: Commit**

```bash
cd ~/Codes/awesome_agent_tools/
git add Tools/AgentCrawl/Engine Tools/AgentCrawl/Skill Tools/AgentCrawl/Service
git commit -m "feat(SP-0): seed 10 sub-project directory skeletons

Each sub-project under Engine/Skill/Service has:
- docs/{README,interface,architecture}.md
- docs/RepoMem/{architecture,decisions}.md
- src/, tests/

Skill/router/README.md placeholds SP-8 (v1+).

Refs: docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md §3, §5, §7

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 2 — Stub LLMClient skeleton in Engine/common/

**Files:**
- Create: `Engine/common/src/llm_client.py`
- Create: `Engine/common/src/__init__.py`
- Create: `Engine/common/docs/interface.md` (overwrite stub from Task 1)
- Create: `config/llm.yaml.example`

- [ ] **Step 2.1: Create `config/` directory at repo root**

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/
mkdir -p config
```

- [ ] **Step 2.2: Write `config/llm.yaml.example`**

```bash
cat > config/llm.yaml.example <<'EOF'
# JarvanKB LLM provider configuration
# Copy to config/llm.yaml and fill credentials in .env (NEVER commit credentials).

profiles:
  default:
    model: claude-opus-4-7              # litellm model id; switch freely
    api_key_env: ANTHROPIC_API_KEY      # env var name to read at runtime

  fallback:
    model: dashscope/qwen-max
    api_key_env: DASHSCOPE_API_KEY

  local:
    model: ollama/llama3
    api_key_env: ""                      # ollama needs no key
    api_base_env: OLLAMA_API_BASE

# Active profile order — first available wins.
active: [default, fallback]
EOF
```

- [ ] **Step 2.3: Write `Engine/common/src/__init__.py`**

```bash
cat > Engine/common/src/__init__.py <<'EOF'
"""JarvanKB shared engine layer.

Contains cross-engine utilities:
- LLMClient — litellm-backed LLM dispatcher (see llm_client.py)
- (planned) BaseSkill — common skill scaffolding
- (planned) CookieReader — read cookies from CookieManager service
"""
EOF
```

- [ ] **Step 2.4: Write `Engine/common/src/llm_client.py` (skeleton)**

```bash
cat > Engine/common/src/llm_client.py <<'EOF'
"""LLMClient — uniform LLM dispatcher with litellm backend.

Design reference: docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md §8.

Status: skeleton only. Body NotImplementedError until first consumer sub-project
(SP-3, SP-6, or SP-7) brings in actual usage. The interface signatures below are
the stable v1 contract — implement against these.
"""

from __future__ import annotations
from typing import Any, Iterator


class LLMClient:
    """Uniform LLM client. Internally uses litellm to route to any provider.

    Use:
        from Engine.common.src.llm_client import LLMClient
        client = LLMClient(profile="default")
        text = client.complete([{"role": "user", "content": "hello"}])
    """

    def __init__(self, profile: str = "default") -> None:
        self.profile = profile
        # Configuration loading happens in first consumer's brainstorming.
        # See config/llm.yaml.example for the schema.

    def complete(self, messages: list[dict], **kwargs: Any) -> str:
        """Single-shot completion. Returns assistant text."""
        raise NotImplementedError(
            "LLMClient.complete pending first consumer implementation. "
            "See SP-3 / SP-6 / SP-7 brainstorming."
        )

    def stream(self, messages: list[dict], **kwargs: Any) -> Iterator[str]:
        """Streaming completion. Yields text chunks."""
        raise NotImplementedError(
            "LLMClient.stream pending first consumer implementation."
        )

    def to_opencode(self) -> Any:
        """v1+ escape hatch: convert to opencode agent loop. Not implemented in v1."""
        raise NotImplementedError("opencode integration planned for v1.x")
EOF
```

- [ ] **Step 2.5: Overwrite `Engine/common/docs/interface.md` with the real contract**

```bash
cat > Engine/common/docs/interface.md <<'EOF'
# Engine/common — Interface

## LLMClient

```python
from Engine.common.src.llm_client import LLMClient

client = LLMClient(profile="default")   # profile defined in config/llm.yaml
text  = client.complete([{"role": "user", "content": "..."}])
chunks = client.stream([{"role": "user", "content": "..."}])
```

**Stability**: signatures (constructor + `complete` + `stream` + `to_opencode`) are the v1 frozen contract.
**Body**: skeleton only in v1 SP-0; first real implementation lands with SP-3 or SP-6.

## Configuration

Reads `config/llm.yaml` (copy from `config/llm.yaml.example`). Provider switches by config alone — no code changes in consumer sub-projects.

## Backend

`litellm` (pip install `litellm`). Supports OpenAI / Anthropic / DashScope (Qwen) / Ollama / Groq / Gemini / Bedrock / many more.
EOF
```

- [ ] **Step 2.6: Verify**

```bash
ls Engine/common/src/ Engine/common/docs/ config/
python3 -c "import sys; sys.path.insert(0, 'Engine/common/src'); import llm_client; c = llm_client.LLMClient(); print(type(c).__name__)"
```

Expected: `llm_client.py`, `__init__.py` listed; Python prints `LLMClient` (constructor works; methods raise NotImplementedError, which is correct skeleton behavior).

- [ ] **Step 2.7: Commit**

```bash
cd ~/Codes/awesome_agent_tools/
git add Tools/AgentCrawl/Engine/common Tools/AgentCrawl/config
git commit -m "feat(SP-0): stub LLMClient skeleton + llm.yaml.example

- Engine/common/src/llm_client.py — stable v1 signatures, NotImplementedError bodies
- Engine/common/docs/interface.md — public contract documented
- config/llm.yaml.example — provider profiles (default/fallback/local), env-var driven

Body implementation deferred to first consumer (SP-3 / SP-6 / SP-7).

Refs: docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md §8

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 3 — Remove OpenSpec workspace and root symlink

**Files:**
- Delete: `openspec` (root symlink)
- Delete: `docs/openspec/` (empty workspace: `changes/`, `specs/`)

⚠️ **HITL gate before this task**: Confirm with user that `openspec list` returned `No active changes found` (already verified in Step A smoke test). If any in-flight change exists, STOP and surface.

- [ ] **Step 3.1: Verify workspace empty (idempotent re-check)**

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/
find docs/openspec -type f
```

Expected: empty output (no files, only empty `changes/` and `specs/` directories).

If output is non-empty: **STOP**, escalate to user with file list. Do not delete.

- [ ] **Step 3.2: Delete root symlink**

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/
rm openspec
ls -la openspec 2>&1
```

Expected error: `ls: cannot access 'openspec': No such file or directory`.

- [ ] **Step 3.3: Delete `docs/openspec/` workspace**

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/
rm -rf docs/openspec
ls docs/openspec 2>&1
```

Expected error: `ls: cannot access 'docs/openspec': No such file or directory`.

- [ ] **Step 3.4: Verify `openspec` CLI now fails when invoked from this repo**

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/
openspec list 2>&1 | head -5
```

Expected: error like `No OpenSpec changes directory found` (or similar). This confirms removal is clean.

If `openspec` is uninstalled globally on this machine, expect `command not found` — also acceptable.

- [ ] **Step 3.5: Commit**

```bash
cd ~/Codes/awesome_agent_tools/
git add -A Tools/AgentCrawl/openspec Tools/AgentCrawl/docs/openspec
git commit -m "chore(SP-0): remove OpenSpec workspace and root symlink

Empty workspace (no in-flight changes verified).
Part of recipe v1→v2 Full Rewrite migration (OpenSpec removed).

Refs: docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md §6.5 (actions 1–2)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 4 — Remove OpenSpec `.claude/` artifacts

**Files:**
- Delete: `.claude/commands/opsx/` (4 md files: apply, archive, explore, propose)
- Delete: `.claude/skills/openspec-{apply-change,archive-change,explore,propose}/` (4 skill dirs)

- [ ] **Step 4.1: Inventory current state**

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/
ls .claude/commands/opsx/ .claude/skills/ | grep -E "opsx|openspec"
```

Expected: 4 files under `opsx/`, 4 dirs starting with `openspec-`.

- [ ] **Step 4.2: Delete opsx commands**

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/
rm -rf .claude/commands/opsx
ls .claude/commands/
```

Expected: `opsx/` no longer listed.

- [ ] **Step 4.3: Delete openspec-* skills**

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/
rm -rf .claude/skills/openspec-apply-change .claude/skills/openspec-archive-change .claude/skills/openspec-explore .claude/skills/openspec-propose
ls .claude/skills/
```

Expected: no `openspec-*` entries.

- [ ] **Step 4.4: Commit**

```bash
cd ~/Codes/awesome_agent_tools/
git add -A Tools/AgentCrawl/.claude
git commit -m "chore(SP-0): remove .claude/{commands/opsx,skills/openspec-*}

- .claude/commands/opsx/{apply,archive,explore,propose}.md
- .claude/skills/openspec-{apply-change,archive-change,explore,propose}/

Part of recipe v1→v2 Full Rewrite migration.

Refs: docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md §6.5 (actions 3–4)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 5 — Rewrite `CLAUDE.md` to recipe v2

**Files:**
- Modify: `CLAUDE.md` (full rewrite of §2, §3, §4, Where-to-Look)

- [ ] **Step 5.1: Replace `CLAUDE.md` with v2 content**

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/
cat > CLAUDE.md <<'EOF'
# CLAUDE.md — JarvanKB

> Always-loaded operating contract for any AI agent working in this directory.
> Distilled from `docs/HarnessStack/README.md` §1–4 (recipe v2 `superpowers-repomem-sendbox-dashboard`).
> For full detail consult `docs/HarnessStack/longterm.md`. Re-read on recipe upgrade.

## 1. Identity

- **HarnessStack scale:** `solo` / horizon `long-lived` / repository type `platform`
- **Active recipe:** `superpowers-repomem-sendbox-dashboard` (**v2**, effective 2026-05-31)
- **Previous recipe:** `openspec-superpowers-repomem-sendbox-dashboard` (v1, deprecated 2026-05-31; see version-plan.md)
- **OpenSpec:** **removed** in v2 Full Rewrite — see `docs/HarnessStack/longterm.md` §Recipe v1→v2 Migration

## 2. Active Methods

| Layer | Method | Status | Notes |
|---|---|---|---|
| Execution Discipline | `Superpowers` | **active** | brainstorming, writing-plans, using-git-worktrees, executing-plans, TDD, verification-before-completion, requesting-code-review, finishing-a-development-branch |
| Repository Memory | `RepoMem` | **active** | persist + temp split; HITL merge runs **after** `finishing-a-development-branch`; **layered** (global `<root>/docs/RepoMem/persist/` + per-module `<module>/docs/RepoMem/`) |
| Harness Enhancement | `sendbox-protocol` | **active** | `<root>/docs/sendbox/` is single source of truth; subagents in side cwds write to it by path |
| Harness Enhancement | `cc-dashboard` | **active** | `<root>/docs/Dashboard/index.md` projects pending user actions; one letter → N rows; hook config `docs/HarnessStack/hooks/cc-dashboard.md` |
| Spec | `OpenSpec` | **removed in v2** | See longterm.md §Recipe v1→v2 Migration; if future Skill needs SDK-grade contract versioning, re-introduce per that module only |

## 3. Per-Task Pipeline (compressed — authoritative in `longterm.md` §Pipeline v2)

1. `RepoMem.read` — load global persist + per-module RepoMem (two layers)
2. `Superpowers.brainstorming` — clarify vague intent *(auto-judge skip on `clear` / trivial fix; subagent → `handoff.md` + Type-B dashboard row)*
3. `RepoMem.capture` — open task-level temporary docs in the relevant module's `docs/RepoMem/temp/<slug>/`
4. `Superpowers.writing-plans` — produce plan, land at `<root>/docs/superpowers/plans/` or `<module>/docs/superpowers/plans/`
5. `using-git-worktrees` + `executing-plans` + **TDD** + `RepoMem.capture` (continuous)
6. `Superpowers.verification-before-completion` — single gate; tests + evidence required before claiming done
7. `Superpowers.requesting-code-review` + `finishing-a-development-branch` — both **ask-first**
8. `RepoMem.merge` (HITL) — promote per-module decisions to global persist when warranted; then `prune` / `split`

Sendbox letters & dashboard rows are **side-effects** of the steps above, not standalone steps.

## 4. Hard Invariants

- **Single task identifier.** `<task> = <slug>` — one string across HarnessStack and RepoMem docs.
- **Add-only.** An active method never deactivates by stealth. Recipe upgrades (e.g. v1→v2 removal of OpenSpec) require a **Full Rewrite** entry in longterm.md.
- **Single verification gate.** `Superpowers.verification-before-completion` is the only mandatory pre-commit check. RepoMem, sendbox, cc-dashboard have no verification role.
- **Merge ordering.** `RepoMem.merge` runs strictly AFTER `finishing-a-development-branch`, never before, always HITL.
- **No content duplication** across per-task document sets (RepoMem temp / HarnessStack `temporary-<task>.md`). HITL reviewer rejects duplicated content.
- **Sendbox is canonical.** The main agent's `<root>/docs/sendbox/` is the only sendbox. Side cwds write to it by path — never fan out.
- **Layered RepoMem.** Subagent in `<module>/` cwd reads two layers (global persist + module memory) on `RepoMem.read`. Writes go to module unless the decision is global-scope, in which case HITL merge promotes it.
- **One letter → N dashboard rows.** Each atomic user action emits its own row.
- **Sendbox & dashboard lifecycles independent.** Burning a letter does NOT cascade-delete rows; marking a row done does NOT trigger letter cleanup.

## Where to Look

| Need | Path |
|---|---|
| Full HarnessStack contract | `docs/HarnessStack/longterm.md` |
| Day-One Init / per-task / long-term usage manual | `docs/HarnessStack/_toUser/README.md` |
| Task-level recipe patch (global scope) | `docs/HarnessStack/temporary-<task>.md` |
| Task-level recipe patch (module scope) | `<module>/docs/HarnessStack/temporary-<task>.md` |
| Repo-local cc-dashboard hook config | `docs/HarnessStack/hooks/cc-dashboard.md` |
| Know what the user owes right now | `docs/Dashboard/index.md` |
| RepoMem layout overview | `docs/RepoMem/README.md` |
| Global long-term memory (loaded by `RepoMem.read`) | `docs/RepoMem/persist/{config,version-plan}.md` + `architecture/` + `memory/` |
| Per-module memory (loaded by `RepoMem.read` in module cwd) | `<module>/docs/RepoMem/{architecture,decisions}.md` + `temp/<slug>/` |
| Frozen pre-OpenSpec decisions (D1–D7, historical) | `docs/RepoMem/persist/memory/pre-openspec-decisions.md` |
| Cross-module brainstorming design | `docs/superpowers/specs/` |
| Per-module brainstorming design | `<module>/docs/superpowers/specs/` |
| Cross-module implementation plan | `docs/superpowers/plans/` |
| Per-module implementation plan | `<module>/docs/superpowers/plans/` |
| Sendbox letters | `docs/sendbox/to<Role>/` |
| Caller-agent contract for using JarvanKB tools | `docs/sendbox/toAgent/handoff.md` (persist-lifecycle) |
| Project README (human-facing) | `README.md` |
| Top-level layout reference | `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` |
EOF
```

- [ ] **Step 5.2: Verify recipe references**

```bash
grep -E "openspec|OpenSpec|change-id|/opsx:" CLAUDE.md
```

Expected: only matches in the "removed in v2" line and the longterm.md cross-reference. No imperative usage of OpenSpec.

- [ ] **Step 5.3: Commit**

```bash
cd ~/Codes/awesome_agent_tools/
git add Tools/AgentCrawl/CLAUDE.md
git commit -m "docs(SP-0): rewrite CLAUDE.md to recipe v2

- Recipe identity: superpowers-repomem-sendbox-dashboard
- Pipeline compressed 13→8 steps (OpenSpec steps removed)
- Hard invariants updated: single verification gate (no more dual), layered RepoMem
- Where-to-Look table updated: per-module vs global paths, no openspec/

Refs: docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md §6

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 6 — Update `docs/HarnessStack/longterm.md` with v1→v2 Full Rewrite record

**Files:**
- Modify: `docs/HarnessStack/longterm.md`

- [ ] **Step 6.1: Read current longterm.md to understand structure**

```bash
head -50 docs/HarnessStack/longterm.md
```

(Hold structure in head; we'll prepend a v2 section and demote v1 to deprecated.)

- [ ] **Step 6.2: Prepend v1→v2 migration section at the top of longterm.md**

Insert after the file's frontmatter / title (find current §1 "Identity" or similar opening and insert before it):

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/

# Capture existing content
EXISTING=$(cat docs/HarnessStack/longterm.md)

cat > docs/HarnessStack/longterm.md <<'EOF'
# HarnessStack longterm — JarvanKB

> Authoritative full contract. Loaded on recipe upgrade, not every session.
> Session-level always-loaded contract = `CLAUDE.md` (distilled).

## Recipe v1 → v2 Migration (2026-05-31, Full Rewrite)

**Trigger**: scope expansion of `AgentCrawl` → `JarvanKB` 10-sub-project family; OpenSpec value assessment (subagent R8) recommended removal for thin-layer formation.

**Decision**: drop OpenSpec from the recipe. Compress pipeline 13 → 8 steps.

**Compliance path**: Full Rewrite under §Full Rewrite Conditions (this section). NOT a stealth downgrade — `add-only` invariant honored via versioned recipe migration.

**Net changes**:
| Aspect | v1 | v2 |
|---|---|---|
| Recipe ID | `openspec-superpowers-repomem-sendbox-dashboard` | `superpowers-repomem-sendbox-dashboard` |
| Active methods | 5 (incl. OpenSpec) | 4 |
| Pipeline length | 13 steps | 8 steps |
| Verification gate | dual (OpenSpec verify + Superpowers verification-before-completion) | single (Superpowers verification-before-completion) |
| Slash commands | `/opsx:propose/apply/verify/archive` | none added; rely on Skill tool |
| Change ID | `change-id` (= slug) tied to OpenSpec workspace | `slug` only (tied to git worktree + RepoMem temp dir) |
| Per-task contract docs | `openspec/changes/<id>/{proposal,design,specs,tasks}.md` | `<module>/docs/RepoMem/temp/<slug>/` + `<module>/docs/superpowers/{specs,plans}/` |
| `openspec/` workspace | required, symlinked from repo root | removed |
| `.claude/skills/openspec-*` | 4 skills installed | removed |
| `.claude/commands/opsx/` | 4 commands | removed |

**Detailed migration actions** logged in `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` §6.5.

**Reintroduction conditions**: a sub-project whose external interface becomes a versioned SDK / API consumed by third parties MAY re-introduce OpenSpec **scoped to that module only**, via a new Full Rewrite entry. Cross-cutting reintroduction requires recipe v3.

---

## Pipeline v2 (authoritative)

EOF

# Now write the canonical v2 pipeline content. Keep it concise; CLAUDE.md has the gist.
cat >> docs/HarnessStack/longterm.md <<'EOF'
The 8-step per-task pipeline (compressed view also in `CLAUDE.md` §3):

1. **`RepoMem.read`** — Subagent in `<module>/` cwd reads two layers: `<root>/docs/RepoMem/persist/` (background) + `<module>/docs/RepoMem/{architecture,decisions}.md` (actionable). Main orchestrator reads only global.

2. **`Superpowers.brainstorming`** — Clarify vague intent. Auto-judge skip on:
   - intent already `clear` and producing-the-design would be redundant
   - trivial fix (typo, single-line bugfix, dep bump)
   - pure refactor with no behavior change
   - spike / <3h exploration with throwaway code
   When spawning subagent for brainstorming, write `handoff.md` letter to `<root>/docs/sendbox/to<Role>/` and open a Type-B dashboard row.

3. **`RepoMem.capture`** — Open task-level temp docs in the relevant module: `<module>/docs/RepoMem/temp/<slug>/{requirements,architecture,decisions}.md`. Cross-module task: open at `<root>/docs/RepoMem/temp/<slug>/` instead.

4. **`Superpowers.writing-plans`** — Produce a step-by-step implementation plan. Land at `<module>/docs/superpowers/plans/YYYY-MM-DD-<slug>.md` (or root if cross-module). When subagent produces plan, send `plan-ready.md` letter back.

5. **`using-git-worktrees` + `executing-plans` + TDD + `RepoMem.capture` (continuous)** — Execute the plan in an isolated worktree. TDD discipline. Capture tacit knowledge to `temp/<slug>/decisions.md` as decisions are made. Subagent boundary at ~A-12 → blocker letter.

6. **`Superpowers.verification-before-completion`** — Single mandatory gate. Run tests + lint + typecheck + manual smoke as applicable; output evidence (commands run + outputs). No claim of "done" without this output.

7. **`Superpowers.requesting-code-review` + `finishing-a-development-branch`** — Both **ask-first**. Reviewer (subagent or user) validates against spec + plan. Finishing produces merge / PR / cleanup decision.

8. **`RepoMem.merge` (HITL)** — Promote `temp/<slug>/` lessons to durable layer. Module-scope decisions stay in `<module>/docs/RepoMem/decisions.md`. Global-scope decisions get promoted to `<root>/docs/RepoMem/persist/memory/` with `[Promoted to global ↗]` marker in module decisions. Any `from-<x>-promote-to-durable.md` letter lands here. Then `prune/split` per RepoMem hygiene.

Sendbox letters & dashboard rows are **side-effects** of the steps above, not standalone steps.

---

## Hard Invariants (v2)

(See `CLAUDE.md` §4 for the compressed version. Both must stay in sync.)

- **Single task identifier.** `<task> = <slug>`.
- **Add-only on methods, with Full Rewrite escape valve.** Methods do not silently deactivate. Recipe migrations require a Full Rewrite entry in this file (as the v1→v2 entry above demonstrates).
- **Single verification gate.** `Superpowers.verification-before-completion`. No replacements.
- **Merge ordering.** `RepoMem.merge` AFTER `finishing-a-development-branch`, HITL, never before.
- **No content duplication** across per-task doc sets.
- **One sendbox per project.** `<root>/docs/sendbox/` only. Side cwds write by path.
- **Layered RepoMem.** Module reads two layers, writes one; HITL promotes module → global.
- **One letter → N dashboard rows.** Independent lifecycles.
- **No silent invariant skips.** Pipeline ordering, merge gates, verification topology are recipe invariants. Exceptions require a declared `Recipe Invariant Exception` in the relevant `temporary-<slug>.md` with reason + compensating action.

---

## Full Rewrite Conditions

A recipe Full Rewrite (versioned migration like v1→v2) is allowed when:

- Strategic scope changes (e.g. monolithic tool → multi-sub-project family)
- A method's value/cost ratio becomes net negative for the project's formation (e.g. OpenSpec for thin-layer projects per R8 analysis)
- Cross-platform constraints force a structural change

Each Full Rewrite MUST:
- Document the trigger, decision, net changes, and reintroduction conditions in this file
- Reference the design/spec that motivated it
- Be committed atomically with the code/doc changes that effect the migration

---

## Related Documents

- `CLAUDE.md` — distilled session-load contract
- `docs/HarnessStack/_toUser/README.md` — user-facing manual
- `docs/HarnessStack/hooks/` — repo-local hook configs (e.g. cc-dashboard)
- `docs/RepoMem/persist/version-plan.md` — phase plan, recipe version history
- `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` — v2 migration design

---

## Archival: v1 Reference (DEPRECATED)

The v1 recipe `openspec-superpowers-repomem-sendbox-dashboard` was active 2026-05-26 → 2026-05-31. Its 13-step pipeline added OpenSpec steps 3 (explore/propose), 5 (consume specs+tasks), 8b (verify), and 11 (archive) — these are now obsolete.

The original v1 longterm.md content is preserved below for historical reference only. **Do not follow it.**

---

EOF

# Append the original content as historical archive
echo "$EXISTING" >> docs/HarnessStack/longterm.md
```

- [ ] **Step 6.3: Sanity check**

```bash
wc -l docs/HarnessStack/longterm.md
grep -c "v2" docs/HarnessStack/longterm.md
grep -c "DEPRECATED" docs/HarnessStack/longterm.md
```

Expected: file got bigger (added migration section + new pipeline + archived old); v2 mentioned several times; DEPRECATED appears at least once.

- [ ] **Step 6.4: Commit**

```bash
cd ~/Codes/awesome_agent_tools/
git add Tools/AgentCrawl/docs/HarnessStack/longterm.md
git commit -m "docs(SP-0): longterm.md → recipe v2 with Full Rewrite migration record

- Prepended Recipe v1→v2 Migration section (trigger, decision, net changes)
- Authoritative v2 8-step pipeline
- Hard invariants v2 (single verification gate, layered RepoMem)
- Full Rewrite Conditions documented
- v1 content preserved verbatim below as DEPRECATED archive

Refs: docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md §6.2–6.4

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 7 — Update `docs/HarnessStack/README.md` + `_toUser/README.md`

**Files:**
- Modify: `docs/HarnessStack/README.md` (recipe identity)
- Modify: `docs/HarnessStack/_toUser/README.md` (8-step pipeline; remove OpenSpec section)

- [ ] **Step 7.1: Update `docs/HarnessStack/README.md`**

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/

# Replace recipe identity line(s) and any OpenSpec mentions
# (Use sed for targeted edits since this file is short)

# First inspect current state
head -30 docs/HarnessStack/README.md
```

- [ ] **Step 7.2: Apply targeted edits via sed**

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/

# Replace recipe ID
sed -i 's|openspec-superpowers-repomem-sendbox-dashboard|superpowers-repomem-sendbox-dashboard|g' docs/HarnessStack/README.md

# Replace project name
sed -i 's|AgentCrawl|JarvanKB|g' docs/HarnessStack/README.md

# Show diff to user for sanity
git diff docs/HarnessStack/README.md | head -40
```

If the sed edits leave OpenSpec-specific paragraphs orphaned (e.g. a section explaining `/opsx:*` commands), open the file in Edit and remove those paragraphs explicitly. After this step:

```bash
grep -n "openspec\|OpenSpec\|/opsx:\|change-id" docs/HarnessStack/README.md
```

Expected: zero matches (or only matches in a "previously included OpenSpec; removed in v2" cross-reference).

If any uncovered orphans, fix with Edit tool — replace the orphan paragraph with a single sentence: `> OpenSpec removed in recipe v2. See longterm.md §Recipe v1→v2 Migration.`

- [ ] **Step 7.3: Update `docs/HarnessStack/_toUser/README.md`**

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/

# Same global substitutions
sed -i 's|openspec-superpowers-repomem-sendbox-dashboard|superpowers-repomem-sendbox-dashboard|g' docs/HarnessStack/_toUser/README.md
sed -i 's|AgentCrawl|JarvanKB|g' docs/HarnessStack/_toUser/README.md

# Inspect remaining OpenSpec references
grep -n "openspec\|OpenSpec\|/opsx:\|change-id\|13 步\|13-step" docs/HarnessStack/_toUser/README.md
```

For each match, open in Edit and either delete the line/section (if purely OpenSpec) or rewrite to v2 equivalent. Specifically:
- Replace "13 步 pipeline" / "13-step" → "8 步 pipeline" / "8-step"
- Replace `/opsx:propose` references with `Skill tool → superpowers:writing-plans`
- Delete sections titled "OpenSpec workflow" or similar

- [ ] **Step 7.4: Verify both files**

```bash
grep -rn "openspec\|OpenSpec\|/opsx:\|change-id\|13 步\|13-step" docs/HarnessStack/README.md docs/HarnessStack/_toUser/README.md
```

Expected: 0 matches (or only intentional cross-references to "previously…removed in v2").

- [ ] **Step 7.5: Commit**

```bash
cd ~/Codes/awesome_agent_tools/
git add Tools/AgentCrawl/docs/HarnessStack/README.md Tools/AgentCrawl/docs/HarnessStack/_toUser/README.md
git commit -m "docs(SP-0): HarnessStack README + _toUser README → v2

- Recipe ID superpowers-repomem-sendbox-dashboard
- Project name AgentCrawl → JarvanKB
- Pipeline 13→8 steps; OpenSpec sections removed
- Cross-reference to longterm.md §Recipe v1→v2 Migration for history

Refs: docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md §6.5 actions 7–8

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 8 — Update RepoMem persist docs (config + version-plan + runbook + pre-openspec banner)

**Files:**
- Modify: `docs/RepoMem/persist/config.md`
- Modify: `docs/RepoMem/persist/version-plan.md`
- Modify: `docs/RepoMem/persist/memory/runbook.md` (remove §0)
- Modify: `docs/RepoMem/persist/memory/pre-openspec-decisions.md` (add v2 banner)

- [ ] **Step 8.1: Update `config.md` recipe reference + project name**

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/

sed -i 's|openspec-superpowers-repomem-sendbox-dashboard|superpowers-repomem-sendbox-dashboard|g' docs/RepoMem/persist/config.md
sed -i 's|AgentCrawl|JarvanKB|g' docs/RepoMem/persist/config.md

# Verify
grep -E "recipe|openspec|AgentCrawl" docs/RepoMem/persist/config.md
```

Expected: only recipe v2 line and any "OpenSpec was removed" cross-ref.

- [ ] **Step 8.2: Replace `version-plan.md` content with v2 phase plan**

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/
cat > docs/RepoMem/persist/version-plan.md <<'EOF'
# version-plan.md

> Long-term version / roadmap notes for JarvanKB.
> Explicitly named in `docs/HarnessStack/longterm.md` §Related Documents.

## Recipe version history

| Version | Recipe ID | Effective | Notes |
|---|---|---|---|
| v1 | `openspec-superpowers-repomem-sendbox-dashboard` | 2026-05-26 → 2026-05-31 | Bootstrap. Deprecated via Full Rewrite. |
| **v2** | `superpowers-repomem-sendbox-dashboard` | 2026-05-31 → | OpenSpec removed for thin-layer formation. See longterm.md §Recipe v1→v2 Migration. |

## Project rename

- **AgentCrawl** (2026-05-26 → 2026-05-31): original scope = Zhihu + Bilibili crawlers
- **JarvanKB** (2026-05-31 → ): scope expanded to crawl + ingester + future knowledge tooling; personal-brand naming for OSS release

Physical rename `Tools/AgentCrawl/` → `Tools/JarvanKB/` performed in a separate session.

## Current phase

- **SP-0 in progress** (2026-05-31): repo skeleton + HarnessStack v2 migration. Design in `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md`.

## Planned sub-projects (10 v1 + 1 v1+)

| ID | Path | Name | Phase enter gate |
|---|---|---|---|
| SP-1 | `Service/crawl/cookie-manager/` | CookieManager (fork CookieCloud + hook) | SP-0 done |
| SP-2 | `Engine/zhihu/` | Zhihu Engine | SP-0 done + SP-1 protocol agreed |
| SP-3 | `Skill/crawl/zhihu-crawl/` | Zhihu Skill | SP-2 implemented |
| SP-4a | `Engine/bilibili/` | Bilibili Engine | SP-0 done; BN docker reachable |
| SP-4b | `Skill/crawl/bilibili-crawl/` | Bilibili Skill | SP-4a implemented |
| SP-5a | `Service/crawl/zhihu-watcher/` | Zhihu favorites watcher | SP-2 implemented |
| SP-5b | `Service/crawl/bilibili-watcher/` | Bilibili favorites watcher | SP-4a implemented |
| SP-6 | `Skill/ingester/crawl-md-saver/` | CrawlMdSaver Skill | SP-3 / SP-4b crawl skills register |
| SP-7 | `Service/ingester/thino-ingester/` | Thino Ingester | SP-6 implemented |
| SP-8 (v1+) | `Skill/router/web-search/` | Web Search Router | v1 done; Zhihu API key acquired |

## v1.0 OSS release plan

When all v1 sub-projects (SP-0 through SP-7) verified end-to-end:

1. Choose Organization name (candidates: `JarvanKB`, `Jarvan`, `JarvanWorks`)
2. Execute fractal split per `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` §10:
   - `git filter-repo --subdirectory-filter <module>/` per sub-project
   - Inherit `docs/HarnessStack/` into each child
   - Initialize child-repo own `docs/{sendbox,Dashboard,RepoMem/persist}/`
   - Create new GitHub repo under Organization, push
3. Mark monorepo (this repo) as umbrella for HarnessStack template + cross-module integration tests

## Compatibility / upgrade notes

- HarnessStack recipe upgrades: see `longterm.md` §Full Rewrite Conditions
- ASR strategy (D3 in `pre-openspec-decisions.md`) reviewed in R5 (2026-05-31): **switched from 通义听悟 to BiliNote/bcut for v1**. D3 marked as superseded but not deleted (historical record).

## How this doc is updated

Append-most. Major changes (phase scope reshuffle, recipe upgrade, project rename) go through `RepoMem.merge` HITL review.
EOF
```

- [ ] **Step 8.3: Remove `runbook.md` §0 (OpenSpec symlink section)**

The §0 section describes the OpenSpec symlink dance. In v2 it's obsolete. Read current state:

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/
head -30 docs/RepoMem/persist/memory/runbook.md
```

Use Edit tool to remove the entire `## 0. 项目布局须知（OpenSpec workspace 软链）` section through the line before `## 1. 环境变量清单`. Replace with a single line cross-reference if desired:

```markdown
> Note: a `§0 OpenSpec workspace` section existed here in v1; OpenSpec was removed in recipe v2. See `docs/HarnessStack/longterm.md §Recipe v1→v2 Migration`.
```

Verify after edit:
```bash
grep -n "OpenSpec\|openspec\|OPENSPEC_DIR_NAME" docs/RepoMem/persist/memory/runbook.md
```

Expected: only the cross-reference line.

- [ ] **Step 8.4: Add v2 banner to `pre-openspec-decisions.md`**

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/

# Prepend a banner to existing file
EXISTING=$(cat docs/RepoMem/persist/memory/pre-openspec-decisions.md)
cat > docs/RepoMem/persist/memory/pre-openspec-decisions.md <<EOF
> ⚠️ **Post-v2 status banner (2026-05-31)**: HarnessStack recipe moved to v2; OpenSpec is **no longer active**. The filename "pre-openspec-decisions" remains historically accurate. D3 (通义听悟 selection) was **superseded** by R5 finding (use BiliNote + bcut). Other D-decisions (D1, D2, D4–D7) remain technically valid where they apply.

$EXISTING
EOF
```

- [ ] **Step 8.5: Verify all four files**

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/
echo "=== config.md ==="; grep -n "recipe\|openspec\|JarvanKB\|AgentCrawl" docs/RepoMem/persist/config.md
echo "=== version-plan.md ==="; head -5 docs/RepoMem/persist/version-plan.md
echo "=== runbook.md ==="; grep -n "OpenSpec\|openspec" docs/RepoMem/persist/memory/runbook.md
echo "=== pre-openspec-decisions.md ==="; head -3 docs/RepoMem/persist/memory/pre-openspec-decisions.md
```

Expected: all show v2-aware content; no stale "use openspec list" instructions; `pre-openspec-decisions.md` banner visible at top.

- [ ] **Step 8.6: Commit**

```bash
cd ~/Codes/awesome_agent_tools/
git add Tools/AgentCrawl/docs/RepoMem/persist/
git commit -m "docs(SP-0): RepoMem persist updates for recipe v2 + project rename

- config.md: recipe ID v2, project JarvanKB
- version-plan.md: full rewrite — v1→v2 history, AgentCrawl→JarvanKB rename, 10 v1 sub-projects + SP-8 v1+, OSS release plan, recipe upgrade pointers
- memory/runbook.md: §0 OpenSpec symlink section removed (obsolete)
- memory/pre-openspec-decisions.md: post-v2 status banner; D3 marked superseded by R5 (BN+bcut)

Refs: docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md §6.5 actions 9–11

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 9 — Clean Dashboard + add SP-0 closure rows

**Files:**
- Modify: `docs/Dashboard/index.md`

- [ ] **Step 9.1: Inspect current Dashboard**

```bash
cat docs/Dashboard/index.md
```

Currently has UN-001 (OpenSpec install, archived), UN-002 (RufloAgent obsoleted, archived), UN-003 (start new orchestrator session, open), UN-004 (Aliyun credentials, open).

- [ ] **Step 9.2: Rewrite Dashboard to reflect SP-0 completion + new v2 state**

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/

cat > docs/Dashboard/index.md <<'EOF'
# User Now — Pending Actions

> Single source of truth for "what the user needs to do next" in JarvanKB.
> Authors: any agent session may append. Reader: user.
> Protocol contract: `~/.claude/skills/cc-dashboard/SKILL.md`
> Repo-local hook (language policy, mark-done owner, triggers): `docs/HarnessStack/hooks/cc-dashboard.md`

## Active

| ID | Type | Action | Where (detail) | Blocker for | Since | Status |
|---|---|---|---|---|---|---|
| UN-005 | B | 在独立 session 中执行物理改名：`mv Tools/AgentCrawl Tools/JarvanKB`，确认 git mv 路径无丢失，commit | `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` §2 | SP-1 brainstorming 启动（路径稳定后） | 2026-05-31 | open |
| UN-006 | F | 决定 v1.0 GitHub Organization 名（候选：JarvanKB / Jarvan / JarvanWorks）— 此项非阻塞 v1 实现，可推迟到 v1 完成度临近 | `docs/RepoMem/persist/version-plan.md` §v1.0 OSS release plan | v1.0 切分 | 2026-05-31 | open |
| UN-007 | B | 起一个独立 Claude Code session（cwd = `Tools/AgentCrawl/`），第一句话告诉它：`read docs/sendbox/toSP0Impler/handoff.md and execute the plan it references`。等它在 `docs/sendbox/toOrchestrator/` 写出 `from-sp0impler-sp0-done.md` 或 blocker letter 后告知 orche | `docs/sendbox/toSP0Impler/handoff.md` | SP-1 brainstorming 启动 | 2026-05-31 | open（impler 完成 SP-0 即可归档）|

## Archive

| ID | Action | Done | By |
|---|---|---|---|
| UN-001 | 授权全局安装 OpenSpec CLI（`npm i -g @fission-ai/openspec` → v1.3.1） | 2026-05-27 | bootstrap session |
| UN-002 | 把 handoff 带到 `~/Codes/AgentCrawlers/` 起 ruflo 会话 — **obsoleted**：2026-05-30 决定继续在当前 repo 开发，迁移取消 | 2026-05-30 | bootstrap session |
| UN-003 | 起新 orchestrator 会话，按 handoff §7 执行 — **completed**：scope 扩展到 10 子项目，SP-0 design + plan 已落盘 | 2026-05-31 | orche session 2 |
| UN-004 | 确认已开通阿里云 AK/SK + Tingwu + OSS bucket — **obsoleted**：R5 (2026-05-31) 决定切换 BN+bcut，v1 不再依赖 Aliyun 凭据 | 2026-05-31 | orche session 2 |
EOF
```

- [ ] **Step 9.3: Verify**

```bash
grep -c "UN-" docs/Dashboard/index.md
```

Expected: 6 matches (2 active + 4 archive).

- [ ] **Step 9.4: Commit**

```bash
cd ~/Codes/awesome_agent_tools/
git add Tools/AgentCrawl/docs/Dashboard/index.md
git commit -m "docs(SP-0): Dashboard cleanup for v2 state

- Archive UN-003 (orchestrator session started, SP-0 design/plan landed)
- Archive UN-004 (Aliyun credentials obsoleted by BN+bcut decision in R5)
- Add UN-005 (physical repo rename, user action in separate session)
- Add UN-006 (GitHub Organization name decision, non-blocking, v1.0 timing)

Refs: docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md §6.5 action 12

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 10 — Write top-level `README.md`

**Files:**
- Modify (rewrite): `README.md`

- [ ] **Step 10.1: Read current README**

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/
cat README.md
```

(Inspect to know what to replace — current likely says "AgentCrawl Phase 1 docs only".)

- [ ] **Step 10.2: Rewrite README to JarvanKB v2 state**

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/
cat > README.md <<'EOF'
# JarvanKB

> **Status**: SP-0 in progress (2026-05-31). Skeleton + recipe v2 land first; sub-projects SP-1 through SP-7 follow.
> **Recipe**: `superpowers-repomem-sendbox-dashboard` (v2, OpenSpec removed)
> **Previous name**: `AgentCrawl` (deprecated 2026-05-31)

JarvanKB is a personal knowledge-base tooling family. It combines:

- **Crawl layer** — pull content from sources (Zhihu, Bilibili)
- **Ingester layer** — digest and integrate content with user notes (DocSaver, ThinoIngester)
- **Service layer** — long-running pollers (cookie manager, favorites watchers)

The repository is a **monorepo with sub-project boundaries**. Each sub-project under `Engine/`, `Skill/`, `Service/` is self-contained and ready to split out into its own OSS repo at v1.0 release.

## Quick map

```
docs/                          # global governance (HarnessStack, RepoMem persist, sendbox, Dashboard, superpowers/specs)
Engine/                        # pure libraries
├── common/                    # LLMClient (litellm) + BaseSkill + cookie reader
├── zhihu/                     # SP-2
└── bilibili/                  # SP-4a
Skill/                         # agent-facing skills
├── crawl/{zhihu-crawl,bilibili-crawl}/
├── ingester/{crawl-md-saver}/
└── router/                    # SP-8 v1+ placeholder
Service/                       # long-running services
├── crawl/{cookie-manager,zhihu-watcher,bilibili-watcher}/
└── ingester/{thino-ingester}/
config/                        # LLM provider config (.yaml; secrets in .env)
```

## How to navigate

| You want… | Read |
|---|---|
| The operating contract (always-loaded) | `CLAUDE.md` |
| Full HarnessStack governance | `docs/HarnessStack/longterm.md` |
| The roadmap and recipe history | `docs/RepoMem/persist/version-plan.md` |
| What the user owes right now | `docs/Dashboard/index.md` |
| Per-sub-project entry | `<module>/docs/README.md` |
| SP-0 (this skeleton) design | `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` |

## Status

- SP-0 (skeleton + recipe v2): **in progress**
- SP-1 (CookieManager): pending SP-0 completion
- SP-2 through SP-7: pending
- SP-8 (web-search router): v1+ candidate

## License

(TBD — to be added before v1.0 OSS release)
EOF
```

- [ ] **Step 10.3: Commit**

```bash
cd ~/Codes/awesome_agent_tools/
git add Tools/AgentCrawl/README.md
git commit -m "docs(SP-0): top-level README → JarvanKB v2

- New project name, recipe v2 identity
- Quick map of monorepo layout (Engine/Skill/Service)
- Navigation table for governance docs
- Status of sub-projects (SP-0 in progress, others pending)

Refs: docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md §1, §3

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 11 — Final sweep + verification + sanity grep

**Files:** none modified; verification only.

- [ ] **Step 11.1: Grep sweep — no stale OpenSpec references outside historical files**

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/
grep -rn "openspec\|OpenSpec\|/opsx:\|change-id" --include="*.md" . \
  | grep -v "docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md" \
  | grep -v "docs/superpowers/plans/2026-05-31-SP-0-jarvankb-skeleton.md" \
  | grep -v "docs/HarnessStack/longterm.md" \
  | grep -v "docs/RepoMem/persist/version-plan.md" \
  | grep -v "docs/RepoMem/persist/memory/pre-openspec-decisions.md" \
  | grep -v "docs/RepoMem/persist/memory/runbook.md" \
  | grep -v "docs/Dashboard/index.md"
```

Expected: **empty output** (zero matches). The whitelist above covers intentional historical mentions.

If any matches appear, open in Edit and either delete or move to a `> Previously…removed in v2` comment.

- [ ] **Step 11.2: Grep sweep — no stale `AgentCrawl` outside historical files**

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/
grep -rn "AgentCrawl" --include="*.md" . \
  | grep -v "docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md" \
  | grep -v "docs/superpowers/plans/2026-05-31-SP-0-jarvankb-skeleton.md" \
  | grep -v "docs/HarnessStack/longterm.md" \
  | grep -v "docs/RepoMem/persist/version-plan.md" \
  | grep -v "docs/Dashboard/index.md" \
  | grep -v "docs/sendbox/toOrchestrator/handoff.md"
```

Expected: **empty output**. Whitelist covers SP-0 docs that document the rename + the persisting handoff letter (which user will burn upon next milestone-done).

- [ ] **Step 11.3: Verify final directory tree matches design §3**

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/
ls -d Engine/{common,zhihu,bilibili} \
      Skill/{crawl/zhihu-crawl,crawl/bilibili-crawl,ingester/crawl-md-saver,router} \
      Service/{crawl/cookie-manager,crawl/zhihu-watcher,crawl/bilibili-watcher,ingester/thino-ingester} \
      docs/{HarnessStack,RepoMem/persist,sendbox,Dashboard,superpowers/specs,superpowers/plans} \
      config 2>&1 | wc -l
```

Expected: 22 (all paths exist; 0 errors).

If any path missing: list and fix.

- [ ] **Step 11.4: Verify removed paths are gone**

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/
for p in openspec docs/openspec .claude/commands/opsx .claude/skills/openspec-apply-change .claude/skills/openspec-archive-change .claude/skills/openspec-explore .claude/skills/openspec-propose; do
  if [ -e "$p" ]; then echo "STILL PRESENT: $p"; fi
done
```

Expected: no output (all paths gone).

- [ ] **Step 11.5: Verify CLAUDE.md is loadable + coherent**

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/
head -20 CLAUDE.md
grep -c "v2" CLAUDE.md
```

Expected: opening shows JarvanKB + recipe v2; "v2" appears multiple times.

- [ ] **Step 11.6: Git status sanity check**

```bash
cd ~/Codes/awesome_agent_tools/
git status --short Tools/AgentCrawl/
git log --oneline -15 -- Tools/AgentCrawl/
```

Expected:
- `git status` clean for `Tools/AgentCrawl/` (only the gstack pre-existing M from before)
- `git log` shows ~10 SP-0 commits on top of `a3522b2 feat(AgentCrawl): scaffold...`

- [ ] **Step 11.7: Write a closure letter for the inheritance handoff**

The current `docs/sendbox/toOrchestrator/handoff.md` says "burn this letter when first `milestone-done.md` is logged". SP-0 completion is the first milestone.

```bash
cd ~/Codes/awesome_agent_tools/Tools/AgentCrawl/

cat > docs/sendbox/toOrchestrator/from-orche-sp0-done.md <<'EOF'
> from: orchestrator session 2 (2026-05-31)
> recipient: any future orchestrator
> mode: milestone-done
> purpose: confirm SP-0 completion + close inheritance handoff
> lifecycle: persist until next milestone, then archive

# SP-0 milestone-done

## What was delivered

- 10 sub-project directories seeded under Engine/Skill/Service with stub docs
- LLMClient skeleton in Engine/common with litellm config example
- OpenSpec fully removed (workspace + root symlink + .claude artifacts)
- Recipe v1 → v2 Full Rewrite migration documented in longterm.md
- CLAUDE.md, version-plan.md, runbook.md, Dashboard updated to v2 state
- Top-level README rewritten for JarvanKB

## What remains

- UN-005: user repo-rename in separate session (non-blocking for next steps)
- UN-006: GitHub Org name (non-blocking, can wait to v1.0 timing)
- SP-1 brainstorming next (CookieManager — fork CookieCloud + hook mechanism)

## Disposition of previous handoff letter

`docs/sendbox/toOrchestrator/handoff.md` (inheritance letter from bootstrap session) can be removed per its own §10 lifecycle clause.
EOF

# Remove the original inheritance handoff per its §10 lifecycle clause
git rm docs/sendbox/toOrchestrator/handoff.md
```

- [ ] **Step 11.8: Final SP-0 closure commit**

```bash
cd ~/Codes/awesome_agent_tools/
git add Tools/AgentCrawl/docs/sendbox/toOrchestrator/
git commit -m "docs(SP-0): milestone-done — close inheritance handoff

- Add from-orche-sp0-done.md confirming SP-0 deliverables
- Burn the inheritance handoff.md per its §10 lifecycle clause

Refs: docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md §11

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

- [ ] **Step 11.9: Tag SP-0 completion (optional but useful for v1.0 release later)**

```bash
cd ~/Codes/awesome_agent_tools/
git tag -a sp0-complete -m "SP-0 skeleton + recipe v2 landed"
git log --oneline -1 sp0-complete
```

Expected: tag points at the milestone-done commit.

---

## Self-Review (run after writing this plan)

### 1. Spec coverage

Checked design.md §1–§13 against tasks:
- §1 background: covered narratively in README + version-plan (Tasks 8, 10)
- §2 rename: design.md captures the decision; physical rename is UN-005, outside plan scope (correct)
- §3 directory skeleton: Task 1
- §4 layered governance: encoded in CLAUDE.md (Task 5) + longterm.md (Task 6) + RepoMem stubs (Task 1)
- §5 sub-module docs structure: Task 1 stubs cover required files; templates kept minimal because real content lands per-SP later
- §6 recipe v2: Tasks 3, 4, 5, 6, 7, 8
- §7 SP分解表: documented in version-plan (Task 8) + per-stub README (Task 1)
- §8 LLMClient: Task 2
- §9 OSS切分协议: documented in version-plan (Task 8), no code action in SP-0 (correct)
- §10 未决项: tracked in Dashboard UN-006 (Task 9)
- §11 实施顺序: this plan is the elaboration of §11 A–G (A is UN-005)
- §12 自审: this section
- §13 后续: Task 11 milestone-done

### 2. Placeholder scan

No "TBD" / "TODO" / "fill in later" in plan steps themselves. Stub files created by Task 1 do contain `(TBD)` markers — this is intentional and correct for module placeholders that get filled by later sub-project brainstorming.

### 3. Type consistency

- `Engine/common/src/llm_client.py` class `LLMClient` — `complete(messages, **kwargs) -> str`, `stream(messages, **kwargs) -> Iterator[str]`, `to_opencode() -> Any` — referenced consistently in `interface.md` (Task 2) and `config/llm.yaml.example` schema.
- Recipe ID `superpowers-repomem-sendbox-dashboard` — consistent across CLAUDE.md (Task 5), longterm.md (Task 6), HarnessStack README (Task 7), config.md (Task 8).
- Path conventions: `<module>/docs/RepoMem/` consistent everywhere.

No inconsistencies found.

### 4. Scope check

This plan delivers a working, testable artifact on its own: a v2-compliant repo skeleton ready to host SP-1 brainstorming. Each task commits independently, so progress is bisectable. The plan does NOT cover SP-1..SP-7 implementation (correctly out of scope; each gets its own design + plan).
