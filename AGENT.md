## 项目给 Agent / Cursor 的说明

本仓库是一个 **AI 工具聚合项目**,收纳可被 agent 调用的 **skill** 与若干独立 **工具/子系统**。
下面约定了目录结构与使用方式,方便代码助手 / Agent 在后续自动扩展时保持一致风格。

## 顶层结构

- `Skills/` —— 可被 agent 调用的 skill,按用途分三类 + 两个生命周期目录(详见下节)。
- `Tools/` —— 独立的 CLI / 服务 / 子系统项目(**不是 skill**):
  - `Tools/utils/` —— 轻量、单一用途的小工具(如 `claude-hud`、`cursor_chat_browser`)。
  - `Tools/CodeTeam/`、`Tools/JarvanKB/` —— 大型自研子系统,以 **git submodule** 引用。
- `README.md` / `README.zh-CN.md` —— 面向人类用户的项目说明。
- `AGENT.md`(当前文件)—— 面向代码助手 / Agent 的开发约定与架构说明。

## `Skills/` 目录约定

- **每个 skill = 一个子目录 + 标准 `SKILL.md`**:
  - `SKILL.md` 含 frontmatter(`name` / `description`),正文保持薄,细节下沉到 `references/`、`scripts/`、`assets/` 等子文件(渐进式披露)。
  - 若 skill 以 git submodule 引入,其内部格式由上游仓库决定,本仓不强改。
- **按用途分类**(数量少时保持三类,增长后再细分):
  - `Skills/maintain/` —— 维护/运维类。
  - `Skills/knowledge/` —— 信息获取类。
  - `Skills/product/` —— 业务/评估决策类。
  - 每个分类目录带一个 `README.md` 索引(每个 skill 一句话 + 链接);顶层 `Skills/README.md` 为导航目录。
- **生命周期目录**(隔离非主线,不参与分类导航):
  - `Skills/in-progress/` —— 开发中/未稳定,不进插件。
  - `Skills/deprecated/` —— 已弃用,保留参考。

- 对 Agent 的操作建议:
  1. 新增 skill:在对应分类下建子目录,写标准 `SKILL.md`;未稳定先放 `in-progress/`。
  2. 未得到用户明确授权前,不要擅自修改其他 skill 的实现逻辑;可在其 README/SKILL 中追加说明或提改进建议。
  3. 移动 submodule 一律用 `git mv` 并 `git submodule sync` 验证,勿手改 `.git` 指针。

## 关于对话历史的位置(Agent 使用须知)

`Tools/utils/cursor_chat_browser/scripts/cursor_chat_browser.py` 是 Cursor **AI Chat(SQLite)** 与 **Agent(JSONL)** 的统一终端入口。当用户通过 **Cursor Remote**(如 Windows 客户端 + Linux SSH 远端)工作时:

- **Agent JSONL** 常出现在**打开工程所在侧**的用户目录(例如远端 Linux 的 `~/.cursor/projects`);在客户端本机也可能有一份。
- **AI Chat 的 SQLite 状态**更常在**运行 Cursor UI 的客户端**的 `workspaceStorage`。

因此使用该脚本时,应明确**当前进程所在机器**是否包含目标数据;需要时用 `CURSOR_WORKSPACE_STORAGE`、`CURSOR_AGENT_TRANSCRIPTS_ROOT` 指向正确根目录,而非在代码中写死路径。脚本通过**实际扫描是否命中数据**区分数据源,而非依赖操作系统类型。
