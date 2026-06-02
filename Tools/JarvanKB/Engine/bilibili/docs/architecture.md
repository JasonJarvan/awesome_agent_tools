# Engine/bilibili — 内部架构（External Summary）

> 对外架构概要。模块私有细节见 `docs/RepoMem/architecture.md`。
> 权威设计：`docs/superpowers/specs/2026-05-31-SP-4a-bilibili-engine-design.md`。

## 设计要点

引擎主导的**字幕优先级联**：引擎自取元数据 + 字幕（`bilibili-api-python`），命中则把字幕作
`prefetched_transcript` 喂 BiliNote（BN 跳过下载 + ASR，只跑 LLM 总结，零 ASR 成本）；未命中则交 BN
下音频 + bcut ASR。BN 在 v1 是**硬依赖**（两条路都过 BN，保证每个视频都有总结，供 `split_transcript`
渐进式揭露的 index 层）。引擎自身**不调 LLM**。

## 单元（每个一职责；网络仅在 3 个单元）

| 单元 | 职责 | I/O |
|---|---|---|
| `url_parser` | BV id / URL / av id → 规范化 `VideoRef` | 纯 |
| `models` | dataclasses（凭据 / 段 / 转录 / 元数据 / 结果 / 配置 / 渲染选项与输出）| — |
| `metadata` | `parse_info`（纯）+ `_get_info_raw`（薄，`bilibili-api-python` get_info）→ `BilibiliMetadata` | 网络 |
| `subtitle` | `pick_track` / `parse_body` / `normalize_url`（纯）+ 薄拉取 → `Transcript?` | 网络 |
| `bilinote_client` | BN HTTP：health / push_cookie / generate_note / poll / transcribe | 网络 |
| `engine` | 编排级联 `BilibiliEngine.transcribe(...)` | — |
| `render` | prose 合并 / frontmatter / 时间戳 / split-index → `RenderedOutput` | 纯 |
| `config` | 读 `config/bilibili-engine.yaml` → `EngineConfig` | 文件 |
| `cli` | 手动测试薄壳 | — |

网络被隔离在 `metadata` / `subtitle` / `bilinote_client`，且各自拆成「薄拉取 + 纯解析器」，所以解析与
渲染逻辑全部可无网络单测（fixture 驱动）。

## 数据流

```
video_ref ─► url_parser ─► metadata.fetch ─► subtitle.fetch ─►
   ├─ 有字幕 ─► bilinote.transcribe(prefetched=字幕) ─► 总结（BN 只跑 LLM）
   └─ 无字幕 ─► bilinote.push_cookie（best-effort）─► bilinote.transcribe() ─► bcut ASR 转录 + 总结
                          └─► BilibiliResult ─► render ─► RenderedOutput（调用方落盘）
```

## v2+（不在 v1）

智能开关（超长自动 split / 按内容自动开时间戳）、BN 可选 + `summarize=False` 离线模式、多 P 全量、
结构化章节抽取 + 章节深链转录锚点。
