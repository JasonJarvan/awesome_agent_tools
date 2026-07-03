---
name: cursor-chat-browser
description: >-
  Browses local Cursor AI chat data in workspaceStorage (SQLite state.vscdb) from
  the terminal: groups by project path, lists chat tabs, shows session summary.
  Use when the user wants to inspect, navigate, or export Cursor chat storage on
  disk, find sessions for a workspace, or debug where Cursor stores panel chat.
---

# Cursor Chat Browser

## What this does

Interactive TUI (questionary + rich) that:

1. Scans default `workspaceStorage` roots (and optional `CURSOR_WORKSPACE_STORAGE`).
2. Lists **workspaces that actually have** AI chat tabs in `ItemTable`.
3. After picking a workspace, lists **tabs** with a short user-message preview.

Bundled script: [scripts/cursor_chat_browser.py](../../scripts/cursor_chat_browser.py) (run from **plugin root**).

## When to use

- User asks to **see / list / browse** Cursor **panel chat** stored under `workspaceStorage`.
- User needs **which folder on disk** corresponds to a project’s chats.
- User hits **lock / WAL** issues and should **quit Cursor** first (read-only SQLite still may conflict).

## How to run (agent)

1. **Dependencies**: Python 3.10+, install from plugin root:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r scripts/requirements.txt
   ```

2. **Execute** (plugin root = directory that contains `.cursor-plugin/` and `scripts/`):

   ```bash
   python scripts/cursor_chat_browser.py
   ```

3. **Non-interactive limitation**: This tool is **menu-driven**; the user must operate the TUI (arrow keys, Enter). If the user only needs automation, point them to programmatic export tools (e.g. [cursor-chat-export](https://github.com/somogyijanos/cursor-chat-export)) or extend this script—do not pretend the menus ran without user input.

## Environment

| Variable | Meaning |
|----------|---------|
| `CURSOR_WORKSPACE_STORAGE` | Override `workspaceStorage` root; multiple paths separated by `;` |

Default paths and data-key details: [reference.md](reference.md).

## Safety and scope

- **Read-only** SQLite open; still avoid sharing exported content (may contain secrets).
- Only keys / shapes documented in reference are supported; **Composer** or future keys may need code changes.
