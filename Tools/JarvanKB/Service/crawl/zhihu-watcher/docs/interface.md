# zhihu-watcher — 对外契约(Interface)

> SP-5a 知乎收藏夹监听服务的稳定对外契约:配置 schema + CLI。
> 本服务是 **daemon,无 HTTP API**;对外面只有「配置文件 + 命令行」。

## 1. 运行形态

- 进程入口:`python -m zhihu_watcher`(或安装后的控制台脚本 `zhihu-watcher`)。
- 默认模式:起 APScheduler `BlockingScheduler` 间隔任务(`max_instances=1`,`coalesce=True`),
  启动时**立即跑一轮**,之后每 `poll_interval_minutes` 跑一轮,常驻直到被杀。
- `--once` 模式:只跑一轮就退出(供冒烟自测 / CI)。

## 2. CLI

```
python -m zhihu_watcher [--config PATH] [--once]
```

| 参数 | 默认 | 说明 |
|---|---|---|
| `--config PATH` | `config/zhihu-watcher.yaml` | YAML 配置文件路径 |
| `--once` | （关）| 只跑一轮 poll 即退出,不起调度器 |

## 3. 配置 schema(YAML)

样例见 `config/zhihu-watcher.example.yaml`。所有字段:

| 键 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `poll_interval_minutes` | int | 否(默认 45)| 轮询间隔(分钟);必须 > 0。建议 30–60 |
| `output_dir` | str | **是** | Markdown 输出根目录(其下按收藏夹分子目录) |
| `state_dir` | str | **是** | seen-id 状态文件目录(需挂 volume 才能重启存活) |
| `cookie_source.base_url` | str | **是** | SP-1 CookieManager 地址(如 `http://127.0.0.1:48088`,或其公网/局域网入口) |
| `cookie_source.uuid` | str | **是** | CookieCloud 箱子 uuid |
| `cookie_source.password` | str | **是** | 箱子解密口令(仅用于内存内解密,绝不落盘明文)|
| `collections` | list | **是** | 至少一个收藏夹 |
| `collections[].id` | str | **是** | 收藏夹 id 或完整 URL(`https://www.zhihu.com/collection/<id>`,内部会取末段) |
| `collections[].name` | str | 否(默认 = id)| 输出目录下的子目录名 |

> `crypto_type` **不在配置里**:它由 SP-1 `GET /get/:uuid` 的响应携带,服务按响应里的
> `crypto_type`(`legacy` / `aes-128-cbc-fixed`)自动选择解密方式。

校验:缺任一必填字段、`collections` 为空、或 `poll_interval_minutes <= 0` → 启动即抛 `ValueError`。

## 4. 与上下游的契约

- **上游 cookie**:HTTP `GET {base_url}/get/{uuid}` → `{encrypted, crypto_type}` → 本服务在内存内解密
  (CookieCloud 协议,见 `Service/crawl/cookie-manager/docs/interface.md §3`)→ 抽 `.zhihu.com` cookie。
- **下游引擎**:对每个新条目调冻结的 SP-2 `zhihu.fetch(url, cookies=...) -> FetchResult`,取
  `.title` + `.content_markdown`(契约见 `Engine/zhihu/docs/interface.md`)。本服务**不**改引擎。

## 5. 输出契约

`<output_dir>/<collection.name>/<sanitize(title)>.md`(撞名 → `<title>_<url_id>.md`):
- sanitize:`\ / " < > |` → 空格;`?` → `？`;`:` → `：`;空标题 → `untitled`。
- 文件内容:首行 `> <原始url>`,换行后接 `FetchResult.content_markdown`;**无 frontmatter**;远程图片 URL 原样保留。

## 6. 状态文件

`<state_dir>/seen-<collection_id>.json`:一个已抓取条目 key 的 JSON 数组,key = `"<type>:<id>"`。
原子写(临时文件 + `os.replace`)。删掉它会导致该收藏夹被重新全量抓取(去重重置)。
