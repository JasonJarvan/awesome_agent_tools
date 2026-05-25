# Cursor Chat Browser — reference

## Default `workspaceStorage` locations

| OS | Path |
|----|------|
| Windows | `%APPDATA%\Cursor\User\workspaceStorage` |
| Linux | `~/.config/Cursor/User/workspaceStorage` and, if present, `~/.cursor-server/data/User/workspaceStorage` |
| macOS | `~/Library/Application Support/Cursor/User/workspaceStorage` |

Override: set `CURSOR_WORKSPACE_STORAGE` to one or more roots separated by `;` (semicolon).

## SQLite

- File: `workspaceStorage/<hash>/state.vscdb`
- Table: `ItemTable`
- Key: `workbench.panel.aichat.view.aichat.chatdata` (JSON with `tabs[]`, aligned with [cursor-chat-export](https://github.com/somogyijanos/cursor-chat-export))

## Limitations

- WAL mode while Cursor is running: usually OK read-only; if locked or errors, fully exit Cursor and retry.
- Other UI surfaces (e.g. Composer) may use different storage; this tool only reflects the above key.
