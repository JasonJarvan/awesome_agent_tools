# RepoMem — AgentCrawl

Repository memory under the `RepoMem` layer of HarnessStack recipe
`superpowers-repomem-sendbox-dashboard` (v2).

For authoritative layout and rules, read `~/.claude/skills/repo-mem/references/`.

## Layout

```
docs/RepoMem/
├── persist/                    # long-term, loaded by RepoMem.read
│   ├── config.md               # language + frontmatter policy
│   ├── version-plan.md         # version / roadmap notes
│   ├── architecture/
│   │   ├── index.md            # domain map
│   │   └── crawl-pipeline.md   # current single active domain
│   └── memory/
│       ├── index.md            # memory map; boundary vs superpowers writing-plans
│       ├── runbook.md          # ops / credentials / cost reference
│       └── pre-openspec-decisions.md   # FROZEN legacy (D1–D7)
└── temp/<slug>/                # task-scoped, RepoMem.capture / merge
```

Layered v2: per-module memory also lives under `<module>/docs/RepoMem/{architecture,decisions}.md` + `temp/<slug>/`.

## Boundary vs Superpowers writing-plans

- **Superpowers writing-plans** outputs (`docs/superpowers/plans/`) own the per-task implementation contract; **RepoMem `temp/<slug>/`** holds task-scoped requirements / architecture / decisions docs
- `memory/` only accepts: operational knowledge (runbook), the frozen `pre-openspec-decisions.md` legacy, or distilled-lessons promoted at `RepoMem.merge` time
- `RepoMem.merge` rejects content that duplicates a per-task plan/spec record

## Pipeline touch points (v2)

| Step | Action |
|---|---|
| 1 | `RepoMem.read` loads `persist/` + per-module `<module>/docs/RepoMem/` (two layers) |
| 3 / 5 | `RepoMem.capture` writes `temp/<slug>/{requirements,architecture,decisions}.md` (continuous) |
| 8 | `RepoMem.merge` (HITL) promotes from `temp/<slug>/` to `persist/` — after `finishing-a-development-branch`; then `prune / split` |
