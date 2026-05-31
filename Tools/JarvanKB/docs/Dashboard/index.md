# User Now — Pending Actions

> Single source of truth for "what the user needs to do next" in JarvanKB.
> Authors: any agent session may append. Reader: user.
> Protocol contract: `~/.claude/skills/cc-dashboard/SKILL.md`
> Repo-local hook (language policy, mark-done owner, triggers, **H2A coupling**): `docs/HarnessStack/hooks/cc-dashboard.md`

## Where else to look

> All Human-to-Agent (H2A) interactions surface through `sendbox/` + this Dashboard. RepoMem / superpowers specs / hooks are agent-internal; pointers below let user find them without memorizing paths.

| 想看 | 去哪 |
|---|---|
| SP 状态板（kanban-like） | 本文件 §SP Status Board ↓ |
| Recipe 历史 / 改名记录 / OSS 切分计划 | `docs/RepoMem/persist/version-plan.md`（A2A 英文参考） |
| 当前 active session 的交接信 | `docs/sendbox/to{Prefix}{Role}/handoff.md`（例：`toSP0Impler/`、`toZhihuCrawlOrche/`） |
| 收到的 milestone-done / blocker 信件 | `docs/sendbox/toOrchestrator/from-*.md` |
| 用户单向信（agent → user） | `docs/sendbox/toUser/*.md` |
| 历史决策 / 调研结论 / 架构 | `docs/RepoMem/persist/memory/` 与 `architecture/` |
| 跨模块 design / plan | `docs/superpowers/{specs,plans}/` |
| 调用 JarvanKB 工具的契约（caller agent） | `docs/sendbox/toAgent/handoff.md` |
| HarnessStack v2 治理 | `docs/HarnessStack/longterm.md` |
| 项目总览（人类可读） | `README.md` |

## SP Status Board

> JarvanKB 子项目状态板（kanban-like）。一屏看全部 SP 状态 + 责任 agent + 进入条件。
> 状态 emoji：🟡 wip / 🔴 blocked / ⚫ done / ⚪ queued / 🟢 ready
>
> 升级触发（任一满足则迁移到 `antopolskiy/kanban-md`）：≥2 个 impler 并发 / 单 SP 内 task ≥10 / 需要 per-task 评论历史。详见 R9 调研结论。

| ID | 名称 | 状态 | Owner Agent | 进入条件 |
|---|---|---|---|---|
| SP-0 | 骨架 + recipe v2 迁移 | ⚫ done | sp0impler | （无）|
| SP-1 | CookieManager（自写 Express 复刻 CookieCloud 协议 + hook） | 🟡 wip (Stage 3) | sp1impler | Stage 3 执行中（greenlit 2026-05-31，subagent-driven，worktree TDD）|
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
| UN-006 | F | 决定 v1.0 GitHub Organization 名（候选：JarvanKB / Jarvan / JarvanWorks）— 此项非阻塞 v1 实现，可推迟到 v1 完成度临近 | `docs/RepoMem/persist/version-plan.md` §v1.0 OSS release plan | v1.0 切分 | 2026-05-31 | open |
| UN-008 | D | Review CodeTeam#1（含 SubOrche 泛化评论）+ CodeTeam#2（HarnessStack v2 consolidated proposal），决定推动上游修复节奏还是先在本仓库本地约定中沉淀 | https://github.com/JasonJarvan/CodeTeam/issues/1 | 后续 sub-project 一致采用 `to{Prefix}{Role}` 命名 | 2026-05-31 | open |

## Archive

| ID | Action | Done | By |
|---|---|---|---|
| UN-001 | 授权全局安装 OpenSpec CLI（`npm i -g @fission-ai/openspec` → v1.3.1） | 2026-05-27 | bootstrap session |
| UN-002 | 把 handoff 带到 `~/Codes/AgentCrawlers/` 起 ruflo 会话 — **obsoleted**：2026-05-30 决定继续在当前 repo 开发，迁移取消 | 2026-05-30 | bootstrap session |
| UN-003 | 起新 orchestrator 会话，按 handoff §7 执行 — **completed**：scope 扩展到 10 子项目，SP-0 design + plan 已落盘 | 2026-05-31 | orche session 2 |
| UN-004 | 确认已开通阿里云 AK/SK + Tingwu + OSS bucket — **obsoleted**：R5 (2026-05-31) 决定切换 BN+bcut，v1 不再依赖 Aliyun 凭据 | 2026-05-31 | orche session 2 |
| UN-007 | 起 SP-0 impler — **done**：SP-0 完整落地（tag `sp0-complete` at `5c28447`）；handoff chain 已 burn | 2026-05-31 | sp0impler |
| UN-009 | 起 SP-1 impler — **done**：SP1Impler 已在跑（Stage 1 wip）；进度跟踪走 `§SP Status Board` SP-1 行，无 user 动作待办 | 2026-05-31 | user + sp1impler |
| UN-010 | 决定 SP-0 final-sweep residue 处理范围 — **resolved**：orche decisions letter ack D1=A（4 文件改 v2）+ D2=A（AgentCrawl 串延到 UN-005）；sp0impler 已执行（commit `de4af04`） | 2026-05-31 | sp0impler + orche |
| UN-005 | 物理改名 `Tools/AgentCrawl/` → `Tools/JarvanKB/` — **done**（user 独立 session 执行；D2 deferred AgentCrawl 串改名 orche 跟进于本 commit，仅历史 narrative 文件保留旧名） | 2026-05-31 | user + orche |
| UN-011 | 起 g3 orche session 继承编排 — **done**：g3（Claude Opus 4.8 1M）已读 g3-handoff、跑完引导检查、接管 SP1Impler 反馈链路；g2 退场；inheritance handoff 已 burn | 2026-05-31 | user + orche g3 |
| UN-012 | 给 SP-1 Stage 3 greenlight + 选执行模式 — **resolved**：user 在 SP1Impler chat 直接给绿灯 + 选 subagent-driven；orche g3 plan 审阅通过（fork→自写偏离由 CookieCloud GPLv3 发现正当化，保 MIT 干净）。SP1Impler 已进入 Stage 3 | 2026-05-31 | user + orche g3 |
