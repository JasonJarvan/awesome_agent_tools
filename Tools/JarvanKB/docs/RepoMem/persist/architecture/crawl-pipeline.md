# Architecture

> ⚠️ **部分 SUPERSEDED（R5, 2026-05-31）**：下文 **B 站管线**（Tingwu 听悟 + OSS 上传 + yt-dlp 抽音频 +
> Paraformer fallback）是 **R5 之前的旧设计，已废弃**。v1 B 站方案改为 **BiliNote Docker + bcut（B站必剪
> 免费云端 ASR）+ 字幕优先级联**，Aliyun/OSS 退出 v1（见 `version-plan.md` §Compatibility notes、
> `credentials.md`、SP-0 design §7 SP-4a）。SP-4a 的权威范围以 SP-0 §7 为准，**勿照本文件 B 站部分实现**。
> **知乎链路**：旧的 CDP `Chrome:9222` → Jina Reader 推测链 **已废弃**（SP-2 实测改走纯 cookie+HTTP，
> 见下方 §知乎链路（SP-2 实现）+ `Engine/zhihu/docs/RepoMem/decisions.md`）。

## B站链路（SP-4a 实现，BiliNote+bcut，已验证 2026-06-02）

R5 后的真实 v1 管线（**取代下文 Tingwu/OSS 旧设计**）。SP-4a 是自托管 **BiliNote（BN）** 的 HTTP 客户端；
引擎自身不调 LLM（BN 内部调）。契约见 `Engine/bilibili/docs/interface.md`，部署见 `Engine/bilibili/deploy/bilinote/`。

**真实流（引擎主导的字幕优先级联）：**
```
video_ref → bilibili-api-python get_info（元数据，公开无需 cookie）
          → get_subtitle(cid)（需 SESSDATA）
   命中字幕 → 作 prefetched_transcript 喂 BN → BN 跳过下载+ASR，只跑 LLM 总结
   未命中   → BN generate_note → yt-dlp 下音频 → bcut（B站必剪免费云 ASR）→ LLM 总结
          → 引擎组装 BilibiliResult → 渲染 Markdown（确定性 prose 合并，无 LLM）
```

**可复用运维坑（SP-5b Watcher 同样消费 BN，务必先看）：**
- **BN `ghcr.io/jefferyhcool/bilinote:latest` 全合一镜像的 nginx 是坏的**：`/` 代理到不存在的 `:8080`，
  且残留 Debian 默认站点遮蔽 `/api/` 代理 → 经 :80 访问 `/api/*` 一律 404，而后端（FastAPI `:8483`）正常。
  → 部署时**宿主端口直接映射后端 `:8483`**，绕开 nginx（引擎只用 `/api/*`，不需要 web UI）。
- **`TRANSCRIBER_TYPE` 环境变量在该镜像里不可靠透传**（supervisord env 坑 + BN 把转写器配置 seed 进
  持久化 SQLite）→ 用 `POST /api/transcriber_config {"transcriber_type":"bcut"}` **显式**设。
- **bcut 本身无需任何 cookie**；BN 的 yt-dlp 下公开视频音频也无需 cookie（会员/付费才需，经
  `POST /api/update_downloader_cookie` 推）。
- **LLM 供应商走 `POST /api/add_provider`**（BN 后端是 OpenAI-compatible，任何兼容端点皆可；API 创建的
  `type` 被强制 `custom`，`name` 须唯一）；读回 `provider_id` 经 `GET /api/get_all_providers`，填进
  `Engine/bilibili/config/bilibili-engine.yaml`（gitignored，不含 key——key 在 BN 的 SQLite）。
- **BN 无鉴权** → 端口只绑 `127.0.0.1`，公网经 SSH tunnel / frp，勿裸暴露。
- 响应包装 `{code,msg,data}`（`code==0` 成功）；提交→轮询 `GET /api/task_status/{id}`（终态 SUCCESS/FAILED）。
- **任何与 BN 通信的进程，运行/部署须清 `ALL_PROXY`/`HTTP(S)_PROXY`**：否则 httpx 经 `trust_env` 继承宿主
  SOCKS 代理 → 连本地 BN 也抛 `socksio` ImportError（构造期即炸，与目标是否 localhost 无关）。或装
  `httpx[socks]` + `NO_PROXY=127.0.0.1,localhost`。SP-5b/SP-4b/docker 部署共担。根因 = 引擎 BN 客户端
  （`BiliNoteClient`）建 httpx.Client 未传 `trust_env=False` → 属 **SP-4a 引擎候选修复**（已由 SubOrche 升级 root；
  机制在代码、不在此提升，但部署规则 + 修复指针提升）。勿当永久 workaround。
