# Pre-OpenSpec Decisions — 2026-05 调研结论存档（**FROZEN LEGACY**）

> ⚠️ **本文件是 pre-OpenSpec 时期的决策遗存。已冻结，不再追加。**
> 从 HarnessStack effective 日开始，所有新决策走 OpenSpec change 归档（`docs/openspec/changes/<change-id>/`）。
> D1–D7 不追溯转 OpenSpec change（避免历史包袱），保留在此处作为背景资料。
> `RepoMem.merge` 不会把本文件视为 memory candidate。

---

本文件锁定阶段一所有关键选型的**当时理由**，防止半年后维护者重新讨论已经决过的问题。
每条决策标注：上下文 / 选项对比 / 最终选择 / 何时该重新评估。

---

## D1：知乎正文采集主路径 = Playwright CDP + 已登录 Chrome

**上下文**：知乎 2024–2025 多次升级 `x-zse-96 / x-zse-93 / x-zst-81` 签名，纯 `requests` + JS 逆向脚本寿命短；未登录直接被重定向到登录墙。

**选项**：
| 方案 | 评价 |
|---|---|
| MediaCrawler/zhihu 模块（fork） | ★★★ Playwright 注入浏览器签名函数，最稳；50k★ 活跃维护 |
| ★ Playwright CDP 复用本机 Chrome | ★★★ 与 MediaCrawler 同思路但更轻；天然继承用户登录态 |
| Jina Reader / Firecrawl / Crawl4AI | ★★ 知乎登录墙下命中率低，做兜底可以，做主路径不行 |
| syaning/zhihuapi-py | ✗ 已停更 ~2018，签名失效 |
| 纯 requests + x-zse-96 逆向 | ✗ 寿命短，每次升级要重写 |

**选择**：CDP 模式为主，Jina Reader 为兜底。

**何时重审**：
- 知乎大改前端渲染（SSR 改成 CSR 或反之）
- 出现稳定的 SaaS API 替代品

---

## D2：B 站视频获取 = bilibili-api-python + yt-dlp 抽音

**上下文**：用户原话提"parsevideo 提取链接"。调研发现 `parsevideo.com` 是个人维护的网页解析站，不可程序化调用。

**选项**（音/字幕能力综合）：yutto ≈ BBDown > bilibili-api-python > bilix > yt-dlp(需 curl-cffi) > you-get/lux(半停滞)

**选择**：
- 元数据 + 字幕 = **bilibili-api-python v17.4.1**（2025-12 更新，封装 wbi/buvid3）
- 抽音轨 = **yt-dlp -f bestaudio -x --audio-format m4a**（生态最大，CLI 集成简单）
- 备选：yutto 在 CLI 体验更好，但 Python import 不如 bilibili-api-python 干净

**何时重审**：bilibili-api-python 停更 / B 站签名再次大改 / Yutto 出 Python SDK

---

## D3：ASR 主路径 = 阿里通义听悟新版 API

**上下文**：用户当前流程参考"parsevideo → 通义听悟"，且明确要求"URL 直传，不下载整片"。本机硬件（GTX 860M 2GB + 7.6 GB RAM）跑不动本地大模型 ASR。

**选项对比**（2025–2026 报价，引自子 agent 调研）：
| 服务 | 30 min 估价 | 一站式（含摘要+关键帧） | 中文表现 |
|---|---|---|---|
| ★ **通义听悟** | **¥0.72** | ★★★ 唯一原生输出关键帧 | ★★★（与 Paraformer 同源） |
| 百炼 Qwen3-ASR-Flash | ¥0.45 | ✗（需自接 Qwen3 总结，自截关键帧） | ★★★ |
| 百炼 Paraformer-v2 | ¥0.20–0.30 | ✗ | ★★★ |
| 科大讯飞 lfasr | ¥1.75–4.95 | ✗ | ★★★ |
| 腾讯云 ASR | ¥0.50–0.75 | ✗ | ★★ |
| 火山豆包 ASR | ¥0.34–1.0 | ✗ | ★★★ |
| OpenAI Whisper API | ¥1.3 | ✗ | ★（中文 WER 12–15%） |
| Groq Whisper-turbo | ¥0.15 | ✗ | ★（同 Whisper） |

