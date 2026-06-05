# zhihu-crawl — SP-3 知乎技能

> **状态：已实现（v1，SP-3 交付，2026-06-05）**
> 类型：skill | 包名：`zhihu-crawl`（`pip install -e Skill/crawl/zhihu-crawl`）

## 这个技能做什么

给定一个知乎 URL（回答 / 专栏文章 / 问题），通过冻结的 SP-2 引擎抓取内容并保存为 Markdown 文件到用户指定路径。当路径"模糊"（传入目录、`output_root`、或省略 `--out`）时，使用 `LLMClient` 将内容分类到 `output_root` 下合适的子文件夹。

## 快速使用

```bash
# 安装（需提前安装 Engine/common 和 Engine/zhihu）
pip install -e Engine/common -e Engine/zhihu -e Skill/crawl/zhihu-crawl

# 配置
cp Skill/crawl/zhihu-crawl/config.example.yaml Skill/crawl/zhihu-crawl/config.yaml
# 编辑 config.yaml：设置 output_root、cookie 服务地址和 password_env

# 运行
zhihu-crawl "https://www.zhihu.com/question/123456/answer/789012"
zhihu-crawl "https://www.zhihu.com/question/123456/answer/789012" --out ~/KB/tech/note.md --json
```

## 文档索引

| 文档 | 内容 |
|---|---|
| [`docs/interface.md`](interface.md) | **公开接口合约（冻结）**：`save_zhihu()` 签名、`SaveResult` 字段、CLI 参数、支持的 URL 形式 |
| [`docs/architecture.md`](architecture.md) | 架构概览：模块结构、数据流、跨 SP 边界 |
| [`SKILL.md`](../SKILL.md) | agentskills.io 描述符：Claude Code / Codex / OpenClaw / Hermes 均可识别 |
| [`config.example.yaml`](../config.example.yaml) | 配置文件模板 |
| [`docs/superpowers/specs/2026-06-02-SP-3-zhihu-skill-design.md`](superpowers/specs/2026-06-02-SP-3-zhihu-skill-design.md) | SP-3 设计文档（brainstorming 输出，架构决策的权威来源） |
| [`docs/RepoMem/architecture.md`](RepoMem/architecture.md) | 内部架构（A2A 英文，模块级 RepoMem） |

## 依赖

- `Engine/zhihu`（SP-2 冻结引擎）— 纯消费者关系
- `Engine/common`（`jarvankb-common`）— `LLMClient`（litellm 后端，SP-3 实现并冻结）
- SP-1 Cookie 管理器 — HTTP 主动拉取，客户端解密（`legacy` + `aes-128-cbc-fixed`）

## 部署 SKILL.md 到运行时

```bash
bash Skill/crawl/zhihu-crawl/scripts/sync-skill.sh
```

将 `SKILL.md` 通过符号链接部署到 `~/.claude/skills/`、`~/.codex/skills/`、`~/.openclaw/skills/`、`~/.hermes/skills/`。
