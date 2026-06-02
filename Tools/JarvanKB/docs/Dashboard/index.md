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

依赖图 → 现在能并行什么

SP-0 ✓ ──┬─ SP-1 ✓ ──┬─ SP-3(知乎Skill)   🟡 wip ← SP-2 ✓
         │            ├─ SP-4b(B站Skill)  ← 等 SP-4a
         │            ├─ SP-5a(知乎Watcher)🟡 wip ← SP-2 ✓
         │            └─ SP-5b(B站Watcher) ← 等 SP-4a
         ├─ SP-2(知乎引擎) ⚫ done
         └─ SP-4a(B站引擎) 进入条件:SP-0 ✓ + BN docker 可达
         
> JarvanKB 子项目状态板（kanban-like）。一屏看全部 SP 状态 + 责任 agent + 进入条件。
> 状态 emoji：🟡 wip / 🔴 blocked / ⚫ done / ⚪ queued / 🟢 ready
>
> 升级触发（任一满足则迁移到 `antopolskiy/kanban-md`）：≥2 个 impler 并发 / 单 SP 内 task ≥10 / 需要 per-task 评论历史。详见 R9 调研结论。

| ID | 名称 | 状态 | Owner Agent | 进入条件 |
|---|---|---|---|---|
| SP-0 | 骨架 + recipe v2 迁移 | ⚫ done | sp0impler | （无）|
| SP-1 | CookieManager（自写 Express 复刻 CookieCloud 协议 + hook） | ⚫ done | sp1impler | 完成 2026-05-31（merge `b84ee0f`，40 tests，协议契约 `Service/crawl/cookie-manager/docs/interface.md`）；Step 8 RepoMem.merge 已完成（impler-driven HITL，激活 credentials 域） |
| SP-2 | 知乎引擎 | ⚫ done | sp2impler | 完成 2026-06-02（merge `f8c14cb`，51 tests + 真站 smoke 全过；纯 cookie+HTTP 无签名/无浏览器）；Step 8 RepoMem.merge 已完成（impler-driven HITL，提升知乎链路根因/坑到 `crawl-pipeline.md`）；契约 `Engine/zhihu/docs/interface.md`；v1.1 评论完整树已 handoff `toZhihuCommentImpler/` |
| SP-3 | 知乎 Skill | 🟡 wip | sp3impler | SubOrche（UN-019）已 spawn → `toSP3Impler/handoff.md`（起会话=UN-020）。范围锁定：cookie=主动 pull、输出=可配置根目录(vault 无关)、**SP-3 落地 `Engine/common` LLMClient 真实现**（vague_path 分类；凭据待用户填 → verify gate）。SP-2 ✓ |
| SP-4a | B 站引擎 | 🔴 blocked (Stage 3 — 离线全done，卡 BN gate) | sp4aimpler | 离线代码全部完成：**56 单测全过、subagent-driven 逐任务两阶段 review + 最终整体 review（READY-FOR-SMOKE）、引擎不调 LLM、无活网络**。11 单元 `Engine/bilibili/src/bilibili/`；契约 `Engine/bilibili/docs/interface.md`；BN 部署件 `Engine/bilibili/deploy/bilinote/`（`TRANSCRIBER_TYPE=bcut`）。**仅剩手动 smoke（Task 16）卡 BN 可达（UN-018）→ 见 `from-sp4aimpler-blocker-bn-docker.md`**。BN 起后我跑 smoke → verify → review/finish → Step 8 merge | |
| SP-4b | B 站 Skill | ⚪ queued | (无) | SP-4a 实现完成 |
| SP-5a | 知乎收藏夹监听服务 | 🟡 wip | sp5aimpler | SubOrche（UN-019）已 spawn → `toSP5aImpler/handoff.md`（起会话=UN-021）。范围锁定：独立服务+自带调度器(默认30–60min)、高水位 `created`、cookie=主动 pull、输出=可配置目录(无分类)。**impler 务必先读 `crawl-pipeline.md` §知乎链路**。SP-2 ✓ |
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
| UN-020 | B | **起 SP3Impler session**（新会话，cwd=`Tools/JarvanKB/`），第一句：`read docs/sendbox/toSP3Impler/handoff.md and start SP-3`。范围已锁定，impler 跑 v2 8 步（含自己的 compressed brainstorm + Step 8 merge）；与 SP5aImpler 并行 | `docs/sendbox/toSP3Impler/handoff.md` | SP-3 落地 | 2026-06-02 | open |
| UN-021 | B | **起 SP5aImpler session**（新会话，cwd=`Tools/JarvanKB/`），第一句：`read docs/sendbox/toSP5aImpler/handoff.md and start SP-5a`。impler 务必先读 `crawl-pipeline.md §知乎链路`；与 SP3Impler 并行 | `docs/sendbox/toSP5aImpler/handoff.md` | SP-5a 落地 | 2026-06-02 | open |
| UN-018 | F | **起 BiliNote docker 并确认 endpoint** —— SP-4a 离线全done，仅卡此项做手动 smoke。部署件已出：`cd Engine/bilibili/deploy/bilinote && cp .env.example .env && docker compose up -d`（`TRANSCRIBER_TYPE=bcut`）→ 开 `http://localhost:3015` 加 LLM 供应商记 `provider_id` → 填 `Engine/bilibili/config/bilibili-engine.yaml`（从 `.example` 复制）→ 回复确认。完整步骤见 blocker 信 / `deploy/bilinote/README.md` | `from-sp4aimpler-blocker-bn-docker.md`（已发）+ `Engine/bilibili/deploy/bilinote/` | SP-4a Task 16 smoke | 2026-06-01 | open |

