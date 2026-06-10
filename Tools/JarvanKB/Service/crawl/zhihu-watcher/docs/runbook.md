# zhihu-watcher — Runbook(部署 / 配置 / 排错)

> service 类模块必备。面向运维者(user)。

## 1. 起服务(USER 操作)

约定:**起 Docker 容器是 user 操作**(同 SP-1/SP-4a 先例)。implementer 只交付部署件。

```bash
cd Service/crawl/zhihu-watcher
cp config/zhihu-watcher.example.yaml config/zhihu-watcher.yaml
$EDITOR config/zhihu-watcher.yaml            # 填 SP-1 连接 + targets
docker compose up -d --build
docker compose logs -f                        # 看轮询日志
```

- 镜像从**仓库根**构建(`context: ../../..` = `Tools/JarvanKB/`),因为要把冻结的
  `Engine/zhihu`(SP-2 引擎)和本服务一起拷进镜像安装。
- 卷:`./config`(只读,放 `zhihu-watcher.yaml`)、`./data/state`(seen-id JSON,**必须持久**)、
  `./data/output`(落盘 Markdown)。`data/` 由 compose 首次运行时创建。

不用 Docker 也可直接跑(需先 `pip install Engine/zhihu` 再 `pip install .`):

```bash
python -m zhihu_watcher --config config/zhihu-watcher.yaml          # 常驻
python -m zhihu_watcher --once --config config/zhihu-watcher.yaml   # 单轮冒烟
```

## 2. 配置要点

完整字段见 `interface.md §3`。关键:
- `cookie_source`:指向你的 SP-1 CookieManager。`base_url` 用局域网/公网入口
  (见 `Service/crawl/cookie-manager/docs/interface.md §8`),`uuid`+`password` 是你的 CookieCloud 箱子。
- `targets`:替代旧版 `collections`,支持两种类型:
  - `type: collection`:显式指定单个收藏夹 id 或完整 URL;`name` 决定输出子目录名(建议与已有
    子目录名对齐)。
  - `type: user`:自动发现该用户所有具名收藏夹;`url_token: me` 使用当前 cookie 对应账号。
    `skip_empty: true`(默认)跳过空收藏夹;`include_default: false`(默认)跳过"我的收藏"。
- `only_after`:可选 ISO 8601 带时区偏移时间戳(如 `2026-01-01T00:00:00+08:00`),只保存此后
  收藏的条目,用于跳过历史回填。**必须带时区偏移**。
- `backfill_on_first_run`:默认 `false`——首次见到收藏夹时记"从现在起"基线,已有历史不回填;
  设为 `true` 则全量抓取历史。
- `max_consecutive_failures` / `failure_cooldown_hours`:连续失败 N 次后触发退避冷却(默认 3 次
  / 24 小时)。**专栏文章(zhuanlan)全文因引擎缺签名器会 403,是 best-effort,靠此退避限制
  无效重试消耗。**
- `state_dir` 一定挂持久卷,否则重启后 seen-id 丢失 → 重新全量抓取。

## 3. 前置:让 SP-1 里有新鲜的 .zhihu.com cookie

本服务**不**自己登录知乎,只从 SP-1 拉 cookie。确保:
1. SP-1 CookieManager 在跑且可达;
2. 你的浏览器 CookieCloud 扩展已把 `.zhihu.com` 的 cookie 推到该箱子(uuid/password 对应)。
   自检:`cookie-manager show domain=.zhihu.com`(在 SP-1 主机上)应能打印 cookie。

## 4. 常见故障

| 现象 | 可能原因 / 处理 |
|---|---|
| 日志 `cookie pull failed` 或解密报错 | `base_url`/`uuid`/`password` 不对,或箱子 `crypto_type` 与口令不匹配;校对 SP-1 配置。本轮跳过,下轮重试 |
| 日志 `no .zhihu.com cookies` | SP-1 箱子里还没有 `.zhihu.com` cookie;先用浏览器扩展推一次 |
| 日志 `listing collection <id> failed`(HTTP 403)| 收藏夹列表端点意外需要签名(v1.1 不引签名器)。连续失败 `max_consecutive_failures` 次后触发冷却(`failure_cooldown_hours`),冷却结束后自动重试。**专栏文章(zhuanlan)全文属于已知 best-effort**,不影响其他类型条目 |
| 日志 `listing ... failed`(网络)| 知乎不可达 / 该收藏夹私有且 cookie 无权限;检查直连(本服务 `trust_env=False`,不走系统代理) |
| 某条目反复抓不到 | SP-2 引擎对该 URL 抛 `ZhihuFetchError`;不标 seen,会一直重试。看引擎日志的 `attempts`/`status` |
| 重启后重复抓取 | `state_dir` 没持久化;挂卷 |

## 5. 查看 / 重置状态

- 看某收藏夹已抓了哪些:`cat data/state/seen-<collection_id>.json`(key=`type:id` 数组)。
- 重置某收藏夹去重(会重新全量抓取):删除对应 `seen-<id>.json`。
- 状态文件若损坏(非法 JSON):本服务会跳过该收藏夹并记 error,不会崩溃;修/删该文件即可。
