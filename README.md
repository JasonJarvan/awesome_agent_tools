## 项目简介

这是一个**本地 AI 工具聚合仓库**，用于集中维护与 Cursor / LLM 协作相关的小工具和技能（skills）。  
当前已包含：

- **`cursor_history_viewer.py`**：在本地浏览 Cursor Agent（Composer）对话历史的命令行工具
- **`skills/`（约定）**：存放零散的 AI 技能脚本，每个技能一个子文件夹，并配套自己的 `README.md`

## 仓库结构约定

- **根目录**
  - `cursor_history_viewer.py`：Cursor Agent 对话记录查看器脚本
  - `README.md`：当前文件，介绍整个工具聚合仓库
  - `AGENT.md`：给 Cursor / 代码助手看的“项目说明书”，约定目录结构与使用方式
  - `skills/`：用于存放各类独立的 AI 技能（可选，目前可以为空）

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

## 工具：Cursor 对话历史查看器

脚本：`cursor_history_viewer.py`

功能：

- 扫描 `~/.cursor/projects`（或通过环境变量自定义）下所有项目的 `agent-transcripts`
- 列出所有 Agent 对话记录，展示`项目 ID`、`conversationId` 与首条用户消息摘要
- 支持按序号查看某条对话，并以【用户】/【助手】的形式打印
- 支持将指定对话导出为 Markdown 文件
- 在 Windows 下可以将某条对话的 `conversationId` 复制到剪贴板

### 安装与使用

1. 在本机克隆本仓库。
2. 进入仓库根目录（即当前 `README.md` 所在目录）。
3. 使用 Python 运行：

```bash
# 交互模式：先列出所有对话，输入序号查看
python cursor_history_viewer.py

# 仅列出所有对话（含对话 ID 与首句标题）
python cursor_history_viewer.py list

# 查看第 N 条对话
python cursor_history_viewer.py view 3

# 按文件路径查看
python cursor_history_viewer.py view "C:\path\to\xxx.jsonl"

# 将第 N 条的对话 ID 复制到剪贴板（Windows）
python cursor_history_viewer.py copy-id 2
```

### 数据来源

Cursor 会把 Agent 对话历史写入本地目录：

- **Windows**：`%USERPROFILE%\.cursor\projects\<项目ID>\agent-transcripts\<对话ID>\<对话ID>.jsonl`
- **macOS / Linux**：`~/.cursor/projects/<项目ID>/agent-transcripts/<对话ID>/<对话ID>.jsonl`

你可以通过环境变量 `CURSOR_AGENT_TRANSCRIPTS_ROOT` 自定义扫描根目录，例如：

```bash
# Windows PowerShell
$env:CURSOR_AGENT_TRANSCRIPTS_ROOT = "D:\your\path\.cursor\projects"
python cursor_history_viewer.py list

# Linux / macOS
export CURSOR_AGENT_TRANSCRIPTS_ROOT="/path/to/.cursor/projects"
python cursor_history_viewer.py list
```

当项目 ID 为纯数字（如 `1773280448224`）时，表示该对话来自「未打开文件夹」的临时窗口。  
若需继续该对话并利用 KV cache，需要在 Cursor 中回到对应的临时窗口并在聊天历史中切换。

## 关于对话历史存储位置（本机 vs 远程）

如果你在 **Windows 11 上运行 Cursor**，并通过 Cursor 远程连接到一台 **Linux 服务器**，然后在 Cursor 中打开服务器上的某个目录进行对话：

- **Agent / Composer 对话的历史记录文件是保存在运行 Cursor 的那台机器上**  
  - 即本例中：保存在 **Windows 11 本机** 的 `%USERPROFILE%\.cursor\projects\...` 下  
  - 远程 Linux 服务器上不会自动生成这些 `agent-transcripts` JSONL 文件（除非远程那边也单独装了 Cursor 并在本地运行）

因此，本项目中的 `cursor_history_viewer.py` 默认也是读取你本机（运行 Cursor 的那台电脑）上的 `.cursor/projects` 目录。
