# v1.1 收藏夹监听服务 — 运维手册(知乎 + B站)

> 给运维者(你)的日常操作手册。两个常驻 daemon:自动把你**新收藏**的知乎条目 / B站视频抓成
> Markdown 落进 Obsidian 仓库。**已于 2026-06-19 部署并验证上线。**
>
> | 服务 | 工作目录 | 容器名 | 输出到 Obsidian | 轮询 | 监听端口 |
> |---|---|---|---|---|---|
> | 知乎 watcher | `Service/crawl/zhihu-watcher` | `jarvankb-zhihu-watcher` | `…/ResourceBase资源库/Zhihu知乎` | 30 分钟 | **无**(纯外拨) |
> | B站 watcher | `Service/crawl/bilibili-watcher` | `jarvankb-bilibili-watcher` | `…/ResourceBase资源库/BiliB站` | 30 分钟 | **无**(纯外拨) |
>
> 本次按你的决定用 **from-now(只抓新收藏)**:历史收藏(知乎 ~2000+ 条 / B站 ~231 视频)**不回填**;
> 从部署时刻起,你**新收藏**的内容会在下一轮被自动抓取入库。

---

## 1. 起 / 停 / 重启 / 看状态

每个服务在自己的工作目录里用 `docker compose`(命令必须在该目录下执行):

```bash
cd Service/crawl/zhihu-watcher        # 或 Service/crawl/bilibili-watcher
docker compose up -d                  # 起(已在跑则免)
docker compose restart                # 改完配置后重启生效
docker compose down                   # 停(容器删除;state/output 卷保留)
docker compose ps                     # 看本服务状态
```

全局快速看两个容器:

```bash
docker ps --filter name=jarvankb-zhihu-watcher --filter name=jarvankb-bilibili-watcher
```

> 改了 `config/*.yaml` 后必须 `docker compose restart` 才生效。改了 `Dockerfile` / 依赖代码,要 `docker compose up -d --build`。

## 2. 看日志 / 判断「它在干活吗」

```bash
cd Service/crawl/zhihu-watcher        # 或 bilibili-watcher
docker compose logs -f                # 实时跟随
docker compose logs --tail=50         # 看最近 50 行
```

**正常长这样**(每轮一行 summary):
- 知乎:`collection <id> (<名字>): N new item(s)` —— 每个收藏夹一行。
- B站:`folder <id> (<名字>): N new, watermark=…` —— 每个收藏夹一行;`early-stop at fav_time<=watermark` 表示该夹没有更新的收藏(正常)。

**判断健康的两个不变量(本次已验证):**
1. **首次落盘**:当你新收藏一条后,下一轮日志该收藏夹会出现 `1 new`,对应 Obsidian 子目录里多一个 `.md`。
2. **去重**:同一条**只会落一次**。再下一轮该条不会重复(知乎靠 seen-set / classify 靠 ledger;B站靠 watermark + bvid seen-set)。

落盘位置:`<上表的 Obsidian 目录>/<收藏夹名>/<标题>.md`。文件首行是原始 URL,无 frontmatter。

## 3. 必须在跑的依赖

| 依赖 | 地址 | 作用 | 自检 |
|---|---|---|---|
| cookie-manager (SP-1) | `127.0.0.1:48088` | 两个 watcher 每轮从这里拉 cookie(box `jasonjarvan`) | `docker ps \| grep cookie-manager` |
| BiliNote (BN) | `127.0.0.1:3015` | **仅 B站**:下载音频 + 字幕/ASR + LLM 总结 | `curl -s http://127.0.0.1:3015/api/sys_check` → `{"code":0,...}` |

> 这两个端口只是 watcher 的**外拨目标**,watcher 自己不监听任何端口。宿主监听服务遵循 **48xxx** 约定
> (cookie-manager 占 `:48088`);本次没有新增任何监听端口。BN 的 `:3015` 早于该约定,沿用。

**cookie 新鲜度(很关键,两类不同):**
- **B站 SESSDATA**:由宿主 cron `bn-cookie-sync.py`(每 30 分钟)自动同步进 BN 并按需重启 BN,无需你管。
  日志在 `~/.local/state/jarvankb/bn-cookie-sync.log`。
- **知乎 `__zse_ck`**:**没有自动续期**。它会随时间过期,过期后知乎专栏/部分文章抓取开始 **403**。
  续期靠**浏览器 CookieCloud 扩展**把新鲜的 `.zhihu.com` cookie 推到 box `jasonjarvan`(背景:UN-032)。
  现象:日志大量 `listing/fetch ... 403` → 去浏览器让扩展重推一次知乎 cookie。

## 4. 增 / 删监听的收藏夹 · 改轮询间隔

改对应的 `config/<svc>-watcher.yaml`(**gitignored,含 box 口令,切勿提交**),然后 `docker compose restart`。

