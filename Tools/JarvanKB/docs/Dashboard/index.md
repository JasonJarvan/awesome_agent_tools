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

SP-0 ✓ ──┬─ SP-1 ✓ ──┬─ SP-3(知乎Skill)   ⚫ done ← SP-2 ✓
         │            ├─ SP-4b(B站Skill)  ← 等 SP-4a
         │            ├─ SP-5a(知乎Watcher)⚫ done(v1.1=UN-024)
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
| SP-2 | 知乎引擎 | ⚫ done | sp2impler | 完成 2026-06-02（merge `f8c14cb`，51 tests + 真站 smoke 全过；纯 cookie+HTTP 无签名/无浏览器）；Step 8 RepoMem.merge 已完成（impler-driven HITL，提升知乎链路根因/坑到 `crawl-pipeline.md`）；契约 `Engine/zhihu/docs/interface.md`；**v1.1 评论完整树 ⚫ done**（merge `9081cbc`，58 tests + live smoke；Step 8 闭环：decisions.md D7 + 提升 child_comment offset 坑到 `crawl-pipeline.md` §知乎链路，by zhihucommentimpler）；**v1.2 限流加固（原 ARTICLE api-fallback 重定范围）🟡 wip**（root g4 直属子 ZhihuArticleImpler；**§4 live-probe 推翻原前提**：`/api/v4/articles/{id}` 需 `x-zse-96`（403 code 10003，≠ 无签名的 `/api/v4/answers/{id}`），镜像 ANSWER 兜底**不可行**、未引签名器；专栏 nav-GET 实测 200、原路径全文可抓 → 28 失败实为 **bulk 瞬时限流** 非结构性门。**user 2026-06-09 决策=A + 加主动限流**：再测 60 连续 nav-GET @~2req/s **零限流** → 限流为**突发/并发敏感**非累计；修法=引擎统一 `_request` 加 **主动限流（最小间隔+抖动，进程共享）+ 403/429 退避重试（遵从 Retry-After）**，4 处出站请求全走它，非破坏 `fetch()`/`FetchResult`，模块级 `configure()` 可调。plan `Engine/zhihu/docs/superpowers/plans/2026-06-09-zhihu-ratelimit-hardening-plan.md`；证据 `…/RepoMem/temp/zhihu-engine-article-fallback/probe-findings.md`） |
| SP-3 | 知乎 Skill | ⚫ done | sp3impler | 完成 2026-06-07(已合并 feat/agentcrawl-bootstrap,功能 tip `c500119`,**40 单测 + 离线 smoke + live vague_path 分类**对真 provider `mimo-v2.5-pro`(OpenAI 协议)通过)。`URL→md` 纯抓取无 LLM;仅 vague 路径调 LLM 分类(推断现有子目录+提议新建;输入=标题+type+清洗后前导 `classify_snippet_chars` 默认 240 省 token);cookie 主动拉取内存解密(绝不落盘明文);**落地 `Engine/common` LLMClient 真身**(`jarvankb_common`,litellm + 自定义 OpenAI 兼容 provider;SP-4b/6/7 复用勿重写);一份 agentskills.io `SKILL.md` 通吃四端。契约 `Skill/crawl/zhihu-crawl/docs/interface.md`。Step 8 RepoMem.merge 已闭环(impler-driven HITL:提升 cookie 解密参考实现 / LLM 共享层 / SKILL.md 打包 / **LLMService v2 路线** 到 persist)。done 信已发 SubOrche。**v2 候选 = LLMService**(D-SP3-4) |
| SP-4a | B 站引擎 | ⚫ done | sp4aimpler | 完成 2026-06-02：**59 单测全过 + 两条路径对真实 BN+真实B站 smoke 通过**（ASR `BV1GJ411x7h7` / 字幕 `BV1BXQABNE4y`→prefetched→mimo-v2.5-pro；prose 可读文本已验证）。subagent-driven 逐任务两阶段 review + 最终整体 review。契约 `Engine/bilibili/docs/interface.md`；部署件 `deploy/bilinote/`。Step 8 RepoMem.merge 已完成（impler-driven HITL，提升 B站 cookie 域=`bilibili.com`无点 + BN+bcut 运维坑到 `credentials.md`/`crawl-pipeline.md`）。done 信已发 orche | |
| SP-4b | B 站 Skill | 🟡 wip | sp4bimpler | SubOrche 已 spawn → `toSP4bImpler/handoff.md`(起会话=UN-025)。结构镜像 SP-3(⚫ done):URL→cookie 拉取→`BilibiliCredential`→**冻结 SP-4a 引擎** `engine.transcribe`+`render`→保存 + vague_path 分类。**跨垂直依赖已解除**:SP-3 已 done、真实 LLMClient(`jarvankb-common`)+ provider `mimo-v2.5-pro` 已配 → **直接复用,勿重写,无 LLM-creds gate**(must-read `persist/memory/llm-shared-layer.md`)。cookie=主动 PULL(`domain=bilibili.com` 无点,SESSDATA;engine interface §5 的 `.bilibili.com` 是过时残留)。live smoke 需 BN(已起 `127.0.0.1:3015`)。SP-4a ✓ **【Stage 1-4 ⚫ 2026-06-07】** RepoMem.read 两层 + compressed brainstorm(5 决策 user 拍板:打包镜像 SP-3 / cookie 复用 / vague_path / 分类输入=标题+总结摘要 / 单文件 render 默认 config 可覆盖)+ design(`docs/.../specs/2026-06-07-SP-4b-bilibili-skill-design.md`)+ 10-task TDD plan(`.../plans/2026-06-07-SP-4b-bilibili-skill-plan.md`)已落 commit `b654662`/`2cfea0f`;plan-ready 已发 SubOrche(`from-sp4bimpler-plan-ready.md`),待 greenlight + 执行模式(默认 subagent-driven)。**cookie 失败非致命**(降级 `credential=None`,异于 SP-3 fail-loud)。`config/bilibili-engine.yaml` 缺失 = **live-smoke 时**的 BN/引擎配置 gate(不阻塞单测) |
| SP-5a | 知乎收藏夹监听服务 | ⚫ done | sp5aimpler | 完成 2026-06-07(merge `7acacb2`,**32 tests + 真站 smoke**:收藏夹端点 200 无 x-zse-96、168 条→140 落盘、二轮去重 0 新增;28 条专栏因 SP-2 api-fallback 仅覆盖 ANSWER 而 403)。纯 cookie+HTTP、seen-id 去重、BlockingScheduler+compose、cookie=SP-1 主动拉取内存解密(绝不落盘明文)。契约 `Service/crawl/zhihu-watcher/docs/interface.md`。Step 8 RepoMem.merge 已闭环(`4a0b45c`,impler-driven HITL:提升收藏夹端点无签名/offset 分页/专栏-403 坑到 `crawl-pipeline.md §知乎链路`)。done 信已发 SubOrche。**v1.1**(两种目标解析模式)handoff 已草拟 → UN-024 |
| SP-5b | B 站收藏夹监听服务 | 🟡 wip | sp5bimpler | SubOrche 已 spawn → `toSP5bImpler/handoff.md`(起会话=UN-026)。结构镜像 SP-5a(⚫ done)的 7 组件 daemon(BlockingScheduler+compose+`--once`);调 **冻结 SP-4a 引擎** → BN 转录;默认 15–30min;cookie=主动 PULL(`bilibili.com` 无点);**impler 务必先读 `crawl-pipeline.md` §B站链路**;live smoke 需 BN(已起 `127.0.0.1:3015`)。**水位特例(用户 2026-06-07 指令)**:不许照 SP-5a armchair 读 API——SP-5a 误读 `content.created`(创作时间)漏了顶层 `created`(收藏时间)而错判"无可靠收藏时间"改走 seen-id。SP-5b **Stage 0 先真站爬 favorites API → 落字段语义文档 → 用户 review/改 → 才实现水位**;默认 `fav_time` 高水位(spec + 用户先验),不可靠才回落 seen-id。SP-4a ✓ **【Stage 0 ⚫ 2026-06-10】真站实证(账号真 cookie)证实 `fav_time` 真存在且≠`pubtime`(铁证:fav 04-24 vs pub 04-16)→ 默认 fav_time 水位成立,纠正 SP-5a 臆断;`order=mtime`=fav_time 降序(可早停);坑=`media_count` 含失效条目,停止跟 `has_more` 勿用总数。字段文档待 user review=UN-029,门不阻塞读代码但阻塞 design 定稿** |
| SP-6 | CrawlMdSaver Skill（爬取-笔记整合） | ⚪ queued | (无) | SP-3 / SP-4b 已注册到 SP-6 |
| SP-7 | Thino 块解析整理服务 | ⚪ queued | (无) | SP-6 实现完成 |
| SP-8（v1+） | Web Search Router（聚合知乎 Skill + Tavily + Exa） | ⚪ queued | (无) | v1 全部完成；知乎 API key 已获取 |

