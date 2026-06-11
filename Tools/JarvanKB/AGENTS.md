# AGENTS.md - JarvanKB Codex Entry Point

Codex sessions in this directory must treat `CLAUDE.md` as the authoritative always-loaded project contract.
Read it before task work, then follow `docs/HarnessStack/longterm.md` when full recipe detail is needed.

Runtime mapping: Superpowers and project skills may mention Claude Code tools. Use the Codex mapping in
`~/.codex/superpowers/skills/using-superpowers/references/codex-tools.md`:
`Task` -> `spawn_agent`, `TodoWrite` -> `update_plan`, and file/shell actions -> native Codex tools.

Important project caveat: JarvanKB recipe v2 removed OpenSpec. Do not use `openspec-*` skills here unless a
future recipe rewrite explicitly reintroduces OpenSpec for a scoped module.
