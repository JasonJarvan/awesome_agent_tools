## 项目给 Agent / Cursor 的说明

本仓库是一个**AI 工具聚合项目**，主要面向在 Cursor 中使用的各种小工具与“skills”。  
下面约定了目录结构与使用方式，方便代码助手/Agent 在后续自动扩展时保持一致风格。

## 顶层结构

- `chat_browser/cursor_chat_browser/scripts/cursor_chat_browser.py`
  - Cursor **AI Chat（SQLite）**与 **Agent（JSONL）** 的统一终端入口。
  - 扫描 `workspaceStorage` / `state.vscdb` 与 `~/.cursor/projects/.../agent-transcripts`，支持双源选择与 `agent list|view|copy-id` 子命令。

- `README.md`
  - 面向人类用户的项目说明，介绍整体定位（AI 工具聚合）、目录结构以及如何使用 `cursor_chat_browser.py`。

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

当用户通过 **Cursor Remote（如 Windows 客户端 + Linux SSH 远端）** 工作时：

- **Agent JSONL** 常出现在**打开工程所在侧**的用户目录（例如远端 Linux 的 `~/.cursor/projects`）；在**客户端本机**也可能有一份，取决于 Cursor 版本与场景。
- **AI Chat 的 SQLite 状态**更常在**运行 Cursor UI 的客户端**的 `workspaceStorage`。

因此：

- 使用 `cursor_chat_browser.py` 时，应明确**当前进程所在机器**是否包含目标数据；需要时用 `CURSOR_WORKSPACE_STORAGE`、`CURSOR_AGENT_TRANSCRIPTS_ROOT` 指向正确根目录，而不是在代码中写死路径。
- 脚本通过**实际扫描是否命中数据**区分数据源，而非依赖操作系统类型。