详细路径见 `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` §7。

## Active

| ID | Type | Action | Where (detail) | Blocker for | Since | Status |
|---|---|---|---|---|---|---|
| UN-006 | F | 决定 v1.0 GitHub Organization 名（候选：JarvanKB / Jarvan / JarvanWorks）— 此项非阻塞 v1 实现，可推迟到 v1 完成度临近 | `docs/RepoMem/persist/version-plan.md` §v1.0 OSS release plan | v1.0 切分 | 2026-05-31 | open |
| UN-008 | D | Review CodeTeam#1（含 SubOrche 泛化评论）+ CodeTeam#2（HarnessStack v2 consolidated proposal），决定推动上游修复节奏还是先在本仓库本地约定中沉淀 | https://github.com/JasonJarvan/CodeTeam/issues/1 | 后续 sub-project 一致采用 `to{Prefix}{Role}` 命名 | 2026-05-31 | open |
| UN-030 | B | **起 HarnessStackImpler session**（新会话，cwd=`Tools/JarvanKB/`），第一句：`read docs/sendbox/toHarnessStackImpler/handoff.md and start`。把 CodeTeam **#3（codegraph code-map）+ #4（Lane Tiering）** 实例化进本仓库 HarnessStack。**关键：两提案是为 `openspec-superpowers-repomem-ecc` recipe 写的，本仓库是 v2 `superpowers-repomem-sendbox-dashboard`（已删 OpenSpec、用 sendbox+dashboard 非 ECC）→ 必须翻译不能照抄**。impler 会**先与你 brainstorm 采纳范围 + 是否授权装 codegraph**（`npm i -g @colbymchenry/codegraph` + `.mcp.json` 改动=用户授权门）。root g4 直属子，完报 `toOrchestrator/`。延续 UN-008 的 CodeTeam 上游流（#1/#2→#3/#4）| `docs/sendbox/toHarnessStackImpler/handoff.md` | #3/#4 本地落地 | 2026-06-10 | open |
| UN-025 | B | **起 SP4bImpler session**（新会话，cwd=`Tools/JarvanKB/`），第一句：`read docs/sendbox/toSP4bImpler/handoff.md and start SP-4b`。范围已锁定,impler 跑 v2 8 步(含自己的 compressed brainstorm + Step 8 merge);镜像 SP-3、复用真实 LLMClient + mimo;与 SP5bImpler 并行 | `docs/sendbox/toSP4bImpler/handoff.md` | SP-4b 落地 | 2026-06-07 | open |
| UN-026 | B | **起 SP5bImpler session**（新会话，cwd=`Tools/JarvanKB/`），第一句：`read docs/sendbox/toSP5bImpler/handoff.md and start SP-5b`。镜像 SP-5a;**先做 Stage 0 真站 favorites-API 调研 → 字段文档待你 review/改 → 才实现水位**(纠正 SP-5a armchair 读 API);与 SP4bImpler 并行 | `docs/sendbox/toSP5bImpler/handoff.md` | SP-5b 落地 | 2026-06-07 | open |
| UN-024 | B | **起 ZhihuWatcherV11Impler session**（新会话，cwd=`Tools/JarvanKB/`），第一句：`read docs/sendbox/toZhihuWatcherV11Impler/handoff.md and start SP-5a v1.1`。SP-5a v1 已 done+merged；v1.1=两种收藏夹目标解析模式(Mode1 按 UserId 列全部 / Mode2 显式 List)，Server 层定位已锁;parent=ZhihuCrawl SubOrche | `docs/sendbox/toZhihuWatcherV11Impler/handoff.md` | SP-5a v1.1 落地 | 2026-06-07 | open |
| UN-029 | D | **Review + 编辑 SP-5b Stage-0 字段文档**(B站收藏夹 API 实证):确认 ① 监听哪些收藏夹(账号下 22 个) ② 水位形态(`fav_time`高水位+seen-id兜底**(推荐)** / 纯 fav_time / 纯 seen-id) ③ 是否只处理 `type==2` 视频。**实证已证 `fav_time` 真存在且≠pubtime(纠正 SP-5a 臆断)**;改完文档或在 chat 拍板即解门,我据此设计水位。门**不阻塞**我读代码,但**阻塞** Step 2 design 定稿 | `Service/crawl/bilibili-watcher/docs/RepoMem/temp/sp5b-bilibili-watcher/favorites-api-fields.md`（信件 `docs/sendbox/toBilibiliCrawlOrche/from-sp5bimpler-blocker-fav-api-review.md`） | SP-5b 水位设计 | 2026-06-10 | open |

