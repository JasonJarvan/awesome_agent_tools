# bilibili-watcher

> **SP-5b Bilibili 收藏夹监听服务** —— 一个常驻 daemon,定时轮询你的 B 站收藏夹,
> 发现新收藏的 UGC 视频就经冻结的 SP-4a Bilibili 引擎转录并存成 Markdown。无人值守、无交互。

## 做什么

- 按配置的间隔(默认 20min,可配)轮询 `folders` 里配置的 B 站**收藏夹**。
- 用 **`fav_time` 高水位线**(早停优化)+ **`bvid` seen-id 集合**(幂等兜底)双层去重:
  每个视频最多转录一次,且从不遗漏。
- 每个新 `type==2` UGC 视频:从 SP-1 CookieManager 拉最新 `bilibili.com` cookie(内存内解密,
  **绝不落盘明文**)→ 调 SP-4a 引擎 `engine.transcribe(bvid, credential=...)` → 存 Markdown 到配置的输出目录。
- 纯落盘,**无 LLM 分类、无 Obsidian/GBrain 语义**(那些归 SP-4b/SP-6/SP-7)。
- 非 `type==2` 条目(音乐、番剧、合集等)记日志跳过,不标 seen、不推水位。

## 输入

一份 YAML 配置(完整字段见 `interface.md` + `config/bilibili-watcher.example.yaml`):
- 轮询间隔、输出目录、状态目录;
- SP-1 连接(`base_url` / `uuid` / `password` / 可选 `auth_token`);
- SP-4a 引擎连接(`bn_base_url` / `provider_id` / `model_name`);
- `render` 渲染选项(transcript、timestamps、split_transcript);
- `folders` 列表:收藏夹 `id`(media_id)+ 可选 `name`(输出子目录名)。

## 输出

输出目录下,**每个收藏夹一个子目录**,每个成功转录的新视频一个 `.md` 文件:
- 文件名 = `<标题 sanitize>.md`,撞名追加 `_<bvid>`;
- 正文首行 `> https://www.bilibili.com/video/<bvid>`,其后是 SP-4a 引擎产出的主体 Markdown
  (BN AI 摘要 + 可读文字版转录);
- **无 YAML frontmatter**;封面/图片 URL 原样保留(不下载)。

## 怎么装

Docker compose(**起容器是 user 操作**,见 `runbook.md`):

```bash
cp config/bilibili-watcher.example.yaml config/bilibili-watcher.yaml   # 填好你的值
docker compose up -d --build
```

冒烟自测(单轮跑完即退,不起调度器):

```bash
python -m bilibili_watcher --once --config config/bilibili-watcher.yaml
```

## 依赖

- **SP-1 CookieManager**(`Service/crawl/cookie-manager/`):bilibili.com cookie 来源(主动拉取)。
- **SP-4a Bilibili 引擎**(`Engine/bilibili/`,冻结):bvid + BilibiliCredential → 转录 Markdown。本服务是纯消费者。
- **BiliNote(BN)**:引擎在 `http://127.0.0.1:3015` 上依赖的转录后端(USER 操作维护)。

## 另见

- 对外契约(配置 + CLI):`interface.md`
- 对外架构摘要:`architecture.md`
- 部署 / 排错:`runbook.md`
- 设计与实现计划:`docs/superpowers/{specs,plans}/2026-06-07-SP-5b-*`
