---
name: MiroResearch
description: Use when a question needs deep, multi-step web research with citations — comparisons, literature/market/technology surveys, "what's the latest on X", fact-finding that spans many sources — and a single quick answer is not enough. Wraps the MiroMind Deep Research API (mirothinker), which autonomously searches the web, fetches pages, and runs code server-side, then returns a synthesized report. Cross-agent (Claude Code, Codex, etc.); requires MIROMIND_API_KEY.
---

# MiroResearch

Run deep research via the MiroMind Responses API. The `mirothinker` model is an
autonomous research agent: given one prompt it plans, searches the web, fetches
pages, optionally runs code — all **server-side** — and returns a synthesized,
cited report. You do not supply tools or execute anything locally.

**Core principle:** delegate the whole research task in one call. The wrapper
submits a background job and polls *internally*, so you make one tool call and
get one report back — no model-driven polling loop, minimal token cost.

## When to Use

- Multi-source questions: "compare X vs Y", "survey the state of Z", "what's the latest on …"
- Fact-finding needing fresh web data and citations
- Anything where one quick LLM answer is insufficient and you'd otherwise search→read→synthesize by hand

**When NOT to use:**
- Simple lookups answerable directly or with one web search → just answer
- Tasks needing local repo/file context the API can't see
- When `MIROMIND_API_KEY` is unavailable

## Quick Reference

Run from this skill's directory (script reads `MIROMIND_API_KEY` from env):

| Goal | Command |
|------|---------|
| Research, wait, get report (default) | `python3 scripts/miro_research.py run "QUERY"` |
| Use flagship model (deeper, slower) | `python3 scripts/miro_research.py run "QUERY" --full` |
| Fire-and-forget, get job id | `python3 scripts/miro_research.py submit "QUERY"` |
| Check status | `python3 scripts/miro_research.py status RESP_ID` |
| Fetch a finished report | `python3 scripts/miro_research.py result RESP_ID` |
| Cancel | `python3 scripts/miro_research.py cancel RESP_ID` |
| List recent jobs | `python3 scripts/miro_research.py list` |

Models: `mirothinker-1-7-deepresearch-mini` (default, fast/cheap),
`mirothinker-1-7-deepresearch` (`--full`, deeper). Both 256k context.

## How to Use (agent workflow)

1. **Default path — `run`:** for almost all cases, call `run "QUERY"`. It blocks
   until the report is ready (deep research takes minutes) and prints the report
   to stdout. Progress/status goes to stderr; usage stats print at the end.
2. **Long jobs / parallelism — `submit` + `status` + `result`:** if you'd rather
   not hold one call open, or want several studies in flight, `submit` returns a
   `resp_…` id immediately; poll `status`; fetch with `result` once `completed`.
   Use this if `run` is likely to exceed its timeout.
3. **Add `--json`** to any read command when you need the raw structured output
   (output items, tool calls, usage) instead of just the report text.

Tune waiting with `--timeout SECONDS` (default 900) and `--interval SECONDS`
(default 10). On timeout the job keeps running server-side — re-fetch later with
`result RESP_ID`.

## Setup

- `MIROMIND_API_KEY` must be set (`sk_live_…`, created in the MiroMind console).
- `MIROMIND_BASE_URL` optional, default `https://api.miromind.ai/v1`.
- Only dependency is `requests` (standard in most envs).

## Common Mistakes

- **Driving the poll loop from the model.** Don't call `submit` then repeatedly
  call `status` yourself for a normal task — that burns tokens. Use `run`, which
  polls inside the process.
- **Treating tool calls as something to execute.** `tool_call` items in the
  output already ran on MiroMind's servers; read `item.result`, never re-run.
- **Expecting OpenAI function-calling / `response_format`.** Not supported. This
  is a self-contained research agent; you only send a prompt and read a report.
- **Too-short timeout.** Deep research is minutes-scale; raise `--timeout` or
  switch to the `submit`/`result` pattern rather than failing fast.

## Files

- `scripts/miro_research.py` — the CLI wrapper (run/submit/status/result/cancel/list).
