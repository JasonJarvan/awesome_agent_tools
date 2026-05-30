# RepoMem — AgentCrawl

Repository memory under the `RepoMem` layer of HarnessStack recipe
`openspec-superpowers-repomem-sendbox-dashboard`.

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
│       ├── index.md            # memory map; boundary vs OpenSpec
│       ├── runbook.md          # ops / credentials / cost reference
│       └── pre-openspec-decisions.md   # FROZEN legacy (D1–D7)
└── temp/<slug>/                # task-scoped, RepoMem.capture / merge
```

## Boundary vs OpenSpec

- **OpenSpec change docs** (`docs/openspec/changes/<change-id>/`) own per-change contracts going forward
- `memory/` only accepts: operational knowledge (runbook), pre-OpenSpec legacy, or distilled-lessons promoted at `RepoMem.merge` time
- `RepoMem.merge` rejects content that duplicates an archived OpenSpec change

## Pipeline touch points

| Step | Action |
|---|---|
| 1 | `RepoMem.read` loads `persist/` |
| 4 / 7 | `RepoMem.capture` writes `temp/<slug>/{requirements,architecture,memory}.md` |
| 12 | `RepoMem.merge` (HITL) promotes from `temp/<slug>/` to `persist/` — after `OpenSpec.archive` |
| 13 | `RepoMem.prune / split` periodic hygiene |
