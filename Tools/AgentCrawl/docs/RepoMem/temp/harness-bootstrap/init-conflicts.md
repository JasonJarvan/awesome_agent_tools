---
slug: harness-bootstrap
status: merged
updated_at: 2026-05-26
task_type: init
---

# RepoMem Init Conflicts — AgentCrawl

## Summary

4 处现有内容与 `repo-mem` 标准 init 输出冲突。全部因为我**早于 repo-mem skill 介入**就建好了 `docs/RepoMem/persist/` 三份文件且未走标准目录形态。

## Conflict Items

### C-01: 多余的 `docs/RepoMem/README.md`

- **现状**：我之前写了一份导览 README（描述 persist/temp 分割、HITL merge 规则）
- **冲突**：标准 init 不输出此文件——它的等价信息分散在 `skill repo-mem` references/、`config.md`、`architecture/index.md`、`memory/index.md`
- **风险**：内容可能与 `skill repo-mem` 的官方 reference 不同步（双源真相）

### C-02: `persist/architecture.md` 是单文件而非 `architecture/` 子目录

- **现状**：单文件 100 行
- **标准**：`architecture/index.md`（域地图）+ `architecture/<domain>.md`（详情）
- **风险**：单文件不易扩展为多域

### C-03: `persist/decisions.md` 在 persist 根，未归 `memory/`

- **现状**：D1–D7 决策日志在 `persist/decisions.md`
- **标准**：决策日志属于"长期记忆"，应放 `persist/memory/decisions.md`
- **风险**：未来加 `memory/` 后会出现"两个 memory 来源"

### C-04: `persist/runbook.md` 在 persist 根，未归 `memory/`

- 同 C-03

## Suggested Resolution Options

| conflict_id | 选项 A | 选项 B | 选项 C |
|---|---|---|---|
| C-01 | **精简保留**（建议默认）：缩到 ~20 行，仅指向 skill references | 全删 | 全保留原样 |
| C-02 | **改名迁移**（建议默认）：`architecture.md` → `architecture/crawl-pipeline.md`，新建 `architecture/index.md` 写域地图 | 保持单文件 `architecture.md` 不动 | 拆成多文件（按域细分） |
| C-03 | **迁移**（建议默认）：`decisions.md` → `memory/decisions.md`，新建 `memory/index.md` | 保留在 persist 根 | 拆分按域归入各 `memory/<domain>.md` |
| C-04 | **迁移**（建议默认）：`runbook.md` → `memory/runbook.md` | 保留在 persist 根 | 拆分 |

## Human Decisions

待你回填，格式：

```
C-01: A
C-02: A
C-03: A
C-04: A
```

（或简单一句 "all A" 表示全部按默认建议）

## Execution Notes

应用顺序（用户批准后）：

1. 创建 `persist/config.md`（带 frontmatter）
2. 创建 `persist/architecture/index.md`、`persist/memory/index.md`
3. `git mv` 三份现有文件到新位置（保留 git 历史；如非 git tracked 则用普通 mv）
4. 修正 README / CLAUDE.md / 旧 architecture.md 内部所有跨文档引用路径
5. 精简 `docs/RepoMem/README.md`（C-01.A）
6. 给本 init 任务 `status: merged` 并把 `init-proposal.md` / 本文件保留到 task closure 后再清理
7. 跑 `git diff` 让用户审阅

完成后本 slug 工作目录留待 step 4（升级 CLAUDE.md）一并 commit；本 init 任务的 RepoMem.merge HITL 推迟到全部 4 步走完一起做。
