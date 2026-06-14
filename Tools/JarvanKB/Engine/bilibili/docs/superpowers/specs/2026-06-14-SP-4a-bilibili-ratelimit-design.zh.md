# SP-4a Bilibili 引擎 v1.x — 限流加固设计（镜像 SP-2 知乎 v1.2）

> 压缩版 brainstorm（handoff §3：只确认节流点形状 + 配置入口 + 默认值，不重新论证「要不要做」）。
> 模板 = SP-2 知乎 v1.2（`Engine/zhihu/src/zhihu/fetcher.py` + `docs/superpowers/plans/2026-06-09-zhihu-ratelimit-hardening-plan.md`）。
> 任务 slug = `bilibili-engine-ratelimit-hardening`。Lane: **full**（引擎模块改动、新增公开面 `configure`、产出 §B站链路 提升）。

## 1. 目标与边界

在引擎**面向 bilibili.com 的出站节流点**加「主动限流 + 节流退避」,**非破坏性**,使 SP-4b（Skill）与
SP-5b（Watcher）经引擎自动继承,无重复。这是**预防性**加固,不是修任何已坏的东西——BN-412 已确认与
此无关（playurl 匿名鉴权 + BN cookie 单例,位于引擎请求路径之下,已修,UN-035）。

**不做:**
- 不碰 v1 冻结契约(`BilibiliEngine`/`transcribe()`/`BilibiliCredential`/`EngineConfig`/`RenderOptions`/
  `result.render()`/dataclass 字段名,见 `interface.md §3`)——只**新增**入口,不改签名。
- 不碰 BN 容器 / BN-412(独立、已修)。
- 不碰 SP-4b / SP-5b(经引擎继承)。

## 2. 节流点形状(决策 1)

引擎有**三条面向 bilibili.com 的直连出站调用**,均经一个新模块 `src/bilibili/ratelimit.py` 收口:

| 调用点 | 位置 | 协议 | 节流时的表现 |
|---|---|---|---|
| `get_info`(元数据) | `metadata._get_info_raw` | bilibili-api-python(异步,`asyncio.run`) | **抛异常** `ResponseCodeException`/`NetworkException` |
| `get_subtitle`(字幕轨) | `subtitle._get_tracks_raw` | bilibili-api-python(异步) | **抛异常** 同上 |
| 字幕正文 CDN GET | `subtitle._get_body_raw` | 裸 `httpx.get` + `raise_for_status()` | **抛** `httpx.HTTPStatusError` |

与 SP-2 的关键差异:**B站调用是「抛异常」而非「返回 `Response`」**,所以收口形状不是 SP-2 的
`_request() -> Response`,而是一个**包装任意 callable 的** `paced(fn)`:

- `_RateLimiter` —— 进程共享最小间隔 pacer,**与 SP-2 逐字一致**(可注入 `_now/_sleep/_rand`、
  `threading.Lock`、慢请求不二次等待 ⇒ 单 URL 首调不等待、突发被平滑)。
- `paced(fn)` —— 每次尝试前 `_limiter.acquire(...)`,跑 `fn()`;遇**节流异常**则退避(指数,遵从
  `Retry-After`)重试;**非节流异常立即原样抛出**(行为不变 ⇒ 412/凭据错误照旧穿透 → 现有 ASR
  降级路径完全不变)。

收口位置 = 各调用现有的 thin wrapper **内部**,因此函数签名、以及现有打桩这些 wrapper 的测试
(`test_metadata`/`test_subtitle`)**都不动**。

**`bilinote_client.py` 的 BN 本地调用不限流(刻意,且与 handoff §1 字面表述偏离):**
依据 `<root>/docs/RepoMem/persist/architecture/crawl-pipeline.md §B站链路`——412/下载是 BN 内部
yt-dlp/playurl,**位于引擎请求路径之下**;引擎自身 bilibili-api 调用(view/subtitle)本就 200,
*「引擎侧限流/反风控与此无关」*。理由二分:
- BN 调用是**本地 `127.0.0.1` 调用,不是 bilibili 调用** —— 给它们加 pace 只增延迟、护不到 bilibili;
- BN 内部对 bilibili 的下载(playurl)我们**无法注入限流**,且其节奏已被 `transcribe()` 频率天然限住
  (每次 transcribe 仅触发一次 BN 下载,而 transcribe 首步 `get_info` 已被限流)。

handoff §1 列了 BN 调用但同时声明 *"confirm by reading — don't trust me blindly"*,本设计据架构记忆
确认后排除之。

## 3. 配置入口(决策 2)

`bilibili.configure(*, min_interval, jitter, max_retries, backoff_base, throttle_codes,
retry_http_statuses, enabled)`,从 `__init__.py` 导出,**镜像** `zhihu.configure(...)`。纯增量、
进程级、与 `fetch`/`transcribe` 并列加进 `__all__`。`configure(enabled=False)` 一键关闭限流+重试。

## 4. 默认值 + 节流信号(决策 3)

`_Config` 默认值**镜像已上线的知乎值**:

