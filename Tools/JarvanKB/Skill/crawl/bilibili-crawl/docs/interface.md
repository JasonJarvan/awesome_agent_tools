# bilibili-crawl — 公开接口合约（v1，冻结）

> 已实现并冻结的 v1 公开 API。所有调用方（LLM agent、脚本、CI）针对本文件编程，不依赖内部实现。
> SP-4b 是 `Engine/bilibili`（SP-4a 冻结引擎）与 `jarvankb_common.LLMClient` 的纯消费者——不修改引擎，
> 亦不持有自己的 LLM 连接配置。

## 1. Python API

### 安装与导入
```bash
pip install -e Engine/common -e Engine/bilibili -e Skill/crawl/bilibili-crawl
```
```python
from bilibili_crawl import save_bilibili, SaveResult
```

### `save_bilibili()` — 主入口
```python
def save_bilibili(
    ref: str,
    save_path: str | None = None,
    *,
    profile: str | None = None,
    config_path: str | None = None,
) -> SaveResult:
```

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `ref` | `str` | （必填）| 视频引用：BV id / `bilibili.com` URL / av id |
| `save_path` | `str \| None` | `None` | `.md` 结尾 = 明确路径直接写入；目录 / `output_root` / `None` / 空 = 模糊路径触发 LLM 分类 |
| `profile` | `str \| None` | `None` | LLM 配置文件名覆盖；`None` 取 `config.yaml` 的 `llm.profile`（默认 `default`，示例配置用 `mimo`） |
| `config_path` | `str \| None` | `None` | `config.yaml` 路径；`None` 取 `BILIBILI_CRAWL_CONFIG` 环境变量，否则当前目录 `config.yaml` |

**异常：** 引擎失败抛 `BilibiliEngineError` 子类（`InvalidVideoRef` / `TranscriptionFailed` /
`TranscriptionTimeout` / `BiliNoteUnavailable`）；配置缺失抛 `FileNotFoundError`。**Cookie 失败不致命**——
降级为无凭据（公开视频 ASR 路径）。

### `SaveResult` — 返回字段
```python
@dataclass
class SaveResult:
    path: str                   # 主文件绝对路径
    transcript_path: str | None # split_transcript=True 时的转录文件绝对路径，否则 None
    title: str                  # 视频标题
    ref: str                    # 原始请求 ref
    transcript_source: str      # "subtitle" | "asr"
    category: str | None        # LLM 分类子文件夹名；明确路径写入时为 None
    was_vague: bool             # True 表示发生了 LLM 路径分类
    proposed_new: bool          # True 表示 LLM 建议了一个新子文件夹
```

## 2. CLI
```bash
bilibili-crawl <ref> [--out PATH] [--json] [--profile NAME] [--config PATH]
```
退出码：`0` 成功 / `1` 通用错误（配置 / cookie / LLM）/ `2` `BilibiliEngineError`（转录失败）/
`3` `BiliNoteUnavailable`（BN 不可达）。

## 3. 支持的 ref 形式
与 `Engine/bilibili` 一致：BV id / `bilibili.com` URL / av id（见 `Engine/bilibili/docs/interface.md`）。

## 4. 依赖的上游接口
- **`Engine/bilibili`（SP-4a，冻结）：** `transcribe(ref, credential=None) -> BilibiliResult`，
  `result.render(RenderOptions(...))`；完整合约见 `Engine/bilibili/docs/interface.md`。
- **`jarvankb_common.LLMClient`（Engine/common，SP-3 冻结）：** `LLMClient(profile).complete(messages) -> str`。

## 5. 配置文件（`config.yaml`）
见 `config.example.yaml`：`output_root` / `cookie{base_url,uuid,password_env}` / `llm{profile}` /
`render{include_transcript,include_timestamps,split_transcript}` / `classify_snippet_chars`。引擎自身配置
（`config/bilibili-engine.yaml`）不在此处。真实 `config.yaml` 被 `.gitignore` 排除，密钥存 `.env`。
