# [crawl-pipeline] 先实测、再实现:别从参考库代码臆测 API 字段语义

> Durable cross-vertical lesson,由 `RepoMem.merge` of `sp5a-watcher-v1.1`(2026-06-10,HITL)提升。
> 跨垂直由 BilibiliCrawl SubOrche 发现并上报;适用于**每一个**会推断 API 字段/分页语义的 crawl SP。
> 精炼教训,非代码机制(机制在各模块/§知乎链路)。

## 根因案例
SP-5a v1 从**参考库代码 + 假设**推断「知乎收藏夹 API 无可靠收藏时间字段」,据此选 seen-id set 并把该结论写进
design §2 —— **错了**:真站每条有**顶层 `created` = 收藏时间**(v1 看错成 `content.created` 发布时间),且条目
**并非** newest-favorited-first。由 BilibiliCrawl SubOrche 在 SP-5b brainstorm 时跨垂直发现并上报
(`docs/sendbox/toOrchestrator/from-bilibilicrawlorche-sp5a-watermark-correction.md`)。

## 规则(所有 crawl SP)
任何**水位 / 分页 / 字段依赖**逻辑落地前,按顺序:
1. **实测爬真站**(真 cookie、真端点),dump 原始 response;
2. **文档化每个有价值属性的真义** → `<module>/docs/RepoMem/temp/<slug>/` 字段文档;
3. **用户复审/编辑该文档**(Stage-0 gate);
4. **才实现**。

已编码为 SP-5b 的 Stage-0 gate;SP-5a v1.1 用同样的实测字段文档闭环
(`Service/crawl/zhihu-watcher/docs/RepoMem/temp/sp5a-watcher-v1.1/api-fields-empirical.md`)。

## 推论也要落在实测上
连下游论断也曾被 armchair 误推:SP-5a v1.1 一度断言「专栏永久 403」—— 实际根因是 `__zse_ck` 时效门 +
answer-only api-fallback(见 `crawl-pipeline.md §知乎链路`),且实测 nav-GET 200 时专栏照常抓取。
**论断要落在实测证据上,不在推理链上**——哪怕推理链看起来很顺。
