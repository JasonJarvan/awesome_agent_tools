# zhihu 引擎 — 公开接口合约（v1，冻结）

> 本文档描述的是已实现并冻结的 v1 公开 API。所有下游消费者（SP-3 Skill、SP-5a Watcher 等）均应针对此文档编程，不得依赖内部实现细节。

---

## 1. 模块导出

```python
from zhihu import fetch, FetchResult, Author, EmbeddedAnswer, Comment, ZhihuType, ZhihuFetchError
```

`__all__` 中的七个名称构成唯一的稳定公开接口；其余内部模块（`fetcher`、`parsers`、`initialdata` 等）不属于公开契约。

---

## 2. `fetch()` — 主入口

### 签名

```python
def fetch(
    url: str,
    cookies: dict | str | None = None,
    *,
    with_comments: bool = False,
    comment_limit: int | None = None,
    timeout: float = 30.0,
) -> FetchResult:
```

### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `url` | `str` | （必填）| 任意合法的知乎 URL，见 §6 支持的 URL 形式 |
| `cookies` | `dict \| str \| None` | `None` | 登录凭证，见 §3 Cookie 输入形式 |
| `with_comments` | `bool` | `False` | 是否同步拉取评论列表，仅对 ANSWER / ARTICLE 有效 |
| `comment_limit` | `int \| None` | `None` | 评论上限；`None` 表示分页拉取全部 |
| `timeout` | `float` | `30.0` | 单次 HTTP 请求超时（秒） |

**返回值：** `FetchResult`（见 §4）。

**异常：** 若所有 body 获取策略均失败，抛出 `ZhihuFetchError`（见 §7）；不会返回哨兵值。

---

## 3. Cookie 输入形式

引擎是纯消费者——它**不**主动获取或刷新 Cookie，也不调用 Cookie 管理器。Cookie 由调用方（SP-3 Skill / SP-5a Watcher）在调用时注入。

三种合法形式：

**字典形式（推荐）**

```python
cookies = {"d_c0": "...", "z_c0": "...", "__zse_ck": "..."}
result = fetch(url, cookies=cookies)
```

**原始 Cookie 头字符串**

```python
cookies = "d_c0=...; z_c0=...; __zse_ck=..."
result = fetch(url, cookies=cookies)
```

引擎内部调用 `http.cookies.SimpleCookie` 解析，再转为字典。

**匿名（不传 Cookie）**

```python
result = fetch(url)   # 或显式传 cookies=None
```

仅能访问知乎的公开内容，部分答案可能因登录墙而失败。

**有意义的 Cookie 键：** `z_c0`（登录态）、`d_c0`（设备 ID）、`__zse_ck`（反爬校验辅助）。

---

## 4. 返回值 — `FetchResult`

```python
@dataclass
class FetchResult:
    url: str                        # 原始请求 URL
    type: ZhihuType                 # ANSWER | ARTICLE | QUESTION
    title: str                      # 内容标题
    author: Author | None           # 作者信息；匿名或无法解析时为 None
    content_markdown: str           # 正文的 Markdown 表示
    metadata: dict                  # 类型相关的元数据（见下表）
    fetched_at: str                 # 抓取时间，ISO-8601 UTC，格式 "2026-06-01T12:00:00Z"
    answers: list[EmbeddedAnswer]   # 仅 QUESTION 类型填充；其余为空列表
    comments: list[Comment]         # 仅 with_comments=True 且类型为 ANSWER/ARTICLE 时填充
    raw: dict | None                # 原始来源实体 dict —— initialData 路径下为解析出的实体对象，api-fallback 路径下为 API JSON，仅 CSS-scrape 兜底路径为 None
```

`metadata` 常见键（视内容类型和解析路径而定，可能缺失）：

| 键 | 类型 | 说明 |
|---|---|---|
| `vote_count` | `int` | 赞同数 |
| `comment_count` | `int` | 评论数 |
| `created_at` | `str \| None` | 创建时间（ISO-8601）|
| `updated_at` | `str \| None` | 最后修改时间（ISO-8601）|

### `to_markdown(with_frontmatter: bool = True) -> str`

将结果序列化为 Markdown 字符串。

- `with_frontmatter=True`（默认）：在正文前追加 YAML frontmatter 块，键为：
  `title`、`author`、`url`、`type`、`vote_count`、`comment_count`、`created_at`、`updated_at`、`fetched_at`、`source: zhihu`。
- `with_frontmatter=False`：仅返回 `content_markdown`，不含 frontmatter。

---

## 5. 数据类型

### `ZhihuType`（`str` 枚举）

```python
class ZhihuType(str, Enum):
    ANSWER   = "answer"
    ARTICLE  = "article"
    QUESTION = "question"
```

### `Author`

```python
@dataclass
class Author:
    name: str
    url: str | None = None
    headline: str | None = None
```

