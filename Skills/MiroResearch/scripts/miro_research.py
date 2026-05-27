#!/usr/bin/env python3
"""MiroMind Deep Research CLI wrapper.

Thin, zero-dependency (requests-only) wrapper over the MiroMind Responses API
(https://platform.miromind.ai/docs). Designed to be called by an LLM agent as a
deep-research tool.

Key design choice: the `run` subcommand submits a background job and then polls
*inside this process* until completion, returning only the final report. This
keeps the calling model's token usage low (one tool call in, one result out)
instead of having the model drive the polling loop itself.

Auth: reads MIROMIND_API_KEY from the environment.
Base URL: MIROMIND_BASE_URL (default https://api.miromind.ai/v1).

Subcommands:
  run     <query>   Submit + poll internally, print final report (default for agents)
  submit  <query>   Submit a background job, print the response id, return immediately
  status  <id>      Print the job status (queued/in_progress/completed/failed/cancelled)
  result  <id>      Print the final report of a finished job
  cancel  <id>      Cancel an in-progress job
  list              List recent jobs (metadata only)

Exit codes: 0 ok, 1 usage/runtime error, 2 job failed, 3 auth/config error.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

try:
    import requests
except ImportError:  # pragma: no cover
    sys.stderr.write("error: the 'requests' package is required (pip install requests)\n")
    raise SystemExit(3)


DEFAULT_BASE_URL = "https://api.miromind.ai/v1"
DEFAULT_MODEL = "mirothinker-1-7-deepresearch-mini"
FULL_MODEL = "mirothinker-1-7-deepresearch"
TERMINAL_STATES = {"completed", "failed", "cancelled", "canceled", "error"}


def _config() -> tuple[str, str]:
    api_key = os.environ.get("MIROMIND_API_KEY", "").strip()
    if not api_key:
        sys.stderr.write(
            "error: MIROMIND_API_KEY is not set.\n"
            "       export MIROMIND_API_KEY=sk_live_... (create one in the MiroMind console).\n"
        )
        raise SystemExit(3)
    base_url = os.environ.get("MIROMIND_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    return api_key, base_url


def _headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def _request(method: str, url: str, api_key: str, *, payload: dict | None = None,
             timeout: int = 60) -> dict:
    try:
        resp = requests.request(method, url, headers=_headers(api_key),
                                json=payload, timeout=timeout)
    except requests.RequestException as exc:
        sys.stderr.write(f"error: network failure calling {url}: {exc}\n")
        raise SystemExit(1)
    if resp.status_code == 401:
        sys.stderr.write("error: 401 Unauthorized — check MIROMIND_API_KEY.\n")
        raise SystemExit(3)
    if resp.status_code >= 400:
        sys.stderr.write(f"error: {method} {url} -> HTTP {resp.status_code}: {resp.text[:500]}\n")
        raise SystemExit(1)
    try:
        return resp.json()
    except ValueError:
        sys.stderr.write(f"error: non-JSON response from {url}: {resp.text[:500]}\n")
        raise SystemExit(1)


# --- response parsing helpers -------------------------------------------------

def _extract_final_text(response: dict) -> str:
    """Pull the assistant's final message text out of a completed response."""
    parts: list[str] = []
    for item in response.get("output", []) or []:
        if item.get("type") != "message":
            continue
        content = item.get("content")
        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("text"):
                    parts.append(block["text"])
                elif isinstance(block, str):
                    parts.append(block)
    return "\n".join(p for p in parts if p).strip()


def _extract_tool_calls(response: dict) -> list[dict]:
    """Collect server-side tool calls (web_search, fetch_url, etc.) with results."""
    calls = []
    for item in response.get("output", []) or []:
        if item.get("type") == "tool_call":
            calls.append({
                "name": item.get("name"),
                "arguments": item.get("arguments"),
                "status": item.get("status"),
                "result": item.get("result"),
            })
    return calls


# --- subcommand implementations ----------------------------------------------

def _pick_model(args) -> str:
    if args.model:
        return args.model
    return FULL_MODEL if getattr(args, "full", False) else DEFAULT_MODEL


def cmd_submit(args) -> int:
    api_key, base_url = _config()
    payload = {"model": _pick_model(args), "input": args.query, "background": True}
    if args.max_output_tokens:
        payload["max_output_tokens"] = args.max_output_tokens
    data = _request("POST", f"{base_url}/responses", api_key, payload=payload)
    rid = data.get("id", "")
    print(rid)
    sys.stderr.write(f"submitted: id={rid} status={data.get('status')}\n")
    return 0


def cmd_status(args) -> int:
    api_key, base_url = _config()
    data = _request("GET", f"{base_url}/responses/{args.id}", api_key)
    print(data.get("status", "unknown"))
    return 0


def cmd_result(args) -> int:
    api_key, base_url = _config()
    data = _request("GET", f"{base_url}/responses/{args.id}", api_key)
    return _emit_result(data, args)


