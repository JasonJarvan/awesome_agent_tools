# zhihu 引擎 — 外部架构概要

> 面向模块消费者和集成者的架构说明。内部设计细节（类图、决策日志）见 `docs/RepoMem/architecture.md`。

---

## 1. 模块单元

```
zhihu/
├── url_router.py      # URL 分类：classify(url) -> (ZhihuType, ids)
├── fetcher.py         # HTTP 层：get_page() / get_api_answer()
├── initialdata.py     # 从页面 HTML 提取 window.__INITIAL_DATA__ JSON
├── parsers/
│   ├── answer.py      # ANSWER 类型解析
│   ├── article.py     # ARTICLE 类型解析
│   ├── question.py    # QUESTION 类型解析（含嵌入答案列表）
│   └── html_scrape.py # CSS 选择器兜底抓取
├── comments.py        # 评论分页拉取（/api/v4/comments）
├── markdown.py        # HTML → Markdown 转换 + frontmatter 渲染
├── models.py          # 数据类：FetchResult / Author / EmbeddedAnswer / Comment / ZhihuType
├── errors.py          # ZhihuFetchError
├── engine.py          # 主协调器：fetch() 入口，串联 fallback 链
└── cli.py             # 命令行入口，薄包装 fetch()
```

各单元职责单一，`engine.py` 是唯一的协调层；外部消费者仅需接触 `engine.py`（通过 `__init__.py` 导出的 `fetch`）和 `models.py` 中的数据类。

---

## 2. Body 获取 Fallback 链

```
fetch(url, cookies, ...)
    │
    ▼
[url_router] classify(url) → (type, ids)
    │
    ▼
[fetcher] get_page(url) → (status, html)
    │
    ├─ status == 200
    │       │
    │       ├─ [initialdata] extract_initial_DATA(html) → data
    │       │       └─ 成功 → [parsers/answer|article|question] → FetchResult ✓
    │       │
    │       └─ initialData 缺失或解析失败
    │               └─ [parsers/html_scrape] scrape_body(html) → FetchResult ✓（最小化）
    │
    └─ status == 403 且 type == ANSWER
            └─ [fetcher] get_api_answer(answer_id) → JSON
                    └─ [engine._from_api_answer] → FetchResult ✓
                    └─ 仍失败 → ZhihuFetchError ✗

所有路径均失败 → ZhihuFetchError（携带 attempts 列表 + 最后 status）
```

**策略名称**（记录在 `ZhihuFetchError.attempts`）：`"html-initialdata"`、`"html-css-scrape"`、`"api-fallback"`。

---

## 3. 关键架构决策

### 无浏览器、无 zse-96 签名

引擎使用 `httpx` 直接发起标准 HTTP 请求，模拟浏览器导航头（`NAV_HEADERS`）。知乎页面将完整的结构化数据以 `window.__INITIAL_DATA__` JSON 注入 HTML，引擎优先解析这份数据，完全绕开了 zse-96 API 签名机制。对于签名墙导致的 403，仅回退到**无签名** `/api/v4` 端点（仅对 ANSWER 类型有效）。

### `trust_env=False` — 直连知乎

所有 `httpx` 请求均以 `trust_env=False` 发出，不读取 `HTTP_PROXY` / `HTTPS_PROXY` 等系统代理环境变量。这是面向中国本地部署的有意设计：引擎直连知乎，不经过系统代理，避免代理配置干扰抓取行为。

### 纯抓取边界

引擎是无状态的单次调用管道：

```
(url, cookies) → fetch() → FetchResult
```

- **不**维护 Session 或 Cookie 存储。
- **不**调用任何 Cookie 管理器（SP-3 / SP-5a 的职责）。
- **不**下载图片（`content_markdown` 保留远程图片 URL）。
- **不**集成 LLM 或后处理逻辑。

### 评论架构

评论通过 `/api/v4/comments` 分页 API 拉取，与主体内容分离，仅在 `with_comments=True` 时触发。结构为扁平两层：顶级评论（`parent_id=None`）+ 一级回复（`parent_id` 指向顶级评论 ID）。仅 ANSWER 和 ARTICLE 支持评论；QUESTION 不支持。

### Markdown 转换

HTML 正文经 `markdownify` 转换，远程图片 URL 保留为 `![](url)` 引用。`FetchResult.to_markdown()` 在正文前追加 YAML frontmatter，可通过 `with_frontmatter=False` 关闭。

---

## 4. 数据流总览

```
外部调用方（SP-3 Skill / SP-5a Watcher）
    │  注入 URL + Cookie
    ▼
fetch(url, cookies, ...)          ← 唯一公开入口
    │
    ├── url_router    分类 + 提取 ID
    ├── fetcher       HTTP GET（trust_env=False）
    ├── initialdata   提取 __INITIAL_DATA__
    ├── parsers       结构化解析 → FetchResult
    ├── html_scrape   兜底 CSS 抓取
    ├── comments      可选评论分页
    └── markdown      HTML→MD + frontmatter
    │
    ▼
FetchResult（含 content_markdown、metadata、answers、comments）
    │
    └── .to_markdown()  → Markdown 字符串（供 KB 存储 / 展示）
```

---

## 5. 参考

- 公开接口合约（签名、字段、错误）：[`docs/interface.md`](interface.md)
- 内部架构记忆（决策历史、模块边界细节）：`docs/RepoMem/architecture.md`
- 设计文档：`docs/superpowers/specs/2026-05-31-SP-2-zhihu-engine-design.md`
