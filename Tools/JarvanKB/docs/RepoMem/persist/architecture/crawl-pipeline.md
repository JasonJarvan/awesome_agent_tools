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
  `GET /api/v4/people/{url_token}/collections?...&offset=&limit=20` 同属导航端点、同样纯 cookie。
- **收藏夹抓正文的坑(SP-5a 真站)**:列表给的内容 URL,**答案页导航 GET 常 403**,但 SP-2 引擎的
  **api-fallback(仅 ANSWER + 403 → `/api/v4/answers/{id}`,无签名)** 能救回;**专栏 ARTICLE
  (`zhuanlan.zhihu.com/p/...`)无此兜底 → 403 即抓不到**(实测 168 条:140 答案救回、28 专栏失败)。
  监听类下游:失败项不入水位会每轮重试 → 考虑失败计数/退避(v1+)。

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
