# Plan — grill-with-docs-restore

> Lane: fast
> Task: `grill-with-docs-restore`
> Owner: GrillDocsImpler (child of root orche g4; handoff `docs/sendbox/toGrillDocsImpler/handoff.md`)
> Date: 2026-06-11
> `specs/` omitted — fast lane; design settled in compressed brainstorm with the user (3 AskUserQuestion decisions, recorded below as D1–D3).

## Goal

Replace the JarvanKB-adapted `grill-with-docs` skill with the authentic community original
(Matt Pocock's CONTEXT.md/ADR-based grilling skill), reconcile the governance docs that
referenced the adapted version as a design-gate, then run the community skill to produce
JarvanKB's project-level grilled context documents.

## Upstream source (gate 4.1 — confirmed)

- Repo: `github.com/mattpocock/skills`, path `skills/engineering/grill-with-docs/`
- Pinned commit: `e3b90b5238f38cdea5996e16861dcae28ef52eda` (2026-05-28)
- Files: `SKILL.md` (88 lines) + `CONTEXT-FORMAT.md` (60) + `ADR-FORMAT.md` (47)
- Corroboration: aihero.dev changelog ("Ubiquitous Language → /grill-with-docs", author Matt
  Pocock), skillsmp.com / agentcookbooks.com / claudemarketplaces.com all index the same repo;
  matches the adapted skill's credit line "the community grill-with-docs (ADR/CONTEXT.md-based)".

## Decisions (user-ratified 2026-06-11, compressed brainstorm)

### D1 — §3 reconciliation = option (b) rename-preserve

The adapted skill (full-lane design-gate, CodeTeam #4 prop 4) is RENAMED to `grill-design`
(`.claude/skills/grill-design/SKILL.md`), semantics unchanged. The name `grill-with-docs` is
freed for the community original. CLAUDE.md §3 + §Where-to-Look and longterm.md (§Pipeline v2
step 2 note, §Lane Tiering table) re-point the design-gate references to `grill-design`.
No stealth deactivation: #4 prop 4 survives under the new name; this Dn records the rename.

### D2 — ADR write-sink redirected to RepoMem

The community skill files are installed VERBATIM (including `ADR-FORMAT.md`). But when running
the skill in JarvanKB, decision-worthy outcomes that pass the skill's 3-condition ADR test go to
RepoMem (`<module>/docs/RepoMem/temp/<slug>/decisions.md` → HITL promote), NOT `docs/adr/`.
Rationale: CLAUDE.md §4 — RepoMem is the single durable decision memory; CLAUDE.md overrides
skill defaults (instruction priority). `docs/adr/` is not created.

### D3 — Multi-context layout: CONTEXT-MAP.md + per-module CONTEXT.md

JarvanKB uses the upstream multi-context structure: root `CONTEXT-MAP.md` (contexts +
relationships) + one `CONTEXT.md` per top-level module group: `Engine/CONTEXT.md`,
`Service/CONTEXT.md`, `Skill/CONTEXT.md`. Glossary-only per CONTEXT-FORMAT.md (no
implementation details). CONTEXT docs complement RepoMem: CONTEXT.md = ubiquitous-language
glossary; RepoMem = architecture rationale + decisions + gotchas. No content duplication.

## Steps

1. ~~Worktree off local `feat/agentcrawl-bootstrap`~~ (done: `.worktrees/grill-with-docs-restore`)
2. This plan doc.
3. `git mv .claude/skills/grill-with-docs .claude/skills/grill-design`; update frontmatter
   `name:` + H1 title (content otherwise unchanged).
4. Write the 3 upstream files verbatim into `.claude/skills/grill-with-docs/`; verify the
   `.gitignore` `!.claude/` re-include keeps both skill dirs tracked.
5. Governance reconciliation per D1 (+ one-line D2 note where the skill is wired).
6. Run the community grill in JarvanKB root → `CONTEXT-MAP.md` + 3 module `CONTEXT.md` (D3),
   grounded in RepoMem persist + specs + module trees; interactive rounds with the user for
   ambiguous terms.
7. Verification-before-completion: (a) skill files valid + tracked (agentskills.io-compliant
   frontmatter; loads as project skill); (b) no dangling `grill-with-docs`-as-design-gate
   reference in CLAUDE.md/longterm.md; (c) CONTEXT docs cite real modules/terms only.
8. Pathspec-scoped commits → finishing-a-development-branch (ask-first) → RepoMem.merge (HITL,
   impler-owned) → done letter `toOrchestrator/from-grilldocsimpler-done.md`.
