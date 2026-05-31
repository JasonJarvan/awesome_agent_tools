# SP-0 — JarvanKB 仓库骨架与 HarnessStack v2 迁移

> **Status**: draft (awaiting user review)
> **Date**: 2026-05-31
> **Author**: orchestrator session (handoff inheritance from `bootstrap-orchestrator`)
> **Scope**: 仓库改名 AgentCrawl → JarvanKB；目录骨架；HarnessStack recipe v1→v2；LLMClient 共享层；v1.0 OSS 切分协议。

---

## 1. 背景与 scope 变化

原 `Tools/JarvanKB/` 仓库定位为"Zhihu + Bilibili 爬虫工具集合"，bootstrap 期已完成 HarnessStack v1 recipe `openspec-superpowers-repomem-sendbox-dashboard` 的脚手架（14 份 RepoMem 文档、CLAUDE.md 13 步 pipeline、OpenSpec 软链工作区、cc-dashboard 看板、sendbox 通道）。

本次重新规划把范围扩展为 **7 件套产品族 + 仓库治理升级**：

| # | 子项目 | 类别 |
|---|---|---|
| 1 | CookieManager 服务（带 WebUI 计划） | Service / crawl |
| 2 | Zhihu 爬取引擎 + Skill | Engine / Skill |
| 3 | Zhihu 收藏夹长期监听服务 | Service / crawl |
| 4 | Bilibili 转录引擎 + Skill | Engine / Skill |
| 5 | Bilibili 收藏夹监听服务 | Service / crawl |
| 6 | DocSaver / crawl-md-saver Skill（爬取-笔记整合包装层） | Skill / ingester |
| 7 | ThinoHelper / thino-ingester 服务（Obsidian Thino 块解析+整理） | Service / ingester |

scope 已超出 "crawler" 范畴，纳入 **Ingester（内容消化层）** 与未来的知识库整理工具。仓库改名势在必行。

---

## 2. 仓库改名

**目标名**：`JarvanKB`（个人品牌 Knowledge Base，OSS 释出时辨识度高）

**v1 阶段**：在本 session 完成 design.md 后，由用户另起 session 物理改名（保留 `AgentCrawl` 历史归档于 RepoMem version-plan）。

**v1.0 OSS release 阶段**：迁移到 **GitHub Organization**（名称待定，候选见未决项），按 §10 的 fractal 切分协议把子模块切出为独立 repo。

---

## 3. 目录骨架

```
JarvanKB/
├── docs/                                  # 全局文档层
│   ├── HarnessStack/                      # 治理（recipe / longterm / hooks / _toUser）
│   ├── RepoMem/persist/                   # 跨模块决策、全局架构
│   ├── sendbox/                           # 全局信件（共用，唯一）
│   ├── Dashboard/                         # 全局看板（共用，唯一）
│   └── superpowers/                       # brainstorming/plans 产出
│       ├── specs/                         # 跨模块 design.md
│       └── plans/                         # 跨模块 implementation plan
├── Engine/                                # 纯库（无 UI、无服务，可独立打包）
│   ├── common/                            # 跨引擎共享（LLMClient with litellm、BaseSkill、cookie reader）
│   │   └── docs/                          # 子模块 docs（见 §5 强制结构）
│   ├── zhihu/                             # SP-2  — MediaCrawler 包装 + cookie + zse-96
│   └── bilibili/                          # SP-4a — BN HTTP 客户端 + bilibili-api-python
├── Skill/                                 # 用户层 skill
│   ├── crawl/
│   │   ├── zhihu-crawl/                   # SP-3
│   │   └── bilibili-crawl/                # SP-4b
│   ├── ingester/
│   │   └── crawl-md-saver/                # SP-6
│   └── router/
│       └── README.md                      # SP-8 v1+ 占位（web-search router）
├── Service/                               # 长期常驻服务
│   ├── crawl/
│   │   ├── cookie-manager/                # SP-1 — fork CookieCloud + hook 机制
│   │   ├── zhihu-watcher/                 # SP-5a
│   │   └── bilibili-watcher/              # SP-5b
│   └── ingester/
│       └── thino-ingester/                # SP-7
├── .claude/                               # 项目级 Claude Code 配置
│   ├── skills/                            # 项目专属 skill 引用（不含 openspec-*，见 §6）
│   └── commands/                          # 项目专属命令（不含 opsx/，见 §6）
├── CLAUDE.md                              # v2 recipe 版本（见 §6）
└── README.md
```