## Archive

| ID | Action | Done | By |
|---|---|---|---|
| UN-019 | 起 ZhihuCrawl SubOrche session（继承 Zhihu 垂直）— **done**：SubOrche 已 boot，compressed brainstorm 锁定 SP-3/SP-5a 跨 SP 边界（cookie=主动 pull、输出=可配置根 vault 无关、LLMClient 真实现归 SP-3）；产出 `toSP3Impler/`+`toSP5aImpler/` 两封 handoff + cookie-pull 决策升级信给 root（`from-zhihucrawlorche-cookie-pull-decisions.md`）；用户新动作转 UN-020/UN-021 | 2026-06-02 | user + zhihucrawl suborche |
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
| UN-013 | cookie-manager 公网暴露 — **done**：公网 HTTPS 全链路验证通（`https://www.zhaoricheng.fun:48098` / 直连 `:48088`）；frps AI 配了 Nginx SSL 代理。剩余"起正式服务 + 扩展填 HTTPS 地址"是用户例行操作，非 orche 待办 | 2026-05-31 | sp1impler + frps AI + user |
| UN-014 | SP-1 sendbox 后处理 — **done**：archive sp0-done、burn sp1-done + toSP1Impler/handoff + toFRPS/handoff；Step 8 merge 由 impler 完成（未重做）；`temp/sp1-cookie-manager/research.md` 保留（impler 刻意保留 + 下游 SP-2/3 参考） | 2026-06-01 | orche g3 |
| UN-015 | 修订 merge 归属规范 — **done**：CLAUDE.md §3 step8 + §4、longterm §Pipeline v2 + §Hard Invariants 均加"impler owns merge closure"，并固化 handoff §3.F 措辞（commit `16da3b6`） | 2026-06-01 | orche g3 |
| UN-016 | 起 SP2Impler session — **done**：SP-2 知乎引擎完成并 merge（`f8c14cb`，51 tests + 真站 smoke）；impler 闭环 Step 8（提升知乎链路根因到 crawl-pipeline.md）；orche 已 burn SP-2 sendbox 链 + codify promotion standard（`96c9548`） | 2026-06-02 | user + sp2impler + orche g3 |
| UN-017 | 起 SP4aImpler session — **done**：SP4aImpler 已在跑（Stage 2 done，plan-ready 已发）；orche g3 审阅通过 → `toSP4aImpler/from-orche-sp4a-greenlight.md`（subagent-driven）；离线 Tasks 1–14 可跑，live smoke 仍 gate 在 UN-018 | 2026-06-02 | user + sp4aimpler + orche g3 |
