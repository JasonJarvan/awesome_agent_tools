#!/usr/bin/env python3
"""
Browse Cursor chat-related storage from the terminal:

1) Classic AI Chat panel: workspaceStorage → state.vscdb (ItemTable key aichat.chatdata).
2) Agent transcripts: ~/.cursor/projects/.../agent-transcripts/*.jsonl.

Both (1) and (2) can exist on the same OS when using local desktop Cursor (Windows/macOS/Linux);
the script detects which stores have data and asks if both are non-empty. Remote-SSH splits them
across client vs server, which is a connection mode issue—not tied to a specific OS.

Optional env:
  CURSOR_WORKSPACE_STORAGE       workspaceStorage roots (semicolon-separated).
  CURSOR_AGENT_TRANSCRIPTS_ROOT  override ~/.cursor/projects parent for JSONL scan.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

CHAT_DATA_KEY = "workbench.panel.aichat.view.aichat.chatdata"


def default_workspace_storage_roots() -> list[Path]:
    roots: list[Path] = []
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            roots.append(Path(appdata) / "Cursor" / "User" / "workspaceStorage")
    elif sys.platform == "darwin":
        roots.append(
            Path.home()
            / "Library"
            / "Application Support"
            / "Cursor"
            / "User"
            / "workspaceStorage"
        )
    else:
        roots.append(Path.home() / ".config" / "Cursor" / "User" / "workspaceStorage")
        roots.append(Path.home() / ".cursor-server" / "data" / "User" / "workspaceStorage")

    override = os.environ.get("CURSOR_WORKSPACE_STORAGE", "").strip()
    if override:
        return [Path(p.strip()).expanduser() for p in override.split(";") if p.strip()]

    return [p for p in roots if p.is_dir()]


def default_agent_projects_root() -> Path:
    raw = os.environ.get("CURSOR_AGENT_TRANSCRIPTS_ROOT", "").strip()
    if raw:
        return Path(raw).expanduser()
    return Path.home() / ".cursor" / "projects"


_UUID_SLUG = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

# Cursor project folder names often encode paths by replacing / (and \\) with "-".
_PATH_SLUG_PREFIXES = (
    "home-",
    "mnt-",
    "media-",
    "var-",
    "opt-",
    "usr-",
    "root-",
    "srv-",
    "private-",
    "users-",
    "Users-",
)


def project_slug_to_display_path(slug: str) -> str:
    """Show a path-like label with '/' between segments instead of '-' (heuristic)."""
    if not slug:
        return slug
    if slug.isdigit():
        return slug
    if _UUID_SLUG.match(slug):
        return slug
    m = re.match(r"^([a-zA-Z])-(.+)$", slug)
    if m and slug.count("-") >= 2:
        drive, rest = m.group(1).upper(), m.group(2)
        return f"{drive}:/{rest.replace('-', '/')}"
    lower = slug.lower()
    if any(lower.startswith(p) for p in _PATH_SLUG_PREFIXES):
        return "/" + slug.replace("-", "/")
    if slug.count("-") >= 2:
        return "/" + slug.replace("-", "/")
    return slug


def file_uri_to_display_path(uri: str) -> str:
    parsed = urlparse(uri)
    if parsed.scheme != "file":
        return uri
    path = unquote(parsed.path or "")
    if sys.platform == "win32" and len(path) >= 3 and path[0] == "/" and path[2] == ":":
        path = path[1:]
    return path or uri


def read_workspace_identity(ws_dir: Path) -> str:
    wj = ws_dir / "workspace.json"
    if not wj.is_file():
        return f"<unknown> ({ws_dir.name})"
    try:
        data = json.loads(wj.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return f"<unreadable workspace.json> ({ws_dir.name})"

    folder = data.get("folder") or data.get("folderUri")
    if isinstance(folder, str) and folder:
        return file_uri_to_display_path(folder)

    workspace = data.get("workspace")
    if isinstance(workspace, str) and workspace:
        return file_uri_to_display_path(workspace)

    return f"<no folder in workspace.json> ({ws_dir.name})"


def open_sqlite_ro(db_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=2.0)


def fetch_chat_tabs(db_path: Path) -> list[dict] | None:
    try:
        conn = open_sqlite_ro(db_path)
    except sqlite3.Error:
        return None
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT value FROM ItemTable WHERE key = ? LIMIT 1",
            (CHAT_DATA_KEY,),
        )
        row = cur.fetchone()
    finally:
        conn.close()

    if not row or row[0] is None:
        return None
    try:
        payload = json.loads(row[0])
    except json.JSONDecodeError:
        return None
    tabs = payload.get("tabs")
    if not isinstance(tabs, list) or not tabs:
        return None
    return tabs


def first_user_preview(tab: dict, max_len: int = 72) -> str:
    for bubble in tab.get("bubbles") or []:
        if bubble.get("type") != "user":
            continue
        text = (
            bubble.get("text")
            or bubble.get("rawText")
            or bubble.get("initText")
            or ""
        )
        if isinstance(text, str) and text.strip():
            one = " ".join(text.split())
            return (one[: max_len - 1] + "…") if len(one) > max_len else one
    return "(无用户首条消息)"


@dataclass
class WorkspaceEntry:
    storage_dir: Path
    db_path: Path
    label: str
    mtime: float
    tabs: list[dict]


def collect_entries(roots: list[Path]) -> list[WorkspaceEntry]:
    out: list[WorkspaceEntry] = []
    for root in roots:
        if not root.is_dir():
            continue
        try:
            children = list(root.iterdir())
        except OSError:
            continue
        for ws_dir in children:
            if not ws_dir.is_dir():
                continue
            db = ws_dir / "state.vscdb"
            if not db.is_file():
                continue
            tabs = fetch_chat_tabs(db)
            if not tabs:
                continue
            try:
                mtime = db.stat().st_mtime
            except OSError:
                mtime = 0.0
            label = read_workspace_identity(ws_dir)
            out.append(
                WorkspaceEntry(
                    storage_dir=ws_dir,
                    db_path=db,
                    label=label,
                    mtime=mtime,
                    tabs=tabs,
                )
            )
    out.sort(key=lambda e: e.mtime, reverse=True)
    return out


def group_by_label(entries: list[WorkspaceEntry]) -> dict[str, list[WorkspaceEntry]]:
    buckets: dict[str, list[WorkspaceEntry]] = {}
    display_for_bucket: dict[str, str] = {}
    for e in entries:
        bucket_key = e.label.casefold() if sys.platform == "win32" else e.label
        buckets.setdefault(bucket_key, []).append(e)
        display_for_bucket.setdefault(bucket_key, e.label)
    return {display_for_bucket[k]: buckets[k] for k in buckets}


def path_basename_label(label: str) -> str:
    s = label.replace("\\", "/").rstrip("/")
    return s.rsplit("/", 1)[-1] if s else label


# --- Agent JSONL ---


def extract_text_from_message(msg: dict | None) -> str:
    if not msg or "content" not in msg:
        return ""
    parts: list[str] = []
    for block in msg.get("content") or []:
        if isinstance(block, dict) and block.get("type") == "text" and "text" in block:
            parts.append(block["text"])
    return "\n".join(parts)


def first_user_query_line(text: str) -> str:
    if not text:
        return "(无标题)"
    text = text.strip()
    if text.startswith("<user_query>"):
        text = text[len("<user_query>") :].strip()
    first_line = text.split("\n")[0].strip()
    return (first_line[:60] + "…") if len(first_line) > 60 else first_line


def collect_agent_transcripts(root: Path) -> list[dict]:
    root = Path(root)
    if not root.is_dir():
        return []
    out: list[dict] = []
    try:
        project_dirs = list(root.iterdir())
    except OSError:
        return []
    for project_dir in project_dirs:
        if not project_dir.is_dir():
            continue
        at_dir = project_dir / "agent-transcripts"
        if not at_dir.is_dir():
            continue
        try:
            chat_dirs = list(at_dir.iterdir())
        except OSError:
            continue
        for chat_dir in chat_dirs:
            if not chat_dir.is_dir():
                continue
            for f in chat_dir.glob("*.jsonl"):
                try:
                    mtime = datetime.fromtimestamp(f.stat().st_mtime)
                except OSError:
                    mtime = None
                out.append(
                    {
                        "path": f,
                        "project_id": project_dir.name,
                        "chat_id": chat_dir.name,
                        "mtime": mtime,
                    }
                )
    out.sort(key=lambda x: (x["mtime"] or datetime.min), reverse=True)
    return out


def agent_transcript_title(entry: dict) -> str:
    path = entry["path"]
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if obj.get("role") == "user" and "message" in obj:
                        text = extract_text_from_message(obj["message"])
                        return first_user_query_line(text)
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return "(无法读取标题)"


def is_no_folder_project(project_id: str) -> bool:
    return project_id.isdigit()


def format_transcript_lines(path: Path) -> list[tuple[str, str]]:
    path = Path(path)
    lines: list[tuple[str, str]] = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    role = obj.get("role", "?")
                    text = extract_text_from_message(obj.get("message") or {})
                    if not text and role != "user":
                        continue
                    if role == "user":
                        if text.startswith("<user_query>"):
                            text = text[len("<user_query>") :].strip()
                        if text.endswith("</user_query>"):
                            text = text[: -len("</user_query>")].strip()
                        lines.append(("user", text))
                    else:
                        lines.append(("assistant", text))
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return lines


def export_transcript_to_dir(transcript_path: Path, output_dir: Path) -> bool:
    transcript_path = Path(transcript_path)
    output_dir = Path(output_dir)
    if not transcript_path.is_file() or not output_dir.is_dir():
        return False
    conversation_id = transcript_path.stem
    out_file = output_dir / f"{conversation_id}.md"
    lines = format_transcript_lines(transcript_path)
    try:
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(f"# 对话记录: {conversation_id}\n\n")
            for role, text in lines:
                label = "【用户】" if role == "user" else "【助手】"
                f.write(f"## {label}\n\n{text}\n\n")
        return True
    except OSError:
        return False


def print_agent_transcript(entry: dict) -> None:
    path: Path = entry["path"]
    project_id: str = entry["project_id"]
    chat_id: str = entry["chat_id"]
    lines = format_transcript_lines(path)
    meta = Table(show_header=False, box=None)
    meta.add_row("conversationId", chat_id)
    meta.add_row("工作区", project_slug_to_display_path(project_id))
    meta.add_row("文件", str(path))
    if is_no_folder_project(project_id):
        meta.add_row(
            "提示",
            "无目录窗口对话：请在 Cursor 中回到该临时窗口，在聊天历史里切换。",
        )
    console.print(Panel(meta, title="Agent 会话信息"))
    if not lines:
        console.print("[yellow](无内容或读取失败)[/yellow]")
        return
    for role, text in lines:
        label = "用户" if role == "user" else "助手"
        console.print(Panel(Text(text), title=label, expand=False))


def run_workspace_flow(roots: list[Path], entries: list[WorkspaceEntry]) -> int:
    groups = group_by_label(entries)
    sorted_labels = sorted(
        groups.keys(),
        key=lambda lbl: max(e.mtime for e in groups[lbl]),
        reverse=True,
    )

    choices = []
    for lbl in sorted_labels:
        elist = groups[lbl]
        total_tabs = sum(len(e.tabs) for e in elist)
        hint = f"{total_tabs} 个会话 · {path_basename_label(lbl)}"
        choices.append(questionary.Choice(title=f"{lbl}\n    ({hint})", value=lbl))

    lines = ["[bold]workspaceStorage（AI Chat 面板）[/bold]"]
    if roots:
        lines.extend(f"[dim]{r}[/dim]" for r in roots)
    console.print(Panel.fit("\n".join(lines), title="数据源"))

    picked = questionary.select(
        "选择一个工作区目录（Enter 确认）",
        choices=choices,
        use_shortcuts=False,
    ).ask()

    if picked is None:
        return 0

    group_entries = groups[picked]
    session_rows: list[tuple[str, WorkspaceEntry, int, dict]] = []
    for ent in sorted(group_entries, key=lambda e: e.mtime, reverse=True):
        for idx, tab in enumerate(ent.tabs):
            session_rows.append((f"{ent.storage_dir.name} · Tab {idx + 1}", ent, idx, tab))

    sess_choices = []
    for title, ent, idx, tab in session_rows:
        preview = first_user_preview(tab)
        ts = tab.get("timestamp") or tab.get("lastSendTime") or ""
        sub = preview
        if ts:
            sub += f" · ts={ts}"
        sess_choices.append(
            questionary.Choice(title=f"{title}\n    {sub}", value=(ent, idx, tab))
        )

    sel = questionary.select(
        "该目录下的 Cursor 会话（Enter 查看摘要）",
        choices=sess_choices,
        use_shortcuts=False,
    ).ask()

    if sel is None:
        return 0

    ent, idx, tab = sel
    table = Table(show_header=False, box=None)
    table.add_row("工作区标签", picked)
    table.add_row("存储目录", str(ent.storage_dir))
    table.add_row("数据库", str(ent.db_path))
    table.add_row("Tab", str(idx + 1))
    table.add_row("气泡数", str(len(tab.get("bubbles") or [])))
    console.print(Panel(table, title="会话信息"))
    console.print(
        Panel(
            first_user_preview(tab, max_len=500),
            title="首条用户消息预览",
        )
    )
    return 0


def run_agent_interactive(projects_root: Path, entries: list[dict]) -> int:
    lines = ["[bold]Agent 转录（JSONL）[/bold]", f"[dim]{projects_root}[/dim]"]
    console.print(Panel.fit("\n".join(lines), title="数据源"))

    choices = []
    for e in entries:
        mtime_str = e["mtime"].strftime("%Y-%m-%d %H:%M") if e["mtime"] else "?"
        title_line = agent_transcript_title(e)
        loc = project_slug_to_display_path(e["project_id"])
        label = f"[{mtime_str}] {loc} · {e['chat_id']}\n    {title_line}"
        choices.append(questionary.Choice(title=label, value=e))

    picked = questionary.select(
        "选择一条 Agent 对话（Enter 查看全文）",
        choices=choices,
        use_shortcuts=False,
    ).ask()

    if picked is None:
        return 0

    print_agent_transcript(picked)

    export_path = questionary.text(
        "导出为 Markdown 的目录路径（留空跳过）:",
    ).ask()

    if not export_path or not str(export_path).strip():
        return 0

    export_dir = Path(str(export_path).strip()).expanduser()
    if export_dir.exists() and not export_dir.is_dir():
        console.print(f"[red]路径已存在但不是目录: {export_dir}[/red]")
        return 1
    if not export_dir.is_dir():
        console.print(f"[yellow]目录不存在: {export_dir}[/yellow]")
        if not questionary.confirm("是否创建该目录并导出？", default=True).ask():
            return 0
        try:
            export_dir.mkdir(parents=True, exist_ok=True)
        except OSError as err:
            console.print(f"[red]创建目录失败: {err}[/red]")
            return 1

    if export_transcript_to_dir(picked["path"], export_dir):
        out_name = picked["path"].stem + ".md"
        console.print(f"[green]已导出到: {export_dir / out_name}[/green]")
    else:
        console.print("[red]导出失败。[/red]")
    return 0


def run_agent_cli(argv: list[str]) -> int:
    root = default_agent_projects_root()
    if not argv:
        entries = collect_agent_transcripts(root)
        if not entries:
            print(f"未找到任何 Agent 对话记录。\n根目录: {root}")
            print("请确认 Cursor 的 agent-transcripts 位于上述目录下。")
            return 1
        return run_agent_interactive(root, entries)

    if argv[0] == "list":
        entries = collect_agent_transcripts(root)
        print(f"共找到 {len(entries)} 条 Agent 对话（根目录: {root}）\n")
        has_no_folder = False
        for i, e in enumerate(entries, 1):
            title = agent_transcript_title(e)
            mtime_str = e["mtime"].strftime("%Y-%m-%d %H:%M") if e["mtime"] else "?"
            proj = e["project_id"]
            loc = project_slug_to_display_path(proj)
            if is_no_folder_project(proj):
                has_no_folder = True
            print(f"  {i:3d}  [{mtime_str}]  {loc}  |  conversationId: {e['chat_id']}")
            print(f"         {title}")
        if has_no_folder:
            print(
                "\n  [说明] 项目名为纯数字的对话来自「未打开文件夹」的临时窗口；"
                "要在 Cursor 里继续该对话请回到对应窗口。"
            )
        return 0

    if argv[0] == "view" and len(argv) >= 2:
        target = argv[1]
        if target.isdigit():
            entries = collect_agent_transcripts(root)
            idx = int(target)
            if 1 <= idx <= len(entries):
                e = entries[idx - 1]
                _cli_view_transcript(e["path"], e["project_id"])
            else:
                print(f"无效序号，请用 1 到 {len(entries)} 之间的数字。", file=sys.stderr)
                return 1
        else:
            _cli_view_transcript(Path(target), None)
        return 0

    if argv[0] == "copy-id" and len(argv) >= 2:
        entries = collect_agent_transcripts(root)
        try:
            idx = int(argv[1])
        except ValueError:
            print("用法: agent copy-id <序号>", file=sys.stderr)
            return 1
        if 1 <= idx <= len(entries):
            cid = entries[idx - 1]["chat_id"]
            print(cid)
            if sys.platform == "win32":
                try:
                    subprocess.run(
                        [
                            "powershell",
                            "-NoProfile",
                            "-Command",
                            f"Set-Clipboard -Value {repr(cid)}",
                        ],
                        check=True,
                        capture_output=True,
                        timeout=5,
                    )
                    print("(已复制到剪贴板)", file=sys.stderr)
                except Exception:
                    pass
            return 0
        print(f"无效序号，请用 1 到 {len(entries)} 之间的数字。", file=sys.stderr)
        return 1

    print(
        "用法: agent | agent list | agent view <序号|jsonl路径> | agent copy-id <序号>",
        file=sys.stderr,
    )
    return 1


def _cli_view_transcript(path: Path, project_id: str | None) -> None:
    path = Path(path)
    if not path.is_file():
        print(f"文件不存在: {path}", file=sys.stderr)
        return
    conversation_id = path.stem
    print(f"\n========== 对话记录: {path.name} ==========")
    print(f"  conversationId: {conversation_id}")
    if project_id and is_no_folder_project(project_id):
        print("  [无目录对话] 请在 Cursor 中回到该临时窗口继续。")
    print()
    lines = format_transcript_lines(path)
    if not lines:
        print("(无内容或读取失败)", file=sys.stderr)
        return
    for role, text in lines:
        label = "【用户】" if role == "user" else "【助手】"
        print(label)
        print(text)
        print()


def run() -> int:
    roots = default_workspace_storage_roots()
    agent_root = default_agent_projects_root()
    sqlite_entries = collect_entries(roots)
    agent_entries = collect_agent_transcripts(agent_root)

    if not sqlite_entries and not agent_entries:
        if roots:
            console.print(
                "[yellow]在以下路径未发现含聊天标签页的 state.vscdb：[/yellow]\n"
                + "\n".join(f"  • {r}" for r in roots)
            )
        else:
            console.print(
                "[red]未找到 Cursor 的 workspaceStorage 目录。[/red]\n"
                "可设置 [bold]CURSOR_WORKSPACE_STORAGE[/bold] 指向该目录（多个用分号分隔）。"
            )
        if agent_root.is_dir():
            console.print(
                f"\n[yellow]在 {agent_root} 下未发现 agent-transcripts（*.jsonl）。[/yellow]"
            )
        else:
            console.print(
                f"\n[yellow]Agent 扫描根目录不存在: {agent_root}[/yellow]\n"
                "可设置 [bold]CURSOR_AGENT_TRANSCRIPTS_ROOT[/bold]。"
            )
        console.print(
            "\n[dim]提示：远程 SSH 到 Linux 时 Agent 记录通常在 "
            f"{Path.home() / '.cursor' / 'projects'}；"
            "AI Chat 面板状态常在装有 Cursor 窗口的机器上的 workspaceStorage。[/dim]"
        )
        return 1 if not roots and not agent_root.is_dir() else 0

    if sqlite_entries and agent_entries:
        src = questionary.select(
            "选择数据源",
            choices=[
                questionary.Choice(
                    title="AI Chat 面板（workspaceStorage / SQLite）",
                    value="sqlite",
                ),
                questionary.Choice(
                    title="Agent 转录（~/.cursor/projects / JSONL）",
                    value="agent",
                ),
            ],
            use_shortcuts=False,
        ).ask()
        if src is None:
            return 0
        if src == "sqlite":
            return run_workspace_flow(roots, sqlite_entries)
        return run_agent_interactive(agent_root, agent_entries)

    if sqlite_entries:
        return run_workspace_flow(roots, sqlite_entries)
    return run_agent_interactive(agent_root, agent_entries)


def main() -> None:
    try:
        argv = sys.argv[1:]
        if argv and argv[0] == "agent":
            raise SystemExit(run_agent_cli(argv[1:]))
        raise SystemExit(run())
    except KeyboardInterrupt:
        console.print("\n[dim]已取消。[/dim]")
        raise SystemExit(130)


if __name__ == "__main__":
    main()
