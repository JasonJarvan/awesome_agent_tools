---
name: zhihu-crawl
description: >
  Use when the user gives a Zhihu URL (answer / article / question) and wants it saved as a Markdown
  note. Fetches via the frozen Zhihu engine and writes Markdown to a chosen path; when the path is vague
  (a folder, the KB root, or omitted) it classifies the content into a subfolder. Do NOT use for
  non-Zhihu URLs or for video transcription.
version: 0.1.0
license: MIT
tags:
  - zhihu
  - crawl
  - markdown
  - knowledge-base
metadata:
  hermes:
    category: knowledge-capture
    required_environment_variables:
      - ANTHROPIC_API_KEY        # or DASHSCOPE_API_KEY (vague-path classification only)
      - COOKIE_MANAGER_PASSWORD  # SP-1 cookie decrypt (name per your config password_env)
  openclaw:
    requires:
      bins: [zhihu-crawl]
    install: "pip install -e Engine/common -e Engine/zhihu -e Skill/crawl/zhihu-crawl"
---

# zhihu-crawl

Save a Zhihu page as Markdown.

## When to use
A user shares a Zhihu URL and wants it in their knowledge base / notes.

## How to run
```bash
zhihu-crawl "<zhihu-url>" --out "<path>" [--comments] [--json]
```
- `--out FILE.md` → write there verbatim.
- `--out DIR` / omit `--out` → vague: classify into a subfolder under the configured `output_root`.
- `--json` → machine-readable result (`path`, `category`, `was_vague`, ...).

## Setup
1. `cp config.example.yaml config.yaml` and set `output_root` + the cookie-manager connection.
2. `cp ../../../config/llm.yaml.example ../../../config/llm.yaml` (repo root) for vague-path classification.
3. Put credentials in `.env` (never in the repo): the cookie password and one LLM `api_key_env`.

## Notes
Reads cookies from SP-1 cookie-manager (pull-only, decrypted in memory). Pure consumer of the frozen
Zhihu engine — see `docs/interface.md`.