### `EmbeddedAnswer`

仅在 QUESTION 类型中使用，表示问题页面 `initialData` 中嵌入的回答。

```python
@dataclass
class EmbeddedAnswer:
    answer_id: str
    author: Author | None
    vote_count: int
    comment_count: int
    created_at: str | None
    updated_at: str | None
    url: str
    content_markdown: str   # initialData 中携带的完整正文；不触发额外请求
```

> **注意：** `content_markdown` 的完整程度取决于知乎页面 `initialData` 实际包含的内容，引擎不发起额外请求来补全。

### `Comment`

表示答案或专栏文章的评论，采用两层扁平结构（顶级评论 + 一级回复）。

```python
@dataclass
class Comment:
    id: str
    parent_id: str | None       # None = 顶级评论；非 None = 对某条顶级评论的回复
    author: Author | None
    content: str
    like_count: int
    created_at: str | None
    reply_to_author: str | None = None   # 被回复者的用户名（可选）
```

---

## 6. 支持的 URL 形式

| 类型 | 示例 URL |
|---|---|
| `ANSWER`（带问题 ID）| `https://www.zhihu.com/question/123456/answer/789012` |
| `ANSWER`（短链）| `https://www.zhihu.com/answer/789012` |
| `ARTICLE`（专栏，主域）| `https://zhuanlan.zhihu.com/p/987654` |
| `ARTICLE`（专栏，路径）| `https://www.zhihu.com/p/987654` |
| `QUESTION` | `https://www.zhihu.com/question/123456` |

不匹配任何形式时，`classify()` 直接抛出 `ZhihuFetchError`。

---

## 7. Body 获取策略（fallback 链）

引擎对每次 `fetch()` 调用按顺序尝试以下策略，首次成功即返回：

```
1. html-initialdata
   GET 页面 HTML → 提取 window.__INITIAL_DATA__ JSON → 专属 parser 解析
   （适用：ANSWER / ARTICLE / QUESTION；需要 200 响应）

2. html-css-scrape
   GET 页面 HTML（同上，200）→ CSS 选择器抓取正文 DOM → 最小化 Markdown
   （兜底：initialData 缺失或解析失败时触发）

3. api-fallback（仅 ANSWER 类型 + 403 响应时触发）
   GET https://www.zhihu.com/api/v4/answers/{answer_id}?include=content
   → 无签名（不使用 zse-96），直接 JSON
```

`attempts` 列表记录本次调用实际尝试的策略名称（`"html-initialdata"`、`"html-css-scrape"`、`"api-fallback"`），随 `ZhihuFetchError` 一同返回，供调用方诊断。

> **api-fallback 限制：** 仅对 `ANSWER` 类型且页面返回 HTTP 403 时触发；`ARTICLE` 和 `QUESTION` 无此兜底。

---

## 8. `ZhihuFetchError`

```python
class ZhihuFetchError(Exception):
    url: str                # 触发错误的原始 URL
    attempts: list[str]     # 已尝试的策略名称列表（可能为空）
    status: int | None      # 最后一次 HTTP 响应状态码；无法获得时为 None
```

所有策略均失败时抛出，携带完整诊断信息，**不**返回 `None` 或哨兵值。

---

## 9. "纯抓取 / Cookie 由外部注入"边界

- 引擎**不**集成 Cookie 管理器，**不**实现 zse-96 签名（完全绕开），**不**下载图片（Markdown 保留远程图片 URL）。
- 所有 HTTP 请求以 `trust_env=False` 发起，不读取系统代理环境变量（`HTTP_PROXY` / `HTTPS_PROXY`）。这是中国本地部署场景下的有意决策：引擎直连知乎，不经过系统代理。
- 决定"抓什么、存什么、用什么 Cookie"是 SP-3 Skill / SP-5a Watcher 的职责，引擎只负责"给定 URL + Cookie → 返回结构化内容"。

---

## 10. CLI

```
usage: zhihu <url> [--cookies PATH] [--comments] [--no-frontmatter]
```

| 参数 | 说明 |
|---|---|
| `url` | 必填，知乎 URL |
| `--cookies PATH` | cookies.json 文件路径；支持浏览器导出格式 `[{name, value}, ...]` 或字典格式 `{name: value}` |
| `--comments` | 开启评论抓取（等价于 `with_comments=True`） |
| `--no-frontmatter` | 输出不含 YAML frontmatter 的纯 Markdown |

**模块调用方式：**

```bash
python -m zhihu "https://www.zhihu.com/question/123456/answer/789012" --cookies cookies.json --comments
```

**控制台脚本（安装后可用）：**

```bash
zhihu "https://www.zhihu.com/question/123456/answer/789012"
```

CLI 将结果打印到标准输出，退出码 `0` 表示成功。
