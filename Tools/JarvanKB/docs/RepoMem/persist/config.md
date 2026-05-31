---
default_language: zh
secondary_languages: []
translation_sync_policy: ask-after-persist-change
---

# RepoMem Config — JarvanKB

## Language Policy（正式化版本，2026-05-31，narrow H2A 版）

按文档**实际受众**二分，**不**按目录位置一刀切。规则随 HarnessStack v2 生效。

| 文档类别 | 主要读者 | 语言 | 典型路径 |
|---|---|---|---|
| **A2A — agent 技术合同 / agent memory** | agent 在 session-load 或工作流中读 | **英文** | `CLAUDE.md`、`docs/HarnessStack/longterm.md` / `README.md`、sendbox 内 agent↔agent 信件（handoff/blocker/milestone-done/decisions/plan-ready 等）、`docs/superpowers/specs/`、`docs/superpowers/plans/`、`<module>/docs/superpowers/`、`<module>/docs/HarnessStack/temporary-*.md`、**`docs/RepoMem/persist/` 大多数文件**（含 `version-plan.md`、`architecture/`、`memory/`），`<module>/docs/RepoMem/{architecture,decisions}.md` |
| **H2A — user 直接读取的参考面** | user 经 Dashboard 跳转读，**或者** user 是文档唯一日常读者 | **{user_language}**（本仓 = 中文） | `docs/Dashboard/index.md`（**含 §SP Status Board / §Where else to look**）、`docs/sendbox/toUser/`、`README.md`、`docs/HarnessStack/_toUser/`、`<module>/docs/{README,interface,architecture,runbook}.md`（子模块对外说明） |
| **Governance config / 策略文档** | agent + user 共读；策略阅读以 user 居多 | **{user_language}** + frontmatter `language` 显式声明 | `docs/RepoMem/persist/config.md`（本文件）、`docs/HarnessStack/hooks/*.md` |

### 边界与例外

- **不按目录一刀切**：`docs/RepoMem/persist/` 大多数是 A2A（agent memory），只有内容本身面向 user 的（如有意做成 user 参考的 architecture overview）才是 H2A。判定标准 = "user 是否日常通过 Dashboard pointer 进入读取？"
- **frontmatter 声明覆盖**：文件顶部 `language: en|zh` + `audience: A2A|H2A` 两字段显式声明优先
- **历史 grandfather**：`docs/RepoMem/persist/{config.md, memory/runbook.md, memory/pre-openspec-decisions.md, architecture/crawl-pipeline.md}` 在 bootstrap 期以中文写就，**保留中文不翻译**（churn 代价高、收益边际；这些文件 v1 期间不会动）。新 persist 文件按上表（A2A=英文）
- **代码标识符 / 命令 / URL / 路径**：永远 ASCII；段落语言不替换它们
- **混合内容**：若一个文件含 A2A + H2A 两块内容（如曾经 version-plan 含 kanban）→ **拆分**到对应文档（kanban → Dashboard），不在单文件内混语言

### Rationale

- **A2A 英文**：agent 模型对英文 token 训练更密；技术术语歧义最小；跨平台 / 跨工具一致；RepoMem persist 主要是 agent 反复检索的"内部记忆"
- **H2A {user_language}**：与用户 `default_language` 一致；降低用户认知负担；H2A 暴露面**少**（Dashboard + sendbox/toUser + README + 子模块对外说明），不是"凡 user 可读 = H2A"

### Sync Policy

`translation_sync_policy: ask-after-persist-change` 意为：persist 文件内容变更后，HITL 审阅时确认是否需要语言同步（当前仅一个语言，无 `multi-lang/` 镜像；预留位）。

### 违反处理

- 发现 A2A 文档误用 user_language → translate to 英文（除非 grandfather 例外）
- 发现 H2A 文档误用英文 → translate to user_language
- **历史违反与修订案例**：
  - 2026-05-31 first commit `1be7989`：把 `version-plan.md` 从 A2A 英文翻成中文 + 声称 "所有 RepoMem persist = 中文"。**过扩展**。
  - 2026-05-31 后续修订：kanban 移出 version-plan → Dashboard §SP Status Board；version-plan 恢复 A2A=英文；本节窄化 H2A scope。grandfather 既存 4 个中文 persist 文件

## Domains (current)

域地图维护在 `architecture/index.md`。当前活跃 1 个，预留 3 个空位。

## Frontmatter

- `config.md`（本文件）：必含 `default_language`、`secondary_languages`、`translation_sync_policy`
- 其他 persist 文件：**不强制** frontmatter（避免噪音）；如需覆盖语言策略，加 `language: <code>`
- 所有 temp 文件：必含 `slug`、`status`、`domains`、`updated_at`；`requirements.md` 还需 `task_type`
