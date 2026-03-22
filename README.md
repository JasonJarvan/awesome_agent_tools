## 项目简介

这是一个**本地 AI 工具聚合仓库**，用于集中维护与 Cursor / LLM 协作相关的小工具和技能（skills）。  
当前已包含：

- **`chat_browser/cursor_chat_browser/`**：终端内浏览 Cursor **AI Chat 面板（SQLite）**与 **Agent 转录（JSONL）** 的脚本与 Cursor 插件，详见 [chat_browser/cursor_chat_browser/README.md](chat_browser/cursor_chat_browser/README.md)
- **`skills/`（约定）**：存放零散的 AI 技能脚本，每个技能一个子文件夹，并配套自己的 `README.md`
  - **`skills/barksy_pipeline/`**：将 Codex 会话历史从 `~/.codex/sessions` 导出为 Markdown，详见 [skills/barksy_pipeline/README.md](skills/barksy_pipeline/README.md)

## 仓库结构约定

- **根目录**
  - `README.md`：当前文件，介绍整个工具聚合仓库
  - `AGENT.md`：给 Cursor / 代码助手看的“项目说明书”，约定目录结构与使用方式
  - `skills/`：用于存放各类独立的 AI 技能（可选，目前可以为空）

- **`chat_browser/cursor_chat_browser/`**
  - 入口脚本：`scripts/cursor_chat_browser.py`（合并了原「仅 Agent JSONL」查看器的全部能力）

- **`skills/` 目录约定**
  - 每个技能使用一个子文件夹，例如：
    - `skills/web-search/`
    - `skills/sql-helper/`
    - `skills/refactor-patterns/`
  - **每个子文件夹必须包含一个 `README.md`**，至少说明：
    - 这个 skill 的用途（做什么）
    - 适用场景 / 输入输出
    - 是否依赖外部服务或环境变量

> 提示：当前仓库内暂未强制创建这些子文件夹，你可以按需要逐步补充。只要遵守“每个 skill 子目录都带有 README”的约定即可。

## 工具：Cursor 聊天与 Agent 历史（cursor_chat_browser）

脚本路径：`chat_browser/cursor_chat_browser/scripts/cursor_chat_browser.py`

功能概要：

- **数据源一**：各系统下的 `workspaceStorage` → `state.vscdb` 中 AI Chat 面板的 Tab（键 `aichat.chatdata`）
- **数据源二**：`~/.cursor/projects/.../agent-transcripts/*.jsonl`（Agent 对话）
- 若两种数据在同一台机器上都存在，启动时会先选择数据源；仅存在一种则直接进入对应流程
- Agent 侧支持：交互浏览、`agent list` / `agent view` / `agent copy-id`（Windows 下 `copy-id` 可写剪贴板）、导出 Markdown
- 列表中将 Cursor 项目目录 slug（原用 `-` 编码的路径）显示为带 `/` 的路径样式（启发式）

### 安装与使用

在插件目录下（见子 README）安装依赖后：

```bash
cd chat_browser/cursor_chat_browser
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r scripts/requirements.txt

# 统一入口（自动识别 SQLite / JSONL / 双源）
python scripts/cursor_chat_browser.py

# 仅 Agent：交互
python scripts/cursor_chat_browser.py agent

# 仅 Agent：命令行
python scripts/cursor_chat_browser.py agent list
python scripts/cursor_chat_browser.py agent view 3
python scripts/cursor_chat_browser.py agent view "/path/to/xxx.jsonl"
python scripts/cursor_chat_browser.py agent copy-id 2
```

### 环境变量

| 变量 | 说明 |
|------|------|
| `CURSOR_WORKSPACE_STORAGE` | 手动指定 `workspaceStorage` 根目录，多个路径用英文分号 `;` 分隔 |
| `CURSOR_AGENT_TRANSCRIPTS_ROOT` | 指定扫描 `agent-transcripts` 的父目录（默认 `~/.cursor/projects`） |

### 数据路径（各平台）

- **Agent JSONL**
  - Windows：`%USERPROFILE%\.cursor\projects\<项目 slug>\agent-transcripts\<对话ID>\<对话ID>.jsonl`
  - macOS / Linux：`~/.cursor/projects/<项目 slug>/agent-transcripts/<对话ID>/<对话ID>.jsonl`
- **AI Chat SQLite**：见子目录 README 与 `skills/cursor-chat-browser/reference.md`

当项目 slug 对应「无文件夹」临时窗口时，Cursor 可能使用**纯数字**目录名；脚本会提示在 Cursor 内回到对应窗口继续会话。

## 关于对话历史存储位置（本机 vs 远程）

使用 **Cursor Remote（如从 Windows 连 Linux SSH）** 时：

- **Agent 转录（JSONL）** 常写在**你当前打开工程所在环境**的用户目录下，例如远程 Linux 上的 `~/.cursor/projects`（在远端终端跑脚本即可扫到）。
- **经典 AI Chat 面板状态（SQLite）** 往往在**运行 Cursor 窗口的客户端**（如 Windows 的 `%APPDATA%\Cursor\...`）；在纯远程 Linux 上可能只有空壳 `workspaceStorage` 或没有 `chatdata`。

因此应**在需要读的那一侧**运行脚本，或通过上述环境变量指向客户端上的 `workspaceStorage`（例如在 WSL 里挂载 Windows 路径）。
