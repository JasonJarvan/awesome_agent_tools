# User Now — Pending Actions

> Single source of truth for "what the user needs to do next" in AgentCrawl/JarvanKB.
> Authors: any agent session may append. Reader: user.
> Protocol contract: `~/.claude/skills/cc-dashboard/SKILL.md`
> Repo-local hook (language policy, mark-done owner, triggers, **H2A coupling**): `docs/HarnessStack/hooks/cc-dashboard.md`

## Where else to look

> All Human-to-Agent (H2A) interactions surface through `sendbox/` + this Dashboard. RepoMem / superpowers specs / hooks are agent-internal; pointers below let user find them without memorizing paths.

| 想看 | 去哪 |
|---|---|
| SP 状态板（kanban-like） | 本文件 §SP Status Board ↓ |
| Recipe 历史 / 改名记录 / OSS 切分计划 | `docs/RepoMem/persist/version-plan.md`（A2A 英文参考） |
| 当前 active session 的交接信 | `docs/sendbox/to{Prefix}{Role}/handoff.md`（例：`toSP0Impler/`） |
| 收到的 milestone-done / blocker 信件 | `docs/sendbox/toOrchestrator/from-*.md` |
| 用户单向信（agent → user） | `docs/sendbox/toUser/*.md` |
| 历史决策 / 调研结论 / 架构 | `docs/RepoMem/persist/memory/` 与 `architecture/` |
| 跨模块 design / plan | `docs/superpowers/{specs,plans}/` |
| 调用 JarvanKB 工具的契约（caller agent） | `docs/sendbox/toAgent/handoff.md` |
| HarnessStack v2 治理（impler 跑完后） | `docs/HarnessStack/longterm.md` |
| 项目总览（人类可读） | `README.md` |

## SP Status Board

> JarvanKB 子项目状态板（kanban-like）。一屏看全部 SP 状态 + 责任 agent + 进入条件。
> 状态 emoji：🟡 wip / 🔴 blocked / ⚫ done / ⚪ queued / 🟢 ready
>
> 升级触发（任一满足则迁移到 `antopolskiy/kanban-md`）：≥2 个 impler 并发 / 单 SP 内 task ≥10 / 需要 per-task 评论历史。详见 R9 调研结论。

| ID | 名称 | 状态 | Owner Agent | 进入条件 |
|---|---|---|---|---|
| SP-0 | 骨架 + recipe v2 迁移 | 🟡 wip | sp0impler | （无 — 当前任务） |
| SP-1 | CookieManager（fork CookieCloud + hook） | ⚪ queued | (无) | SP-0 完成 |
| SP-2 | 知乎引擎 | ⚪ queued | (无) | SP-0 完成 + SP-1 协议敲定 |
| SP-3 | 知乎 Skill | ⚪ queued | (无) | SP-2 实现完成 |
| SP-4a | B 站引擎 | ⚪ queued | (无) | SP-0 完成；BN docker 可达 |
| SP-4b | B 站 Skill | ⚪ queued | (无) | SP-4a 实现完成 |
| SP-5a | 知乎收藏夹监听服务 | ⚪ queued | (无) | SP-2 实现完成 |
| SP-5b | B 站收藏夹监听服务 | ⚪ queued | (无) | SP-4a 实现完成 |
| SP-6 | CrawlMdSaver Skill（爬取-笔记整合） | ⚪ queued | (无) | SP-3 / SP-4b 已注册到 SP-6 |
| SP-7 | Thino 块解析整理服务 | ⚪ queued | (无) | SP-6 实现完成 |
| SP-8（v1+） | Web Search Router（聚合知乎 Skill + Tavily + Exa） | ⚪ queued | (无) | v1 全部完成；知乎 API key 已获取 |

详细路径见 `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` §7。

## Active

| ID | Type | Action | Where (detail) | Blocker for | Since | Status |
|---|---|---|---|---|---|---|
| UN-003 | B | 起新 orchestrator 会话，按 handoff §7 提交当前状态 + 开 Phase 2 OpenSpec change `bilibili-audio-mvp` | `docs/sendbox/toOrchestrator/handoff.md` | Phase 2 开工（B站音频→OSS→Tingwu 最小链路） | 2026-05-30 | open |
| UN-004 | F | 确认已开通：阿里云 AK/SK + Tingwu 服务 + OSS bucket（同区域，私有，prefix `agent-crawl/` 24h 生命周期） | `docs/RepoMem/persist/memory/runbook.md` §1–2 | UN-003 步骤 3（`/opsx:propose` 之前的凭据 pre-flight） | 2026-05-30 | open（拟在 SP-0 impler Task 9 中归档为 obsoleted — R5 已切换 BN+bcut）|
| UN-007 | B | 起一个独立 Claude Code session（cwd = `Tools/AgentCrawl/`），第一句话告诉它：`read docs/sendbox/toSP0Impler/handoff.md and execute the plan it references`。等它在 `docs/sendbox/toOrchestrator/` 写出 `from-sp0impler-sp0-done.md` 或 blocker letter 后告知 orche | `docs/sendbox/toSP0Impler/handoff.md` | SP-1 brainstorming 启动 | 2026-05-31 | open |
| UN-008 | D | Review CodeTeam#1（含 SubOrche 泛化评论），决定推动上游修复节奏还是先在本仓库本地约定中沉淀 | https://github.com/JasonJarvan/CodeTeam/issues/1 | 后续 sub-project 一致采用 `to{Prefix}{Role}` 命名 | 2026-05-31 | open |

## Archive

| ID | Action | Done | By |
|---|---|---|---|
| UN-001 | 授权全局安装 OpenSpec CLI（`npm i -g @fission-ai/openspec` → v1.3.1） | 2026-05-27 | bootstrap session |
| UN-002 | 把 handoff 带到 `~/Codes/AgentCrawlers/` 起 ruflo 会话 — **obsoleted**：2026-05-30 决定继续在当前 repo 开发，迁移取消 | 2026-05-30 | bootstrap session |
