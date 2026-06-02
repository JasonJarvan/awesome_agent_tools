# Engine/bilibili — 对外契约（Interface）

> SP-4a Bilibili Engine 的稳定公开接口。下游需要转录的子项目（SP-4b B站 Skill、SP-5b B站 Watcher）
> 按本文件集成，不要依赖内部实现细节。
> 权威设计：`docs/superpowers/specs/2026-05-31-SP-4a-bilibili-engine-design.md`。

## 1. 它是什么

给一个 B站视频引用（BV id / `bilibili.com` URL / av id），返回**元数据 + 转录**（字幕优先，回退
BiliNote + bcut ASR）+ BiliNote 的 **AI 总结**（best-effort）。引擎是自托管 **BiliNote（BN）** 的
HTTP 客户端；引擎自身**不调 LLM**（BN 在其内部流水线里调）。

## 2. 安装与导入

src-layout 包。`pip install -e .`（或 `.[dev]`）后：

```python
from bilibili import (
    BilibiliEngine, BilibiliCredential, EngineConfig, RenderOptions,
    BilibiliResult, transcribe, BilibiliEngineError,
)
```

## 3. 公开 API（v1 冻结契约）

```python
cred = BilibiliCredential(sessdata="...", bili_jct=None, buvid3=None)  # sessdata 必填，余可选

engine = BilibiliEngine.from_config()        # 读 config/bilibili-engine.yaml
# 或显式: BilibiliEngine(EngineConfig(bn_base_url=..., provider_id=..., model_name=...))

result = engine.transcribe("BV1xx...", credential=cred)
result.metadata.title           # str
result.metadata.cid             # int
result.transcript.source        # "subtitle" | "asr"
result.transcript.language      # str | None
result.transcript.full_text     # str
result.transcript.segments      # list[TranscriptSegment(start, end, text)]
result.summary_markdown         # str | None（BN 的 AI 笔记；章节以标题内嵌其中）

rendered = result.render(RenderOptions(
    include_transcript=True, include_timestamps=False, split_transcript=False, slug=None))
rendered.main_markdown          # str
rendered.transcript_markdown    # str | None（仅 split_transcript=True 时非空）
rendered.suggested_names        # {"main": "<slug>.md", "transcript": "<slug>.transcript.md"}

# 便捷函数：构造默认引擎并转录，返回 BilibiliResult
md = transcribe("BV1xx", credential=cred).to_markdown()
```

**稳定性**：构造器、`BilibiliCredential`、`EngineConfig`、`RenderOptions`、`transcribe()`、
`engine.transcribe()`、`result.render()` / `to_markdown()`，以及上述 dataclass 字段名 = v1 冻结契约。
内部实现可自由变动。

## 4. 渲染开关

| 开关 | 默认 | 作用 |
|---|---|---|
| `include_transcript` | `True` | 是否含转录正文 |
| `include_timestamps` | `False` | `False` → segments 合并成**可读段落**（确定性启发式，无 LLM）；`True` → `[mm:ss] …` 列表 |
| `split_transcript` | `False` | `True` → 主文件 = frontmatter + 总结（index）+ 转录文件链接；转录正文进 `transcript_markdown`（渐进式揭露）|

引擎**不写盘**：`render()` 返回内容（`RenderedOutput`），由调用方按 `suggested_names` 落盘。

## 5. 凭据与 cookie 边界

引擎接收**结构化** `BilibiliCredential` 作 input，**不自取 cookie**。`sessdata` 喂
`bilibili-api-python`（元数据 + 字幕）；ASR 路径会 best-effort 把 cookie 推给 BN（覆盖会员/付费视频的
音频下载）。下游 SP-4b/5b 从 SP-1 cookie-manager（`domain=.bilibili.com`，见
`Service/crawl/cookie-manager/docs/interface.md`）取凭据再注入——引擎不依赖 SP-1。

## 6. 错误

`BilibiliEngineError` 基类 → `InvalidVideoRef` / `CredentialError` / `BiliNoteUnavailable`（BN 不可达，
即 Stage-3 gate）/ `TranscriptionFailed`（BN 任务 FAILED）/ `TranscriptionTimeout`（轮询超时）。
字幕路径无字幕轨**不是错误**——是触发 ASR 回退的正常信号。

## 7. 依赖 BiliNote

需一个可达的自托管 BiliNote 实例（`TRANSCRIBER_TYPE=bcut`）。部署见 `deploy/bilinote/`（起容器是用户
操作）。引擎配置 `config/bilibili-engine.yaml`（从 `config/bilibili-engine.example.yaml` 复制，填
`provider_id`）。
