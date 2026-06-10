---
slug: harnessstack-codegraph-lanetiering
status: active
domains: [harnessstack-governance]
updated_at: 2026-06-10
---

# Task decisions — harnessstack-codegraph-lanetiering

> Working memory only. Durable record = `docs/superpowers/specs/2026-06-10-harnessstack-codegraph-lanetiering-design.md` (the spec IS the item-by-item mapping record per handoff §7). This file holds only what the spec does not.

- **D1 (user, gate):** #3 full adoption — install codegraph now + `.mcp.json`; #4 adopt as drafted; Lane declared in plan-doc frontmatter. (U1–U3 in spec §1)
- **D2 (user, mid-flight):** grill-with-docs gap must be CLOSED, not skipped — author project-local skill. Overrode impler's does-not-map draft. (U4)
- **D3 (impler):** longterm.md v2 block lacks a Harness Enhancement Layer section (handoff's "§5 ~L200" pointer lands in the deprecated v1 archive) — new `## Harness Enhancement Layer (v2)` section needed; noted for the done-letter so root can fix stale pointers in future handoffs.
- **D4 (impler):** Add-only determination — both issues additive, NOT a Full Rewrite (spec §4). No escalation.
- **D5 (impler, corrected during planning):** `.mcp.json` is GITIGNORED in JarvanKB (plaintext API key — `Tools/JarvanKB/.gitignore:2`), so the codegraph server entry is a machine-local edit; canonical snippet lives in `longterm.md` for replication. `.codegraph/` added to `.gitignore`.
- **D6 (impler):** repo-root `.gitignore:5` ignores ALL `.claude/` dirs — to commit the project skill, `Tools/JarvanKB/.gitignore` must re-include with `!.claude/` (deeper gitignore wins; keep `.claude/settings.local.json` ignored). Caveat: project skills load from the session cwd's `.claude/skills/` — sessions cwd'd into a module dir may not see it; grill-with-docs targets root-level/full-lane design work, acceptable.
