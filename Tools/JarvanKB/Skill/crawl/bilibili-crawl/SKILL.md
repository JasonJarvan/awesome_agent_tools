---
name: bilibili-crawl
description: >
  Use when the user gives a Bilibili video reference (BV id, a bilibili.com URL, or an av id) and wants it
  transcribed and saved as a Markdown note. Transcribes via the frozen Bilibili engine (subtitle-first, ASR
  fallback) and writes Markdown to a chosen path; when the path is vague (a folder, the KB root, or omitted)
  it classifies the note into a subfolder. Do NOT use for non-Bilibili URLs or for article/text crawling.
version: 0.1.0
license: MIT
tags:
  - bilibili
  - video
  - transcription
  - markdown
  - knowledge-base
metadata:
  hermes:
    category: knowledge-capture
    required_environment_variables:
      - MIMO_API_KEY            # or another config/llm.yaml profile key (vague-path classification only)
      - COOKIE_MANAGER_PASSWORD # SP-1 cookie decrypt (name per your config password_env)
  openclaw:
    requires:
      bins: [bilibili-crawl]
    install: "pip install -e Engine/common -e Engine/bilibili -e Skill/crawl/bilibili-crawl"
---

# bilibili-crawl

Transcribe a Bilibili video and save it as Markdown.

## When to use
A user shares a Bilibili video (BV / URL / av) and wants the transcript + AI summary in their knowledge base.

## How to run
```bash
bilibili-crawl "<BV-id-or-url>" --out "<path>" [--json]
```
- `--out FILE.md` → write there verbatim.
- `--out DIR` / omit `--out` → vague: classify into a subfolder under the configured `output_root`.
- `--json` → machine-readable result (`path`, `transcript_path`, `category`, `transcript_source`, ...).

## Setup
1. `cp config.example.yaml config.yaml` and set `output_root` + the cookie-manager connection.
2. Ensure the repo-root `config/llm.yaml` has the `mimo` profile (vague-path classification) and
   `config/bilibili-engine.yaml` points at a reachable BiliNote.
3. Put credentials in `.env` (never in the repo): the cookie password and one LLM `api_key_env`.

## Notes
Reads cookies from SP-1 cookie-manager (pull-only, decrypted in memory; a missing cookie degrades to the
public-video ASR path, never fatal). Pure consumer of the frozen Bilibili engine — see `docs/interface.md`.
