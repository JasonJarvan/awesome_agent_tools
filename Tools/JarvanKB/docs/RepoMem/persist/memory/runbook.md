# Runbook — 环境配置 + 故障恢复

> Note: a `§0 OpenSpec workspace` section existed here in v1; OpenSpec was removed in recipe v2. See `docs/HarnessStack/longterm.md §Recipe v1→v2 Migration`.

## 1. 环境变量清单

复制 `.env.example` 到 `.env`（**不要提交**），填入：

| 变量 | 必需? | 用途 | 获取 |
|---|---|---|---|
| `ALIBABA_TINGWU_AK` | ★ | 通义听悟新版 API AccessKey ID | 阿里云控制台 → AccessKey 管理 |
| `ALIBABA_TINGWU_SK` | ★ | 通义听悟新版 API AccessKey Secret | 同上 |
| `OSS_ENDPOINT` | ★ | OSS 区域端点，例：`oss-cn-shanghai.aliyuncs.com` | OSS 控制台 → 概览 |
| `OSS_BUCKET` | ★ | 用于上传音轨的 Bucket 名 | OSS 控制台 → 创建 Bucket |
| `OSS_ACCESS_KEY_ID` | ★ | OSS AK（可与听悟 AK 同一对） | 同上 |
| `OSS_ACCESS_KEY_SECRET` | ★ | OSS SK | 同上 |
| `DASHSCOPE_API_KEY` | ◎ | 百炼 Paraformer-v2 兜底 / Qwen3 总结 | 百炼控制台 → API-KEY |
| `BILIBILI_SESSDATA` | ◎ | 拿高清音频 / AI 字幕 | 浏览器登录 bilibili 后从 cookie 复制 |
| `ZHIHU_COOKIE` | ◎ | 知乎 Jina fallback 用，含 `d_c0`、`z_c0` | 浏览器 devtools 复制完整 cookie 串 |
| `JINA_API_KEY` | ○ | Jina Reader 提速 + 提配额（免费 20 RPM） | jina.ai → API key |

★ = Tingwu 主路径必需；◎ = 强烈建议；○ = 可选。

## 2. 凭据获取要点

### 通义听悟（新版 API）
- 新版 API 走的是阿里云 AK/SK 签名（不是 DashScope key）
- 控制台路径：阿里云首页 → 智能语音交互 → 听悟 → API 文档
- 计费：按音频时长，ASR ¥0.6/h + 章节速览 / 摘要 / PPT 抽取各 ¥0.064–0.64/h
- **首次开通**需要在听悟控制台开通服务

### OSS Bucket 设置建议
- 区域：与听悟同区域（一般上海 `oss-cn-shanghai`）
- 读写权限：私有
- 生命周期：建议给 `agent-crawl/` 前缀设置 **24h 自动删除**（音轨是临时产物）
- 防盗链：留空（听悟服务端拉流）

### B 站 SESSDATA
浏览器登录 bilibili → F12 → Application → Cookies → 复制 `SESSDATA` 值
注意 SESSDATA 有效期约半年，过期表现为：`get_subtitle()` 返回空、`yt-dlp` 拿不到高码音轨。

### 知乎 cookie
浏览器登录 zhihu → F12 → Network → 任一请求 → Headers → Cookie 整串复制
关键字段：`d_c0`、`z_c0`。失效表现为：被重定向到登录墙。

### 本机 Chrome CDP（知乎主路径）
启动一个带远程调试端口的 Chrome 实例（保留你日常的登录状态）：
```
google-chrome --remote-debugging-port=9222 --user-data-dir=$HOME/.config/google-chrome
```
脚本通过 `playwright.connect_over_cdp("http://127.0.0.1:9222")` 复用其 context。
**重要**：不要用这个实例做敏感操作，CDP 暴露的是已登录状态。

## 3. 常见故障

| 症状 | 可能原因 | 处理 |
|---|---|---|
| Tingwu 任务返回 `4xx ACCESS_DENIED` | AK/SK 没开通听悟服务 / Bucket 跨区域 | 控制台开通；OSS Bucket 与听悟同区 |
| Tingwu 任务卡 `RUNNING` 超 30min | 音频时长 > 6h 或文件 > 6GB | 切片上传，每段 ≤ 4h |
| `yt-dlp` 报 412 / 403 | B 站风控 | `pip install "yt-dlp[default,curl-cffi]"` 启用浏览器指纹 |
| `get_subtitle()` 返回 `[]` | SESSDATA 失效 / 视频无字幕 | 重取 SESSDATA；确认是否真的无字幕（站内播放器是否能开 CC） |
| 知乎页 Playwright 拿到空 HTML | CDP 端口不通 / 未登录 | 确认 `curl http://127.0.0.1:9222/json/version` 有返回；浏览器重登 |
| Jina Reader 返回部分内容 | 知乎登录墙 / Jina 限流 | 配 `ZHIHU_COOKIE` 并通过 `X-Set-Cookie` 转发；或申请 Jina key 提配额 |
| 本机 ASR OOM | RAM 不足 | 改用线上；或停掉浏览器/IDE 释放内存再重试 |

## 4. 成本估算速查

| 单次任务 | 估价 |
|---|---|
| 知乎单页 | ¥0（仅本机/Jina 配额） |
| B 站 30 min（有字幕） | ¥0 |
| B 站 30 min（走听悟 ASR + 摘要 + 关键帧） | **≈ ¥0.72** |
| B 站 30 min（走 Paraformer + Qwen 自接总结） | ≈ ¥0.45 + 几分钱 token |
| 本地 SenseVoice-Small 兜底 | ¥0，CPU 跑 30 min 视频约 3–5 分钟 |

## 5. 日志与产物路径

- 转写产物：`output/bilibili_{bvid}.{md,json}`、`output/zhihu_{id}.{md,json}`
- 中间音轨：`/tmp/agentcrawl/audio/{bvid}.m4a`（任务结束删除）
- 日志：`logs/agentcrawl-{YYYYMMDD}.log`（按天滚动）
- OSS 临时对象：`agent-crawl/{bvid}-{ts}.m4a`（24h 生命周期）
