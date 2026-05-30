---
default_language: zh
secondary_languages: []
translation_sync_policy: ask-after-persist-change
---

# RepoMem Config — AgentCrawl

## Language

- **Primary**: 中文（zh）—— 与用户工作语言一致，对应根 `CLAUDE.md` 的 `Always respond in 中文` 强制规则。
- **Secondary**: 无。

CLAUDE.md 与 HarnessStack/* 是英文技术合同，但**不归 RepoMem 治理**（它们属于 Harness 层契约），因此不需要进 `multi-lang/` 镜像。

## Domains (current)

域地图维护在 `architecture/index.md`。当前活跃 1 个，预留 3 个空位。

## Frontmatter

- `config.md`（本文件）：必含 `default_language`、`secondary_languages`、`translation_sync_policy`
- 其他 persist 文件：**不强制** frontmatter（避免噪音）
- 所有 temp 文件：必含 `slug`、`status`、`domains`、`updated_at`；`requirements.md` 还需 `task_type`