**命名约定**：
- `Skill/crawl/<platform>-crawl/`：拉取型 skill
- `Skill/ingester/<name>/`：消化整合型 skill
- `Service/crawl/<platform>-watcher/`：长期监听服务
- `Service/ingester/<name>/`：消化层服务
- `Engine/<platform>/`：底层库，按平台扁平
- `Engine/common/`：跨引擎共享代码（**包含 LLMClient**，见 §8）

---

## 4. 分层契约（核心创新）

JarvanKB 采用 **monorepo + 分层关注分离**，区别于"每子仓库都复制全套基础设施"的完整 fractal。

| 物件 | 主仓库（全局） | 子模块（本地） | 备注 |
|---|---|---|---|
| sendbox | `<root>/docs/sendbox/` ✓ | — | CLAUDE.md "One sendbox per project" 硬不变量；侧 cwd subagent 写到这里（路径） |
| Dashboard | `<root>/docs/Dashboard/` ✓ | — | 用户视角统一；一封信→N 行的协议保留 |
| HarnessStack — recipe / longterm / _toUser / hooks | `<root>/docs/HarnessStack/` ✓ | — | 治理 recipe 不分模块 |
| HarnessStack — temporary | `<root>/docs/HarnessStack/temporary-<task>.md` | `<module>/docs/HarnessStack/temporary-<task>.md` | 任务级 recipe 补丁（如 Recipe Invariant Exception 声明）；任务完结即清理或 HITL merge 提升 |
| RepoMem | `<root>/docs/RepoMem/persist/` | `<module>/docs/RepoMem/` | **分层关注分离**（见下） |
| superpowers/specs/ + plans/ | `<root>/docs/superpowers/` | `<module>/docs/superpowers/` | 跟 RepoMem 同分层策略 |
| OpenSpec | — | — | **v2 移除**（见 §6） |

### 4.1 RepoMem 分层契约

**主仓库 `<root>/docs/RepoMem/persist/`**：
- 跨模块决策、全局架构、recipe-level 不变量、跨模块凭据
- 当前已存在的 14 份文档保留并提升到此层

**子模块 `<module>/docs/RepoMem/`**：
```
<module>/docs/RepoMem/
├── architecture.md      # 模块内部架构（区别于 docs/architecture.md 的"对外契约"）
├── decisions.md         # 决策日志（追加式，时间倒序）
└── temp/<change-id>/    # 任务级临时 docs（HITL merge 后清理）
```

**Read 协议**：subagent 在 `<module>/` cwd 启动 → `RepoMem.read` 顺序读两层：
1. 主仓库 `<root>/docs/RepoMem/persist/`（提供背景，优先级低）
2. 本模块 `<module>/docs/RepoMem/`（提供 actionable，优先级高）

**Merge 协议**：HITL 时如发现子模块 decision 应提升为全局，把 `<module>/docs/RepoMem/decisions.md` 的某条 promote 到 `<root>/docs/RepoMem/persist/memory/`，并在子模块 decisions.md 留 `[Promoted to global ↗]` 引用。

### 4.2 superpowers/ 分层契约

- 主仓库 `<root>/docs/superpowers/specs/`：跨模块 design（如本 SP-0、未来 SP-5a+5b 共享 watcher 框架的 design）
- 子模块 `<module>/docs/superpowers/specs/`：单模块 design（SP-1、SP-2 等大多数子项目）
- plans/ 同上策略

**superpowers skill 本身**（brainstorming/writing-plans/TDD 等可执行物）安装在 user 级 `~/.claude/skills/superpowers/`，**不属于项目**，全局加载。

---

## 5. 子模块 docs/ 强制结构