## Archive

| ID | Action | Done | By |
|---|---|---|---|
| UN-028 | 决定 SP-2 v1.2 方向（blocker）— **done**：user 选 **A**（引擎加固，守 D1 无签名、拒 B 签名器）并加码要求"先做主动限流避免被抓 + 被拒重试"。impler 安全测得限流为突发敏感（60 连续 nav-GET @~2req/s 零限流）→ 重定范围为「统一 `_request` 加主动限流 + 403/429 退避重试（遵从 Retry-After）」，plan 已落 `Engine/zhihu/docs/superpowers/plans/2026-06-09-zhihu-ratelimit-hardening-plan.md`；进度走 §SP Status Board SP-2 行（v1.2 🟡 wip） | 2026-06-09 | user + zhiharticleimpler |
| UN-027 | 起 ZhihuArticleImpler session（SP-2 v1.2）— **done**：会话已起并跑完 RepoMem.read 两层 + 读 §2/§3 代码缝 + green baseline（58 tests）+ §4 gating live-probe。probe 推翻前提（articles `/api/v4` 需签名、专栏 nav-GET 实测 200），未写代码即命中 §4 blocker → escalate `from-zhihuarticleimpler-blocker-zse96.md`，user 新动作转 **UN-028** | 2026-06-07 | user + zhiharticleimpler |
| UN-022 | 起 BilibiliCrawl SubOrche session（继承 Bilibili 垂直）— **done**：SubOrche 已 boot，compressed brainstorm 锁定 SP-4b/SP-5b 两个 B站特有跨 SP 决策——(1) SP-4b LLMClient 跨垂直依赖已解除(SP-3 done、真实 LLMClient+mimo 已配 → 直接复用)、(2) SP-5b 水位按用户指令改"Stage 0 真站爬 API → 字段文档待 user review → 才实现"(纠正 SP-5a armchair 误读 `content.created`)；产出 `toSP4bImpler/`+`toSP5bImpler/` 两封 handoff；用户新动作转 UN-025/UN-026。SP-5a 顶层 `created`=收藏时间的纠正(跨垂直、出 SubOrche scope)**已按 user 决定升级 root g4** → `toOrchestrator/from-bilibilicrawlorche-sp5a-watermark-correction.md`,建议折进 SP-5a v1.1(UN-024) | 2026-06-07 | user + bilibilicrawl suborche |
| UN-023 | 起 g4 root orche session 继承编排 — **done**：g4（Claude Opus 4.8 1M）已读 `g4-handoff.md`、跑完引导检查（git log + 三个 SubOrche 收件箱 + 五大 must-read）、确认 SP-3/SP-5a 已 done+merged 且 SP-3 LLM 凭据 gate 已解（live `mimo-v2.5-pro`）；g3 退场，g4 接管治理 + 两条 SubOrche 线 + SP-6/7 排程；`g4-handoff.md` 已 burn，version-plan generations g4 行已标识 | 2026-06-07 | user + orche g4 |
| UN-021 | 起 SP5aImpler session — **done**：会话已起并在跑;Stage 1–4(design+plan)已落、user 批准;进度跟踪走 §SP Status Board SP-5a 行 | 2026-06-02 | user + sp5aimpler |
| UN-020 | 起 SP3Impler session — **done**：SP-3 已在跑（LLMClient 真实现已落、interface 冻结、code-review 完；近完成，卡用户 LLM 凭据做 live smoke）；进度走 §SP Status Board SP-3 行 | 2026-06-07 | user + sp3impler |
| UN-018 | 起 BiliNote docker + 确认 endpoint — **done**：用户起容器（compose 映射后端 `:8483`，因 `latest` 镜像 nginx 坏）；SP4aImpler 经 API 配 `TRANSCRIBER_TYPE=bcut` + 注册 mimo-v2.5-pro 供应商，跑通 ASR + 字幕两条路径 smoke。SP-4a 已 done | 2026-06-02 | user + sp4aimpler |
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
