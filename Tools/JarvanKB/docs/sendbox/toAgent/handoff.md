> from: JarvanKB maintainer
> recipient: any calling agent (Hermes / Claude Code / scripted client)
> purpose: stable consumer-facing contract for using JarvanKB
> lifecycle: persist — promote to durable docs only via RepoMem.merge HITL

# JarvanKB — Caller Agent Handoff

> **Placeholder.** Maintainer will fill this in once Phase 2 scripts exist.
> Until then any calling agent must NOT attempt to run JarvanKB tools —
> see `../../../README.md` "Phase 1" section.

## What lives here

Letters under `docs/sendbox/toAgent/` describe **how a caller agent uses
JarvanKB**:

- this `handoff.md` — single-recipient entry letter, stable contract
- future `from-maintainer-<topic>.md` letters — capability additions, breaking changes, deprecations

Because the lifecycle is `persist`, this directory is NOT subject to the
default `burn` letter cleanup. Any change here must flow through
`RepoMem.merge` HITL, same gate as `persist/` docs.

## What does NOT live here

- HarnessStack / RepoMem internal task coordination (those go in `to<OtherRole>/`)
- Transient stop-and-ask between sessions (those use the standard letter lifecycle)
- Implementation details (those live in `docs/RepoMem/persist/architecture/`)

## Sections to fill (Phase 2)

1. **Trigger conditions** — when a caller agent should reach for JarvanKB
2. **Tool catalog** — each script's input / output contract
3. **Pre-flight credential check** — env vars to verify before any call
4. **Fallback policy** — what to do when Tingwu / Playwright CDP fails
5. **Output format** — markdown frontmatter spec, json schema