每个 `<module>/docs/` 必须包含以下文件（自包含，OSS 切分时直接成立）：

```
<module>/docs/
├── README.md                  # [必须] 1 屏内：做什么 + 输入 + 输出 + 怎么装
├── interface.md               # [必须] 对外契约：函数签名 / CLI 参数 / HTTP 端点
├── architecture.md            # [必须] 对外架构摘要（与内部 RepoMem/architecture.md 区分）
├── runbook.md                 # [可选] 部署/配置/凭据/常见故障；service 类必须
├── changelog.md               # [可选] release 后必填
├── HarnessStack/              # [按需] 任务级 recipe 补丁
├── RepoMem/                   # [必须] 见 §4.1
│   ├── architecture.md
│   ├── decisions.md
│   └── temp/
└── superpowers/               # [按需] 单模块 design / plan
    ├── specs/
    └── plans/
```

**核心要求**：模块拆出去 v1.0 时是独立 OSS repo，`docs/` 必须能脱离 monorepo 独立成立。

---

## 6. HarnessStack Recipe v1 → v2 迁移

### 6.1 决议

经 R8 调研评估，**完全移除 OpenSpec**。理由摘要：

1. JarvanKB v1 子项目 = 薄壳形态（fork、HTTP 客户端、library 包装），单 change 1–3 天，OpenSpec 卖点"长生命周期契约迭代史"产生不出来
2. OpenSpec 95% 功能与 Superpowers + RepoMem + sendbox 重叠；唯一净损失是 `specs/ + archive/` 契约史，但 thin layer 用不上
3. 业界 prior art 支持：Anthropic Superpowers 官方文档不提 OpenSpec；最深入的中文三栈对比建议"先双栈、瓶颈出现再加 OpenSpec"
4. 工程开销：每 change 5–8 次额外 LLM 调用 + ~15min；10 子项目 × `openspec init/update` 维护乘 10
5. 退路明确：未来某个 Skill 演化为对外稳定 SDK 时，可只对该子模块重新引入 OpenSpec

### 6.2 Recipe 版本变迁

| 版本 | Recipe ID | 状态 |
|---|---|---|
| v1 | `openspec-superpowers-repomem-sendbox-dashboard` | **deprecated** — 仅 bootstrap 期间使用 |
| **v2** | `superpowers-repomem-sendbox-dashboard` | **active** — 自本 design.md 落盘起 |

**合规路径**：按 `docs/HarnessStack/longterm.md` 的 **Full Rewrite Conditions** 执行 versioned recipe migration，**非自动降级**。Migration 记录到 `docs/RepoMem/persist/version-plan.md`，标 v1 deprecated、v2 active。

### 6.3 v2 新 Pipeline（8 步）

```
1. RepoMem.read              — 读两层（主仓库 persist + 本模块）
2. Superpowers.brainstorming — 创意层澄清；auto-judge skip on clear/trivial
3. RepoMem.capture           — 打开 temp/<slug>/{requirements,architecture}.md
4. Superpowers.writing-plans — 产出 plan，落 docs/superpowers/plans/
5. using-git-worktrees + executing-plans + TDD
   + RepoMem.capture (continuous)
6. Superpowers.verification-before-completion  — 跑测试 + evidence
7. requesting-code-review (ask-first)
   + finishing-a-development-branch (ask-first)
8. RepoMem.merge (HITL) + prune/split
```

**关键变化**（vs v1 13 步）：
- 移除步骤 3 `OpenSpec.explore/propose`
- 移除步骤 5 中"消费 OpenSpec specs+tasks"
- 移除步骤 8 中 `OpenSpec.verify`（双闸门 → 单闸门，由 Superpowers verification-before-completion 独立担当）
- 移除步骤 11 `OpenSpec.archive`
- 步骤号从 13 压缩到 8

### 6.4 v2 不变量

- ✅ Single task identifier：`<task> = <slug>`（不再叫 change-id）
- ✅ Add-only：v2 是 v1 的 **Full Rewrite migration**，不是降级
- ✅ Single verification gate：Superpowers verification-before-completion 独立担当
- ✅ Merge ordering：RepoMem.merge 在 finishing-a-development-branch 之后，HITL
- ✅ No content duplication
- ✅ Sendbox & Dashboard 不变量保留（One sendbox per project；one letter → N rows；独立生命周期）

