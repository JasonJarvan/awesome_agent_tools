# zhihu-watcher — 对外架构摘要

> 面向使用者的架构概览。内部设计细节见 `RepoMem/architecture.md`;完整设计见
> `docs/superpowers/specs/2026-06-02-SP-5a-zhihu-watcher-design.md`。

## 一句话

一个同步的常驻 daemon:`BlockingScheduler` 每 N 分钟跑一轮「遍历所有配置的收藏夹」,
每轮对每个收藏夹做 拉 cookie → 列条目 → 去重 → 抓取 → 落盘。

## 轮询一轮的数据流

```
APScheduler(BlockingScheduler, interval=N min, max_instances=1, coalesce)
  └─ watcher.run_cycle()
       cookies = cookie_provider.get_cookies()        # ① SP-1 GET + 内存解密(瞬态)
       for 每个收藏夹:
         items = favorites_client.list_items(id, cookies)   # ② offset 翻页(无签名,直连)
         seen  = watermark_store.load(id)              # ③ 载入 seen-id 集合
         for item in items:
           if item.key in seen: continue              #    去重
           doc = fetcher.fetch(item.url, cookies)      # ④ 调冻结 SP-2 引擎
           if doc is None: continue                    #    失败→跳过,不标 seen(下轮重试)
           saver.save(...)                             # ⑤ 落盘(参考 repo 格式)
           seen.add(item.key); watermark_store.save(id, seen)   # ⑥ 每条成功后即时持久化
```

## 组件(7 个,各自单一职责、可独立测试)

| 组件 | 职责 |
|---|---|
| `config` | 载入 + 校验 YAML 配置 → dataclass |
| `cookie_provider` | 从 SP-1 拉 `.zhihu.com` cookie,内存内解密(legacy / aes-128-cbc-fixed),绝不落盘明文 |
| `favorites_client` | 列收藏夹内条目(`/api/v4/collections/{id}/items` offset 翻页,跟 `is_end` 兜底),纯 cookie 无签名、`trust_env=False` 直连 |
| `watermark_store` | 持久化 seen-id 集合(每收藏夹一份 JSON,原子写) |
| `fetcher` | 包冻结 SP-2 `zhihu.fetch`,失败优雅降级返回 None |
| `saver` | 落 Markdown(标题 sanitize、撞名加 url_id、`> url` 首行、无 frontmatter、远程图) |
| `watcher` | 编排一轮 + 接线真实组件(`build_watcher`);`__main__` 提供 CLI + 调度器 |

`watcher` 通过**依赖注入**接收各协作组件 → 整轮可用 fake 完整测试(去重不变量有集成测试守护)。

## 健壮性(daemon 永不崩)

每个失败面都被捕获并继续:cookie 拉取失败 → 跳过本轮;某收藏夹列表失败 / 状态文件损坏 →
跳过该收藏夹;单条目 fetch/save 抛任何异常 → 记日志跳过该条目(不标 seen,下轮重试)。
`max_instances=1` 保证慢轮不叠加。

## 依赖边界

- **SP-1 CookieManager**:cookie 主动拉取(HTTP GET + 自解密)。
- **SP-2 知乎引擎**(冻结):URL + cookie → 结构化 Markdown。本服务纯消费,不改引擎。
- 不依赖、不内建:LLM、分类、Obsidian/GBrain/Thino、图片下载。
