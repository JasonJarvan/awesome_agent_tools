# bilibili-watcher — Runbook(部署 / 配置 / 排错)

> service 类模块必备。面向运维者(user)。

## 1. 起服务(USER 操作)

约定:**起 Docker 容器是 user 操作**(同 SP-1/SP-4a 先例)。implementer 只交付部署件。

```bash
cd Service/crawl/bilibili-watcher
cp config/bilibili-watcher.example.yaml config/bilibili-watcher.yaml
$EDITOR config/bilibili-watcher.yaml            # 填 SP-1 连接 + engine + folders
docker compose up -d --build
docker compose logs -f                           # 看轮询日志
```

- 镜像从**仓库根**构建(`context: ../../..` = `Tools/JarvanKB/`),因为要把冻结的
  `Engine/bilibili`(SP-4a 引擎)和本服务一起拷进镜像安装。
- `network_mode: host`:**必须**,BN 在 `127.0.0.1:3015`,SP-1 在 `127.0.0.1:48088`,
  桥接网络无法直接访问宿主机 127 地址。
- 卷:`./config`(只读,放 `bilibili-watcher.yaml`)、`./data/state`(水位 + seen JSON,**必须持久**)、
  `./data/output`(落盘 Markdown)。`data/` 由 compose 首次运行时创建。

不用 Docker 也可直接跑(需先安装引擎和本包):

```bash
pip install -e Engine/bilibili && pip install -e Service/crawl/bilibili-watcher
python -m bilibili_watcher --config config/bilibili-watcher.yaml          # 常驻
python -m bilibili_watcher --once --config config/bilibili-watcher.yaml   # 单轮冒烟
```

## 2. 配置要点

完整字段见 `interface.md §3`。关键:

- `cookie_source`:指向你的 SP-1 CookieManager。`base_url` 用局域网/公网入口
  (见 `Service/crawl/cookie-manager/docs/interface.md §8`),`uuid`+`password` 是你的 CookieCloud 箱子。
  若箱子设了 `server.auth_token`,则同时填 `auth_token`。
- `engine.bn_base_url`:BiliNote 后端地址,默认 `http://127.0.0.1:3015`(宿主机端口,见 crawl-pipeline.md §B站链路)。
  `provider_id` 从 `GET /api/get_all_providers` 查;`model_name` 在 BN 中注册。
- `folders`:每项填 `id`(B 站收藏夹 media_id)+ 可选 `name`(输出子目录名)。
  id 从收藏夹页 URL 末段取,或 Stage-0 `list-all` API 查。
- `state_dir` 一定挂持久卷,否则重启后水位 + seen-id 丢失 → 重新全量转录。

## 3. 前置:BN 依赖(关键)

本服务的核心依赖是 **BiliNote(BN)** — SP-4a 引擎的转录后端,运行在 `127.0.0.1:3015`。

**BN 必须在服务启动前先跑起来**。BN 是 USER 操作(见 crawl-pipeline.md §B站链路)。
BN 宕机时,每个视频的转录请求都会抛 `BiliNoteUnavailable`,该视频**不**进 seen-set,
下轮 BN 恢复后自动重试。整个 daemon 不会崩,但不会有任何输出。

## 4. 前置:让 SP-1 里有新鲜的 bilibili.com cookie

本服务**不**自己登录 B 站,只从 SP-1 拉 cookie。确保:
1. SP-1 CookieManager 在跑且可达;
2. 你的浏览器 CookieCloud 扩展已把 **`bilibili.com`**(无前缀点)的 SESSDATA + bili_jct cookie 推到该箱子。
   自检:`cookie-manager show domain=bilibili.com`(在 SP-1 主机上)应能打印 SESSDATA。

## 5. 常见故障

| 现象 | 可能原因 / 处理 |
|---|---|
| 日志 `cookie pull failed` 或解密报错 | `base_url`/`uuid`/`password` 不对,或箱子 `crypto_type` 与口令不匹配;校对 SP-1 配置。本轮跳过,下轮重试 |
| 日志 `no bilibili.com SESSDATA available` | SP-1 箱子里还没有 `bilibili.com` cookie;先用浏览器扩展推一次 |
| API 返回 `code=-101`(账号未登录) | SESSDATA 已过期;刷新 B 站登录状态,让 CookieCloud 扩展重新推 cookie |
| 日志 `listing folder <id> failed`(HTTP 非 200 或 code!=0) | cookie 过期、网络不通、收藏夹私有且无权访问;检查 cookie 有效性 + 直连(本服务 `trust_env=False`) |
| `BiliNoteUnavailable` / `BN down` | BN 后端未启动或地址有误;检查 `engine.bn_base_url` + BN 服务状态。受影响视频下轮自动重试 |
| 某视频反复转录失败 | SP-4a 引擎对该 bvid 抛 `TranscriptionFailed`(bvid 失效/视频不可访问);不标 seen,会持续重试。检查引擎日志 |
| 重启后重复转录 | `state_dir` 没持久化;挂卷 |
| 文件数比收藏夹条目少 | 非 `type==2` 条目(音乐/番剧/合集)被过滤,属预期行为 |

## 6. 查看 / 重置状态

- 看某收藏夹已处理状态:`cat data/state/state-<folder_id>.json`(watermark + seen bvid 数组)。
- 重置某收藏夹(重新全量转录):删除对应 `state-<id>.json`。
- 状态文件若损坏(非法 JSON):本服务会跳过该收藏夹并记 error,不会崩溃;修/删该文件即可。