**选择**：
- 默认：**通义听悟新版 API**（最贴近用户现有流程 + 唯一一站式）
- 兜底 1：**百炼 Paraformer-v2**（同源精度，纯 ASR 更便宜，需自接 Qwen3 总结）
- 兜底 2（本地）：**SenseVoice-Small ONNX int8**（830 MB，CPU 可跑，30 min 视频 3–5 min）

**关键修正**：听悟**官方拒绝 bilibili.com 域名直链**。"parsevideo 给的 B 站直链" 之所以能跑，是因为该签名 URL 暂未带 Referer 防盗链，**不稳定，随时失效**。正经做法 = 本地 yt-dlp 抽 m4a → OSS → 给听悟 OSS URL。

**何时重审**：
- 听悟改价或停服
- Qwen3-ASR-Flash 上线"附带摘要+关键帧"参数
- 出现支持 bilibili 直链的合规中文 ASR

---

## D4：不本地下载整片视频 = 仅抽 m4a 音轨

**上下文**：用户明确反对"先下载视频再转录"。本机磁盘 370G 充裕但 RAM 紧；带宽与隐私角度也偏好"只传必需"。

**选择**：`yt-dlp -f bestaudio -x --audio-format m4a`，30 min 视频音轨约 10–30 MB（vs 完整视频 200–2000 MB）。

**何时重审**：用户后续需求扩展到"提取关键帧时也需要本地视频"（当前由听悟服务端做，所以不需要）

---

## D5：形态 = 工具集合（system），不是 skill / agent

**上下文**：用户明确"AgentCrawl 现阶段是 crawl 和 cookie 管理工具的集合，不是 skill"。

**含义**：
- 不写 SKILL.md / AGENTS.md（无 frontmatter、无触发规则、无 agent 指令）
- 没有"何时调用我"的元描述——由上层 agent 自行判断
- 每个 `scripts/*.py` 是自包含的 CLI / 可 import 模块，I/O 契约写在文件自己的 docstring 里
- cookie/凭据管理 与 爬取脚本 是并列的两类工具，不是某个 skill 的内部细节

**何时重审**：当多个 agent 反复需要相同的"何时调用"判断，再考虑包一层 skill / MCP server 复用判断逻辑。

---

## D6：归属 = `Tools/AgentCrawl/`，不是 Hermes 源码内子目录

**上下文**：Hermes Agent 是 tarball 解压 + pip 安装（v0.14.0, 非 git clone），改其源码会被 `hermes update` 覆盖。

**选择**：放在 `awesome_agent_tools/Tools/AgentCrawl/` 下独立维护。Hermes / 其他 agent 通过 CLI / import / subprocess 调用。

---

## D7：阶段一只产文档，不写代码

**用户明确决定**。契约先行：
- 第一步：用 README + docs 把"做什么、为什么这么设计、凭据怎么配"写清
- 第二步：照设计填实现

阶段一交付物 = 4 个文件：README、architecture、runbook、decisions。

---

## 信息溯源（关键链接）

- Tingwu 计费：https://help.aliyun.com/zh/tingwu/pricing-and-billing-rules
- Tingwu 不支持 bilibili 域名（FAQ）：https://help.aliyun.com/zh/tingwu/ai-model-capability
- Qwen3-ASR：https://github.com/QwenLM/Qwen3-ASR
- bilibili-api-python：https://pypi.org/project/bilibili-api-python
- MediaCrawler：https://github.com/NanmiCoder/MediaCrawler
- Cansiny0320/bilibili-video-summary-agent（参考实现）：https://github.com/Cansiny0320/bilibili-video-summary-agent
- SenseVoice：https://github.com/FunAudioLLM/SenseVoice
- 听悟 vs Paraformer / 价格表 完整出处见上一轮 ASR 调研 subagent 的引用列表（任务 ID a765613376a8a2793）
