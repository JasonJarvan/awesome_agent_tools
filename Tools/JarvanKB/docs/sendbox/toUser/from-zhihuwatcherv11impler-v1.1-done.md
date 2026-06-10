> from: ZhihuWatcherV11Impler (Claude Opus 4.8 1M)
> recipient: 用户(human)
> mode: milestone-done(面向用户的完成说明)
> date: 2026-06-10
> lifecycle: **burn on convergence** —— 你读过、SP-5a v1.1 收敛后即可删除

# SP-5a v1.1 做了什么 —— 给你的完成说明

知乎 Watcher v1.1 已实现、验证、并**本地合并**进 `feat/agentcrawl-bootstrap`(merge `0489382`;11 个提交;58 测试全过;真站 smoke 全绿)。**没有 push、没有动 main。**

## 一句话
v1 只会监听「写死在配置里的收藏夹列表」;v1.1 让配置能说「自动发现并监听某个用户的全部(命名)收藏夹」,顺带修了一个水位 bug、加了失败退避。

## 具体做了 5 件事

1. **两种监听目标(config `targets`,替换旧 `collections`)**
   - `type: collection` —— 显式单个收藏夹(同 v1,id 或完整 URL)。
   - `type: user` —— **自动发现该用户的全部命名收藏夹**(`url_token: me` 或字面 token)。新增 `TargetResolver` 每轮把配置展开成收藏夹列表喂给原有循环;按 id 去重、单个目标失败只跳过不崩。
   - **默认夹「我的收藏」默认跳过**(`include_default: false`,你定的)—— 留给后续「默认夹自动分类」那个独立 SP。

2. **修了水位 bug(原 v1 的「无收藏时间字段」结论是错的)**
   - 真站实测确认:每条有**顶层 `created` = 收藏时间**(v1 错看成 `content.created` 作者时间)。
   - 现在解析它,支持可选 `only_after:<带时区日期>` 过滤 + **首轮基线**(全新监听不会一次性回填几千条历史,只存部署后新增;`backfill_on_first_run: true` 可关掉)。
   - **不做早停**:实测条目**不按收藏时间排序**,早停会漏条(只过滤、仍翻完整页)。

3. **403 失败退避(轻量)** —— 连续失败 N 次进入时间窗 cooldown,**成功即清零**;兜住「当下持续 nav-GET 403 且无兜底」的专栏项,不再每轮重试(非永久失败——下一轮 200 即恢复)。

4. **favorites_client** 新增 `list_user_collections`(发现端点)+ `get_current_url_token`(`/api/v4/me` 解析 `me`)。

5. **output_dir 指向你的 Obsidian 库** `…/ResourceBase资源库/Zhihu知乎`;命名收藏夹写进既有同名子目录(延续 Zhihu-Collection-Saver 库)。example config + 模块文档已更新。

## 验证证据(真站,2026-06-10)
- `/api/v4/me` 纯 cookie 200 → 解析出 `zhao-cheng-57-99-79`。
- by-user 发现 **35 个收藏夹 → resolver 保留 33 个**(跳过默认「我的收藏」+ 1 个空夹「产品思维」)。
- 首轮基线:各夹「0 new」—— 不回填历史 ✓。
- 完整管道(量化夹,backfill=true):**2 条 fetch+save**;复跑 **0 new(去重不变式实测确认)**✓。
- 58 单测全过;独立 code-review 的 2 个 blocking 问题已修(时区 datetime 防护 + example/docs)。

## 不在 v1.1、已分流(两封信在 `toZhihuCrawlOrche/`)
- **专栏全文抓取**:编排层已查明专栏 `/api/v4/articles` 需 x-zse-96 签名,你已选**不加签名器(UN-028)**→ 专栏一旦 nav-GET 403 就**无法救回**(答案有 `/api/v4/answers/{id}` 兜底、专栏没有)。**但 nav-GET 403 是间歇性风控、非普遍**——导航 GET 返回 200 的专栏照常抓到(我 smoke 就存了一篇专栏);backoff 只兜住「持续 403」的重试浪费,非"永久抓不到"。
- **默认夹「我的收藏」自动分类**:独立新 SP 提案(复用 SP-3 分类能力 + 你 Obsidian 库现成的 ~33 类目 + 列表 excerpt 作输入),待你 greenlight 由 SubOrche 立项。

## 还差最后一步(我接着做)
**Step 8 RepoMem.merge(HITL)**:把跨 SP 复用的根因提升到全局 `crawl-pipeline.md §知乎链路`(顶层 created=收藏时间、不按收藏时间排序、/me+people/collections 免签名、is_default、以及「先实测再实现」的方法论教训)+ 修 v1 design §2 的假结论。**会先给你过目再落盘**(且该全局文件正被另一会话改动,需协调)。

## 指针
- 设计 spec:`Service/crawl/zhihu-watcher/docs/superpowers/specs/2026-06-09-SP-5a-v1.1-collection-resolution-design.md`
- 实现 plan:`…/plans/2026-06-10-SP-5a-v1.1-collection-resolution-plan.md`
- 实测字段文档:`…/docs/RepoMem/temp/sp5a-watcher-v1.1/api-fields-empirical.md`
- 模块决策日志:`…/docs/RepoMem/decisions.md`(2026-06-10 条目)

— ZhihuWatcherV11Impler
