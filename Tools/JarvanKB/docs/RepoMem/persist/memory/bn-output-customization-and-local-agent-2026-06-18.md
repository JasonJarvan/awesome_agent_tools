---
language: en
audience: A2A
status: research finding (backs deferred reach task Dashboard UN-051; awaiting user confirm before toUser report)
created: 2026-06-18
---

# BiliNote (BN) Note-Output Customization + Local-Agent Backing — Research Backing

> Subagent finding (2026-06-18), verified against the live `jarvankb-bilinote` container (stock
> `ghcr.io/jefferyhcool/bilinote:latest`) + upstream `github.com/JefferyHcool/BiliNote` + our
> `Engine/bilibili`. Backs **Dashboard UN-051** (deferred, reach domain). User-facing report (`toUser/`) to be
> written after user confirmation.

## Ground truth
- **One model hook for all providers.** `gpt/gpt_factory.py` routes every provider (incl. our `custom`
  `mimo-v2.5-*`) through `UniversalGPT`, which makes **one non-streaming OpenAI chat-completion** to the provider's
  `base_url`. The note = a single Chinese `user` message (no system msg) = `BASE_PROMPT` + per-`format` blocks +
  `style` block + `extras` (verbatim). API params (`format:list=[]`, `style:str=None`, `extras:str=None`) flow into
  the prompt with **zero validation** (unknown values silently dropped).
- **LIVE BUG (our side):** `bilinote_client.py` sends `style:"summary"` + `format:[]`. `"summary"` is **not a valid
  style** (`note_styles` = minimal/detailed/academic/tutorial/xiaohongshu/life_journal/task_oriented/business/
  meeting_minutes) → falls through to `''` → **no style added**. `"summary"` is actually a *format* value (the
  `## AI 总结` block) put in the wrong field. **Net today: bare `BASE_PROMPT` notes — no style, no TOC, no
  AI-summary, no timestamps.** Cheapest highest-value fix in the whole report.
- `MERGE_PROMPT` only fires on long videos chunked past `OPENAI_MAX_REQUEST_BYTES` (45MB default). BN env knobs
  (`*_BYTES`, retries, `NOTE_OUTPUT_DIR`) are transport-only; `temperature` hardcoded 0.7 (not env-driven).

## Q1 — ways to customize BN output (least → most invasive)
| # | Lever | Changes | Cost | Invasiveness |
|---|---|---|---|---|
| 1 | **Fix + use `style`** (valid value) | tone/verbosity/persona blurb | one-line in `bilinote_client.py`+yaml | lowest (bugfix) |
| 2 | **Use `format`** (`toc`/`summary`/`link`/`screenshot`) | TOC, explicit AI-summary section, jump/screenshot (latter = heavy media path) | change hardcoded `format:[]` | lowest |
| 3 | **`extras`** (free-text appended) | **most flexible no-fork lever** — arbitrary sections/caps/headings/conventions | add `extras` knob, thread through | low — **recommended primary surface** |
| 4 | **Engine-side post-processing** of returned md | deterministic reshape/front-matter/KB-links on our side | new transform in client return path | low (our code only) |
| 5 | **Swap model** (BN DB + yaml) | quality/language/cost ceiling | config/ops, zero code | low (ops) |
| 6 | env (`*_BYTES`/retries) | chunking threshold/transport | compose env | low; `temperature` needs bind-mount/fork |
| 7 | **Bind-mount custom `prompt.py`** | full prompt-text control (BASE/MERGE/blocks) no fork | vendor+version file, pin image digest | moderate — max-power no-fork |
| 8 | **Fork BN** | everything incl. control flow | maintain fork+build | highest |
**Rec:** do #1 now (live no-op); make **#3 `extras` + #4 post-processing** the standard surface; reserve #7 for
prompt internals; fork only if Q2 must live inside BN.

## Q2 — back BN's LLM step with a LOCAL AGENT?
**Feasible & clean — BN can't tell the difference.** BN's only contract = `POST {base_url}/v1/chat/completions`
(non-streaming; reads `.choices[0].message.content`). Point `base_url` at a **local OpenAI-compatible shim** (pure
config: register a `custom` provider, `base_url=http://host.docker.internal:<port>/v1`) → shim drives a local agent
and returns the note. **Zero BN/engine code change.**
- **`claude -p`** (headless): non-interactive, `--output-format json`, `--bare` single-shot, reads stdin. Per-call
  cold-start latency negligible vs ASR. **⚠️ 2026-06-15 billing change: `claude -p`/Agent SDK now bill a SEPARATE
  metered automation credit pool, NOT the interactive subscription** → "free under my subscription" is no longer
  true; weakens the cost case.
- **"hermes agent"** = likely NousResearch Hermes Agent (local agent runtime + cron + local-exec) — matches repo
  context; can serve the same shim role.
- **Don't build the OpenAI layer from scratch:** fork `i-am-logger/claude-code-proxy` (CLI-spawn, swappable to
  Hermes) or `RichardAtCT/claude-code-openai-wrapper` (SDK, tools-off-by-default).
- **Streaming NOT required.** Risks: N× spawn on chunked long videos; map agent failures to retryable HTTP; metered cost.
- **Verdict:** NOT worth it for plain note-gen (slower/costlier than the mimo API, no gain if single-shot tool-less).
  **Worth it ONLY for a "deep note" mode** where the agent uses tools/our Obsidian KB (backlinks, dedupe, vault
  placement), multi-step reasoning, or reuses a running local Hermes/OpenClaw agent. → **deferred, opt-in, behind
  the shim; not a replacement** for the default mimo path.

## Two flags (decision-relevant)
1. **Live bug:** `style:"summary"` no-op + `format:[]` → bare `BASE_PROMPT` notes today (no AI-summary section).
   One-line #1+#2 fix is the cheapest highest-value action.
2. **Cost reality shifted:** `claude -p` metered since 2026-06-15 → local-agent shim only justified for
   tool/KB-augmented deep-note, not as a cheaper substitute.

Sources: code.claude.com/docs/en/headless; genaiunplugged (2026-06-15 billing); i-am-logger/claude-code-proxy;
RichardAtCT/claude-code-openai-wrapper; github.com/nousresearch/hermes-agent.
