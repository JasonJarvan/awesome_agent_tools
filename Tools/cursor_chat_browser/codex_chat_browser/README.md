# Codex Chat Browser（终端）

在终端里**浏览**本机 **Codex CLI** 会话 JSONL（默认 `~/.codex/sessions`），用 Rich 展示消息与工具调用，并可**导出为 Markdown**。批量按 `cwd` 过滤导出与 [skills/barksy_pipeline/codexhistory_export.py](../../../skills/barksy_pipeline/codexhistory_export.py) 行为一致，对应本子命令 **`batch-export`**。

## 依赖

- Python **3.10+**
- `pip install -r requirements.txt`（`questionary`、`rich`）

## 用法

```bash
cd chat_browser/cursor_chat_browser/codex_chat_browser
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 交互：列出会话 → 选一条 → 终端内查看 → 可选导出 .md
python codex_chat_browser.py

# 仅列出
python codex_chat_browser.py list

# 按列表序号查看 / 按 JSONL 路径查看
python codex_chat_browser.py view 3
python codex_chat_browser.py view ~/.codex/sessions/.../foo.jsonl

# 复制第 N 条的 Session ID（Windows 下尝试写入剪贴板）
python codex_chat_browser.py copy-id 2

# 批量导出：仅 cwd 与 --cwd 一致的会话，跳过输出目录已有 Session ID（与 barksy 脚本一致）
python codex_chat_browser.py batch-export
python codex_chat_browser.py batch-export --cwd /path/to/project --output-dir ./codexhistory
```

## 环境变量

| 变量 | 说明 |
|------|------|
| `CODEX_SESSIONS_DIR` | 覆盖默认的 `~/.codex/sessions`（`list` / `view` 序号 / 交互模式均使用） |

## 数据说明

- 仅处理首行为 `session_meta` 的 JSONL；会话元数据含 `id`、`cwd`、`timestamp`、`cli_version` 等。
- **交互导出**：可输入**文件路径**或**目录**（目录下写入 `<jsonl 主名>.md`）。
- **`batch-export`**：与 `codexhistory_export.py` 相同——只导出 `payload.cwd` 等于 `--cwd` 的会话，且若某 Session ID 已在输出目录任意 `.md` 中出现则跳过。

## 与 barksy_pipeline 的关系

- **浏览 / 单条导出 / 列表**：请用本目录脚本。
- **项目内一键批量归档**：仍可使用 `skills/barksy_pipeline/codexhistory_export.py`，或使用本脚本的 `batch-export`（逻辑对齐，便于只维护一处时可逐步以本脚本为准）。

## 许可证

与所属仓库一致。