### 6.5 移除 OpenSpec 的物理动作清单（Migration Tasks）

在 SP-0 实施阶段（writing-plans 后）需要执行：

1. `rm openspec` （删除根软链）
2. `rm -rf docs/openspec/`（**HITL 确认** —— 当前是空 workspace，无 in-flight change）
3. `rm -rf .claude/skills/openspec-*`（4 个 skill 文件）
4. `rm -rf .claude/commands/opsx/`（4 个 slash command）
5. `npm uninstall -g @fission-ai/openspec`（清理全局 CLI）
6. 修改 `CLAUDE.md`：recipe ID 改为 v2、pipeline 改为 8 步、移除 OpenSpec 相关引用、更新 Where-to-Look 表
7. 修改 `docs/HarnessStack/longterm.md`：标 v1 deprecated 段落、新增 v2 active 段落、Full Rewrite 记录
8. 修改 `docs/HarnessStack/README.md`：recipe identity 更新
9. 修改 `docs/RepoMem/persist/version-plan.md`：v1→v2 跨界事件记录
10. 修改 `docs/RepoMem/persist/memory/runbook.md` §0：移除"不要删 openspec 软链"段落（不再适用）
11. 修改 `docs/RepoMem/persist/memory/pre-openspec-decisions.md`：文件名保留（"pre-openspec" 仍历史准确），加 banner 标注"v2 之后 OpenSpec 已移除"
12. 更新 `docs/Dashboard/index.md`：清理 OpenSpec 相关 UN 行

---

## 7. SP 分解最终表

### v1 子项目（10 个）

| ID | 路径 | 名 | 类型 | 关键决策 |
|---|---|---|---|---|
| **SP-0** | `<root>/` | 仓库骨架 + recipe v2 | refactor | 本 design.md |
| **SP-1** | `Service/crawl/cookie-manager/` | CookieManager | service | fork CookieCloud + 接 upload API 协议 + hook 机制（exec/write_file）+ CLI；WebUI 放 v1+ |
| **SP-2** | `Engine/zhihu/` | Zhihu Engine | engine | MediaCrawler + Cookie + zse-96 签名（必须用浏览器 context 计算，不能纯 HTTP）；评论 schema 两层平铺（不自研树）|
| **SP-3** | `Skill/crawl/zhihu-crawl/` | Zhihu Skill | skill | URL → 调引擎 → 询问保存路径 + 自动分类（vague_path） |
| **SP-4a** | `Engine/bilibili/` | Bilibili Engine | engine | BiliNote Docker 客户端，TRANSCRIBER_TYPE=bcut（B站必剪，免费云端 ASR）；字幕优先级联 BN 自带；bilibili-api-python 抓元数据 |
| **SP-4b** | `Skill/crawl/bilibili-crawl/` | Bilibili Skill | skill | 同 SP-3 结构 |
| **SP-5a** | `Service/crawl/zhihu-watcher/` | Zhihu Watcher | service | 收藏夹定时监听（默认 30–60min），高水位 `created` 戳记，调 SP-2 引擎 |
| **SP-5b** | `Service/crawl/bilibili-watcher/` | Bilibili Watcher | service | 收藏夹定时监听（默认 15–30min），高水位 `fav_time`，调 SP-4a 引擎 → BN 转录 |
| **SP-6** | `Skill/ingester/crawl-md-saver/` | CrawlMdSaver | skill | 注册其他 crawl skill，输入=URL+笔记 / 源文档+笔记，输出=合并 md，frontmatter 含用户笔记元数据 |
| **SP-7** | `Service/ingester/thino-ingester/` | ThinoIngester | service | 监听 Thino_path（v1 配置填写），解析 Thino 块 → 调 SP-6 → append 整理结果回块尾 |

### v1+ 候选

