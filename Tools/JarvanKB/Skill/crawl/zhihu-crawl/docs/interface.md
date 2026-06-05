# zhihu-crawl — 公开接口合约（v1，冻结）

> 本文档描述已实现并冻结的 v1 公开 API。所有调用方（LLM agent、脚本、CI）均应针对此文档编程，不得依赖内部实现细节。
> SP-3 是 `Engine/zhihu`（SP-2 冻结引擎）和 `jarvankb_common.LLMClient` 的纯消费者——本技能不修改引擎，亦不持有自己的 LLM 连接配置。

---

## 1. Python API

### 安装与导入

```bash
pip install -e Engine/common -e Engine/zhihu -e Skill/crawl/zhihu-crawl
```

```python
from zhihu_crawl import save_zhihu, SaveResult
```

### `save_zhihu()` — 主入口

```python
def save_zhihu(
    url: str,
    save_path: str | None = None,
    *,
    with_comments: bool = False,
    comment_limit: int | None = None,
    profile: str | None = None,
    config_path: str | None = None,
) -> SaveResult:
```

#### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `url` | `str` | （必填）| 知乎 URL（回答 / 专栏文章 / 问题），见下方"支持的 URL 形式" |
| `save_path` | `str \| None` | `None` | 保存路径；`.md` 结尾 = 明确路径，直接写入；目录 / `output_root` / `None` / 空字符串 = 模糊路径，触发 LLM 分类 |
| `with_comments` | `bool` | `False` | 是否同步抓取评论（透传至 SP-2 引擎） |
| `comment_limit` | `int \| None` | `None` | 评论上限；`None` 表示拉取全部 |
| `profile` | `str \| None` | `None` | LLM 配置文件名覆盖；`None` 时取 `config.yaml` 中的 `llm.profile`（默认 `"default"`） |
| `config_path` | `str \| None` | `None` | `config.yaml` 路径；`None` 时取 `ZHIHU_CRAWL_CONFIG` 环境变量，否则当前目录 `config.yaml` |

**返回值：** `SaveResult`（见下节）。

**异常：** 引擎全部策略失败时抛出 `ZhihuFetchError`（来自 `Engine/zhihu`）；配置缺失 / Cookie 解密失败时抛出 `FileNotFoundError` / `ValueError`；不返回哨兵值。

---

### `SaveResult` — 返回字段

```python
@dataclass
class SaveResult:
    path: str            # 写入文件的绝对路径
    title: str           # 内容标题
    type: str            # "answer" | "article" | "question"
    url: str             # 原始请求 URL
    category: str | None # LLM 分类选定的子文件夹名；明确路径写入时为 None
    was_vague: bool      # True 表示发生了 LLM 路径分类
    proposed_new: bool   # True 表示 LLM 建议了一个新子文件夹（output_root 下原本不存在）
```

---

## 2. CLI

### 安装后可用

```bash
zhihu-crawl <url> [--out PATH] [--comments] [--comment-limit N] [--json] [--profile NAME] [--config PATH]
```

### 参数说明

| 参数 | 说明 |
|---|---|
| `url` | （必填）知乎 URL |
| `--out PATH` | 保存路径；`.md` 文件 = 明确写入，目录 / 省略 = 模糊（LLM 分类） |
| `--comments` | 开启评论抓取（等价于 `with_comments=True`） |
| `--comment-limit N` | 评论上限（整数） |
| `--json` | 将 `SaveResult` 以 JSON 格式输出到标准输出（供调用方 agent 机器解析） |
| `--profile NAME` | LLM 配置文件名覆盖 |
| `--config PATH` | `config.yaml` 路径覆盖 |

### 退出码

| 退出码 | 含义 |
|---|---|
| `0` | 成功 |
| `1` | 通用错误（配置 / Cookie / LLM 等） |
| `2` | `ZhihuFetchError`（引擎抓取失败） |

### 示例

```bash
# 明确路径写入
zhihu-crawl "https://www.zhihu.com/question/123/answer/456" --out ~/KB/tech/note.md

# 模糊路径，LLM 自动分类到子文件夹
zhihu-crawl "https://www.zhihu.com/question/123/answer/456" --out ~/KB/zhihu

# 省略 --out，完全由 LLM 分类
zhihu-crawl "https://www.zhihu.com/question/123/answer/456"

# 机器可读输出（供 agent 解析）
zhihu-crawl "https://www.zhihu.com/question/123/answer/456" --json
```

---

## 3. 支持的 URL 形式

与 `Engine/zhihu` 保持一致，见 `Engine/zhihu/docs/interface.md` §6。

| 类型 | 示例 URL |
|---|---|
| `ANSWER`（带问题 ID）| `https://www.zhihu.com/question/123456/answer/789012` |
| `ANSWER`（短链）| `https://www.zhihu.com/answer/789012` |
| `ARTICLE`（专栏）| `https://zhuanlan.zhihu.com/p/987654` |
| `QUESTION` | `https://www.zhihu.com/question/123456` |

---

## 4. 依赖的上游接口

- **`Engine/zhihu`（SP-2，冻结）：** `fetch(url, cookies, ...)` → `FetchResult`，完整合约见 `Engine/zhihu/docs/interface.md`。
- **`jarvankb_common.LLMClient`（Engine/common，SP-3 实现并冻结）：** `LLMClient(profile).complete(messages)` → `str`，完整合约见 `Engine/common/docs/interface.md`。

本技能不修改上述两个接口，亦不依赖其内部实现细节。

---

## 5. 配置文件（`config.yaml`）

```yaml
output_root: ~/KB/zhihu       # 模糊路径写入的根目录
cookie:
  base_url: http://127.0.0.1:48088
  uuid: <uuid>
  password_env: COOKIE_MANAGER_PASSWORD   # 环境变量名，值为 Cookie 解密密码
llm:
  profile: default             # 对应 config/llm.yaml 中的 profile 名
```

完整示例见 `config.example.yaml`。真实配置（`config.yaml`）已被 `.gitignore` 排除，密钥存于 `.env`，永不提交至仓库。
