# bilibili-watcher — 对外架构摘要

> 面向使用者的架构概览。内部设计细节见 `RepoMem/architecture.md`;完整设计见
> `docs/superpowers/specs/2026-06-07-SP-5b-bilibili-watcher-design.md`。

## 一句话

一个同步的常驻 daemon:`BlockingScheduler` 每 N 分钟跑一轮「遍历所有配置的收藏夹」,
每轮对每个收藏夹做 拉 cookie → 列条目 → 双层去重 → 转录 → 落盘。

## 轮询一轮的数据流

```
APScheduler(BlockingScheduler, interval=N min, max_instances=1, coalesce)
  └─ watcher.run_cycle()
       cookies = cookie_provider.get_cookies()        # ① SP-1 GET + 内存解密(bilibili.com,瞬态)
       cred    = build_credential(cookies)             #    BilibiliCredential(sessdata, bili_jct)
       for 每个收藏夹:
         state = watermark_store.load(folder.id)       # ② 载入 {watermark, seen}
         items = favorites_client.list_items(          # ③ order=mtime 翻页,type==2 过滤,
                     folder.id, cookies,               #    fav_time 早停(<=watermark 停翻页),
                     since_fav_time=state.watermark)   #    has_more==False 结束
         for item in items:
           if item.bvid in state.seen: continue        #    seen-id 去重
           doc = fetcher.fetch(item.bvid, cred)        # ④ 冻结 SP-4a 引擎 → main_markdown
           if doc is None: continue                    #    失败→跳过,不标 seen(下轮重试)
           saver.save(...)                             # ⑤ 落盘(subfolder/title.md)
           state.seen.add(bvid); store.save(...)       # ⑥ 即时持久化 seen
         watermark_store.advance(...)                  # ⑦ §5 水位推进(有失败则保守回退)
```

## 组件(7 个,各自单一职责、可独立测试)

| 组件 | 职责 |
|---|---|
| `config` | 载入 + 校验 YAML 配置 → dataclass |
| `cookie_provider` | 从 SP-1 拉 `bilibili.com` cookie,内存内解密(legacy / aes-128-cbc-fixed),绝不落盘明文 |
| `favorites_client` | 列收藏夹条目(`/x/v3/fav/resource/list` order=mtime 翻页,type==2 过滤,`fav_time` 早停,`has_more` 结束) |
| `watermark_store` | 持久化每收藏夹 `{watermark, seen}` JSON,§5 保守推进规则,原子写 |
| `fetcher` | 包冻结 SP-4a 引擎,失败优雅降级返回 None(BN 宕机 → `BilibiliEngineError`) |
| `saver` | 落 Markdown(标题 sanitize、撞名加 bvid、`> url` 首行、无 frontmatter、远程图) |
| `watcher` | 编排一轮 + 接线真实组件(`build_watcher`);`__main__` 提供 CLI + 调度器 |

`watcher` 通过**依赖注入**接收各协作组件 → 整轮可用 fake 完整测试(去重 + 水位不变量有集成测试守护)。

## 水位机制(Δ2,SP-5a 无)

双层机制保证每个视频**最多转录一次、绝不遗漏**:

- **`fav_time` 高水位线**:order=mtime 返回列表按 fav_time 倒序,一旦遇到 `fav_time ≤ W` 即停翻页
  (早停优化,O(新条目) 而非 O(全量))。
- **`bvid` seen-id 集合**:幂等兜底,同一 bvid 无论何时出现都跳过。

水位推进规则(§5):无失败时推到本轮最新 fav_time;有失败时退到 `min(failed_fav_times) − 1`
以保证失败条目下轮仍可被列出重试。

## 健壮性(daemon 永不崩)

每个失败面都被捕获并继续:cookie 拉取失败 → 跳过本轮;某收藏夹列表失败 / 状态文件损坏 →
跳过该收藏夹;单条目 fetch/save 抛任何异常 → 记日志跳过该条目(不标 seen,下轮重试)。
`max_instances=1` 保证慢轮不叠加。

## 依赖边界

- **SP-1 CookieManager**:bilibili.com cookie 主动拉取(HTTP GET + 自解密)。
- **SP-4a Bilibili 引擎**(冻结):bvid + BilibiliCredential → 结构化 Markdown。本服务纯消费,不改引擎。
- **BiliNote(BN)**:引擎在 `127.0.0.1:3015` 上依赖的转录后端;BN 宕机则引擎报 `BiliNoteUnavailable`,
  本轮受影响视频不进 seen-set 等下轮重试。
- 不依赖、不内建:LLM、分类、Obsidian/GBrain/Thino、图片下载。
