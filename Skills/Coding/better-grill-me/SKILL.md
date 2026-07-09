---
name: better-grill-me
description: Use when you want to stress-test a plan or design before building, or when tempted to ask the user a batch of clarifying questions. A *bounded* interview — reads existing materials first, asks only outcome-changing questions, scales depth to error cost, and stops on an explicit condition. Prefer this over an open-ended relentless grilling that risks turning alignment into interrogation.
---

# Better Grill Me

## Overview

Flipped-interaction is good: the agent surfaces the missing information and puts hidden decisions on the table instead of pretending a vague request is enough. **Relentlessly walking every branch of the design tree is not** — it has no natural end, and it dumps the cost of information-gathering back onto the user.

**Core principle:** A good collaborator finds the gaps that matter. A bad one hands you a form and asks you to fill in every blank. This skill keeps the flip and adds a floor and a ceiling.

Whether to ask at all is **not** a function of how complex the task is. It is a function of three things: **is information actually missing, how large is the cost of getting it wrong, and how reversible is the outcome.** A huge task with a complete PRD, design, API spec, and tests needs few questions. A one-line task that deletes production data, alters a schema, or ships publicly needs at least one.

## The Four Rules

**1. Read before you ask.** Anything findable in existing materials is not a question. Check `CONTEXT.md` / `CONTEXT-MAP.md`, `docs/adr/`, README, PRD/spec, design files, tests, existing components, and issue/PR history — then the code itself. *Facts* you look up; only genuine *decisions that are the user's to make* go to the user.

**2. Ask only outcome-changing questions.** If option A and option B produce no perceptible difference in the deliverable, do not ask — pick the reasonable default and **record it** so the user can override later. Ask only when the answer visibly changes what gets built.

**3. Scale depth to error cost.**

| Ask more (interrogate) | Do first, ask later (or not at all) |
|---|---|
| Irreversible / one-way door | Reversible, easy to undo |
| Cross-module, large blast radius | Local, self-contained |
| Touches auth, security, privacy | Cosmetic / low-risk |
| Mutates or deletes production data | Verifiable in ~10 minutes |
| Schema / migration / public release | A button you can move back in a minute |
| Paid or otherwise irreversible action | |

When executing the task costs less than answering the questions about it, **just do it** and report what you chose.

**4. Stop on an explicit condition.** Cap at **5 high-impact questions**, OR stop the moment **goal + boundaries + acceptance criteria + irreversible decisions** are all clear — whichever comes first. Every remaining small question gets a recommended default that you apply and log, not a prompt.

## Question Quality

- **One question at a time**, each with your **recommended answer** attached, so the user can approve or amend in one word. A firehose of parallel questions is bewildering and loses dependency order.
- **Low- vs high-fidelity.** Low-fidelity decisions (routing, URL, data model, naming, error handling) can be settled with text now — ask those. High-fidelity decisions ("how should this screen *feel*") cannot be reliably settled by interrogation — **build a prototype or mock and let the user react to it** instead of trying to nail it in words.
- **Never weaponize a choice.** Do not hand a non-expert three expert-only options and then treat their coin-flip as a firm requirement — that only moves the error from "the model guessed" to "the model forced you to guess." If the user can't judge, recommend a low-risk default and proceed; escalate only when the choice genuinely changes direction *and* the user is positioned to decide.

This skill augments a user who has planning ability; it does not manufacture judgment the user lacks.

## When NOT to grill

- The task is small, reversible, and fully specified by existing materials → skip the interview, do it, report choices.
- You only want to pin down or record terminology and decisions as you go → use [better-grill-with-docs](../better-grill-with-docs/SKILL.md).

## Red Flags — you have slipped back into interrogation

- You are asking something you could have found in `CONTEXT.md`, the ADRs, the spec, or the code.
- Your question wouldn't change the deliverable either way ("what animation duration?" on a button-move task).
- You are past 5 high-impact questions and still going.
- Goal, boundaries, acceptance criteria, and irreversible decisions are already clear, but you keep asking.
- You are asking the user to arbitrate between options only a specialist could evaluate.
- You are trying to settle a look-and-feel question in words instead of showing a prototype.

**All of these mean: stop asking. Apply a recorded default, or build the thing and report what you chose.**

## Rationalization Table

| Excuse | Reality |
|---|---|
| "Better to be thorough and ask everything upfront." | Thoroughness is asking the *right* questions, not all of them. Reading beats asking. |
| "This might matter later." | If it doesn't change the deliverable now, log a default and move on. |
| "I should let the user decide." | Only decisions that change direction *and* that the user can judge. Otherwise recommend and proceed. |
| "Shared understanding isn't complete yet." | "Complete" has no floor. Stop at goal + boundaries + acceptance + irreversible decisions. |
| "It's just one more question." | Answering it may cost more than doing the task. Check error cost first. |
| "I can't be sure without asking." | You can, for anything reversible and cheap to verify. Do it, then confirm. |

## Provenance

A tightening of the `grilling` / `grill-me` technique (Matt Pocock, github.com/mattpocock/skills), redesigned around the critique that its stop condition ("until shared understanding") is unbounded. The four rules and stop condition follow the analysis at zhihu.com/question/2054005413406946147 (作者:一人变量).
