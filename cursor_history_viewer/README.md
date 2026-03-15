# Cursor Agent 对话记录查看器

在本地查看 Cursor IDE 的 **Agent（Composer）对话历史**，支持跨项目列出、按序号查看、复制对话 ID。  
对话数据来自 `~/.cursor/projects` 下的 agent-transcripts（JSONL），无需打开 Cursor 即可浏览与检索。

## 功能

- **全局列表**：扫描所有项目的 Agent 对话，按时间倒序展示，并显示每条对话的 `conversationId`
- **查看内容**：将 JSONL 解析为可读的【用户】/【助手】对话文本
- **无目录对话说明**：对「未打开文件夹」的临时窗口对话（项目名为纯数字）给出继续对话的提示
- **复制对话 ID**：通过 `copy-id` 子命令将指定对话的 ID 复制到剪贴板（Windows 下使用 PowerShell）

## 环境要求

- Python 3.6+
- 无需额外依赖（仅使用标准库）

## 安装与使用

1. 将本仓库克隆或下载到本地。
2. 在终端中进入仓库目录，执行：

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

## 数据来源说明

Cursor 将 Agent 对话写入本地目录：

- **Windows**：`%USERPROFILE%\.cursor\projects\<项目ID>\agent-transcripts\<对话ID>\<对话ID>.jsonl`
- **macOS / Linux**：`~/.cursor/projects/<项目ID>/agent-transcripts/<对话ID>/<对话ID>.jsonl`

项目 ID 为**纯数字**（如 `1773280448224`）时，表示该对话来自「未打开任何文件夹」的临时窗口。  
若需继续该对话并利用 KV cache，只能在 Cursor 中回到该窗口，在聊天历史里切换；Cursor 目前不支持通过对话 ID 直接打开某条对话。

## 自定义扫描目录

默认扫描 `~/.cursor/projects`。若你的 Cursor 数据在其他路径，可设置环境变量：

```bash
# Windows PowerShell
$env:CURSOR_AGENT_TRANSCRIPTS_ROOT = "D:\your\path\.cursor\projects"
python cursor_history_viewer.py list

# Linux / macOS
export CURSOR_AGENT_TRANSCRIPTS_ROOT="/path/to/.cursor/projects"
python cursor_history_viewer.py list
```

## 许可证

MIT
