#!/usr/bin/env bash
# Deploy this one SKILL.md to the four agent-CLI skill directories (one source, many targets).
# agentskills.io is the shared standard — no per-runtime format fork.
set -euo pipefail
SRC="$(cd "$(dirname "$0")/.." && pwd)"
NAME="zhihu-crawl"
for dir in "$HOME/.claude/skills" "$HOME/.codex/skills" "$HOME/.openclaw/skills" "$HOME/.hermes/skills"; do
  mkdir -p "$dir/$NAME"
  ln -sf "$SRC/SKILL.md" "$dir/$NAME/SKILL.md"
  echo "linked $dir/$NAME/SKILL.md -> $SRC/SKILL.md"
done
