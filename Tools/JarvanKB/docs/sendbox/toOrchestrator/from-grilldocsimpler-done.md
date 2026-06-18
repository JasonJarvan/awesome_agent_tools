> from: GrillDocsImpler (child of root orche g4)
> to: root orchestrator
> re: task `grill-with-docs-restore` — DONE
> lifecycle: burn after root reads
> date: 2026-06-18

# Done — grill-with-docs-restore

All three deliverables landed and merged into local `feat/agentcrawl-bootstrap`
(merge commit `5d34239`, --no-ff). Branch + worktree cleaned up.

## 1. Community source (gate 4.1)

Authentic upstream identified with confidence: **Matt Pocock, `mattpocock/skills`**,
path `skills/engineering/grill-with-docs/`, pinned commit `e3b90b5`. Corroborated by
aihero.dev changelog + skillsmp/agentcookbooks/claudemarketplaces indexes; matches the
adapted skill's own credit line. Installed **verbatim** (md5-verified against source):
`SKILL.md` + `CONTEXT-FORMAT.md` + `ADR-FORMAT.md`.

## 2. Skill replaced + loads

- `.claude/skills/grill-with-docs/` is now the **community original** (glossary/CONTEXT.md
  producer). `.claude/skills/grill-design/` holds the **former adapted design-gate**
  (semantics unchanged, just renamed).
- **Live-verified both load**: a headless `claude -p` session in the worktree listed both
  with correct descriptions; and this session's own skill list now shows `grill-design`
  (design-gate) + `grill-with-docs` (community "Grilling session… CONTEXT.md").
- `.gitignore` `!.claude/` re-include keeps all four files tracked.

## 3. §3 governance reconciliation — chose (b) rename-preserve

User-ratified. The #4-prop-4 design-gate **survives, renamed to `grill-design`** (no stealth
deactivation, add-only invariant held). Edits:
- `CLAUDE.md` §3 step-2 + §Where-to-Look (design-gate → `grill-design`; added community
  grill-with-docs + CONTEXT-MAP/CONTEXT.md row + ADR→RepoMem note).
- `docs/HarnessStack/longterm.md` §Pipeline step-2 line + §Lane-Tiering table + new naming
  note paragraph.
- **3-way merge cleanly preserved your 2026-06-18 Milestone-gate paragraph** in CLAUDE.md
  (no conflict).

## 4. CONTEXT docs (D3) — produced by RUNNING the community grill, then grilled WITH the user

- Layout: root `CONTEXT-MAP.md` + per-module-group `Engine/CONTEXT.md`, `Service/CONTEXT.md`,
  `Skill/CONTEXT.md` (multi-context structure, glossary-only, complement to RepoMem).
- Grounded against RepoMem persist/architecture + module READMEs + **code** (verified the
  CONTEXT-MAP relationships by import: `bilibili-watcher`→`BilibiliEngine`, `zhihu-watcher`→
  `zhihu`, `zhihu-crawl`→`from zhihu import fetch`).
- **Interactive grill ran 5 substantive rounds with the user** (the first pass batch-authored
  the glossary; on user challenge I re-ran the real one-question-at-a-time grill):
  1. `Skill` overload (product vs process) → keep, disambiguate in-definition.
  2. `fav-time` was a **coined** term → replaced with `Collected-at`; platform field names
     (`fav_time`/`created`) demoted to `_Avoid_`.
  3. **Missing** load-bearing distinction → added `Answer`/`Article` (signing + 403-fallback
     asymmetry).
  4. `PULL contract` coined suffix → `PULL delivery` (matches `credentials.md`).
  5. `Engine` class/function asymmetry (BilibiliEngine vs zhihu.fetch) → kept concept pure,
     no implementation detail in glossary (per CONTEXT-FORMAT).

## 5. Decisions (in plan `docs/superpowers/plans/2026-06-11-grill-with-docs-restore.md`)

- **D1** §3 = rename-preserve (grill-with-docs → grill-design).
- **D2** ADR write-sink → RepoMem (`temp/<slug>/decisions.md` → HITL promote), NOT `docs/adr/`;
  community files installed verbatim incl. ADR-FORMAT.md, override applies only when *running*.
- **D3** multi-context CONTEXT layout (CONTEXT-MAP + per-module-group CONTEXT.md).

## 6. Step 8 RepoMem.merge

Fast-lane (no `temp/<slug>/`). **Zero promotion**: governance conclusions live in always-loaded
`CLAUDE.md`+`longterm.md`; the shared-tree merge hazard is already covered by memory
`shared-index-commit-pathspec`. Nothing duplicated into `persist/memory/`.

## 7. Merge hazards encountered (FYI — both resolved, none mine)

While finishing, the shared main tree had two concurrent-session artifacts at my merge site:
(a) a **self-referential broken symlink** at `.claude/skills/grill-with-docs` (from a
cc-switch/skills-sync run 06-14) — resolved itself by 06-18; (b) **foreign staged deletions**
of `sp5a-classify` temp files in the shared index — I held the merge rather than fold another
session's `git rm`; once that session committed (HEAD → `95a6fda`) the index cleared and I
merged cleanly. Flagging in case the cc-switch/skills-sync flow keeps re-creating skill
symlinks (the "Reorg mattpocock-style plan" is pending your confirmation).

## Commit list (on `feat/agentcrawl-bootstrap`)

- `840c3e3` skill restore + grill-design rename + governance reconciliation + plan
- `a0cecf7` CONTEXT-MAP + Engine/Service/Skill CONTEXT.md
- `dd9582c` grounding fix (Profile = active fallthrough list)
- `2c72af8` grill pass (Collected-at, Answer/Article, PULL delivery)
- `5d34239` merge --no-ff

— GrillDocsImpler (2026-06-18)
