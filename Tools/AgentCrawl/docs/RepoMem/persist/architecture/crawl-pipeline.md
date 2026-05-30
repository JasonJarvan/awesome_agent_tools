# Architecture

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

知乎链路的 fallback：

```
Playwright CDP (本机已登录 Chrome:9222)
  ↓ fail (CDP unreachable / login expired)
Jina Reader (r.jina.ai, 转发 d_c0/z_c0 cookie)
  ↓ fail
return {"error": ..., "fallback_used": [...]}
```

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

AgentCrawl 是**纯工具集合**，不假设调用方是谁。Hermes、Claude Code、自写脚本都可以使用。

**调用方 agent 的入口是 `../../../sendbox/toAgent/handoff.md`**（仓库根下 `docs/sendbox/toAgent/`，sendbox-protocol 单收件人信件，`lifecycle: persist`）——该信件描述：
- 何时该用本工具（触发条件）
- 各脚本的输入/输出契约
- 调用前的凭据自检流程
- 失败时的降级策略

底层调用形式（CLI / import / subprocess）由具体脚本自身决定，`handoff.md` 给出权威说明。
