---
language: zh
audience: H2A
---

# GitHub 平台概念参考 — v1.0 OSS 释出决策用

> **用途**：当 JarvanKB v1.0 OSS release 临近时（Dashboard UN-006 触发），决定"代码托管在哪个 namespace + 是否要 Organization + 付费层级"用的参考。
> **场景**：user 偶读；orche/agent 一般不需要这层平台知识。

## 三层概念（GitHub 平台）

```
┌──────────────────────────────────────────────────┐
│  Account (User OR Organization)  —— 命名空间      │
│  ┌────────────────────────────────────────────┐  │
│  │  Repository (repo)  —— 代码容器（git）       │  │
│  │  ┌──────────────────────────────────────┐  │  │
│  │  │  Project (board)  —— kanban 看板视图  │  │  │
│  │  └──────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

| 概念 | 是什么 | 装什么 | URL 形式 |
|---|---|---|---|
| **Account** | 命名空间持有者；分 **User**（个人）和 **Organization**（团队 namespace） | 多个 Repository | `github.com/<account>` |
| **Repository (repo)** | 实际的 git 仓库 | 代码 + issues + PRs + (可选)Projects | `github.com/<account>/<repo>` |
| **Project** | **看板视图功能**（kanban），不是代码容器 | issues / PRs / draft items（来自 1 个或多个 repo） | `github.com/<account>/<repo>/projects/<n>` 或 `github.com/orgs/<org>/projects/<n>` |

**关键纠正**：**Project ≠ Repo**。Project 是覆盖在 issues/PRs 之上的看板，类似 Trello/Jira board 嵌进 GitHub。它**不能装代码**。Repo 才是装代码的。

## JarvanKB v1.0 释出 3 个选项

| 选项 | URL 例子 | 适合 | 我（g2）的推荐度 |
|---|---|---|---|
| **A. User account（当前模式）** | `github.com/JasonJarvan/zhihu-engine`<br>`github.com/JasonJarvan/cookie-manager`<br>... | 单人 OSS、少协作、最简单；与 `CodeTeam` 等现有项目共栈 | ⭐⭐ 可行 |
| **B. Organization** ⭐ 推荐 | `github.com/Jarvan/zhihu-engine`<br>`github.com/Jarvan/cookie-manager`<br>... | 个人品牌 + 项目隔离；未来有 contributor 易加；Org-level Project 看板可统一管 | ⭐⭐⭐ 最优 |
| **C. Monorepo（不拆）** | `github.com/JasonJarvan/JarvanKB` 一个 repo 装全部 | design.md §9 已决定拆分 → C 已被否决 | ❌ 不在选项内 |

### 推 B (Organization) 的理由

1. **个人品牌 + 项目隔离**：`JasonJarvan` 个人账户已有 CodeTeam 等其他项目；JarvanKB 7+ 子 repo 全堆在个人下会"无序生长"
2. **未来 contributor 容易加**：Org 可加 team / 权限组；User 只能"协作者"列表
3. **品牌叙事**：`github.com/Jarvan/zhihu-engine` 读起来像"产品"；`github.com/JasonJarvan/zhihu-engine` 像"个人脚本"
4. **OSS 友好**：Org 有专门 OSS 风格 settings、Sponsors、Discussions 等

### A (User account) 也完全可行

特别是想免运维（Org 要管 members / teams / billing tier）。很多单人 OSS 维护者就用 User account。如果你**不打算长期招 contributor**，A 简洁。

## Project 这层应该怎么用？

Project 不是替代品；它是看板**视图**。典型用法：
- 你已有 Org `Jarvan` + 多个 repo
- 在 Org 层级建 Project board（`github.com/orgs/Jarvan/projects/1`），把所有 repo 的 issues 都拉进来做 kanban
- → **这就是 R9 调研里的 "GitHub Projects v2" 选项**，**被否决**因为造成"Dashboard + GitHub Projects 双真相源"，违反 §H2A Coupling

**结论**：JarvanKB 当前**不用** GitHub Projects。SP 状态板留在 `docs/Dashboard/index.md §SP Status Board`。

## 付费情况

**结论**：**Free tier 完全够用，不需要付费**。

GitHub Organizations 自 2020-04 起免费层就开放：

| Free for Organizations 包含 | 限额 |
|---|---|
| 无限 **public** 仓库 | ∞ |
| 无限 **private** 仓库 | ∞ |
| 无限协作者 / Team 成员 | ∞ |
| GitHub Actions on public repos | 无限分钟 |
| GitHub Actions on private repos | 2000 min / 月 |
| Packages 存储 | 500 MB |
| Issues / Projects / Discussions / Wiki | 全部有 |

### 何时才需付费

仅以下场景考虑升级到 **Team ($4/user/月)** 或 **Enterprise**：

| 升级触发 | 解读 |
|---|---|
| Private repo CI/CD 超 2000 min/月 | JarvanKB 是 public OSS，不踩这条线 |
| Private repo 需要 branch protection rules | public repo 免费层就有，private 才付费 |
| 需要 audit log / SAML SSO | 企业合规，单人项目无关 |
| Codespaces 共享额度 | 你本地开发，无关 |

**对 JarvanKB 的占用预估**：7 个 sub-project repos 全 public → Actions 无限可用；预估 CI/CD 不超 2000 min/月（即便 private 也 OK）；Packages 用不到 500 MB。

## 实际创建步骤（v1.0 释出时执行，现在不用）

到 v1.0 release 临近：

1. 登录 GitHub → 右上角头像 → "Your organizations" → "New organization"
2. 选 **Free** plan
3. 填 Org 名（候选 `Jarvan` / `JarvanWorks` —— UN-006 那时决）
4. 选 "My personal account"（owner = 你自己）
5. 跳过 邀请 members（单人项目）
6. 后续按 `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md §9` fractal 切分协议，把每个子 repo push 进 Org

## 触发条件

本文档**仅在 Dashboard UN-006 准备解决时使用**。日常 SP-1..SP-7 工作不需要看这份。