| ID | 路径 | 名 | 说明 |
|---|---|---|---|
| **SP-8** | `Skill/router/web-search/` | Web Search Router | 聚合知乎官方 Skill（`zhihu_search_skills.zip` 等 3 个）+ Tavily MCP + Exa；不 vendor 知乎 zip（避免漂移），README 写"下载并解压到 `~/.claude/skills/`"；待用户邮件申请 `openplatform@zhihu.com` 拿 Access Secret 后激活 |

### 依赖图

```
SP-0 (骨架 + recipe v2)
   ├──> SP-1 (CookieManager) ──┬──> SP-3 (Zhihu Skill)
   │                            ├──> SP-4b (Bilibili Skill)
   │                            ├──> SP-5a (Zhihu Watcher)
   │                            └──> SP-5b (Bilibili Watcher)
   ├──> SP-2 (Zhihu Engine) ────┼──> SP-3
   │                            └──> SP-5a
   ├──> SP-4a (Bilibili Engine)─┼──> SP-4b
   │                            └──> SP-5b
   └──> SP-6 (CrawlMdSaver) ────> SP-7 (ThinoIngester)
                 ↑
       SP-3 / SP-4b 注册到 SP-6
```

**关键关系**：SP-1 是所有"需要 cookie 的子项目"的硬前置；SP-2/SP-4a 是各自 skill+watcher 的硬前置；SP-6 是 SP-7 的硬前置；SP-3/SP-4b 通过"注册到 SP-6"形成软依赖。

---

## 8. LLMClient 共享层

**位置**：`Engine/common/llm_client.py`

**设计**：
- 用户子项目通过 `from common.llm_client import LLMClient` 引入
- 接口稳定：`complete(messages, **kwargs) -> str`、`stream(messages, **kwargs) -> Iterator[str]`
- 内部用 **litellm** 路由到 OpenAI / Anthropic / DashScope / Ollama / 任意家
- Provider 切换通过**配置文件**（`<root>/config/llm.yaml`），不写死任何家
- v1+ 接入位：`to_opencode()` 方法预留，将来切换为 opencode agent loop 时接口不变

**示意**：
```python
# Engine/common/llm_client.py
import litellm
from .config import load_llm_config

class LLMClient:
    def __init__(self, profile: str = "default"):
        self.cfg = load_llm_config(profile)
    
    def complete(self, messages, **kwargs) -> str:
        return litellm.completion(
            model=self.cfg.model,          # e.g. "claude-opus-4-7" / "dashscope/qwen-max" / "ollama/llama3"
            messages=messages,
            api_key=self.cfg.api_key,
            **kwargs
        ).choices[0].message.content
    
    def to_opencode(self):  # v1+ 接入位
        raise NotImplementedError("opencode integration planned for v1.x")
```

**使用场景**：
- SP-3/SP-4b：Skill 内 vague_path 自动分类
- SP-6：合并用户笔记与原文的"整理"步骤
- SP-7：解析 Thino 块后的格式化

**v1 默认 provider**：在配置里设 `claude-opus-4-7`，回落 `dashscope/qwen-max`。具体凭据放 `.env`，不入仓库。

---

## 9. v1.0 OSS Fractal 切分协议

**触发时机**：v1 全部 10 个子项目实现并验证通过，准备 OSS 释出时。

**切分动作**（每个子模块）：

```bash
# 1. 用 git filter-repo 切出子目录历史
cd /tmp && git clone <jarvankb-monorepo> jarvankb-mirror
cd jarvankb-mirror
git filter-repo --subdirectory-filter Engine/zhihu/

# 2. 复制主仓库共享根 → 子仓库
cp -r <jarvankb-monorepo>/docs/HarnessStack/ docs/HarnessStack/

# 3. 新建子仓库自有的协调层
mkdir -p docs/{sendbox,Dashboard}
touch docs/sendbox/toAgent/handoff.md docs/Dashboard/index.md

# 4. 提升 RepoMem 起点
mkdir -p docs/RepoMem/persist
mv docs/RepoMem/*.md docs/RepoMem/persist/  # 之前的 module-level 内容提升为 persist 起点

# 5. 新建独立 GitHub repo（在 Organization 下）
gh repo create JarvanKB-Org/zhihu-engine --public --source=. --push
```