- **BN 的 yt-dlp 取 bilibili 元数据可能被风控持续 `HTTP 412`**（已知 hazard）→ 转写整体失败；**推 cookie
  （`POST /api/update_downloader_cookie`）实测不解**（2026-06-10）。修法在 BN/ops 侧：升级 BN 的 yt-dlp / 换出口 IP /
  补 wbi+反检测 headers。监听/Skill 类消费者优雅降级（不入水位、下轮自动重试）。**当前实际中断状态见 UN-035**
  （勿用 persist 记运行态）。架构注：412 在 BN 的 yt-dlp、**位于引擎请求路径之下**——引擎自身 `bilibili-api-python`
  调用是 200，**引擎侧限流/反风控不解此问题**；反风控若要做属**引擎层**（勿在 SP-4b/SP-5b 重复，类比 SP-2 v1.2
  硬化的是引擎 `_request` 非消费者），是 **SP-4a v1.x（root 主、引擎冻结）**，且也只硬化引擎调用、非 BN 下载器。

## B站收藏夹 API（SP-5b Watcher 首爬，真站实证 2026-06-10；下游收藏夹消费者必看）

监听/抓取收藏夹的下游（SP-5b 及未来）按此集成；分层读协议下别的 cwd 读不到 SP-5b 模块 `decisions.md`，故提升于此。

- 端点 `GET api.bilibili.com/x/v3/fav/resource/list?media_id={夹id}&pn=&ps=20&order=mtime&type=0&platform=web`；
  夹列表 `GET /x/v3/fav/folder/created/list-all?up_mid={mid}`。**纯 cookie（SESSDATA）+ 浏览器 headers，无签名**；
  响应 `{code,message,ttl,data}`（`code==0`；`-101`=未登录/cookie 过期）。陆站**直连**（`trust_env=False`，勿走境外代理）。
- ⭐ **每条收藏项带 `fav_time`=收藏时刻，≠视频 `pubtime`/`ctime`（发布时间）**（铁证：同条 fav 2026-04-24 vs
  pub 2026-04-16，差 8 天）。喂引擎用 `bvid`；`type==2`=普通 UGC 视频（音频/番剧/合集 type≠2，引擎不支持 → 过滤）。
- ⭐ **`order=mtime` ⇒ `data.medias[]` 按 `fav_time` 倒序**（最新收藏在前）⇒ 可早停（遇 `fav_time<=水位` 即停本夹）。
- ⚠️ **分页 = `pn`/`ps` 页码 + `data.has_more` 停止；绝不能用 `data.info.media_count` 自算停止**——失效/删除视频
  计入 `media_count` 却不在 `medias[]` 返回（实测夹 count=4 仅返 3）。这是 §知乎链路「勿从 totals 早停」的 B站翻版。
- 这条 `fav_time` 实证**正面闭环了 SP-5a 当年的臆断**（SP-5a 凭记忆判"无可靠收藏时间"→ 错走 seen-id；B站实证有
  `fav_time`）。durable 教训见 `memory/empirical-api-first.md`：**爬取类 API 的字段/分页语义先真站实证 + 落文档待
  user review，勿凭记忆或参考库代码臆断**。

## 总数据流

```
                ┌──────────────────────┐
   user URL ──► │  router (by domain)  │ ──► zhihu_fetch  ──► save_local
                └────────┬─────────────┘
                         │
                         ▼
                  bilibili_pipeline
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
  get cid (bilibili-api-python)
        │
   try official / AI subtitle ──── hit ───► transcript (source=subtitle)
        │ miss
        ▼
   yt-dlp -x m4a (audio only, 10–30 MB / 30min)
        │
        ▼
   oss_upload  ─────────► signed URL (1h TTL)
        │
        ▼
   Tingwu async file transcription
   (summarization=true, chapters=true, pptExtraction=true)
        │
        ▼
   poll task → download result → transcript + summary + chapters + keyframes
        │
        ▼
   save_local → output/bilibili_BVxx.{md,json}
```

## 为什么是这种形状

### 关键约束（来自本机 + 用户偏好）

| 约束 | 影响 |
|---|---|
| 本机 GPU = GTX 860M (2GB, 2014) + NVML 驱动版本不匹配 | 本地 ASR 大模型不可用 |
| 本机 RAM = 7.6 GB（free 仅 4.8 GB） | 本地 ASR 仅能跑 SenseVoice-Small / Whisper-tiny |
| 用户明确反对"先下载视频" | 只能抽音频，不能整片下载 |
| 用户当前流程参考 "parsevideo → 听悟" | 但 parsevideo 是网页解析站，不能 API；听悟拒绝 bilibili 域名 |

### 三个关键决策

1. **抽音频 + 上 OSS + 喂听悟**，而不是 "B 站直链塞听悟"
   通义听悟官方明确不接受 bilibili.com 域名（防盗链 + ToS）。即便 parsevideo 临时签名 URL 暂时能跑，随时失效。本地 `yt-dlp -x` 只抽音轨，30 min 视频约 10–30 MB，比下载整片节省 10× 带宽和磁盘。

