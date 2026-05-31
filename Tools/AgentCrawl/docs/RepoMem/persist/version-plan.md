# version-plan.md

> JarvanKB 的长期版本与路线图记录。
> 由 `docs/HarnessStack/longterm.md` §Related Documents 显式引用。

## Recipe 版本历史

| 版本 | Recipe ID | 生效区间 | 说明 |
|---|---|---|---|
| v1 | `openspec-superpowers-repomem-sendbox-dashboard` | 2026-05-26 → 2026-05-31 | Bootstrap 阶段。经 Full Rewrite 流程废弃。 |
| **v2** | `superpowers-repomem-sendbox-dashboard` | 2026-05-31 → | 移除 OpenSpec，适配薄壳子项目形态。详见 `longterm.md §Recipe v1→v2 Migration`。 |

## 项目改名

- **AgentCrawl**（2026-05-26 → 2026-05-31）：原范围 = 知乎 + B 站爬虫
- **JarvanKB**（2026-05-31 → ）：范围扩展到 crawl + ingester + 未来知识库整理工具；个人品牌命名，便于 OSS 释出辨识
- 物理改名 `Tools/AgentCrawl/` → `Tools/JarvanKB/` 由用户在独立 session 完成（Dashboard UN-005 跟踪）

## 当前阶段

- **SP-0 in progress**（2026-05-31）：仓库骨架 + HarnessStack v2 迁移
  - 设计稿：`docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md`
  - 实施计划：`docs/superpowers/plans/2026-05-31-SP-0-jarvankb-skeleton.md`
  - Impler 交接信：`docs/sendbox/toSP0Impler/handoff.md`

## 子项目状态板（10 v1 + 1 v1+）

> 这张表同时承担 JarvanKB SP 级 kanban 的功能（依据 R9 调研结论"方案 1 增强"）。
> 升级触发条件（任一满足则迁移到 `antopolskiy/kanban-md`）：≥2 个 impler 并发 / 单 SP 内 task 数 ≥10 / 需要 per-task 评论历史。
>
> 状态 emoji：🟡 wip / 🔴 blocked / ⚫ done / ⚪ queued / 🟢 ready

| ID | 路径 | 名称 | 状态 | Owner Agent | 进入条件 |
|---|---|---|---|---|---|
| SP-0 | `<root>/` | 骨架 + recipe v2 迁移 | 🟡 wip | sp0impler | （无 — 当前任务） |
| SP-1 | `Service/crawl/cookie-manager/` | CookieManager（fork CookieCloud + hook 机制） | ⚪ queued | (无) | SP-0 完成 |
| SP-2 | `Engine/zhihu/` | 知乎引擎 | ⚪ queued | (无) | SP-0 完成 + SP-1 协议敲定 |
| SP-3 | `Skill/crawl/zhihu-crawl/` | 知乎 Skill | ⚪ queued | (无) | SP-2 实现完成 |
| SP-4a | `Engine/bilibili/` | B 站引擎 | ⚪ queued | (无) | SP-0 完成；BN docker 可达 |
| SP-4b | `Skill/crawl/bilibili-crawl/` | B 站 Skill | ⚪ queued | (无) | SP-4a 实现完成 |
| SP-5a | `Service/crawl/zhihu-watcher/` | 知乎收藏夹监听服务 | ⚪ queued | (无) | SP-2 实现完成 |
| SP-5b | `Service/crawl/bilibili-watcher/` | B 站收藏夹监听服务 | ⚪ queued | (无) | SP-4a 实现完成 |
| SP-6 | `Skill/ingester/crawl-md-saver/` | CrawlMdSaver Skill（爬取-笔记整合包装层） | ⚪ queued | (无) | SP-3 / SP-4b 已注册到 SP-6 |
| SP-7 | `Service/ingester/thino-ingester/` | Thino 块解析整理服务 | ⚪ queued | (无) | SP-6 实现完成 |
| SP-8（v1+） | `Skill/router/web-search/` | Web Search Router（聚合知乎官方 Skill + Tavily + Exa） | ⚪ queued | (无) | v1 全部完成；知乎 API key 已获取 |

## v1.0 OSS 释出计划

待全部 v1 子项目（SP-0..SP-7）端到端验证通过后：

1. 选定 GitHub Organization 名（候选：`JarvanKB` / `Jarvan` / `JarvanWorks`）—— Dashboard UN-006 跟踪
2. 按 `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` §9 执行 fractal 切分：
   - 对每个子项目跑 `git filter-repo --subdirectory-filter <module>/`
   - 把主仓 `docs/HarnessStack/` 复制进子仓作为治理起点
   - 在每个子仓初始化独立的 `docs/{sendbox,Dashboard,RepoMem/persist}/`
   - 在 Organization 下新建 GitHub repo 并推送
3. 主仓（本仓）保留为 umbrella，承载 HarnessStack template + 跨子项目集成测试

## 兼容性 / 升级说明

- HarnessStack recipe 升级：见 `longterm.md §Full Rewrite Conditions`
- ASR 策略（`pre-openspec-decisions.md` D3）在 2026-05-31 R5 调研中**修订**：**v1 从通义听悟切换为 BiliNote + bcut（B站必剪免费云端 ASR）**。D3 标注为 superseded，文件不删（历史溯源）

## 本文件的更新方式

追加为主（append-most）。重大变更（阶段范围重排、recipe 升级、项目改名）走 `RepoMem.merge` HITL 审阅。

> **同步说明**：本文件内容由 plan Task 8.2 heredoc（`docs/superpowers/plans/2026-05-31-SP-0-jarvankb-skeleton.md`）镜像。impler 执行 Task 8 时会以相同内容覆盖写入（eager-materialization 模式 —— 提前把 plan 落地内容写到目标位置，让 impler 写操作变成 idempotent overwrite，避免 H2A 暴露面在 impler 完成前的 user-blocking 间隙）。若在 impler 运行前手动编辑本文件，需同步编辑 plan heredoc。
