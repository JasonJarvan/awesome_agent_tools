#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor Agent 对话记录查看器
扫描 .cursor/projects 下所有 agent-transcripts，列出并查看 JSONL 对话内容。

用法:
  python cursor_agent_transcript_viewer.py           # 交互：列清单→选序号查看→可输入目录导出或回车退出
  python cursor_agent_transcript_viewer.py list      # 仅列出所有对话（含对话 ID）
  python cursor_agent_transcript_viewer.py view 3    # 查看第 3 条
  python cursor_agent_transcript_viewer.py view "C:\\...\\xxx.jsonl"  # 按路径查看
  python cursor_agent_transcript_viewer.py copy-id 2 # 复制第 2 条的对话 ID 到剪贴板
  # 交互模式下展示会话后：直接回车退出；输入目录则导出。若目录不存在则提示「按回车创建并导出，按 ESC 退出」

环境变量 CURSOR_AGENT_TRANSCRIPTS_ROOT 可指定扫描根目录，默认 ~/.cursor/projects

关于「无目录」对话（project 为纯数字如 1773280448224）：
  这类对话来自「未打开文件夹」的临时窗口。要继续并尽量利用 KV cache，只能在同一
  窗口内切回该对话；Cursor 目前不支持通过对话 ID 直接打开。若窗口已关：可尝试
  File → Open Recent 中是否有「无文件夹」项，或完全退出 Cursor 后重启并选择恢复上次会话。
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime


def _read_enter_or_esc():
    """等待用户按回车或 ESC，返回 'enter' 或 'esc'。"""
    if sys.platform == "win32":
        try:
            import msvcrt
            while True:
                ch = msvcrt.getwch()
                if ch in ("\r", "\n"):
                    return "enter"
                if ch == "\x1b":
                    return "esc"
        except Exception:
            pass
    else:
        try:
            import tty
            import termios
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch = sys.stdin.read(1)
                if ch in ("\r", "\n"):
                    return "enter"
                if ch == "\x1b":
                    return "esc"
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
        except Exception:
            pass
    # 降级：用 input，回车=创建，输入 n=退出
    try:
        line = input().strip().lower()
        return "esc" if line == "n" else "enter"
    except (EOFError, KeyboardInterrupt):
        return "esc"

# 默认 Cursor 项目根目录（存放各项目 agent-transcripts 的上级）
def _default_projects_root():
    home = Path.home()
    return home / ".cursor" / "projects"

PROJECTS_ROOT = Path(os.environ.get("CURSOR_AGENT_TRANSCRIPTS_ROOT", str(_default_projects_root())))


def _extract_text_from_message(msg):
    """从 message 中提取可读文本（只取 type=text 的 content）。"""
    if not msg or "content" not in msg:
        return ""
    parts = []
    for block in msg.get("content") or []:
        if isinstance(block, dict) and block.get("type") == "text" and "text" in block:
            parts.append(block["text"])
    return "\n".join(parts)


def _first_user_query_line(text):
    """从首条用户消息中取一行作为标题，去掉 <user_query> 包装。"""
    if not text:
        return "(无标题)"
    text = text.strip()
    if text.startswith("<user_query>"):
        text = text[len("<user_query>"):].strip()
    first_line = text.split("\n")[0].strip()
    return (first_line[:60] + "…") if len(first_line) > 60 else first_line


def collect_transcripts(root: Path):
    """收集所有 agent-transcripts 下的 .jsonl 文件。"""
    root = Path(root)
    if not root.is_dir():
        return []
    out = []
    for project_dir in root.iterdir():
        if not project_dir.is_dir():
            continue
        at_dir = project_dir / "agent-transcripts"
        if not at_dir.is_dir():
            continue
        for chat_dir in at_dir.iterdir():
            if not chat_dir.is_dir():
                continue
            for f in chat_dir.glob("*.jsonl"):
                try:
                    mtime = datetime.fromtimestamp(f.stat().st_mtime)
                except OSError:
                    mtime = None
                out.append({
                    "path": f,
                    "project_id": project_dir.name,
                    "chat_id": chat_dir.name,
                    "mtime": mtime,
                })
    # 按修改时间倒序
    out.sort(key=lambda x: (x["mtime"] or datetime.min), reverse=True)
    return out


def get_title(entry):
    """读取首条用户消息作为标题。"""
    path = entry["path"]
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if obj.get("role") == "user" and "message" in obj:
                        text = _extract_text_from_message(obj["message"])
                        return _first_user_query_line(text)
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return "(无法读取标题)"


def _is_no_folder_project(project_id: str) -> bool:
    """project_id 为纯数字时表示无目录的临时窗口。"""
    return project_id.isdigit()


def list_transcripts(entries, with_title=True, show_conversation_id=True):
    """打印对话列表。"""
    has_no_folder = False
    for i, e in enumerate(entries, 1):
        title = get_title(e) if with_title else ""
        mtime_str = e["mtime"].strftime("%Y-%m-%d %H:%M") if e["mtime"] else "?"
        proj = e["project_id"]
        if _is_no_folder_project(proj):
            has_no_folder = True
        line = f"  {i:3d}  [{mtime_str}]  {proj}"
        if show_conversation_id:
            line += f"  |  conversationId: {e['chat_id']}"
        print(line)
        if with_title and title:
            print(f"         {title}")
    if has_no_folder:
        print("\n  [说明] 项目名为纯数字（如 1773280448224）的对话来自「未打开文件夹」的临时窗口。"
              "要继续该对话并利用 KV cache，请在 Cursor 中回到该窗口并在聊天历史里切换；"
              "若已关闭，可尝试 File → Open Recent 或重启后恢复上次会话。")
    return len(entries)


