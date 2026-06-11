# bilibili-watcher — 对外契约(Interface)

> SP-5b Bilibili 收藏夹监听服务的稳定对外契约:配置 schema + CLI。
> 本服务是 **daemon,无 HTTP API**;对外面只有「配置文件 + 命令行」。

## 1. 运行形态

- 进程入口:`python -m bilibili_watcher`(或安装后的控制台脚本 `bilibili-watcher`)。
- 默认模式:起 APScheduler `BlockingScheduler` 间隔任务(`max_instances=1`,`coalesce=True`),
  启动时**立即跑一轮**,之后每 `poll_interval_minutes` 跑一轮,常驻直到被杀。
- `--once` 模式:只跑一轮就退出(供冒烟自测 / CI)。

## 2. CLI

```
python -m bilibili_watcher [--config PATH] [--once]
```

| 参数 | 默认 | 说明 |
|---|---|---|
| `--config PATH` | `config/bilibili-watcher.yaml` | YAML 配置文件路径 |
| `--once` | （关）| 只跑一轮 poll 即退出,不起调度器 |

## 3. 配置 schema(YAML)

样例见 `config/bilibili-watcher.example.yaml`。所有字段:

### 3.1 顶级标量

| 键 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `poll_interval_minutes` | int | 否(默认 20)| 轮询间隔(分钟);必须 > 0。SP-0 建议 15–30 |
| `output_dir` | str | **是** | Markdown 输出根目录(其下按收藏夹分子目录) |
| `state_dir` | str | **是** | 状态文件目录(`state-<folder_id>.json`);需挂 volume 才能重启存活 |

### 3.2 `cookie_source` 块

| 键 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `cookie_source.base_url` | str | **是** | SP-1 CookieManager 地址(如 `http://127.0.0.1:48088`) |
| `cookie_source.uuid` | str | **是** | CookieCloud 箱子 uuid |
| `cookie_source.password` | str | **是** | 箱子解密口令(仅用于内存内解密,绝不落盘明文)|
| `cookie_source.auth_token` | str | 否 | 若箱子配置了 `server.auth_token`,则填此值作为 `X-CookieCloud-Token` 请求头 |

> `crypto_type` **不在配置里**:由 SP-1 `GET /get/:uuid` 的响应携带,服务自动按 `legacy` /
> `aes-128-cbc-fixed` 解密。

### 3.3 `engine` 块

| 键 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `engine.bn_base_url` | str | **是** | BiliNote(BN)后端地址(如 `http://127.0.0.1:3015`) |
| `engine.provider_id` | str | **是** | BN provider id(从 `GET /api/get_all_providers` 获取) |
| `engine.model_name` | str | **是** | BN 中注册的模型名 |

### 3.4 `render` 块(均可选)

| 键 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `render.include_transcript` | bool | `true` | 是否包含文字转录正文 |
| `render.include_timestamps` | bool | `false` | 是否在转录中包含时间戳 |
| `render.split_transcript` | bool | `false` | 是否将摘要与转录分成两个文件(v1 静态开关;出合集见设计 §11) |

### 3.5 `folders` 列表

| 键 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | str | **是** | 收藏夹 `media_id`(从 B 站收藏夹 URL 中取) |
| `name` | str | 否(默认 = id)| 输出子目录名;建议与已有目录名对齐 |

校验:缺任一必填字段、`folders` 为空、或 `poll_interval_minutes <= 0` → 启动即抛 `ValueError`。

## 4. 与上下游的契约

- **上游 cookie**:HTTP `GET {base_url}/get/{uuid}` → `{encrypted, crypto_type}` → 本服务内存内解密
  (CookieCloud 协议,见 `Service/crawl/cookie-manager/docs/interface.md §3`)→ 抽 `bilibili.com`(无前缀点)cookie。
- **下游引擎**:对每个新 `type==2` 视频调冻结的 SP-4a `engine.transcribe(bvid, credential=BilibiliCredential(...))`,
  取 `result.render(RenderOptions(...)).main_markdown`(契约见 `Engine/bilibili/docs/interface.md`)。本服务**不**改引擎。

## 5. 输出契约

`<output_dir>/<folder.name>/<sanitize(title)>.md`(撞名 → `<title>_<bvid>.md`):
- sanitize:`\ / " < > |` → 空格;`?` → `？`;`:` → `：`;空标题 → `untitled`。
- 文件内容:首行 `> https://www.bilibili.com/video/<bvid>`,换行后接 `main_markdown`;**无 frontmatter**;远程图片 URL 原样保留。

## 6. 状态文件

`<state_dir>/state-<folder_id>.json`:JSON 对象 `{"watermark": <fav_time_int>, "seen": ["BV...", ...]}`。
原子写(临时文件 + `os.replace`)。删掉它会导致该收藏夹被重新全量抓取(水位 + 去重重置)。
