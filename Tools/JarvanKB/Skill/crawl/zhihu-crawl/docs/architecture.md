# zhihu-crawl — 架构概览（v1）

> 外部向架构说明。内部实现细节见 `docs/RepoMem/architecture.md`。
> SP-3 是纯消费者：不修改 `Engine/zhihu`（SP-2 冻结引擎），不持有独立 LLM 服务。

---

## 1. 多 agent 运行时打包面

SP-3 提供三层接入面，适配不同调用方：

| 层级 | 制品 | 服务对象 |
|---|---|---|
| 通用基础 | 可导入 Python 包 `zhihu_crawl` + 控制台脚本 `zhihu-crawl`（`--json` 结构化输出） | Hermes（pip 安装后 `import` / `subprocess`）、Codex、OpenClaw、脚本客户端 |
| Agent Skill 描述符 | **单一** `SKILL.md`（agentskills.io 标准，frontmatter `name`/`description`/`version`/`tags`） | Claude Code（P0）、Codex、OpenClaw、Hermes——同一文件跨四个运行时 |
| 发现合约 | `docs/sendbox/toAgent/handoff.md` 中的 SP-3 条目（CLI/import I/O） | 任意调用方 agent |

`scripts/sync-skill.sh` 将唯一的 `SKILL.md` 通过符号链接部署到 `~/.claude/skills/`、`~/.codex/skills/`、`~/.openclaw/skills/`、`~/.hermes/skills/`——一份源文件，多个部署目标。

---

## 2. 模块结构

```
Skill/crawl/zhihu-crawl/
├── SKILL.md                      # agentskills.io 描述符（驱动 CLI）
├── pyproject.toml                # dist=zhihu-crawl；脚本入口 zhihu-crawl = zhihu_crawl.cli:main
├── config.example.yaml           # 配置模板（真实配置 config.yaml 已 gitignore）
├── scripts/sync-skill.sh         # 将 SKILL.md 部署到四个运行时 skill 目录
├── src/zhihu_crawl/
│   ├── __init__.py               # 公开 API 导出：save_zhihu, SaveResult
│   ├── api.py                    # save_zhihu(...) -> SaveResult（可导入核心）
│   ├── cli.py                    # argparse 薄层 → api；支持 --out/--json/--comments/--profile
│   ├── cookie.py                 # SP-1 主动拉取：GET /get/:uuid + 客户端解密；仅在内存中
│   ├── classify.py               # 模糊路径分类：列举子文件夹 + LLM 推断/建议新文件夹
│   ├── config.py                 # 模块配置加载（output_root、Cookie 源、LLM profile）
│   └── saver.py                  # 路径解析 + Markdown 写入
├── docs/                         # interface.md（冻结）、architecture.md、RepoMem/、superpowers/
└── tests/                        # 单元测试（引擎 / LLMClient / Cookie 服务均已 mock）
```

---

## 3. 数据流

```
save_zhihu(url, save_path=None, *, with_comments=False, comment_limit=None, profile=None)
  │
  ├─ load config（output_root、Cookie 源、LLM profile）
  ├─ cookie.pull()
  │     GET {base_url}/get/{uuid} → {encrypted, crypto_type}
  │     → 客户端解密（legacy CryptoJS 或 aes-128-cbc-fixed）
  │     → cookie_data[".zhihu.com"] → {name: value} 字典
  │     （明文 Cookie 仅驻留内存，永不写盘）
  ├─ fetch(url, cookies=cookie_dict, ...)   ← SP-2 冻结引擎
  │     → FetchResult（ZhihuFetchError 在所有策略失败时抛出，透传给调用方）
  ├─ md = result.to_markdown()
  │     （引擎已生成含 source: zhihu 的 YAML frontmatter）
  ├─ 路径解析：
  │     save_path 指向 .md 文件  → 明确写入，直接使用
  │     save_path 为目录 / output_root / None / 空字符串  → 模糊：
  │         classify.classify(result, output_root, LLMClient)
  │             列举 output_root 下现有子目录 + (title, type, snippet) → LLMClient.complete()
  │             → 选择现有子文件夹 或 建议新文件夹名（已 slug 化）
  │         target = <output_root>/<category>/<slug(title)>.md
  │         碰撞时追加数字后缀
  └─ saver.write(target, md) → SaveResult
```

---

## 4. 跨 SP 边界

| 边界 | 行为 |
|---|---|
| SP-1（Cookie 管理器） | 主动拉取（`GET /get/:uuid`），永不使用 push 路径（已永久取消） |
| SP-2 引擎（`Engine/zhihu`） | 纯消费者，不修改引擎任何文件 |
| `jarvankb_common.LLMClient` | 消费者，SP-3 实现并冻结了真实 litellm 体；SP-6 按原样复用 |
| SP-5a（Bilibili Watcher） | 独立并行，无依赖；Cookie 解密模式有小重复，属有意设计（handoff §1） |

---

## 5. 错误处理概要

| 情形 | 行为 |
|---|---|
| 引擎全部策略失败 | `ZhihuFetchError` 透传；CLI 打印诊断信息，非零退出 |
| Cookie 服务不可达 / 解密失败 | 显式报错；不静默降级 |
| LLM 不可用（模糊路径） | 分类报错；明确路径写入不受影响 |
| 路径碰撞 | 文件名追加数字后缀（`note-2.md`、`note-3.md`……） |
| 配置文件缺失 | `FileNotFoundError`（在任何网络调用前抛出） |