def view_transcript(path: Path, project_id: str = None):
    """逐条打印一场对话。"""
    path = Path(path)
    if not path.is_file():
        print(f"文件不存在: {path}", file=sys.stderr)
        return
    conversation_id = path.stem  # 文件夹名与 .jsonl 主名相同，即 conversationId
    print(f"\n========== 对话记录: {path.name} ==========")
    print(f"  conversationId: {conversation_id}")
    if project_id and _is_no_folder_project(project_id):
        print("  [无目录对话] 要继续请在 Cursor 中回到该临时窗口，在聊天历史里切换到此对话。")
    print()
    lines = _format_transcript_lines(path)
    if not lines:
        print("(无内容或读取失败)", file=sys.stderr)
        return
    for role, text in lines:
        label = "【用户】" if role == "user" else "【助手】"
        print(label)
        print(text)
        print()


def _format_transcript_lines(path: Path):
    """从 JSONL 生成可读的对话行（用于打印或导出）。"""
    path = Path(path)
    lines = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    role = obj.get("role", "?")
                    text = _extract_text_from_message(obj.get("message") or {})
                    if not text and role != "user":
                        continue
                    if role == "user":
                        if text.startswith("<user_query>"):
                            text = text[len("<user_query>"):].strip()
                        if text.endswith("</user_query>"):
                            text = text[:-len("</user_query>")].strip()
                        lines.append(("user", text))
                    else:
                        lines.append(("assistant", text))
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return lines


def export_transcript_to_dir(transcript_path: Path, output_dir: Path) -> bool:
    """将对话导出到指定目录，文件名为 {conversationId}.md。返回是否成功。"""
    transcript_path = Path(transcript_path)
    output_dir = Path(output_dir)
    if not transcript_path.is_file():
        return False
    if not output_dir.is_dir():
        return False
    conversation_id = transcript_path.stem
    out_file = output_dir / f"{conversation_id}.md"
    lines = _format_transcript_lines(transcript_path)
    try:
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(f"# 对话记录: {conversation_id}\n\n")
            for role, text in lines:
                label = "【用户】" if role == "user" else "【助手】"
                f.write(f"## {label}\n\n{text}\n\n")
        return True
    except OSError:
        return False


def main():
    root = PROJECTS_ROOT
    args = sys.argv[1:]

    if args and args[0] == "list":
        entries = collect_transcripts(root)
        print(f"共找到 {len(entries)} 条 Agent 对话（根目录: {root}）\n")
        list_transcripts(entries)
        return

    if args and args[0] == "view" and len(args) >= 2:
        target = args[1]
        if target.isdigit():
            entries = collect_transcripts(root)
            idx = int(target)
            if 1 <= idx <= len(entries):
                e = entries[idx - 1]
                view_transcript(e["path"], project_id=e["project_id"])
            else:
                print(f"无效序号，请用 1 到 {len(entries)} 之间的数字。", file=sys.stderr)
        else:
            view_transcript(Path(target))
        return

    if args and args[0] == "copy-id" and len(args) >= 2:
        entries = collect_transcripts(root)
        try:
            idx = int(args[1])
            if 1 <= idx <= len(entries):
                cid = entries[idx - 1]["chat_id"]
                print(cid)
                # 尝试写入剪贴板（Windows PowerShell）
                try:
                    import subprocess
                    subprocess.run(
                        ["powershell", "-NoProfile", "-Command", f"Set-Clipboard -Value {repr(cid)}"],
                        check=True, capture_output=True, timeout=5
                    )
                    print("(已复制到剪贴板)", file=sys.stderr)
                except Exception:
                    pass
            else:
                print(f"无效序号，请用 1 到 {len(entries)} 之间的数字。", file=sys.stderr)
        except ValueError:
            print("用法: copy-id <序号>", file=sys.stderr)
        return

    # 交互模式
    entries = collect_transcripts(root)
    if not entries:
        print(f"未找到任何 Agent 对话记录。\n根目录: {root}")
        print("请确认 Cursor 的 agent-transcripts 位于上述目录下。")
        return

    print(f"共找到 {len(entries)} 条 Agent 对话（根目录: {root}）\n")
    list_transcripts(entries)
    print("\n输入序号查看该对话，直接回车退出: ", end="")
    try:
        line = input().strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return
    if not line:
        return
    viewed_path = None
    if line.isdigit():
        idx = int(line)
        if 1 <= idx <= len(entries):
            e = entries[idx - 1]
            viewed_path = e["path"]
            view_transcript(viewed_path, project_id=e["project_id"])
        else:
            print(f"无效序号: {idx}")
            return
    else:
        candidate = Path(line)
        if candidate.is_file():
            viewed_path = candidate
            view_transcript(viewed_path)
        else:
            print(f"文件不存在: {candidate}", file=sys.stderr)
            return

    # 展示后：输入目录则导出，直接回车退出
    if viewed_path is None:
        return
    print("输入目录路径导出对话，直接回车退出: ", end="")
    try:
        export_dir_input = input().strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return
    if not export_dir_input:
        return
    export_dir = Path(export_dir_input)
    if not export_dir.is_dir():
        if export_dir.exists():
            print(f"错误：路径已存在但不是目录: {export_dir}", file=sys.stderr)
            return
        print(f"目录不存在: {export_dir}")
        print("按回车创建该目录并导出，按 ESC 退出: ", end="", flush=True)
        key = _read_enter_or_esc()
        print()
        if key == "esc":
            return
        try:
            export_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"创建目录失败: {e}", file=sys.stderr)
            return
    if export_transcript_to_dir(viewed_path, export_dir):
        out_name = viewed_path.stem + ".md"
        print(f"已导出到: {export_dir / out_name}")
    else:
        print("导出失败。", file=sys.stderr)


if __name__ == "__main__":
    main()

