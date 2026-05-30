# AgentCrawl

> 一套**爬取工具 + cookie/凭据管理工具**的集合，面向需要采集知乎正文与 B 站视频（转写 + 总结 + 关键帧）的 agent 系统（如 Hermes Agent）使用。
> 输入：知乎 URL / B 站 BV 号。输出：本地 markdown + json，含正文 / ASR 转写 / 摘要 / （视频）关键帧。

## 定位

AgentCrawl **不是 agent，也不是 skill**——它是一组可被 agent 编排调用的独立工具（Python 脚本 / CLI），加上配套的 cookie / token 管理逻辑。

- 不绑定 Hermes：纯 Python 工具，任何 agent / 脚本都能调
- 不内嵌总结策略：转写/摘要由所选 ASR 服务（默认通义听悟）直接产出，AgentCrawl 只负责"把内容拿到 + 落盘"
- 不做 prompt 工程：上层 agent 决定怎么用这些素材

**调用方 agent 的入口 = `docs/sendbox/toAgent/handoff.md`**——稳定契约，`lifecycle: persist`。任何 caller agent 在调用脚本前先读它。

## 设计目标

1. **不下载整片视频**：B 站只抽音频（m4a，10–30 MB / 30 min），上传 OSS 后交给云端 ASR
2. **线上 ASR 默认，本地仅兜底**：本机 GTX 860M / 7.6 GB RAM，本地大模型 ASR 不实用
3. **凭据集中管理**：B 站 SESSDATA、知乎 d_c0/z_c0、阿里云 AK/SK、Jina key 等统一在 `.env`，并提供 cookie 失效检测/刷新工具

## 现状（阶段一）

只有**目录骨架 + 设计文档**。代码尚未实现。

```
Tools/AgentCrawl/
├── README.md                                   # 本文件（人类入口）
├── CLAUDE.md                                   # AI agent 始终加载的运行契约（蒸馏自 HarnessStack §1–4）
└── docs/
    ├── HarnessStack/                           # 项目自身的工作契约
    │   ├── README.md
    │   ├── longterm.md
    │   └── _toUser/                            # 用户手册
    ├── RepoMem/                                # 长期/临时仓库记忆
    │   ├── README.md
    │   ├── persist/
    │   │   ├── config.md                       # 语言 / frontmatter 策略
    │   │   ├── version-plan.md                 # 版本与路线
    │   │   ├── architecture/
    │   │   │   ├── index.md                    # 域地图
    │   │   │   └── crawl-pipeline.md           # 现唯一活跃域
    │   │   └── memory/
    │   │       ├── index.md
    │   │       ├── runbook.md                  # 凭据配置 / OSS / 故障表
    │   │       └── pre-openspec-decisions.md   # FROZEN：D1–D7 遗存
    │   └── temp/<slug>/                        # 任务级临时记忆
    └── sendbox/                                # sendbox-protocol 信件树
        └── toAgent/
            └── handoff.md                      # 调用方 agent 的入口契约（persist 终身）
```

> OpenSpec workspace 已就位：物理目录 `docs/openspec/`，根目录 `openspec` 是指向它的符号链接（让 CLI 从仓库根可发现）。
> slash 命令 `.claude/commands/opsx/*` + skills `.claude/skills/openspec-*`（重启 IDE 后加载）。

阶段二会补：

```
├── scripts/
│   ├── zhihu_fetch.py          # Playwright CDP → markdown
│   ├── bilibili_audio.py       # bilibili-api-python + yt-dlp 抽 m4a
│   ├── oss_upload.py           # 签名 URL，24h TTL
│   ├── tingwu_transcribe.py    # 通义听悟新版 API（异步 + 轮询）
│   └── save_local.py
├── cookies/
│   ├── manager.py              # 读写/校验/过期检测
│   └── refresh_chrome_cdp.py   # 从本机已登录 Chrome 同步 cookie
├── cli.py                      # python -m agentcrawl ...
├── requirements.txt
└── .env.example
```

## 快速判断要读哪份文档

| 目的 | 文档 |
|---|---|
| 决定要不要用 / 它能做什么 | 本 README |
| AI agent 在本项目内工作（始终加载的契约） | `CLAUDE.md` + `docs/HarnessStack/` |
| 调用方 agent 想知道**如何使用 AgentCrawl** | `docs/sendbox/toAgent/handoff.md` |
| 想知道数据怎么流转 / 为什么这么设计 | `docs/RepoMem/persist/architecture/crawl-pipeline.md` |
| 配 cookie / OSS / 排查故障 / 估成本 | `docs/RepoMem/persist/memory/runbook.md` |
| 想知道"为什么选听悟而不是 X"（历史 D1–D7） | `docs/RepoMem/persist/memory/pre-openspec-decisions.md` |
| 未来每次决策为何这么定 | `docs/openspec/changes/<change-id>/`（待 OpenSpec 落地） |
| 版本 / 路线 | `docs/RepoMem/persist/version-plan.md` |

## 上下文

- 所属仓库：`awesome_agent_tools`（AI 工具聚合，见根目录 `AGENT.md`）
- 主要消费者：Hermes Agent v0.14.0（pip 安装，非 git clone）；其他 agent 也可调
- pre-OpenSpec 调研结论（D1–D7）冻结在 `docs/RepoMem/persist/memory/pre-openspec-decisions.md`，新决策走 OpenSpec change
