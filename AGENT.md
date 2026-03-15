## 项目给 Agent / Cursor 的说明

本仓库是一个**AI 工具聚合项目**，主要面向在 Cursor 中使用的各种小工具与“skills”。  
下面约定了目录结构与使用方式，方便代码助手/Agent 在后续自动扩展时保持一致风格。

## 顶层结构

- `cursor_history_viewer.py`
  - Cursor Agent 对话记录查看器的实现文件。
  - 读取本机 `~/.cursor/projects`（或 `CURSOR_AGENT_TRANSCRIPTS_ROOT` 环境变量指定的目录）下的 `agent-transcripts` JSONL 文件，支持列出、查看、导出对话。

- `README.md`
  - 面向人类用户的项目说明，介绍整体定位（AI 工具聚合）、目录结构以及如何使用 `cursor_history_viewer.py`。

- `AGENT.md`（当前文件）
  - 面向代码助手 / Agent 的“开发约定与架构说明”。

- `skills/`（约定目录，可以后续逐步补充）
  - 用于存放零散的 AI skills，每个 skill 使用一个**独立子文件夹**。

## `skills/` 目录约定

- 目录结构示例：

  - `skills/web-search/`
  - `skills/sql-helper/`
  - `skills/refactor-patterns/`

- 约定：
  - **每个 skill 子目录必须包含一个 `README.md`**
    - 描述该 skill 的用途、输入输出格式、依赖项（例如是否依赖某个 MCP、外部 API、环境变量等）。
    - 如有脚本/配置文件，也建议在 README 中写明调用方式与注意事项。
  - 若将来需要引入配置文件，可约定统一命名方式，例如：
    - `config.example.json` / `.env.example` 等，仅作示例，不直接包含私密信息。

- 对 Agent 的操作建议：
  - 若需要新增一个 skill，请：
    1. 在 `skills/` 下创建新的子目录（例如 `skills/my-new-skill/`）。
    2. 在该目录内创建详尽的 `README.md`，按照上述约定说明该 skill。
    3. 再根据需要添加代码文件 / 配置文件。
  - 在未得到用户明确授权前，不要擅自修改其他 skill 子目录中的实现逻辑，可在 README 中追加说明或提出改进建议。

## 关于对话历史的位置（Agent 使用须知）

当用户在 **本机（例如 Windows 11）运行 Cursor**，并通过 Cursor 远程连接到另一台 **Linux 服务器** 时：

- Cursor Agent / Composer 的对话历史（`agent-transcripts`）是保存在**运行 Cursor 的那台机器本地**：
  - 例如：`%USERPROFILE%\.cursor\projects\...` 或 `~/.cursor/projects/...`
  - 远程 Linux 服务器上默认不会出现这些 JSONL 历史文件。

因此：

- 当你（Agent）在本项目中使用 `cursor_history_viewer.py`，应默认认为它读取的是**本机 Cursor 数据目录**，而非远程服务器上的路径。
- 如需适配特殊目录，应通过环境变量 `CURSOR_AGENT_TRANSCRIPTS_ROOT` 进行配置，而不是在代码中写死其他路径。

