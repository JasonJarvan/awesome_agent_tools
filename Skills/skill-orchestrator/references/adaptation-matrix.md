# Adaptation Matrix

Use this document when a discovered skill belongs to one ecosystem and needs to be adapted for another.

## General Rule

Usually the reusable part is the content:

- workflow logic
- reference material
- scripts
- templates and assets

Usually the non-portable part is the packaging:

- frontmatter fields
- runtime metadata
- tool permission declarations
- UI metadata
- command-dispatch or runtime-specific integration details

## Claude Code -> Codex

Often reusable:

- `SKILL.md` body
- `scripts/`
- `references/`
- `assets/`

Usually needs adaptation:

- remove or rewrite Claude-specific frontmatter such as `allowed-tools`
- align the triggering description with Codex expectations
- add `agents/openai.yaml` if Codex UI metadata is desired

Expected effort:

- light if the skill is mostly procedural
- moderate if the skill relies on Claude-specific tool constraints or conventions

## Codex -> Claude Code

Often reusable:

- `SKILL.md` body
- bundled resources

Usually needs adaptation:

- rewrite metadata to Claude-compatible frontmatter
- remove dependence on Codex-specific `agents/openai.yaml`
- re-express any Codex-specific runtime assumptions

Expected effort:

- light to moderate

## OpenClaw -> Codex Or Claude Code

Often reusable:

- general workflow body
- references
- scripts

Usually needs adaptation:

- remove OpenClaw-specific runtime fields
- replace command-dispatch assumptions
- verify compatibility with the target runtime's skill-discovery model

Expected effort:

- moderate when the skill depends on OpenClaw runtime semantics

## Portable Skill Design Guidance

When creating a new skill that should travel well:

1. keep the workflow instructions platform-neutral
2. put reusable logic in `scripts/`, `references/`, and `assets/`
3. keep platform-specific behavior in thin adapter documents or metadata files
4. avoid hard-wiring runtime-specific fields into the core logic

## Ask Before Adapting

Before adapting, explain:

- the source ecosystem
- the target ecosystem
- the likely effort level
- the main fields or files that must change

Then ask the user whether to proceed.
