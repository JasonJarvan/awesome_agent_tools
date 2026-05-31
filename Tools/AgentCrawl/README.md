# JarvanKB

> **Status**: SP-0 in progress (2026-05-31). Skeleton + recipe v2 land first; sub-projects SP-1 through SP-7 follow.
> **Recipe**: `superpowers-repomem-sendbox-dashboard` (v2; the Spec layer was dropped — see `docs/HarnessStack/longterm.md §Recipe v1→v2 Migration`).
> **History**: renamed from its 2026-05 bootstrap codename — see `docs/RepoMem/persist/version-plan.md §Project rename`.

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
