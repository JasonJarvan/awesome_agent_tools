# zhihu-watcher — Runbook(部署 / 配置 / 排错)

> service 类模块必备。面向运维者(user)。

## 1. 起服务(USER 操作)

约定:**起 Docker 容器是 user 操作**(同 SP-1/SP-4a 先例)。implementer 只交付部署件。

```bash
cd Service/crawl/zhihu-watcher
cp config/zhihu-watcher.example.yaml config/zhihu-watcher.yaml
$EDITOR config/zhihu-watcher.yaml            # 填 SP-1 连接 + 收藏夹
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
- `collections`:你自己账号的收藏夹 id(或完整 URL)。`name` 决定输出子目录名。
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
| 日志 `listing collection <id> failed`(HTTP 403)| 收藏夹端点意外需要 `x-zse-96` 签名(2026-06 实测不需要)。**这是 blocker**:v1 不引签名器,需上报 |
| 日志 `listing ... failed`(网络)| 知乎不可达 / 该收藏夹私有且 cookie 无权限;检查直连(本服务 `trust_env=False`,不走系统代理) |
| 某条目反复抓不到 | SP-2 引擎对该 URL 抛 `ZhihuFetchError`;不标 seen,会一直重试。看引擎日志的 `attempts`/`status` |
| 重启后重复抓取 | `state_dir` 没持久化;挂卷 |

## 5. 查看 / 重置状态

- 看某收藏夹已抓了哪些:`cat data/state/seen-<collection_id>.json`(key=`type:id` 数组)。
- 重置某收藏夹去重(会重新全量抓取):删除对应 `seen-<id>.json`。
- 状态文件若损坏(非法 JSON):本服务会跳过该收藏夹并记 error,不会崩溃;修/删该文件即可。