```python
min_interval = 0.3      # 请求间最小间隔(秒)
jitter       = 0.2      # 每次等待叠加 U(0, jitter)
max_retries  = 3        # 节流时反应式重试次数
backoff_base = 0.5      # backoff = base * 2**attempt (+ jitter)
throttle_codes      = frozenset({-509, -799})   # bilibili「请求过于频繁」类业务码
retry_http_statuses = (429,)                     # HTTP 429
enabled      = True
```

**节流分类器 `_throttle_signal(exc) -> (is_throttle, retry_after|None)`**(鸭子类型,`ratelimit.py`
**不硬 import bilibili_api**,对库版本漂移更稳):
- `httpx.HTTPStatusError` 且 `status in retry_http_statuses` → `(True, 解析 Retry-After 头)`;
- 否则 `getattr(exc,"status",None) in retry_http_statuses`(库的 `NetworkException.status`)→ `(True, None)`;
- 否则 `getattr(exc,"code",None) in throttle_codes`(库的 `ResponseCodeException.code`)→ `(True, None)`;
- 其余一律 `(False, None)` → 立即抛出、不重试。

**`412` 明确不视作节流**(鉴权/BN 内部信号,handoff §1 + 架构记忆)——既不在 `retry_http_statuses`、
也不在 `throttle_codes`,故经分类器自然穿透。`-101`(未登录/凭据)同理穿透 → 现有 `CredentialError` 路径不变。

`Retry-After` 解析复用 SP-2 的 `_retry_after_seconds`(delta-seconds 或 HTTP-date)。

## 5. 单 URL 无延迟(验收关键)

- 新进程**首个** bilibili 调用 `_last≈0` ⇒ 不等待(SP-2 同理)。
- 单次 `transcribe()`:ASR 路径(无 SESSDATA)只有 `get_info` 一次直连 ⇒ **零额外延迟**;字幕命中路径
  有 `get_info`→`get_subtitle`→正文 三次,后两次各至多等 `min_interval(+jitter)` ⇒ 额外 ≤ ~2×0.4≈0.8s,
  被 BN 的 LLM 总结(数秒~分钟级)淹没 ⇒ *「~无感」*(与 SP-2 同一验收口径:首调不等待 + 总开销远小于主耗时)。

## 6. 测试策略(TDD,镜像 SP-2 的 67 测覆盖,适配「抛异常」语义)

B站模块**无 pytest-httpx**(只 `pytest`),现有测试用 `unittest.mock.patch` + 本地 fixture。新测试同风格:
- 限流:`_RateLimiter` 二次调用被 pace、足够时间已过则不等待(injectable clock,复制 SP-2)。
- 分类器:429 httpx、`NetworkException(status=429)`、`ResponseCodeException(code=-509)` → throttle;
  `code=-412`/`-101`/通用异常 → 非 throttle。
- `paced()`:429 后重试成功、`-509` 后重试成功、遵从 `Retry-After`、非节流(412)**立即抛出且只调 1 次**、
  超 `max_retries` 后抛最后一次。
- 配置:`configure()` 改 `_cfg`、默认值保守。
- 接线:`_get_body_raw` 经 monkeypatch `httpx.get` 验证 429 重试;`_get_info_raw`/`_get_tracks_raw`
  经 spy `paced` 验证「确实路由经 paced」。
- 非破坏:`test_public_api` 扩展——契约符号仍可导入 + `configure` 新增可导入。
- `conftest.py`(新建)autouse fixture:重置 `_limiter` + `enabled=False` + `_sleep` 置空,
  使现有 59 测保持快/确定;节流测试显式 `configure(enabled=True)` opt-in。

## 7. 验证门(verification-before-completion)

- 全单测绿(59 基线 + 新增),`PYTHONPATH=src python3 -m pytest -q`(worktree 内必须 `PYTHONPATH=src`
  覆盖 editable-install 指向主 worktree 的坑)。
- **真实 smoke**(BN 在 `127.0.0.1:3015`):
  1. 默认 `configure()` 开启下,连续触发引擎 bilibili 直连调用,日志显示请求起始间隔 ≥ `min_interval`(限流可观测生效);
  2. 新进程首调不等待 + 单次 `transcribe()` 端到端转录成功、额外延迟 ≤ ~1s;
  3. 不强造 429;若自然出现则确认经退避自愈(记 attempts)。

## 8. 文档与 Step-8

- `docs/interface.md` 增「内置限流与重试(v1.x,非破坏性)」节(镜像 zhihu `§11`):限流仅覆盖引擎
  **bilibili 直连**调用、BN 本地调用不在内、412 不当节流、`bilibili.configure(...)` 可调可关。
- Step-8(impler 自闭环):机制留在代码;模块特定 → `Engine/bilibili/docs/RepoMem/decisions.md`(新 D 条,
  镜像知乎 D8);**跨 SP 可复用**的 B站节流根因/坑(哪些码=throttle、真实 Retry-After 行为)→ 提升到
  `crawl-pipeline.md §B站链路`(HITL)。

## 9. 自检

- 覆盖:主动限流(§2)+ 节流退避遵从 Retry-After(§4)+ 3 处直连全收口(§2)+ 非破坏(无签名改动)+
  可配置(§3)+ 文档(§8)。✓
- 与 SP-2 唯一形状差异 = `paced(fn)` 包 callable(因 B站抛异常)而非 `_request()->Response`,已说明。✓
- BN 排除有架构记忆背书,非拍脑袋。✓