def cmd_cancel(args) -> int:
    api_key, base_url = _config()
    data = _request("POST", f"{base_url}/responses/{args.id}/cancel", api_key)
    print(data.get("status", "unknown"))
    return 0


def cmd_list(args) -> int:
    api_key, base_url = _config()
    data = _request("GET", f"{base_url}/responses?limit={args.limit}", api_key)
    for item in data.get("data", []) or []:
        print(f"{item.get('id')}\t{item.get('status')}\t{item.get('model')}\t{item.get('created_at')}")
    return 0


def cmd_run(args) -> int:
    """Submit a background job, poll internally, print the final report."""
    api_key, base_url = _config()
    payload = {"model": _pick_model(args), "input": args.query, "background": True}
    if args.max_output_tokens:
        payload["max_output_tokens"] = args.max_output_tokens

    submitted = _request("POST", f"{base_url}/responses", api_key, payload=payload)
    rid = submitted.get("id")
    if not rid:
        sys.stderr.write(f"error: no response id returned: {json.dumps(submitted)[:500]}\n")
        return 1
    sys.stderr.write(f"submitted: id={rid} model={payload['model']}; polling...\n")

    deadline = time.monotonic() + args.timeout
    interval = args.interval
    data = submitted
    while time.monotonic() < deadline:
        status = (data.get("status") or "").lower()
        if status in TERMINAL_STATES:
            break
        time.sleep(interval)
        data = _request("GET", f"{base_url}/responses/{rid}", api_key)
        sys.stderr.write(f"  status={data.get('status')}\n")
    else:
        sys.stderr.write(
            f"error: timed out after {args.timeout}s (id={rid}, last status={data.get('status')}).\n"
            f"       resume later with: result {rid}\n"
        )
        return 1

    return _emit_result(data, args)


def _emit_result(data: dict, args) -> int:
    status = (data.get("status") or "").lower()
    if status in {"failed", "error"}:
        sys.stderr.write(f"error: job {data.get('id')} ended with status={status}: "
                         f"{json.dumps(data.get('error') or {})[:500]}\n")
        return 2
    if status in {"cancelled", "canceled"}:
        sys.stderr.write(f"job {data.get('id')} was cancelled.\n")
        return 2
    if status != "completed":
        sys.stderr.write(f"warning: job {data.get('id')} not completed (status={status}).\n")

    if getattr(args, "json", False):
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    text = _extract_final_text(data)
    print(text if text else "(no final message text found)")
    if getattr(args, "show_tools", False):
        calls = _extract_tool_calls(data)
        if calls:
            sys.stderr.write(f"\n--- {len(calls)} tool call(s) ---\n")
            for c in calls:
                sys.stderr.write(f"  [{c['status']}] {c['name']} {json.dumps(c['arguments'], ensure_ascii=False)[:200]}\n")
    usage = data.get("usage") or {}
    if usage:
        sys.stderr.write(f"\nusage: {json.dumps(usage, ensure_ascii=False)}\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="MiroMind Deep Research CLI wrapper")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_model_opts(sp):
        sp.add_argument("--model", help=f"model id (default {DEFAULT_MODEL})")
        sp.add_argument("--full", action="store_true",
                        help=f"use the flagship model {FULL_MODEL}")
        sp.add_argument("--max-output-tokens", type=int, dest="max_output_tokens",
                        help="cap on output tokens")

    sp_run = sub.add_parser("run", help="submit + poll internally + print report")
    sp_run.add_argument("query")
    add_model_opts(sp_run)
    sp_run.add_argument("--interval", type=float, default=10.0, help="poll interval seconds (default 10)")
    sp_run.add_argument("--timeout", type=int, default=900, help="max seconds to wait (default 900)")
    sp_run.add_argument("--json", action="store_true", help="print raw JSON instead of report text")
    sp_run.add_argument("--show-tools", action="store_true", help="print tool calls to stderr")
    sp_run.set_defaults(func=cmd_run)

    sp_submit = sub.add_parser("submit", help="submit background job, print id")
    sp_submit.add_argument("query")
    add_model_opts(sp_submit)
    sp_submit.set_defaults(func=cmd_submit)

    sp_status = sub.add_parser("status", help="print job status")
    sp_status.add_argument("id")
    sp_status.set_defaults(func=cmd_status)

    sp_result = sub.add_parser("result", help="print final report of a finished job")
    sp_result.add_argument("id")
    sp_result.add_argument("--json", action="store_true")
    sp_result.add_argument("--show-tools", action="store_true")
    sp_result.set_defaults(func=cmd_result)

    sp_cancel = sub.add_parser("cancel", help="cancel an in-progress job")
    sp_cancel.add_argument("id")
    sp_cancel.set_defaults(func=cmd_cancel)

    sp_list = sub.add_parser("list", help="list recent jobs")
    sp_list.add_argument("--limit", type=int, default=20)
    sp_list.set_defaults(func=cmd_list)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