**知乎** `config/zhihu-watcher.yaml`:
- 改间隔:`poll_interval_minutes: 30`。
- 监听范围:`targets:` 里
  - `type: user, url_token: me` —— 自动发现你账号下**所有具名收藏夹**(无需逐个列;新建的下一轮自动纳入)。
  - `type: collection, id: "721323262", classify: true` —— 默认收藏夹「我的收藏」,**自动分类**进已有的 ~33 个子目录之一。
- 不想分类、想原样平铺某夹:加一条 `type: collection, id: "<id>", name: "<子目录名>"`(不带 `classify`)。

**B站** `config/bilibili-watcher.yaml`:
- 改间隔:`poll_interval_minutes: 30`。
- 监听范围:`folders:` 是**显式列表**(B站 watcher **不**支持自动发现全部)。本次已列你**全部 22 个**收藏夹。
  - 新建了 B站收藏夹想纳入 → 在 `folders:` 加 `- id: "<media_id>"` + `name: "<子目录名>"`。`media_id` 取收藏夹页 URL 末段。
  - 注:你有两个都叫「效率工具」的收藏夹(id 2391175167 / 2189619267),它们会**合并**写进同一个 `效率工具/` 子目录(正常,可接受)。

> 增删收藏夹**不会**回填该夹历史(from-now)。想要某夹回填全部历史:删掉它的 state 文件再重启 ——
> 知乎删 `data/state/seen-<id>.json`;B站删 `data/state/state-<id>.json`(会**重新全量抓取/转录**该夹,慎用)。

## 5. 失败行为(daemon 永不崩,失败自动退避/重试)

- **知乎**:某条抓取失败 → 不标记 seen,下轮重试;连续失败 `max_consecutive_failures`(默认 3)次 → 进入
  `failure_cooldown_hours`(默认 24h)冷却;累计失败 `circuit_break_threshold`(默认 10)次 → 永久跳过并
  写进 **关注清单** `<Zhihu知乎>/_zhihu-watcher-attention.md`(定期看一眼这个文件即可)。
  - **专栏文章(zhuanlan)全文 403 是已知 best-effort**(引擎无签名器);不影响回答/其他类型条目。
- **B站**:某视频转录失败 → 不标记 seen,watermark 守在失败条目下方,**下轮自动重试**;整夹/整 daemon 不受影响。

## 6. 常见故障速查

| 现象 | 处理 |
|---|---|
| 日志 `cookie pull failed` / `Connection refused` | cookie-manager 没起或不可达;`docker ps` 看 `cookie-manager` |
| 知乎大量 `403` | `__zse_ck` 过期 → 浏览器 CookieCloud 扩展重推知乎 cookie(§3) |
| B站 `code=-101` 账号未登录 | SESSDATA 过期 → 让扩展重推 B站 cookie;cron 会自动同步进 BN |
| B站 `BiliNoteUnavailable` / `BN down` | BN 没起;到 `Engine/bilibili/deploy/bilinote` 里 `docker compose up -d`,`curl …/api/sys_check` 自检 |
| B站 `HTTP 412` 下载失败 | BN downloader cookie 失效;cron `bn-cookie-sync.py` 会自动修;手动:见 `bilibili-watcher/docs/runbook.md §5` 的 SOP |
| **B站 `401 Invalid API Key`** | **BN 的 MiMo 供应商 key 失效**(本次部署时遇到过,已刷新)。重刷:见下方「BN key 刷新」 |
| B站 `上传提交失败: 第三方服务异常` | bcut 云端 ASR 对**个别无字幕视频**报错(部署时实测某购物视频如此);属 BN/bcut 侧、**非 watcher bug**。有字幕的视频走字幕、零 ASR 成本;该条会下轮重试,不影响其他视频 |
| 重启后重复抓取 | `state_dir` 没持久化(本次已挂卷,正常不会发生) |

**BN key 刷新**(当 B站转录报 `401 Invalid API Key` 时):BN 给 MiMo 供应商存了一份独立的 api_key,会过期。
用 repo 根 `.env` 里有效的 `MIMO_API_KEY` 刷新它(localhost、可逆):
```bash
# 用 .env 里的 MIMO_API_KEY 调 BN /api/update_provider 更新 xiaomitokenplan 供应商;不要把 key 打到屏幕上
PID=cf11f2fc-42ac-4d44-871d-fbb282a2fe0b
KEY=$(grep '^MIMO_API_KEY=' .env | cut -d= -f2-)
curl -s -X POST http://127.0.0.1:3015/api/update_provider -H 'Content-Type: application/json' \
  -d "{\"id\":\"$PID\",\"api_key\":\"$KEY\"}"        # 期望 {"code":0,"msg":"更新模型供应商成功",...}
```
(B站用的模型是 BN 注册的 `mimo-v2.5`;知乎分类用 `config/llm.yaml` 的 `mimo` 档,同样指向 `mimo-v2.5`。)

## 7. 这事以后归谁管

**watcher 运维域 → ReachOrche**(reach 层)。本次由 root 完成首发部署;后续的 watcher 运维/扩展归 ReachOrche。
权威排错细节见各自 `docs/runbook.md` 与 `docs/RepoMem/persist/architecture/crawl-pipeline.md §B站链路 / §知乎链路`。
