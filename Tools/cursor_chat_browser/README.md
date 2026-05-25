# Cursor Chat Browser（终端 + Cursor 插件）

在终端里浏览 Cursor 的聊天相关数据：

1. **AI Chat 面板**：`workspaceStorage` → `state.vscdb`（SQLite，键 `aichat.chatdata`）
2. **Agent 对话**：`~/.cursor/projects/.../agent-transcripts/*.jsonl`

两种数据可在**同一台本机**（Windows / macOS / Linux 桌面 Cursor）同时存在；脚本会扫描两边，**若都有内容则先让你选数据源**。使用 **Remote SSH** 时，JSONL 常在远程机、`workspaceStorage` 里带完整聊天状态常在客户端——在对应机器上运行本脚本，或用手动环境变量指向客户端目录。

本目录已按 [Cursor Plugins](https://cursor.com/docs/plugins) 规范打包为可提交市场的插件：含 **manifest**、**Skill**（`skills/cursor-chat-browser/SKILL.md`）与 **脚本**（`scripts/`）。

## 目录结构（插件）

```text
cursor_chat_browser/
├── .cursor-plugin/
│   └── plugin.json
├── README.md
├── scripts/
│   ├── cursor_chat_browser.py
│   └── requirements.txt
└── skills/
    └── cursor-chat-browser/
        ├── SKILL.md
        └── reference.md
```

## 功能

- **SQLite（AI Chat）**
  - 自动定位各系统下常见的 `workspaceStorage`（见 `skills/cursor-chat-browser/reference.md`）
  - 仅列出在 `state.vscdb` 中**确实存在聊天 Tab** 的工作区
  - 通过 `workspace.json` 解析项目路径；Windows 下对路径做**大小写不敏感**合并
  - Linux 下额外尝试远程服务端路径：`~/.cursor-server/data/User/workspaceStorage`
- **JSONL（Agent）**
  - 扫描 `CURSOR_AGENT_TRANSCRIPTS_ROOT`（默认 `~/.cursor/projects`）下全部 `agent-transcripts`
  - 交互选择会话、Rich 展示全文、可选导出 Markdown
  - 命令行：`agent` | `agent list` | `agent view …` | `agent copy-id …`（Windows 下 `copy-id` 尝试写入剪贴板）
  - 列表中将 Cursor 的项目目录 slug（路径段原用 `-` 连接）显示为 **`/a/b/c` 形式**（启发式，便于阅读）

## 环境要求

- Python **3.10+**
- 依赖见 `scripts/requirements.txt`（`questionary`、`rich`）

## 安装与运行

在**本目录（插件根目录）**执行：

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r scripts/requirements.txt

# 统一入口（SQLite + JSONL）
python scripts/cursor_chat_browser.py

# 只要 Agent 子命令（与已移除的独立 viewer 等价）
python scripts/cursor_chat_browser.py agent
python scripts/cursor_chat_browser.py agent list
```

在菜单中用方向键选择，**Enter** 确认；**Ctrl+C** 退出。

## 本地加载插件（提交前自测）

1. 将本插件目录复制或**符号链接**到 `~/.cursor/plugins/local/cursor-chat-browser`（目录名可自定，但需包含 `.cursor-plugin/plugin.json`）。
2. 重启 Cursor 或执行 **Developer: Reload Window**。
3. 在 **Settings → Rules** 中确认 Skill **cursor-chat-browser** 出现；需要时在对话中用 `/cursor-chat-browser` 调用。

符号链接示例：

```bash
ln -s /path/to/cursor_chat_browser ~/.cursor/plugins/local/cursor-chat-browser
```

## 发布到 Cursor Marketplace

市场插件需为**公开 Git 仓库**，并由 Cursor **人工审核**。步骤摘要：

1. 将本目录（或包含本插件的仓库）推送到 GitHub 等公开远端。
2. 在 manifest 中补全 `repository` / `homepage`（可选但建议）。
3. 打开 [Publish Plugins](https://cursor.com/marketplace/publish) 提交仓库链接。
4. 对照官方 [Plugins reference · Submission checklist](https://cursor.com/docs/reference/plugins.md) 自检：有效 `plugin.json`、Skill 元数据、`README` 说明用法与限制。

官方文档：[Plugins](https://cursor.com/docs/plugins) · [Skills 格式](https://cursor.com/docs/skills.md)

## 环境变量

| 变量 | 说明 |
|------|------|
| `CURSOR_WORKSPACE_STORAGE` | 手动指定 `workspaceStorage` 根目录。多个路径用**英文分号** `;` 分隔（例如 WSL 访问 Windows 目录时）。设置后**不再**使用默认路径。 |
| `CURSOR_AGENT_TRANSCRIPTS_ROOT` | 指定包含各项目子目录的父路径（其下应有 `*/agent-transcripts/`）。默认 `~/.cursor/projects`。 |

## 数据说明与限制

- **AI Chat**：读取 `ItemTable` 中键 **`workbench.panel.aichat.view.aichat.chatdata`**（与 [cursor-chat-export](https://github.com/somogyijanos/cursor-chat-export) 一致）。若未来版本将 **Composer** 等存到其它键，需扩展查询逻辑。
- **Agent**：与 Cursor 写入的 JSONL 结构一致；首条用户消息可能为 `<attached_files>` 等占位，属数据源本身。
- Cursor 正在运行时 SQLite 可能处于 **WAL** 模式；本工具以只读打开，多数情况可用。若遇锁或损坏提示，可先完全退出 Cursor 再试。

## 许可证

与所属仓库一致；本工具为便于本地查看个人数据的辅助脚本，请自行承担使用风险并注意导出内容中的敏感信息。
