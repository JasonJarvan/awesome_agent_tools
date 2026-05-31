---
status: active
scope: this-repo (JarvanKB)
skip-protocol: never (recipe-mandated)
authority: HarnessStack longterm.md §Hooks; cc-dashboard skill SKILL.md
---

# cc-dashboard Hook — JarvanKB

## Purpose

Maintain `docs/Dashboard/index.md` as **single source of truth for pending user actions** in this repo, projected out of:

- sendbox letters under `docs/sendbox/`
- any session identifying a user-blocking action with no sendbox doc

The hook codifies repo-specific choices for this repo only. The portable protocol contract lives in `~/.claude/skills/cc-dashboard/SKILL.md`.

## Data Location

- **Canonical path**: `docs/Dashboard/index.md`
- **Sections**: `## Active` (open) + `## Archive` (rolling 14 days, then `git rm`)

## Language Policy

| Field | Language | Reason |
|---|---|---|
| `Action` column body | **中文** | RepoMem `config.md` 设 `default_language: zh`；用户工作语言中文 |
| Schema enums (`Type`, `Status`) | ASCII | Skill 协议跨语言约定 |
| Structural fields (`ID`, `Since`, paths, URLs) | ASCII | 同上 |
| Archive `By` 列（session 名 / agent 名） | ASCII | Letter `created_in` 标签本就要求 ASCII |

例：

```
| UN-001 | A | 选定听悟 ASR 凭据策略：AK/SK 还是 STS 子账号 | docs/sendbox/toUser/from-maintainer-credentials.md | Phase 2 第一次跑通 | 2026-05-26 | open |
```

## Row Schema

| Column | Required | 说明 |
|---|---|---|
| `ID` | yes | `UN-NNN` 单调递增；新建行 = `max(Active ∪ Archive) + 1` |
| `Type` | yes | A/B/C/D/E/F（见下） |
| `Action` | yes | 中文祈使句一行 |
| `Where (detail)` | yes | 信件相对路径 / 外部链接（带 anchor） |
| `Blocker for` | yes | 该动作不做会阻塞什么（L2 ship / 决策 / release） |
| `Since` | yes | `YYYY-MM-DD` 行创建日 |
| `Status` | yes | `open` 或 `done` |

## Action Types

| Code | Type | JarvanKB 场景举例 |
|---|---|---|
| **A** | Decision / Approve | 批准 design / plan；选凭据策略；review HITL ack |
| **B** | Start session | 启 Phase 2 implementer session 写 `bilibili_audio.py` |
| **C** | Review / Merge | review PR；走 verify；合并 branch |
| **D** | Read + Triage | 读调研报告决定下一步范围 |
| **E** | Destructive ops | 用户手动做 `git push --force` / `rm -rf .worktrees/<task>` |
| **F** | Ops / Admin | 阿里云 OSS 桶创建；依赖安装（pip/npm）；token 轮换 |

如果一个待办不属于 A–F 任何一项，**先质疑是否真的 user-blocking**。

## Write Triggers

| Trigger | Row count | Typical type |
|---|---|---|
| 写 `docs/sendbox/toUser/*.md` | 1..N（每个 atomic ask 一行） | A / C / D |
| 写 `docs/sendbox/to<Implementer>/handoff.md` | ≥1（至少 "Start <Implementer> session"） | B |
| 发现 user-blocking 动作但没有 sendbox 信件（如外部 MR 待合并、凭据过期） | 1 | C / D / F |

**铁律**：1 letter → N rows，绝不 collapse 成 1 letter → 1 row。

## Mark-Done Protocol

**Option (a) — Any session + user**（skill 默认 + 我们采纳）：

- 任一 agent session 观测到动作已完成 → 标 `done` + 把行从 `Active` 挪到 `Archive`（同一 commit）
- 用户也可以直接编辑（`UN-005 done` 一句话即可触发）
- 偶有重复标记（无害）；偶有遗忘（用户下次注意时自然修正）

## Archive Protocol

- `Archive` 滚动保留 **14 天**
- 超期行 `git rm`，依赖 git log 保完整历史
- 不上自动化；touch dashboard 时顺手清

## Sendbox-protocol Coupling

cc-dashboard 与 sendbox-protocol **lifecycle 独立**：

- 信件 burn 不级联删 dashboard 行
- 行 mark-done 不触发信件清理
- 一封信里 3 个 ask → 3 行；某行 done 时其他行仍 open
- 信可能先 burn（收件人 lifecycle 结束）而衍生行仍 open（罕见，但允许）

## H2A Coupling (JarvanKB local rule, 2026-05-31)

所有 Human-to-Agent 交互 **必须** 经由下面之一暴露给 user，user 不应需要"记住有哪些路径"：

1. `docs/sendbox/toUser/*.md` 信件（单收件人，lifecycle 受控）
2. `docs/Dashboard/index.md § Active` 行（pending action，按 6 种 Type 分类）
3. `docs/Dashboard/index.md § Where else to look`（指向用户可能需要读的长形文档；**链接而非复制**）

**约束**：

- RepoMem persist / superpowers specs / hook 配置 / HarnessStack longterm 均为 agent-internal —— 它们的内容如对 user 有价值，**必须**在 §Where else to look 加锚点（行类型按内容选择 D 类型 Read+Triage 或仅作为 reference link）
- §Where else to look 的链接**不复制内容**，避免双真相源漂移（参见 R9 调研结论 anti-pattern #1）
- 任何新增的 H2A 通道（如未来加 web UI、加 Slack bot）应被 wrap 进上述三个 surface 之一，而非自立门户

**Rationale**：user 是项目的唯一人类参与者，应只在两个 surface 检查"我现在该做什么"（Dashboard）+"agent 给我留了什么信"（sendbox）。其他文档都是 agent 内部协作产物。

**Upstream sync**：本规则待 SP-0 完成后汇总进 CodeTeam follow-up issue（与 CodeTeam#1 合并或独立 issue 视上游 maintainer 偏好）。

## Hook Boundary

本 hook **不得**：

- 改任何 pipeline 步骤顺序 / merge gates / verification topology
- 成为 L2 work unit / RepoMem persist content 的真相源
- 级联删除 / 修改 upstream sendbox 信件
- 替代 tracker 工具（Linear / Multica）

违反任一项 → 本 hook 失效，须修复后才能重启。

## Seed Backfill 说明

Day-One Init §5–6 要求：seed 完 `docs/Dashboard/index.md` 后扫已存在的 sendbox 信件 / handoff / 外部 tracker，把**已完成**动作直接放 `Archive`（不要塞 `Active`）。

JarvanKB v2 状态下，初始 dashboard 由 SP-0 落地，Seed Backfill 已发生（UN-001..004 in Archive，UN-005+ in Active）。新 hook 部署到其他 repo 时按 cc-dashboard SKILL.md §Day-One Init 执行 seed。
