# MiroResearch

A cross-agent **skill** that wraps the [MiroMind Deep Research API](https://platform.miromind.ai/docs)
(`mirothinker` models) as a single deep-research tool an LLM agent can call.

Given one prompt, the MiroMind model autonomously **plans, searches the web, fetches pages,
and runs code — all server-side** — then returns a synthesized, citation-backed report.
You don't supply tools or execute anything locally.

## Why this design

Deep research is a minutes-scale job. The wrapper's main entry point (`run`) submits a
**background** job and polls **inside the script** until completion, so the calling model
makes *one* tool call and gets *one* report back — instead of driving a polling loop itself
and burning tokens on every status check.

## Install

The skill lives in this repo and is symlinked into the agent skills dir:

```bash
ln -sfn "$PWD/Skills/MiroResearch" ~/.claude/skills/MiroResearch
# optional: register with cc-switch SSOT
cc-switch skills import-from-apps -a claude ~/.claude/skills/MiroResearch
```

## Configuration

| Env var | Required | Default | Notes |
|---------|----------|---------|-------|
| `MIROMIND_API_KEY` | yes | — | Create in the MiroMind console. Put it in `~/.zshenv` so non-interactive tool shells can read it. |
| `MIROMIND_BASE_URL` | no | `https://api.miromind.ai/v1` | Override only if your gateway differs. |

Only dependency: `requests`.

## Usage

```bash
P=~/.claude/skills/MiroResearch/scripts/miro_research.py

# Research, wait, print the final report (default for agents)
python3 $P run "Compare the top open-source deep-research agent frameworks in 2026"

# Deeper / slower flagship model
python3 $P run "QUERY" --full

# Fire-and-forget for long or parallel jobs
ID=$(python3 $P submit "QUERY")
python3 $P status "$ID"
python3 $P result "$ID"          # add --json for raw structured output
python3 $P cancel "$ID"
python3 $P list
```

`run` flags: `--interval SECONDS` (poll cadence, default 10), `--timeout SECONDS`
(default 900; on timeout the job keeps running server-side — re-fetch with `result ID`),
`--json`, `--show-tools`.

## Models

| Model | Flag | Notes |
|-------|------|-------|
| `mirothinker-1-7-deepresearch-mini` | (default) | Fast, cheaper |
| `mirothinker-1-7-deepresearch` | `--full` | Deeper, slower |

Both: 256k context, 16k max output.

## Notes / gotchas

- `tool_call` items in the output already ran on MiroMind's servers — read `item.result`, never re-run.
- No OpenAI-style function calling or `response_format`; you send a prompt and read a report.
- Use `run` for normal tasks; don't have the model poll `status` in a loop (wastes tokens).
