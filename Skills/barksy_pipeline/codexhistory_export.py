import argparse
import json
import re
from pathlib import Path


SESSION_ID_PATTERN = re.compile(r"Session ID:\s*`([^`]+)`")


def flatten_content(content):
    parts = []
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


def load_jsonl_rows(path):
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def find_existing_session_ids(output_dir):
    session_ids = set()
    for path in output_dir.glob("*.md"):
        content = path.read_text(encoding="utf-8")
        for match in SESSION_ID_PATTERN.findall(content):
            session_ids.add(match)
    return session_ids


def build_markdown(session_path, rows):
    meta = {}
    tool_names = {}
    entries = []

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
            tool_names[call_id] = payload.get("name", "")
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
                    "name": tool_names.get(payload.get("call_id"), ""),
                    "output": payload.get("output", ""),
                }
            )
            continue

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
                    entry["arguments"].rstrip(),
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
                    entry["output"].rstrip(),
                    "```",
                    "",
                ]
            )

    return meta.get("id", ""), "\n".join(lines).rstrip() + "\n"


def export_sessions(sessions_dir, output_dir, current_cwd):
    sessions_dir = Path(sessions_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    existing_ids = find_existing_session_ids(output_dir)
    results = []

    for session_path in sorted(sessions_dir.rglob("*.jsonl")):
        rows = load_jsonl_rows(session_path)
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


def build_parser():
    parser = argparse.ArgumentParser(
        description="Export Codex session history for the current project into Markdown files."
    )
    parser.add_argument(
        "--cwd",
        default=str(Path.cwd()),
        help="Only export sessions whose recorded cwd matches this path. Defaults to the current directory.",
    )
    parser.add_argument(
        "--sessions-dir",
        default=str(Path.home() / ".codex" / "sessions"),
        help="Codex sessions directory. Defaults to ~/.codex/sessions.",
    )
    parser.add_argument(
        "--output-dir",
        default="codexhistory",
        help="Directory to write Markdown exports into. Defaults to ./codexhistory.",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    results = export_sessions(args.sessions_dir, args.output_dir, args.cwd)
    exported = sum(1 for item in results if item["status"] == "exported")
    skipped = sum(1 for item in results if item["status"] == "skipped")
    print(f"Exported {exported} session(s), skipped {skipped} existing session(s).")
    for item in results:
        suffix = f" -> {item['path']}" if item["path"] else ""
        print(f"{item['status']}: {item['session_id']}{suffix}")


if __name__ == "__main__":
    main()