2. **字幕优先于 ASR**
   B 站约 30%+ 视频已有 CC 字幕或 AI 字幕（需 SESSDATA cookie）。直接拿字幕零成本、零延迟、零误差。`bilibili-api-python.get_subtitle(cid)` 一行搞定。

3. **听悟作为默认 ASR（而非纯 Paraformer）**
   听悟新版 API 是市面**唯一原生输出"ASR + 章节摘要 + 关键帧 PPT 抽取"**的中文 API（2026-05）。30 min 视频估价约 ¥0.72，比百炼 Paraformer + 自接总结 + 自截关键帧的总成本低且少 3 个串联失败点。

### Fallback 链

```
Tingwu (default)
  ↓ fail (network / quota / file format)
Paraformer-v2 on DashScope (pure ASR)
  ↓ fail
SenseVoice-Small local (only if RAM check passes)
  ↓ fail
return {"error": ..., "fallback_used": [...]}
```

### 知乎链路（SP-2 实现，2026-06-02 落地）

实现 = **纯 cookie + HTTP（无浏览器、无 zse-96 签名器）**。机制细节见代码 +
`Engine/zhihu/docs/{interface.md, RepoMem/decisions.md D1–D5}`。此处仅记**非代码可推导、
SP-5a Watcher 复用必知**的根因/坑（分层读协议下 SP-5a 在 `Service/crawl/zhihu-watcher/` cwd
不会读到 `Engine/zhihu` 的模块记忆，故提升于此）：

- **旧「Playwright CDP `Chrome:9222` → Jina Reader」推测链：未采用、已废弃。** 实测知乎页面
  导航 GET 内嵌 `js-initialData`（服务端渲染）即够，无需浏览器、无需 Jina 转发。
- **`comment_v5` 的 `offset` 是毒**：带 `offset` 请求返回空 `data` + 自引用 `paging.next`
  → 死循环。必须**游标分页**（首调只带 `order_by`+`limit`，跟 `paging.next` 到 `is_end`）。
  勿"简化"回 offset。
- **子评论端点 `child_comment` 反而是 offset 模型**（v1.1 实测，区别于 `root_comment` 的游标）：
  `/api/v4/comment_v5/comment/{root_id}/child_comment` 的 `paging.next` 内嵌 `offset=`。**但仍跟
  `paging.next` 逐字翻页**（勿自构 offset）—— 对游标 / offset 两种模型都对，且免疫上面那条 offset 毒药。
  两个坑：①root 响应的 `child_comment_next_offset` **可能是 `None` 即便该 root 有几十条子评论**（且内联
  预览为空）→ 判定"是否要拉完整子树"必须看 `child_comment_count > len(内联预览)`，**别**信
  `child_comment_next_offset`；②child 端点同样**无需 `x-zse-96`**（纯 cookie 200，D5 延伸到子端点）。
- **`js-initialData`=camelCase（`voteupCount`/`createdTime`…），`/api/v4`=snake_case**：
  同一实体两套键名，解析需双向兜底（`first(raw, camel, snake)`）。
- **`comment_v5` 无需 `x-zse-96`**（2026-06 实测确认，非假设）；若未来 403 再引 RSSHub
  MIT 签名器（MediaCrawler 的禁商用、勿 vendor）。
- **知乎直连**（`trust_env=False`）：宿主有 `HTTP_PROXY`/`ALL_PROXY`（给境外站），知乎是
  陆站直连即达，走境外代理慢且招风控。
- cookie 注入式（`d_c0`/`z_c0`/`__zse_ck`），来源 = SP-1 cookie-manager。
- **收藏夹端点同样无需 `x-zse-96`**（SP-5a Watcher **2026-06-07 真站确认**,168 条/9 页）：
  `GET /api/v4/collections/{id}/items?offset=&limit=20` 纯 cookie + 浏览器 headers 即 200,**offset 翻页**
  ——停止条件用 `paging.is_end` 或 `len(已收集) >= paging.totals`,**勿用 `offset >= totals`**(API 把少于
  `totals` 的条目分散到多页 + `is_end` 迟到时会早停漏条)。用户收藏夹列表
  `GET /api/v4/people/{url_token}/collections?...&offset=&limit=20` 同属导航端点、同样纯 cookie(每个收藏夹对象带
  `is_default`——仅默认夹「我的收藏」为 true——+ `item_count`);`GET /api/v4/me` 亦无签名,把 `url_token: me`
  解析成当前 cookie 用户 token(SP-5a v1.1 真站确认)。
