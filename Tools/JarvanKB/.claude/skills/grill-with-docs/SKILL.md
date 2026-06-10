---
name: grill-with-docs
description: Use when a full-lane task has a draft design/spec in docs/superpowers/specs/ and writing-plans has not run yet — stress-tests the draft against RepoMem architecture/decisions and current-code ground truth (codegraph), sharpening terminology and surfacing contradictions before they become an execution plan.
---

# Grill With Docs (JarvanKB v2 adaptation)

Deep design review of a DRAFT spec, grounded in the repository's durable knowledge. Adapted from the community grill-with-docs (ADR/CONTEXT.md-based) to recipe v2 (CodeTeam #4 prop 4, instantiated 2026-06-10): the doc context here is RepoMem, NOT docs/adr/ or CONTEXT.md — do not create those.

## When to run (auto-judge)

- Full-lane tasks only (fast lane has no design tree — see `docs/HarnessStack/longterm.md §Lane Tiering (v2)`).
- Window: after a draft spec exists in `docs/superpowers/specs/` (or `<module>/docs/superpowers/specs/`), BEFORE invoking writing-plans.
- Auto-judge tier: run when there is a non-trivial design worth grilling (new architecture, new contract surface, cross-module behavior). Skip mechanically-full tasks (e.g. dependency bumps) with a one-line note in the plan: `grill-with-docs: skipped — <reason>`.

## Process

### 1. Gather context (in order)

1. Global: `docs/RepoMem/persist/architecture/` + `docs/RepoMem/persist/memory/` (decision rationale, gotchas).
2. Module: `<module>/docs/RepoMem/{architecture,decisions}.md` for every module the design touches.
3. Current-code ground truth: codegraph `query`/`callers`/`impact` on the symbols the design names (grep fallback where the graph is sparse — dynamic-Python callees).
4. Prior specs in `docs/superpowers/specs/` overlapping this design's scope.

### 2. Grill the draft

1. **Domain fidelity** — does the design use the vocabulary already established in RepoMem architecture docs? Same concept, same name?
2. **Decision consistency** — does it contradict a recorded decision (spec `### Dn`, module `decisions.md`, `persist/memory/`)? Flag it: either the design changes, or the old decision is explicitly superseded — say which.
3. **Reality check** — do the symbols/flows the design references exist as described (codegraph)? A design built on a stale mental model fails here.
4. **Module depth & leakage** — simple interfaces, deep implementations? Does it leak one module's knowledge into another?
5. **Contract surface** — does it add public contract surface without declaring it? (That flips the Lane selection rule — re-check the lane.)

### 3. Write findings back (write-sinks)

- Sharpened terminology + corrected statements → edit the spec text in place.
- Decision-worthy outcomes → the spec's `### Dn` decision list.
- Implementation-time gotchas discovered while grilling → `RepoMem/temp/<slug>/` (full lane has it).
- Do NOT create `CONTEXT.md`, `docs/adr/`, or any new doc category.

## Principles

- Docs are the spec, code is the implementation; when they disagree, flag it and say which should change.
- The grill teaches: cite the RepoMem doc or codegraph evidence behind each finding.
- Missing docs are no excuse: grill against code ground truth and note what RepoMem should have contained.
