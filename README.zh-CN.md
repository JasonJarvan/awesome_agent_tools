# Awesome Agent Tools

[English](README.md) | 中文

这是一个面向智能体工作流的开源工具仓库，重点关注可复用的 skill、实用的编排流程，以及清晰、可维护的设计。

这个仓库围绕一个简单但很重要的原则展开：

> 不要过早创建新 skill。
> 先搜索是否已有可信、成熟的现成方案。
> 只有当某个工作流在真实任务里跑通之后，才把它沉淀成可复用的 skill。

当前仓库中的核心产物，是一个跨平台的 `skill-orchestrator`。它帮助智能体先搜索、再比较、再适配，最后才决定是否创建新的 skill。

## Clone 注意事项

仓库里有多处 git submodule，指向各自的独立仓库
（在 `Skills/maintain/`、`Skills/product/` 与 `Tools/` 下）。
普通 `git clone` 完之后，那些目录是空的，需要一并初始化 submodule：

```bash
git clone --recurse-submodules https://github.com/JasonJarvan/awesome_agent_tools.git
# 或者已经 clone 完了：
git submodule update --init --recursive
```

之后想顺带把 submodule 的上游更新一起拉下来：

```bash
git pull --recurse-submodules
```

## 仓库里有什么

Skills 按用途分类归置在 `Skills/` 下(索引见 [`Skills/README.md`](Skills/README.md)):

