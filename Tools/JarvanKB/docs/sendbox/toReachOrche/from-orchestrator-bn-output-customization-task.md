> from: RootOrchestrator g5
> recipient: ReachOrche g1
> type: deferred reach-domain task handoff (Dashboard UN-051)
> lifecycle: keep until you schedule/complete it (no root gate)
> created: 2026-06-18

# Deferred reach task — BN note-output customization (UN-051)

The bilibili engine + BiliNote (BN) integration are your domain forward (reach layer). This files a **deferred**
task for BN note-output customization, scoped + de-scoped per the user's 2026-06-18 decisions. **No root gate** —
schedule it when you pick up the bili-engine domain.

## Background (verified research)
BN routes every provider through one OpenAI **chat-completion** to a configurable `base_url`; the note is a single
Chinese `user` message = `BASE_PROMPT` + per-`format` blocks + `style` block + `extras`. **Live bug:** our
`Engine/bilibili/.../bilinote_client.py` sends `style:"summary"` (an invalid style → silently dropped) + `format:[]`
→ today we get **bare `BASE_PROMPT` notes** (no style, no TOC, no explicit "## AI 总结"). Full backing +
ranked-methods table: `docs/RepoMem/persist/memory/bn-output-customization-and-local-agent-2026-06-18.md`.
User-facing summary: `docs/sendbox/toUser/2026-06-18-bn-summary-findings-and-decisions.md`.

## In scope (deferred — your schedule, your lane/SP call)
1. **Fix the `style:"summary"` no-op** in `Engine/bilibili/src/bilibili/bilinote_client.py` +
   `config/bilibili-engine.yaml`: set a valid `style`, and decide whether to enable the `summary` format block
   (explicit "## AI 总结" section) and/or `toc`.
2. **Adopt `extras` + engine-side post-processing as the standard BN-output customization surface** — thread an
   `extras` knob through `generate_note`; add a post-process transform on the returned markdown (template /
   front-matter / KB-links). This covers most output-shaping with zero BN change, fully testable our side.
3. (optional) bind-mount a custom `prompt.py` only if prompt *internals* (BASE_PROMPT body / language rules /
   merge) must change. Fork BN only as a last resort.

## Explicitly OUT of scope — user dropped 2026-06-18
- **Local-agent backing** (point BN's `base_url` at a local `claude -p` / hermes OpenAI-compatible shim):
  **DROPPED.** Reasons: `claude -p` is **metered since 2026-06-15** (no longer free under subscription); only worth
  it for tool/KB-augmented "deep notes," not plain summaries. The full feasibility analysis (shim sketch, fork
  `i-am-logger/claude-code-proxy`, risks) is preserved in the backing memory **for a possible future "deep note"
  mode** — but it is NOT part of this task. Do not build it unless the user revives it.

## Constraints
- **Non-disruptive.** v1.1 ships the bare base-prompt notes as-is (user choice, WatcherDeploy live now); this task
  improves output later without breaking the deployed watchers.
- Coordinate with root only if it changes a frozen cross-SP contract (it shouldn't — these are bili-engine-local).

— root orche g5 (2026-06-18)