**Organization 命名**：候选 `JarvanKB`、`JarvanKB-Org`、`Jarvan`，待 v1.0 临近时再敲。

---

## 10. 未决项

记录已知但当前不阻塞 SP-0 的待定问题：

1. **v1.0 GitHub Organization 名** — 等 v1 完成度临近 100% 时敲；可能候选：`JarvanKB`（与 repo 名重名风险）/ `Jarvan` / `JarvanWorks`
2. **SP-8 web-search router 的"路由策略"** — 进 SP-8 brainstorming 再敲；当前只占位
3. **Cookie Manager 与 CookieCloud 协议的细节** — 进 SP-1 brainstorming 再敲；R1 建议两条路径（fork CC 加 WebUI/hook，或自家服务实现 CC upload 协议）
4. **Zhihu 数据开放平台 Access Secret 是否走 v1** — 当前结论是 v1 不依赖；用户后续可发邮件 `openplatform@zhihu.com` 申请
5. **BiliNote 是否在 v1 后期上游 PR 添加 DashScope/听悟 transcriber** — 等 bcut/kuaishou 质量验证再定
6. **OpenSpec 移除时的物理动作执行时点** — 当前建议放 SP-0 实现阶段（在 writing-plans 之后、SP-1 brainstorming 之前）一次性完成
7. **`pre-openspec-decisions.md` D3（通义听悟选型）现已被 R5 推翻** — 文件本身是 FROZEN LEGACY，加 banner 标注"v2 之后 ASR 路径切换为 BiliNote/bcut" 而非编辑历史决策

---

## 11. 实施顺序（待 SP-0 writing-plans 细化）

粗粒度：

```
A. 仓库重命名（用户另起 session 完成；本 design 落盘后立即可做）
B. 新建目录骨架（mkdir 全部子模块 docs/、HarnessStack/、RepoMem/ 等）
C. 移除 OpenSpec（§6.5 的 12 个物理动作）
D. 写 v2 CLAUDE.md、longterm.md、version-plan.md migration 记录
E. 移植 14 份现有 RepoMem 文档到新位置（基本是 path 不动，但去除 OpenSpec 引用）
F. 提交 baseline commit："refactor(SP-0): JarvanKB skeleton + HarnessStack v2 (remove OpenSpec)"
G. SP-1 brainstorming 启动
```

A–F 之间的依赖关系会在 writing-plans 产出的 plan 文档里细化。

---

## 12. 自审报告（design 写完后立即跑）

按 brainstorming skill 要求执行的 4 项检查：

| 检查 | 结果 |
|---|---|
| **Placeholder scan** | 已扫描；§10 未决项明确标注"非阻塞"；其余无 TBD/TODO |
| **内部一致性** | §3 目录树 / §4 分层契约 / §5 子模块 docs / §6 v2 recipe / §7 SP 分解 互相呼应；§6.5 Migration 动作清单与 §11 实施顺序对齐 |
| **Scope check** | 单 spec 覆盖：仓库改名 + 目录骨架 + recipe 迁移 + LLMClient + 切分协议 + SP 分解。**SP-1..SP-7 各自独立 design 在后续 brainstorming 产出**，本 SP-0 不展开 |
| **Ambiguity** | §4 表头"主仓库（全局）"含义已注释；§8 LLMClient 给出代码示例减少歧义；§6 recipe v1/v2 名字明确列出 |

---

## 13. 后续动作

本 design 落盘并通过用户 review 后：

1. **Invoke `superpowers:writing-plans` skill** 产出实现 plan
2. plan 落到 `docs/superpowers/plans/2026-05-31-SP-0-jarvankb-skeleton-plan.md`
3. 按 plan 执行：仓库改名（用户）→ 骨架创建 → OpenSpec 移除 → recipe v2 文档更新 → baseline commit
4. SP-0 完结后进入 **SP-1 (CookieManager) brainstorming**

---

**End of SP-0 design.md**
