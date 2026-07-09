---
name: better-grill-with-docs
description: Use at the start of a change when the plan is fuzzy and the domain language isn't settled, and you want to stress-test both before any code exists — and leave a paper trail. A bounded interview (reads first, asks only outcome-changing questions, stops on an explicit condition) that also writes resolved terms to CONTEXT.md and hard one-way decisions to ADRs inline. Prefer over an open-ended grilling that risks interrogation.
---

# Better Grill With Docs

## Overview

Same bounded interview as [better-grill-me](../better-grill-me/SKILL.md), plus a **paper trail**: a plain interview evaporates when the session ends; this one captures each term the moment it resolves into a `CONTEXT.md` glossary, and records genuinely one-way decisions as ADRs. The alignment survives the conversation instead of living only in someone's head.

**REQUIRED BACKGROUND:** Read [better-grill-me](../better-grill-me/SKILL.md) first — the Four Rules, stop condition, red flags, and rationalization table govern this skill too. This document adds only the docs layer.

## The interview (inherited, condensed)

1. **Read before you ask** — and here `CONTEXT.md`, `CONTEXT-MAP.md`, and `docs/adr/` are the *first* things you read. They ARE the existing shared understanding; do not re-ask what they already settle.
2. **Ask only outcome-changing questions**; log defaults for the rest.
3. **Scale depth to error cost** — one-way doors get interrogated, reversible things get done.
4. **Stop explicitly** — ≤5 high-impact questions, or when goal + boundaries + acceptance criteria + irreversible decisions are clear.

One question at a time, each with a recommended answer.

## The docs layer

### Glossary — `CONTEXT.md` (write inline)

When the interview sharpens a fuzzy or overloaded term into a canonical one, write it to `CONTEXT.md` **right then** — do not batch at the end. Challenge conflicts as they surface: *"Your glossary defines 'cancellation' as X, but you seem to mean Y — which is it?"* and *"You said 'account' — Customer or User? Those are different things."*

`CONTEXT.md` is a **glossary and nothing else** — pure vocabulary, in the project's own words. No implementation details, no spec, no scratch notes.

### Decisions — ADRs under `docs/adr/` (offer sparingly)

Offer an ADR only when **all three** are true:

1. **Hard to reverse** — changing your mind later has meaningful cost.
2. **Surprising without context** — a future reader will ask "why this way?"
3. **The result of a real trade-off** — there were genuine alternatives.

If any one is missing, skip it. Most sessions produce a sharper glossary and **few or no ADRs** — that is the intended shape. Do not ask the user to rubber-stamp reversible choices; that is exactly the interrogation the bounded interview exists to prevent.

### File structure

Create files **lazily** — nothing exists until the first term or decision crystallizes.

```
/
├── CONTEXT.md               ← glossary (single-context repo)
├── docs/adr/                ← 0001-....md, 0002-....md
└── src/
```

If a `CONTEXT-MAP.md` exists at the root, the repo is multi-context: write each resolved term to the relevant context's own `CONTEXT.md`, and system-wide decisions to the root `docs/adr/`.

## It's working if

- It reads `CONTEXT.md` and the ADRs before asking anything, and doesn't re-ask what they settle.
- It asks one question at a time and stops on the bound — not a questionnaire.
- Terms land in `CONTEXT.md` the moment they resolve, in the project's own words.
- ADRs stay rare; reversible choices are defaulted and logged, not put to a vote.

## When NOT to use

- You only want the interview, no artifacts → [better-grill-me](../better-grill-me/SKILL.md).
- The plan is already clear and you just need to record terminology/decisions → drive the docs layer directly without the interview.
- You are somewhere it's not safe to write files into the repo → this skill is stateful; use [better-grill-me](../better-grill-me/SKILL.md) instead.

## Provenance

A tightening of `grill-with-docs` (Matt Pocock, github.com/mattpocock/skills), which paired the unbounded `grilling` interview with `domain-modeling`. This version keeps the domain-modeling paper trail but replaces the relentless interview with the bounded one from [better-grill-me](../better-grill-me/SKILL.md), per the critique at zhihu.com/question/2054005413406946147 (作者:一人变量).