- **收藏夹条目的「收藏时间」= 顶层 `created`,非 `content.created`**(SP-5a v1.1 **2026-06-10 真站确认**,纠正 v1 误判):
  每条 `data[]` 有**顶层 `created`**(ISO8601,如 `2026-05-23T09:00:04+08:00`)= 加入收藏夹时间;`content.created`/
  `content.created_time` 是内容**发布**时间(≠ 收藏时间)。**且条目不按收藏时间排序**(实测:某夹 item[0] 收藏于
  2025-08、item[1..2] 于 2026-05)→ 可按 `created` **过滤**(只收某时间后),**不可据此早停翻页**(同「勿
  `offset >= totals` 早停」之理,会漏掉排在旧条目后的新条目);去重仍用 seen-id。
- **收藏夹抓正文的坑(SP-5a 真站)**:列表给的内容 URL,**答案页导航 GET 常 403**,但 SP-2 引擎的
  **api-fallback(仅 ANSWER + 403 → `/api/v4/answers/{id}`,无签名)** 能救回;**专栏 ARTICLE
  (`zhuanlan.zhihu.com/p/...`)无此兜底 → 403 即抓不到**(实测 168 条:140 答案救回、28 专栏失败)。
  监听类下游:失败项不入水位会每轮重试 → 考虑失败计数/退避(v1+)。
- **导航页 HTML 有 `__zse_ck` 时效门**(SP-2 v1.2 真站 **2026-06-10** 确认,**修正上文「导航页 200 即够、无需签名」的乐观表述**):
  `www.zhihu.com/...` 与 `zhuanlan.zhihu.com/p/...` 的导航 GET 需**新鲜 `__zse_ck`**;过期/缺失 → 403 返回**反爬挑战页**
  (body 含 `<meta id="zh-zse-ck">` + `zse_ck` JS tracker,非正文)。新鲜 `__zse_ck`(浏览器算、cookie-manager 同步)时
  透明通过——故 06-07/09 探测 nav 全 200(当时 cookie 新鲜)。**重试/退避救不了过期**(每次重试还是挑战页),只有新鲜
  `__zse_ck` 能。→ 监听类下游长期跑须**定期从浏览器同步新鲜 cookie**;根治需 `__zse_ck` 求解器(破 D1,root 决策,未做)。
- **cookie domain-key = `.zhihu.com`(带点)**:cookie-manager 存的知乎 cookie 在**带点** key 下(`zhihu.com` 无点 key 已空)。
  所有消费者(SP-3/SP-5a)`show domain=` 必须用 `.zhihu.com`(与 B 站「无点/带点」坑同源)。
- **`/api/v4/articles/{id}` 需 `x-zse-96` 签名**(403 `code 10003`,任何 `include=`),与无签名的 `/api/v4/answers/{id}`(上文)
  **不对称** → **无对应的无签名 article api-fallback 可镜像**,故 SP-2 v1.2 未加、亦未引签名器(守 D1);
  `api.zhihu.com/articles/{id}` → 403 `code 40362`(风控)。
- **知乎风控=突发/并发敏感型**(非累计;60 连续 nav-GET @~2req/s 零限流)→ SP-2 引擎已**内置主动限流(请求间最小间隔+
  抖动,进程共享)+ 403/429 退避(遵从 `Retry-After`)**,4 处出站请求全走 `fetcher._request`,批量消费者自动受益、单 URL
  几乎无感;入口 `zhihu.configure(...)`(机制在代码,见 `Engine/zhihu/docs/interface.md §11`)。**注:此层治突发限流,非
  `__zse_ck` 门(正交)**。

## 模块边界

| 模块 | 职责 | 不做什么 |
|---|---|---|
| `zhihu_fetch` | 拿到知乎单页正文 markdown | 不做总结、不做翻译 |
| `bilibili_pipeline` | 视频 → 转写 / 摘要 / 关键帧 | 不做下载整片、不做剪辑 |
| `oss_upload` | 把本地小文件推到 OSS，返回签名 URL | 不做长期存储管理 |
| `tingwu_transcribe` | 听悟提交 + 轮询 + 结果解析 | 不做格式转换（交给 save_local） |
| `save_local` | 落 markdown + json | 不做云同步、不做去重 |

每个模块**独立可测、独立失败**，上层 pipeline 负责编排和降级。

## 与上层 agent 的关系

JarvanKB 是**纯工具集合**，不假设调用方是谁。Hermes、Claude Code、自写脚本都可以使用。

**调用方 agent 的入口是 `../../../sendbox/toAgent/handoff.md`**（仓库根下 `docs/sendbox/toAgent/`，sendbox-protocol 单收件人信件，`lifecycle: persist`）——该信件描述：
- 何时该用本工具（触发条件）
- 各脚本的输入/输出契约
- 调用前的凭据自检流程
- 失败时的降级策略

底层调用形式（CLI / import / subprocess）由具体脚本自身决定，`handoff.md` 给出权威说明。
