# Architecture Index — AgentCrawl

## 域地图

| Domain | 状态 | 文件 | 覆盖范围 |
|---|---|---|---|
| `crawl-pipeline` | **活跃** | `crawl-pipeline.md` | 知乎/B站抓取、字幕优先、yt-dlp 抽音、OSS、听悟链路、模块边界 |
| `harness` | 预留 | — | HarnessStack / RepoMem / OpenSpec 自身演进的架构记忆 |
| `credentials` | 预留 | — | cookie / SESSDATA / 阿里云 AK / OSS 凭据生命周期与刷新逻辑 |
| `asr-summary` | 预留 | — | 听悟 / Paraformer / 本地 SenseVoice 切换策略，与 `crawl-pipeline` 解耦 |

域只有"用得到才开文件"——预留域写在地图里即可，等真有内容时再 `git mv` 或新增。

## 域选择规则

- 选 `domains` 字段时从本表 `状态 = 活跃` 的项里挑
- temp 文档可同时贴多个域（多域任务）
- 域名升级（重命名 / 拆分 / 合并）必须通过 `RepoMem.merge` HITL 审阅
