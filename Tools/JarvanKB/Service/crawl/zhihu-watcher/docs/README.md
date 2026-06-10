# zhihu-watcher

> **SP-5a 知乎收藏夹监听服务** —— 一个常驻 daemon,定时轮询你的知乎收藏夹,
> 发现新收藏的内容就经冻结的 SP-2 知乎引擎抓取并存成 Markdown。无人值守、无交互。

## 做什么

- 按配置的间隔(默认 45min,可配 30–60)轮询 `targets` 里配置的知乎**收藏夹**。
- 用持久化的 **seen-id 集合**去重:只处理还没见过的条目,绝不重复抓取。
- 每个新条目:从 SP-1 CookieManager 拉最新 cookie(内存内解密,**绝不落盘明文**)→ 调
  SP-2 引擎 `zhihu.fetch(url, cookies)` → 存 Markdown 到配置的输出目录。
- 纯落盘,**无 LLM、无分类、无 Obsidian/GBrain 语义**(那些归 SP-6/SP-7)。
- **专栏文章(zhuanlan)全文不可抓取**:知乎专栏端点需要签名器(SP-2 v1.2 未引入),会返回
  403。此类条目以 best-effort 方式保存,连续失败后触发退避(`max_consecutive_failures` /
  `failure_cooldown_hours`)以避免无限重试。

## 输入

一份 YAML 配置(完整字段见 `interface.md` + `config/zhihu-watcher.example.yaml`):
- 轮询间隔、输出目录、状态目录;
- SP-1 连接(`base_url` / `uuid` / `password`);
- `targets` 列表:两种类型:
  - `type: collection` — 显式指定单个收藏夹(id 或完整 URL,可选子目录名);
  - `type: user` — 自动发现该用户的所有**具名**收藏夹(`url_token: me` 或明文 token);
    默认跳过空收藏夹(`skip_empty: true`)和"我的收藏"(`include_default: false`,留待分类器)。
- 可选水位线(`only_after`)和首次运行回填开关(`backfill_on_first_run`)。

## 输出

输出目录下,**每个收藏夹一个子目录**,每个新条目一个 `.md` 文件:
- 文件名 = `<标题sanitize>.md`,撞名追加 `_<url_id>`;
- 正文首行 `> <原始url>`,其后是 SP-2 引擎产出的正文 Markdown;
- **无 YAML frontmatter**;图片保留远程 URL(不下载)。
- 此输出约定对齐参考项目 `github.com/JasonJarvan/Zhihu-Collections-MCP`。

## 怎么装

Docker compose(**起容器是 user 操作**,见 `runbook.md`):

```bash
cp config/zhihu-watcher.example.yaml config/zhihu-watcher.yaml   # 填好你的值
docker compose up -d --build
```

冒烟自测(单轮跑完即退,不起调度器):

```bash
python -m zhihu_watcher --once --config config/zhihu-watcher.yaml
```

## 依赖

- **SP-1 CookieManager**(`Service/crawl/cookie-manager/`):cookie 来源(主动拉取)。
- **SP-2 知乎引擎**(`Engine/zhihu/`,冻结):抓取单页 → Markdown。本服务是纯消费者。

## 另见

- 对外契约(配置 + CLI):`interface.md`
- 对外架构摘要:`architecture.md`
- 部署 / 排错:`runbook.md`
- 设计与实现计划:`docs/superpowers/{specs,plans}/2026-06-02-SP-5a-*`
