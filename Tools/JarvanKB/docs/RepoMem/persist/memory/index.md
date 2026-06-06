# Memory Index — JarvanKB

长期"非架构、非 spec"的可持续知识——运维手册、历史决策遗存、教训。

## 现有文件

| 文件 | 性质 | 何时读 |
|---|---|---|
| `runbook.md` | 操作手册：凭据配置、OSS 桶策略、故障表、成本估算、**§6 Tavily MCP 作用域/启用** | 配环境 / 排查故障 / 估算运行成本 / SP-8 web-search 接手 |
| `pre-openspec-decisions.md` | **冻结的遗存**：D1–D7 调研结论（bootstrap 期产生） | 阅读历史背景；**新决策不写这里**，走 `<module>/docs/RepoMem/temp/<slug>/decisions.md` |
| `llm-shared-layer.md` | 共享 LLM 层（`jarvankb_common.LLMClient`，litellm + 自定义 OpenAI 兼容 provider）+ 多 runtime agentskills.io `SKILL.md` 打包契约（SP-3 落地，2026-06-07） | SP-4b/SP-6/SP-7 接 LLM 或打包 skill 时 |

## 与 superpowers writing-plans / RepoMem temp 的边界

- **未来每个非平凡决策 = 一个 `<module>/docs/RepoMem/temp/<slug>/decisions.md` 条目**（HITL merge 时决定是否 promote 到 `docs/RepoMem/persist/memory/`，并在 module decisions 留 `[Promoted to global ↗]` 标记）
- `memory/` 只接受：(a) 操作类知识（runbook 类）；(b) `finishing-a-development-branch` 后由 `RepoMem.merge` 提炼出的 durable lessons；(c) bootstrap 期历史遗存（见 `pre-openspec-decisions.md`）
- `RepoMem.merge` 拒绝**复制** per-task plan/spec 内容到 memory——只接受**精炼后的教训**

## 域归属

memory 文件不强制按域拆分，但**强烈建议**在文件内 H2 标题用域名前缀（如 `## [crawl-pipeline] xxx`），便于 `RepoMem.read --scoped` 抓取。
