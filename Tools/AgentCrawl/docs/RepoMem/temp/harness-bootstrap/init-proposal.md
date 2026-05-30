---
slug: harness-bootstrap
status: merged
updated_at: 2026-05-26
task_type: init
---

# RepoMem Init Proposal — AgentCrawl

## Repository Summary

AgentCrawl 是「爬取工具 + cookie/凭据管理工具」的集合，挂在 `awesome_agent_tools/Tools/AgentCrawl/`。
目标消费者：Hermes Agent 及任何 Python agent / 脚本。
当前阶段：**文档骨架，无代码**。HarnessStack 刚激活（recipe = `superpowers-repomem-sendbox-dashboard`，effective 2026-05-26）。

## Detected Documentation Sources

| 路径 | 性质 | 当前处理 |
|---|---|---|
| `README.md` | 人类入口，介绍定位 | 保持原位 |
| `CLAUDE.md` | AI 始终加载契约（HarnessStack §1–4 蒸馏） | 保持原位；本任务后续会补 Where to Look 表 |
| `docs/HarnessStack/{README,longterm}.md` | 项目工作契约 + 用户手册（`_toUser/README.md`） | 保持原位（用户手写） |
| `docs/HarnessStack/_toUser/README.md` | Day-One Init 手册 | 保持原位 |
| `docs/RepoMem/README.md` | 我之前写的 RepoMem 布局说明 | **可能与 repo-mem 标准 init 输出冲突 → conflict C-01** |
| `docs/RepoMem/persist/version-plan.md` | 已存在 | 保留，确认符合 frontmatter 后接受 |
| `docs/RepoMem/persist/architecture.md` | 设计/数据流/选型理由 | **位置不符标准布局 → conflict C-02** |
| `docs/RepoMem/persist/decisions.md` | D1–D7 决策日志 | **位置不符标准布局 → conflict C-03** |
| `docs/RepoMem/persist/runbook.md` | 凭据配置 / 故障排查 | **位置不符标准布局 → conflict C-04** |
| `docs/toAgent/` | 下游使用者契约（空目录，待维护者手写） | 不归 RepoMem 管，保持原位 |

## Candidate Domains

当前阶段（无代码）暂只识别出 1 个核心域，预留 3 个未来域：

| Domain | 当下覆盖 | 备注 |
|---|---|---|
| `crawl-pipeline` | 现有 architecture.md / decisions.md / runbook.md 全部内容 | 唯一活跃域 |
| `harness` *(预留)* | HarnessStack / RepoMem 自身演进决策 | 现阶段空 |
| `credentials` *(预留)* | cookie / SESSDATA / 阿里云 AK / OSS 凭据管理 | 等 Phase 2 写 cookie manager 时拆出 |
| `asr-summary` *(预留)* | 听悟 / Paraformer / 本地 SenseVoice 切换策略 | 现阶段并入 `crawl-pipeline`，未来拆 |

## Suggested Persistent Layout

```text
docs/RepoMem/persist/
├── config.md                       ★ 新建
├── version-plan.md                 ✓ 已有
├── architecture/
│   ├── index.md                    ★ 新建：域地图 + 现状摘要
│   └── crawl-pipeline.md           ← 由现 architecture.md 改名移入
└── memory/
    ├── index.md                    ★ 新建：长期记忆地图
    ├── decisions.md                ← 由现 decisions.md 移入
    └── runbook.md                  ← 由现 runbook.md 移入
```

并保留：
- `docs/RepoMem/README.md`（我之前写的导览） — **建议精简后继续保留**，让人/agent 在 README 层即可看懂 persist+temp 分割
- `docs/RepoMem/temp/.gitkeep` — 保留
- `docs/RepoMem/temp/harness-bootstrap/`（本任务工作目录）

## Migration Suggestions

| 动作 | 源 | 目标 | 影响 |
|---|---|---|---|
| 改名 + 迁移 | `persist/architecture.md` | `persist/architecture/crawl-pipeline.md` | 现 README / CLAUDE.md 引用要同步改 |
| 迁移 | `persist/decisions.md` | `persist/memory/decisions.md` | 同上 |
| 迁移 | `persist/runbook.md` | `persist/memory/runbook.md` | 同上 |
| 新建 | — | `persist/config.md` | 见下文 frontmatter |
| 新建 | — | `persist/architecture/index.md` | 域地图 |
| 新建 | — | `persist/memory/index.md` | 长期记忆地图 |
| 补 frontmatter | — | 所有现有 .md（version-plan、迁移后三份） | 加 slug/domains 等元信息（仅 temp 强制；persist 是否加？见 OQ-3） |

`config.md` 拟用 frontmatter：

```yaml
---
default_language: zh
secondary_languages: []
translation_sync_policy: ask-after-persist-change
---
```

理由：用户工作语言中文（根 `CLAUDE.md` 强制 "Always respond in 中文"），现有 architecture/decisions/runbook 也以中文为主。HarnessStack / CLAUDE.md 是英文技术合同但**不归 RepoMem 治理**，无需放 multi-lang。

## Open Questions

1. **域粒度**：现阶段只用 `crawl-pipeline` 一个域，还是预先把 `credentials` / `asr-summary` 拆出空文件占位？（默认建议：单域，预留域写在 `architecture/index.md` 域地图里，文件等真需要时再开。）
2. **`runbook.md` 归属**：放 `memory/runbook.md` 还是 `persist/` 根？我倾向 `memory/`——它是"长期运行手册"，符合"长期可变更知识"语义。
3. **persist 文件是否要 frontmatter**：`frontmatter.md` 只强制 temp 文档；persist 是否也加 slug/domains？建议**只在 `config.md` 强制**，其他 persist 文件不加（避免噪音）。
4. **`docs/RepoMem/README.md` 是否保留**：标准 init 输出里没这个文件。建议**保留并精简**到 ~20 行（指向 standard layout 文档而非自己重述）。
5. **是否同时把 sendbox-protocol / cc-dashboard 的 init 也合并到本 slug**：技术上是同一次 bootstrap，但 repo-mem skill 只管 RepoMem。建议**分开**：本 slug 只做 RepoMem，cc-dashboard / sendbox 各开自己的工序（不需要 slug，它们是配置级动作）。

## Recommended Next Step

回答 OQ-1..5（用 `OQ-N: 答案`格式即可），同时请审 `init-conflicts.md` 的 C-01..C-04 选项。
**默认全部按上方建议**（默认值在每个 OQ 后已标注）。
你说 "approve all defaults" 我就应用迁移并继续到 Step 2（cc-dashboard）。
