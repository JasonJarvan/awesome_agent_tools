# zhihu — 知乎内容抓取引擎（SP-2）

给定一个知乎 URL，返回结构化的 Markdown 正文 + 元数据，可选附带评论列表。

---

## 做什么

- 输入：知乎答案 / 专栏文章 / 问题的 URL，以及可选的登录 Cookie。
- 输出：`FetchResult` 对象，包含 Markdown 正文、标题、作者、元数据（赞同数、评论数、时间戳等），以及可序列化为带 YAML frontmatter 的 Markdown 字符串。
- 对问题页面，额外解析页面内嵌的 `EmbeddedAnswer` 列表（完整正文，无需额外请求）。
- 支持按需拉取答案 / 文章的评论（扁平两层结构）。

引擎**不**集成 LLM、**不**下载图片、**不**实现 zse-96 签名，是纯 HTTP 抓取 + HTML 解析管道。

---

## 安装

```bash
cd Engine/zhihu
pip install -e .
```

Python 3.11+ / 依赖：`httpx`、`beautifulsoup4`、`markdownify`（见 `pyproject.toml`）。

---

## Python 用法

```python
from zhihu import fetch

r = fetch("https://www.zhihu.com/question/123456/answer/789012",
          cookies={"z_c0": "...", "d_c0": "..."})
print(r.to_markdown())
```

带评论：

```python
r = fetch(url, cookies=cookies, with_comments=True, comment_limit=50)
for c in r.comments:
    print(c.author.name if c.author else "匿名", c.content)
```

匿名抓取（仅公开内容）：

```python
r = fetch(url)   # cookies 默认为 None
```

---

## CLI 用法

```bash
# 安装后使用控制台脚本
zhihu "https://www.zhihu.com/question/123456/answer/789012" --cookies cookies.json --comments

# 或通过模块调用
python -m zhihu "https://zhuanlan.zhihu.com/p/987654" --no-frontmatter
```

`cookies.json` 接受浏览器导出格式（`[{name, value}, ...]`）或字典格式（`{name: value}`）。

---

## 参考

- **完整接口合约（参数、字段、fallback 链、错误处理）：** [`docs/interface.md`](interface.md)
- **设计文档（决策、架构背景）：** [`docs/superpowers/specs/2026-05-31-SP-2-zhihu-engine-design.md`](../../../docs/superpowers/specs/2026-05-31-SP-2-zhihu-engine-design.md)
- **内部架构记忆（模块边界、历史决策）：** [`docs/RepoMem/architecture.md`](../docs/RepoMem/architecture.md)
