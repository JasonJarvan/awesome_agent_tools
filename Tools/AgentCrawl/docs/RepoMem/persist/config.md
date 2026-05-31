---
default_language: zh
secondary_languages: []
translation_sync_policy: ask-after-persist-change
---

# RepoMem Config — JarvanKB

## Language Policy（正式化版本，2026-05-31）

按 H2A / A2A 受众二分。规则随 HarnessStack v2 生效。

| 文档类别 | 主要读者 | 语言 | 典型路径 |
|---|---|---|---|
| **A2A — agent 技术合同** | agent 在 session-load 时读 | **英文** | `CLAUDE.md`、`docs/HarnessStack/longterm.md`、`docs/HarnessStack/README.md`、sendbox 内 agent↔agent 信件（handoff/blocker/milestone-done/decisions/plan-ready 等）、`docs/superpowers/specs/`、`docs/superpowers/plans/`、`<module>/docs/superpowers/`、`<module>/docs/HarnessStack/temporary-*.md` |
| **H2A — 用户可读参考** | user 经 Dashboard 跳转读 | **中文**（= `default_language`） | `docs/Dashboard/index.md`、`docs/RepoMem/persist/`（含 `config.md`、`version-plan.md`、`architecture/`、`memory/`）、`docs/sendbox/toUser/`、`README.md`、`docs/HarnessStack/_toUser/`、`<module>/docs/{README,interface,architecture,runbook}.md` |
| **子模块内部 RepoMem** | agent 写、user 偶查 | **中文**（默认 H2A） | `<module>/docs/RepoMem/{architecture,decisions}.md`；模块内部纯技术决策可在文件首声明 `language: en` 后用英文（exception） |

### 边界与例外

- **A2A 优先**：若文档既被 agent 加载又被 user 偶读，按 A2A 处理（英文）—— 因 agent 数量远高于读频
- **H2A 优先**：若文档主要是 user 通过 Dashboard `§Where else to look` 进入的参考，按 H2A 处理（中文）—— 即便 agent 也会读
- **声明覆盖**：单文件可在 frontmatter 加 `language: en` / `language: zh` 显式覆盖；缺省按上表
- **代码标识符、命令、URL、文件路径**：永远 ASCII；段落语言不替换它们

### Rationale

- **A2A 英文**：agent 模型对英文 token 训练更密；技术术语歧义最小；跨平台 / 跨工具一致
- **H2A 中文**：与用户 `default_language: zh` 一致；降低用户认知负担

### Sync Policy

`translation_sync_policy: ask-after-persist-change` 意为：persist 文件内容变更后，HITL 审阅时确认是否需要语言同步（当前仅一个语言，无 `multi-lang/` 镜像；预留位）。

### 违反处理

- 发现 H2A 文档（如 `docs/RepoMem/persist/version-plan.md`）误用英文 → translate to 中文
- 发现 A2A 文档误用中文 → translate to 英文（罕见，因 agent 接近所有都是英文写）
- 历史违反案例：2026-05-31 `version-plan.md` 初次 eager-materialize 时误用英文，已修复

---

## Language（旧 §Language 段，保留兼容）

- **Primary**: 中文（zh）—— 与用户工作语言一致，对应根 `CLAUDE.md` 的 `Always respond in 中文` 强制规则
- **Secondary**: 无

CLAUDE.md 与 HarnessStack/* 是英文技术合同（A2A，详见 §Language Policy），但**不归 RepoMem 治理**（它们属于 Harness 层契约），因此不需要进 `multi-lang/` 镜像。

## Domains (current)

域地图维护在 `architecture/index.md`。当前活跃 1 个，预留 3 个空位。

## Frontmatter

- `config.md`（本文件）：必含 `default_language`、`secondary_languages`、`translation_sync_policy`
- 其他 persist 文件：**不强制** frontmatter（避免噪音）；如需覆盖语言策略，加 `language: <code>`
- 所有 temp 文件：必含 `slug`、`status`、`domains`、`updated_at`；`requirements.md` 还需 `task_type`
