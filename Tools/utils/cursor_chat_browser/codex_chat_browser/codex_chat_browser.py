#!/usr/bin/env python3
"""
Browse and export Codex CLI session JSONL from the terminal (interactive + CLI).

Reads ~/.codex/sessions/**/*.jsonl (override with CODEX_SESSIONS_DIR).

CLI:
  python codex_chat_browser.py              # interactive
  python codex_chat_browser.py list
  python codex_chat_browser.py view 3
  python codex_chat_browser.py view /path/to/session.jsonl
  python codex_chat_browser.py copy-id 2
  python codex_chat_browser.py batch-export [--cwd ...] [--sessions-dir ...] [--output-dir ...]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

console = Console()

SESSION_ID_PATTERN = re.compile(r"Session ID:\s*`([^`]+)`")


def default_sessions_dir() -> Path:
    raw = os.environ.get("CODEX_SESSIONS_DIR", "").strip()
    if raw:
        return Path(raw).expanduser()
    return Path.home() / ".codex" / "sessions"


def flatten_content(content) -> str:
    parts: list[str] = []
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if text:
                    parts.append(text)
                elif item.get("type") == "input_image":
                    parts.append("[image omitted]")
            elif isinstance(item, str):
                parts.append(item)
    elif isinstance(content, str):
        parts.append(content)
    return "\n\n".join(part for part in parts if part).strip()


def load_jsonl_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def find_existing_session_ids(output_dir: Path) -> set[str]:
    session_ids: set[str] = set()
    for path in output_dir.glob("*.md"):
        content = path.read_text(encoding="utf-8")
        for match in SESSION_ID_PATTERN.findall(content):
            session_ids.add(match)
    return session_ids


def parse_session_rows(rows: list[dict]) -> tuple[dict, list[dict]]:
    """Return (session_meta_payload, transcript_entries) same structure as build_markdown loop."""
    meta: dict = {}
    tool_names: dict[str, str] = {}
    entries: list[dict] = []

    for row in rows:
        row_type = row.get("type")
        payload = row.get("payload", {}) or {}
        timestamp = row.get("timestamp", "")

        if row_type == "session_meta":
            meta = payload
            continue

        if row_type == "response_item" and payload.get("type") == "message":
            role = payload.get("role")
            if role in {"user", "assistant"}:
                entries.append(
                    {
                        "kind": "message",
                        "timestamp": timestamp,
                        "role": role,
                        "phase": payload.get("phase"),
                        "text": flatten_content(payload.get("content", [])),
                    }
                )
            continue

        if row_type == "response_item" and payload.get("type") == "function_call":
            call_id = payload.get("call_id")
            tool_names[str(call_id)] = payload.get("name", "")
            entries.append(
                {
                    "kind": "tool_call",
                    "timestamp": timestamp,
                    "name": payload.get("name", ""),
                    "arguments": payload.get("arguments", ""),
                }
            )
            continue

        if row_type == "response_item" and payload.get("type") == "function_call_output":
            entries.append(
                {
                    "kind": "tool_output",
                    "timestamp": timestamp,
                    "name": tool_names.get(str(payload.get("call_id")), ""),
                    "output": payload.get("output", ""),
                }
            )
            continue

    return meta, entries


def build_markdown(session_path: Path, rows: list[dict]) -> tuple[str, str]:
    meta, entries = parse_session_rows(rows)
    lines = [
        f"# {session_path.stem}",
        "",
        "## Metadata",
        "",
        f"- Source: `{session_path}`",
        f"- Session ID: `{meta.get('id', '')}`",
        f"- Started At: `{meta.get('timestamp', '')}`",
        f"- CWD: `{meta.get('cwd', '')}`",
        f"- CLI Version: `{meta.get('cli_version', '')}`",
        "",
        "## Transcript",
        "",
    ]

    for entry in entries:
        if entry["kind"] == "message":
            role = "User" if entry["role"] == "user" else "Assistant"
            phase = f" ({entry['phase']})" if entry.get("phase") else ""
            lines.extend(
                [
                    f"### {role}{phase} [{entry['timestamp']}]",
                    "",
                    entry["text"] or "[empty]",
                    "",
                ]
            )
        elif entry["kind"] == "tool_call":
            lines.extend(
                [
                    f"### Tool Call `{entry['name']}` [{entry['timestamp']}]",
                    "",
                    "```json",
                    str(entry["arguments"]).rstrip(),
                    "```",
                    "",
                ]
            )
        elif entry["kind"] == "tool_output":
            lines.extend(
                [
                    f"### Tool Output `{entry['name'] or 'unknown'}` [{entry['timestamp']}]",
                    "",
                    "```text",
                    str(entry["output"]).rstrip(),
                    "```",
                    "",
                ]
            )

    return meta.get("id", ""), "\n".join(lines).rstrip() + "\n"


def first_user_preview(entries: list[dict], max_len: int = 72) -> str:
    for e in entries:
        if e.get("kind") == "message" and e.get("role") == "user":
            text = (e.get("text") or "").strip()
            if text:
                one = " ".join(text.split())
                return (one[: max_len - 1] + "…") if len(one) > max_len else one
    return "(无用户首条消息)"


@dataclass
class CodexSessionEntry:
    path: Path
    session_id: str
    cwd: str
    started: str
    cli_version: str
    mtime: datetime | None
    preview: str


def collect_codex_sessions(sessions_dir: Path) -> list[CodexSessionEntry]:
    out: list[CodexSessionEntry] = []
    if not sessions_dir.is_dir():
        return out
    for session_path in sorted(sessions_dir.rglob("*.jsonl")):
        try:
            rows = load_jsonl_rows(session_path)
        except (OSError, json.JSONDecodeError):
            continue
        if not rows or rows[0].get("type") != "session_meta":
            continue
        meta, entries = parse_session_rows(rows)
        sid = meta.get("id") or ""
        if not sid:
            continue
        try:
            mtime = datetime.fromtimestamp(session_path.stat().st_mtime)
        except OSError:
            mtime = None
        out.append(
            CodexSessionEntry(
                path=session_path,
                session_id=sid,
                cwd=str(meta.get("cwd", "")),
                started=str(meta.get("timestamp", "")),
                cli_version=str(meta.get("cli_version", "")),
                mtime=mtime,
                preview=first_user_preview(entries),
            )
        )
    out.sort(key=lambda x: (x.mtime or datetime.min), reverse=True)
    return out


def print_session_rich(session_path: Path) -> None:
    try:
        rows = load_jsonl_rows(session_path)
    except (OSError, json.JSONDecodeError) as e:
        console.print(f"[red]读取失败: {e}[/red]")
        return
    if not rows or rows[0].get("type") != "session_meta":
        console.print("[yellow]不是有效的 Codex session JSONL（缺少 session_meta）。[/yellow]")
        return
    meta, entries = parse_session_rows(rows)
    meta_tbl = Table(show_header=False, box=None)
    meta_tbl.add_row("Session ID", meta.get("id", ""))
    meta_tbl.add_row("Started", str(meta.get("timestamp", "")))
    meta_tbl.add_row("CWD", str(meta.get("cwd", "")))
    meta_tbl.add_row("CLI", str(meta.get("cli_version", "")))
    meta_tbl.add_row("文件", str(session_path))
    console.print(Panel(meta_tbl, title="Codex 会话"))

    for e in entries:
        if e["kind"] == "message":
            role = "用户" if e["role"] == "user" else "助手"
            phase = f" · {e['phase']}" if e.get("phase") else ""
            title = f"{role}{phase} [{e['timestamp']}]"
            console.print(Panel(Text(e.get("text") or "[empty]"), title=title, expand=False))
        elif e["kind"] == "tool_call":
            title = f"工具调用 `{e['name']}` [{e['timestamp']}]"
            body = Syntax(
                str(e.get("arguments", "")),
                "json",
                theme="monokai",
                word_wrap=True,
            )
            console.print(Panel(body, title=title, expand=False))
        elif e["kind"] == "tool_output":
            title = f"工具输出 `{e.get('name') or 'unknown'}` [{e['timestamp']}]"
            console.print(
                Panel(
                    Text(str(e.get("output", ""))),
                    title=title,
                    expand=False,
                )
            )


def export_sessions(
    sessions_dir: Path,
    output_dir: Path,
    current_cwd: str,
) -> list[dict]:
    """Same behavior as skills/barksy_pipeline/codexhistory_export.export_sessions."""
    output_dir.mkdir(parents=True, exist_ok=True)
    existing_ids = find_existing_session_ids(output_dir)
    results: list[dict] = []

    for session_path in sorted(sessions_dir.rglob("*.jsonl")):
        try:
            rows = load_jsonl_rows(session_path)
        except (OSError, json.JSONDecodeError):
            continue
        if not rows:
            continue
        first = rows[0]
        if first.get("type") != "session_meta":
            continue
        meta = first.get("payload", {})
        if meta.get("cwd") != str(current_cwd):
            continue

        session_id, markdown = build_markdown(session_path, rows)
        if not session_id:
            continue
        if session_id in existing_ids:
            results.append({"session_id": session_id, "status": "skipped", "path": None})
            continue

        output_path = output_dir / f"{session_path.stem}.md"
        output_path.write_text(markdown, encoding="utf-8")
        existing_ids.add(session_id)
        results.append(
            {
                "session_id": session_id,
                "status": "exported",
                "path": str(output_path),
            }
        )

    return results


def run_interactive(sessions_root: Path, entries: list[CodexSessionEntry]) -> int:
    console.print(
        Panel.fit(
            f"[bold]Codex 会话[/bold]\n[dim]{sessions_root}[/dim]",
            title="扫描路径",
        )
    )
    choices = []
    for e in entries:
        mtime_str = e.mtime.strftime("%Y-%m-%d %H:%M") if e.mtime else "?"
        label = (
            f"[{mtime_str}] {e.session_id[:8]}…\n"
            f"    cwd: {e.cwd}\n"
            f"    {e.preview}"
        )
        choices.append(questionary.Choice(title=label, value=e))

    picked = questionary.select(
        "选择一条 Codex 会话（Enter 查看）",
        choices=choices,
        use_shortcuts=False,
    ).ask()
    if picked is None:
        return 0

    print_session_rich(picked.path)

    export_path = questionary.text(
        "导出为 Markdown 的文件路径或目录（留空跳过；若填目录则写入 <stem>.md）:",
    ).ask()
    if not export_path or not str(export_path).strip():
        return 0

    target = Path(str(export_path).strip()).expanduser()
    if target.is_dir() or str(export_path).strip().endswith(("/", "\\")):
        target.mkdir(parents=True, exist_ok=True)
        out_file = target / f"{picked.path.stem}.md"
    else:
        out_file = target
        out_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        rows = load_jsonl_rows(picked.path)
        _, md = build_markdown(picked.path, rows)
        out_file.write_text(md, encoding="utf-8")
        console.print(f"[green]已写入: {out_file}[/green]")
    except OSError as err:
        console.print(f"[red]写入失败: {err}[/red]")
        return 1
    return 0


def run_list_cli(entries: list[CodexSessionEntry], sessions_root: Path) -> None:
    print(f"共找到 {len(entries)} 条 Codex 会话（根目录: {sessions_root}）\n")
    for i, e in enumerate(entries, 1):
        mtime_str = e.mtime.strftime("%Y-%m-%d %H:%M") if e.mtime else "?"
        print(f"  {i:3d}  [{mtime_str}]  {e.session_id}")
        print(f"         cwd: {e.cwd}")
        print(f"         {e.preview}")


def run_view_cli(target: str, entries: list[CodexSessionEntry]) -> int:
    if target.isdigit():
        idx = int(target)
        if 1 <= idx <= len(entries):
            print_session_rich(entries[idx - 1].path)
            return 0
        console.print(f"[red]无效序号，请用 1 到 {len(entries)}。[/red]")
        return 1
    p = Path(target).expanduser()
    if p.is_file():
        print_session_rich(p)
        return 0
    console.print(f"[red]文件不存在: {p}[/red]")
    return 1


def run_copy_id_cli(idx_str: str, entries: list[CodexSessionEntry]) -> int:
    try:
        idx = int(idx_str)
    except ValueError:
        print("用法: copy-id <序号>", file=sys.stderr)
        return 1
    if 1 <= idx <= len(entries):
        sid = entries[idx - 1].session_id
        print(sid)
        if sys.platform == "win32":
            try:
                subprocess.run(
                    [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        f"Set-Clipboard -Value {repr(sid)}",
                    ],
                    check=True,
                    capture_output=True,
                    timeout=5,
                )
                print("(已复制到剪贴板)", file=sys.stderr)
            except Exception:
                pass
        return 0
    console.print(f"[red]无效序号。[/red]")
    return 1


def run_batch_export_cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="导出 cwd 匹配的 Codex 会话为 Markdown（与 barksy_pipeline 行为一致）。"
    )
    parser.add_argument(
        "--cwd",
        default=str(Path.cwd()),
        help="只导出 session_meta.cwd 与此路径一致的会话",
    )
    parser.add_argument(
        "--sessions-dir",
        default=str(default_sessions_dir()),
        help="Codex sessions 目录",
    )
    parser.add_argument(
        "--output-dir",
        default="codexhistory",
        help="Markdown 输出目录",
    )
    args = parser.parse_args(argv)
    results = export_sessions(
        Path(args.sessions_dir),
        Path(args.output_dir),
        args.cwd,
    )
    exported = sum(1 for item in results if item["status"] == "exported")
    skipped = sum(1 for item in results if item["status"] == "skipped")
    print(f"Exported {exported} session(s), skipped {skipped} existing session(s).")
    for item in results:
        suffix = f" -> {item['path']}" if item["path"] else ""
        print(f"{item['status']}: {item['session_id']}{suffix}")
    return 0


def run() -> int:
    sessions_root = default_sessions_dir()
    entries = collect_codex_sessions(sessions_root)

    if not entries:
        if sessions_root.is_dir():
            console.print(
                f"[yellow]在 {sessions_root} 下未发现有效 Codex session JSONL。[/yellow]"
            )
        else:
            console.print(
                f"[red]目录不存在: {sessions_root}[/red]\n"
                "可设置环境变量 [bold]CODEX_SESSIONS_DIR[/bold]。"
            )
        return 1

    return run_interactive(sessions_root, entries)


def main() -> None:
    argv = sys.argv[1:]
    try:
        if argv and argv[0] == "list":
            root = default_sessions_dir()
            ent = collect_codex_sessions(root)
            if not ent:
                print(f"未找到会话。根目录: {root}")
                raise SystemExit(1)
            run_list_cli(ent, root)
            raise SystemExit(0)
        if argv and argv[0] == "view" and len(argv) >= 2:
            target = argv[1]
            if target.isdigit():
                root = default_sessions_dir()
                ent = collect_codex_sessions(root)
                if not ent:
                    print(f"未找到会话。根目录: {root}")
                    raise SystemExit(1)
                raise SystemExit(run_view_cli(target, ent))
            raise SystemExit(run_view_cli(target, []))
        if argv and argv[0] == "copy-id" and len(argv) >= 2:
            root = default_sessions_dir()
            ent = collect_codex_sessions(root)
            if not ent:
                print(f"未找到会话。根目录: {root}")
                raise SystemExit(1)
            raise SystemExit(run_copy_id_cli(argv[1], ent))
        if argv and argv[0] == "batch-export":
            raise SystemExit(run_batch_export_cli(argv[1:]))
        if argv:
            console.print(
                "[yellow]未知子命令。[/yellow] 用法: list | view … | copy-id … | batch-export …"
            )
            raise SystemExit(1)
        raise SystemExit(run())
    except KeyboardInterrupt:
        console.print("\n[dim]已取消。[/dim]")
        raise SystemExit(130)


if __name__ == "__main__":
    main()