- **`Skills/maintain/`** —— 维护/运维类:
  - `skill-orchestrator/` —— 旗舰:可跨平台复用的编排型 skill,在 Codex、Claude Code、OpenClaw 等生态里发现、评估、适配和创建 skill。
  - `cc-relocate-project/` *(git submodule → [JasonJarvan/cc-relocate-project](https://github.com/JasonJarvan/cc-relocate-project))* —— 安全搬迁/重命名 Claude Code 项目,不丢失可 `--resume` 的会话历史。
  - `ops-doc-maintainer/` *(git submodule → [JasonJarvan/ops-doc-maintainer](https://github.com/JasonJarvan/ops-doc-maintainer))* —— 跨平台(Linux + Windows)运维文档维护 skill,每次调用自动判断平台,维护端口/Docker/Nginx/SSH/PostgreSQL/全局 CLI 等热点文档。

- **`Skills/knowledge/`** —— 信息获取类:
  - `MiroResearch/` —— 深度、多步、带引用的联网研究(封装 MiroMind Deep Research API)。
  - `web-search/` —— 统一走 `bailian_web_search` MCP 工具做网页搜索。

- **`Skills/product/`** —— 业务/评估决策类:
  - `idea-evaluator/` —— 用投资人视角评估一句话产品 idea 的商业价值与天花板。
  - `interviewer-designer/` *(git submodule → [JasonJarvan/interviewer-designer](https://github.com/JasonJarvan/interviewer-designer))* —— 把简历转成一小时面试官手册(公开核实、即用题库、现场打分)。

- `Skills/in-progress/`、`Skills/deprecated/` —— 隔离非主线 skill 的生命周期目录。

独立工具与子系统放在 `Tools/` 下(**不是 skill**):

- `Tools/utils/` —— 轻量工具:`claude-hud` *(git submodule)* 与 `cursor_chat_browser`。
- `Tools/CodeTeam/` *(git submodule → [JasonJarvan/CodeTeam](https://github.com/JasonJarvan/CodeTeam))* —— 多 agent 协作 harness 子系统(HarnessFactory、RepoMem、cc-sendbox 等)。
- `Tools/JarvanKB/` *(git submodule → [JasonJarvan/JarvanKB](https://github.com/JasonJarvan/JarvanKB))* —— 知识库爬取引擎(知乎/B 站引擎、watcher、crawl skills)。

## 为什么要做这个项目

团队在使用 AI coding agent 时，很快会遇到同一个问题：

- 有时真正需要的是一个 `skill`
- 有时需要的是一个 `MCP server`
- 有时只需要一个 `CLI tool`
- 有时最好的做法其实是什么都不要新建，而是复用已有能力

很多项目一开始就直接创建新东西。这个仓库刻意反着来：把“创建”当成最后一步，而不是第一步。

这带来了三个核心设计原则：

1. 先搜索，再构建。
2. 在适配或生成新工具之前，一定先让用户确认。
3. 尽量把可复用逻辑做成平台无关，把平台差异压缩进薄薄的一层适配。

## `skill-orchestrator`

`skill-orchestrator` 当前有意只聚焦在 skill，不把 MCP 编排直接混进来。这是一个刻意的边界设计。

规划中的层次是：

1. `skill-orchestrator`
2. `mcp-orchestrator`
3. 更上层的 capability orchestrator，用来统一在 skill、MCP、CLI 等能力之间编排

这样第一版会更聚焦，也更容易验证设计是否成立。

### 这个 skill 做什么

当用户提出一个需求时，这个 skill 会尝试：

1. 分析用户需求，判断最适合先查哪一种 source type。
2. 优先搜索高优先级已注册源。
3. 在运行时支持的情况下并行搜索多个源。
4. 返回少量高信号候选，而不是一长串原始链接。
5. 询问用户是采用、继续搜索、适配，还是创建新 skill。
6. 如果找到的是别的生态里的 skill，就先询问用户是否要做适配转换。

### 为什么它是跨平台的

这个 skill 的设计分成两层：

可移植核心：

- 搜索策略
- source registry
- 候选评分规则
- 候选展示格式
- 跨平台适配规则

平台特定部分：

- Codex 的元数据约定
- Claude Code 的 frontmatter 或工具限制
- OpenClaw 的运行时字段
- 子智能体调用、并行搜索、用户确认交互方式上的差异

也就是说，核心内容是可以复用的，但打包形式不一定完全一样。

## 仓库结构

```text
awesome_agent_tools/
├── README.md
├── README.zh-CN.md
├── AGENT.md
├── Skills/
│   ├── README.md                             # 顶层导航
│   ├── maintain/                             # 维护/运维类
│   │   ├── skill-orchestrator/               # 旗舰(SKILL.md + references/ + scripts/ + assets/)
│   │   ├── cc-relocate-project/              # submodule → JasonJarvan/cc-relocate-project
│   │   └── ops-doc-maintainer/               # submodule → JasonJarvan/ops-doc-maintainer（跨平台）
│   ├── knowledge/                            # 信息获取类
│   │   ├── MiroResearch/                     # SKILL.md + scripts/
│   │   └── web-search/                       # SKILL.md
│   ├── product/                              # 业务/评估决策类
│   │   ├── idea-evaluator/                   # SKILL.md
│   │   └── interviewer-designer/             # submodule → JasonJarvan/interviewer-designer
│   ├── in-progress/                          # 非主线:开发中
│   └── deprecated/                           # 非主线:已弃用
└── Tools/
    ├── utils/                                # 轻量工具
    │   ├── claude-hud/                       # submodule → JasonJarvan/claude-hud
    │   └── cursor_chat_browser/
    ├── CodeTeam/                             # submodule → JasonJarvan/CodeTeam
    └── JarvanKB/                             # submodule → JasonJarvan/JarvanKB
```

## 如何使用这个 skill

这个 skill 面向那些支持 `SKILL.md` 入口文件的智能体运行时。

典型使用方式：

1. 把 skill 文件夹放到目标运行时可发现的位置。
2. 提出一个“想找工具/想找可复用工作流”的请求。
3. 让 skill 先决定应该从哪种 source type 开始查。
4. 查看候选摘要。
5. 决定是采用、适配、继续搜索，还是创建新 skill。

如果你想在智能体运行时之外做一轮可重复的“半自动搜索”，可以直接运行附带脚本：

```bash
cd Skills/maintain/skill-orchestrator/scripts
python -m pip install -r requirements.txt
python search_skills.py "documentation co-authoring skill for Claude Code" --ecosystem claude_code
```

脚本会把 Markdown 和 JSON 输出写入 `Skills/maintain/skill-orchestrator/output/`。

当没有找到足够强的候选，或者你虽然找到了候选但仍然更倾向于自建时，输出里还会包含一个结构化的 `creation brief`，可以直接作为创建新 skill 的起点。

对于基于网页的 source 查询，脚本已经支持重试和 fallback provider。因此即使某个搜索引擎临时失败，也会优雅降级成 source notes，而不是直接让整个搜索流程报错退出。

示例请求：

- “Find a community skill for structured code review in Claude Code.”
- “Search for a Codex-compatible skill for repository archaeology.”
- “I need a cross-platform skill for issue triage. Reuse something existing if possible.”
- “Search skill markets first, then GitHub, then help me create one if nothing is strong enough.”

## 它是怎么搜索的

整个搜索策略刻意偏保守，不追求一次性撒太大网。

### Source Types

第一版只聚焦 skill discovery，不把 MCP 编排放进来。目前主要 source types 是：

- agent-specific skill markets
- GitHub
- 其他 skill 目录、社区聚合页或生态注册源

所有已注册源都放在 [`Skills/maintain/skill-orchestrator/references/sources.yaml`](Skills/maintain/skill-orchestrator/references/sources.yaml) 里，方便随着生态变化手工维护。

### 优先级模型

对于 agent-specific market，源会被分成两层：

- `tier_1`：优先且更可信的第一轮源
- `tier_2`：更广泛、实验性更强的补充源

编排器会优先并行搜索所有 `tier_1` 源；只有当没有足够强的结果时，才会继续进入 `tier_2`。

### 候选数量控制

这个编排器不会把命中的所有结果都倒给用户。

默认规则是：

- 默认返回 `Top 3`
- 最多不超过 `5`
- 不为了凑数展示弱候选
- 如果一个候选明显最好，就只给它加一个备选

这样用户更容易做决策。

## 关键设计文件

这个 skill 不是一个单纯的 prompt 文件，而是一组小而清晰的系统化文档：

- [`SKILL.md`](Skills/maintain/skill-orchestrator/SKILL.md)
  编排器本身的操作说明。

- [`sources.yaml`](Skills/maintain/skill-orchestrator/references/sources.yaml)
  可编辑的 source registry，按 source type、agent 生态和优先级组织。

- [`decision-rules.md`](Skills/maintain/skill-orchestrator/references/decision-rules.md)
  负责路由、评分、停止条件和候选数量规则。

- [`result-schema.md`](Skills/maintain/skill-orchestrator/references/result-schema.md)
  规定返回给用户的候选信息应包含哪些关键字段。

- [`adaptation-matrix.md`](Skills/maintain/skill-orchestrator/references/adaptation-matrix.md)
  说明 Codex、Claude Code、OpenClaw 之间如何做适配转换。

- [`search-playbook.md`](Skills/maintain/skill-orchestrator/references/search-playbook.md)
  规定搜索时该如何扩展、何时升级搜索范围、如何和用户同步决策边界。

## 为什么 README 写得这么详细

这个仓库既是给人看的，也是给 agent 看的。

这会形成一个张力：

- 人类需要清晰的架构、边界和设计动机
- agent 需要更紧凑、更可执行的操作说明

这里的解决方式是把职责分开：

- 根目录 `README.md` / `README.zh-CN.md` 面向人类
- skill 文件夹里的文档更多面向 agent runtime

## 当前范围与后续规划

当前范围：

- skill discovery
- 候选评估
- 用户确认
- 跨平台适配规划
- 搜索失败后的 creation brief

后续规划：

- 单独的 `mcp-orchestrator`
- 更上层的 capability orchestrator
- 更丰富的直连 source 抓取器
- 自动检查 source freshness

## 贡献方式

最有价值的贡献通常集中在这些方向：

- 改进 `sources.yaml` 里的注册源
- 优化 decision rules
- 强化跨平台适配说明
- 提供真实世界里 skill 复用成功的案例

如果要提改动，优先考虑那些能让编排器更清晰、更可信，而不是单纯变得更复杂的改动。

## 一句话哲学

最好的 skill，往往是那个你根本不必重新创建的 skill；而最值得你亲手创建的 skill，应该来自一个已经在真实任务里证明有效的工作流。
