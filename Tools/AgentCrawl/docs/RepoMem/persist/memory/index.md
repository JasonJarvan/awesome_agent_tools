# Memory Index — AgentCrawl

长期"非架构、非 spec"的可持续知识——运维手册、历史决策遗存、教训。

## 现有文件

| 文件 | 性质 | 何时读 |
|---|---|---|
| `runbook.md` | 操作手册：凭据配置、OSS 桶策略、故障表、成本估算 | 配环境 / 排查故障 / 估算运行成本 |
| `pre-openspec-decisions.md` | **冻结的遗存**：D1–D7 调研结论（pre-OpenSpec 时期产生） | 阅读历史背景；**新决策不写这里**，走 OpenSpec change 归档 |

## 与 OpenSpec 的边界

- **未来每个非平凡决策 = 一个 OpenSpec change**，归档在 `docs/openspec/changes/<change-id>/`
- `memory/` 只接受：(a) 操作类知识（runbook 类）；(b) OpenSpec 归档后由 `RepoMem.merge` 提炼出的 durable lessons；(c) pre-OpenSpec 历史遗存
- `RepoMem.merge` 拒绝**复制** OpenSpec change 内容到 memory——只接受**精炼后的教训**

## 域归属

memory 文件不强制按域拆分，但**强烈建议**在文件内 H2 标题用域名前缀（如 `## [crawl-pipeline] xxx`），便于 `RepoMem.read --scoped` 抓取。
