---
slug: sp5b-bilibili-watcher
status: reviewed
domains: [crawl]
updated_at: 2026-06-10
language: zh
audience: H2A
---

# SP-5b Stage 0 — B 站收藏夹 API 字段实证研究（用户评审稿）

> **这是一份 HITL 评审件。** 请你审阅 + 直接编辑本文档,尤其确认/修正下面标 ⭐ 的结论。
> 你批准后,我才据此设计 watermark(默认 `fav_time` 高水位,见 §6)。
>
> **方法**:2026-06-10 用你本机 SP-1 box 的真实 cookie(`domain=bilibili.com`,无前导点)**真实调用**了 B 站
> 收藏夹 API(非凭记忆/非看文档)。账号 mid=`21309967`(uname=`码总日成`),登录态正常。cookie 真值全程
> 只在内存、未落盘、未打印。下面所有字段/取值均来自真实响应。

---

## 1. 涉及的三个端点(全部 host = `api.bilibili.com`,纯 cookie + 浏览器 headers,无签名)

| 用途 | 端点 | 关键参数 | 鉴权 |
|---|---|---|---|
| 确认登录 + 取 mid | `GET /x/web-interface/nav` | — | 需 SESSDATA |
| 列出账号下**所有创建的收藏夹** | `GET /x/v3/fav/folder/created/list-all` | `up_mid={mid}` | 需 SESSDATA |
| 列出**单个收藏夹内的条目** | `GET /x/v3/fav/resource/list` | `media_id={收藏夹id}` `pn=` `ps=` `order=mtime` `type=0` `platform=web` | 需 SESSDATA |

- 响应统一包装 `{code, message, ttl, data}`,`code==0` 成功。(注意:与 BN 引擎的 `{code,msg,data}` 是不同服务,勿混。)
- ⭐ **鉴权**:列自己账号的收藏夹是私有数据,**必须带 SESSDATA**。无 cookie 时这些端点取不到你的列表(区别于引擎对**公开视频**可无 cookie 跑元数据+ASR)。
- **直连**:B 站是陆站,脚本用 `proxies={http:None,https:None}` 直连(同 §知乎链路 `trust_env=False` 立场,勿走宿主的境外代理)。

---

## 2. 收藏夹列表(`list-all`)——单个收藏夹对象字段

`data.list[]` 每个元素(只列 watcher 关心的):

| 字段 | 实测值示例 | 含义 |
|---|---|---|
| `id` | `121291467` / `2216104467` | ⭐ **收藏夹 media_id** —— 即喂给 `resource/list` 的 `media_id`,也是配置里要填的 id |
| `fid` | `1212914` | 短 fid(`id` 去掉尾部 mid 后缀);**配置用 `id` 即可,别用 `fid`** |
| `title` | `默认收藏夹` / `AI生成` | 收藏夹名 → 可作输出子目录名 |
| `media_count` | `4` / `41` | 收藏夹内条目总数(**含失效条目**,见 §4 坑) |
| `attr` | `0` / `2` / `22` | 属性位;**bit0=1 表示私密,bit0=0 公开**。实测全部偶数 → 都是公开夹 |
| `fav_state` | `0` | 当前用户是否已收藏该"收藏夹"(对自己的夹无意义) |

**实测:你账号下有 22 个收藏夹**(节选,⭐ 请圈出要让 watcher 监听的):

```
id=121291467  默认收藏夹   (4)        id=2507799767 自我提升   (12)
id=3345103467 育儿         (3)        id=2391175667 健康       (2)
id=2862144767 金融赚钱     (30)       id=2391175167 效率工具   (9)
id=2837364467 职场社交     (3)        id=2435926767 装修购房   (23)
id=2821851467 儿童视频     (3)        id=2438445167 外挂开发   (3)
id=2854853067 催眠儿歌     (12)       id=2216638867 知识技能   (6)
id=2681252167 社会科学     (7)        id=2189619267 效率工具   (7)
id=2615277467 购物         (1)        id=2216104467 AI生成     (41)
id=2651190967 娱乐折腾     (10)       id=2036145767 商业       (15)
id=2507802867 人文读书     (3)        id=1857970567 美食       (8)
                                      id=1338899667 游戏       (18)
                                      id=1195057867 编程折腾   (11)
```

> ⭐ **待你决定**:监听全部 22 个?还是只挑若干(如 `AI生成`/`编程折腾`/`商业`/`自我提升`)?(配置里逐个列 id+name。)

---

## 3. 收藏条目(`resource/list` → `data.medias[]`)——⭐ 核心字段语义

`data` 顶层:`{info, medias, has_more, ttl}`。
- `data.info` = 该收藏夹的元信息(title/media_count/attr/cnt_info/cover/upper…)。
- `data.has_more` (bool) = ⭐ **是否还有下一页(分页停止条件,见 §4)**。
- `data.medias[]` = 本页条目,**每个条目字段如下**(实测 media[0] 全字段):

| 字段 | 实测值示例 | 含义 / watcher 用途 |
|---|---|---|
| `bvid` / `bv_id` | `BV1orQJB2Edt` | ⭐ **视频 BV 号 → 直接喂引擎 `engine.transcribe(bvid, credential=cred)`** |
| `id` | `116409619185824` | 收藏资源 id(长 id,= avid 体系);喂引擎用 `bvid` 更稳 |
| `type` | `2` | ⭐ **资源类型:`2`=普通 UGC 视频**。其他可能值:音频/番剧(ogv)/合集(season)——**非 type=2 引擎多半不支持,需过滤**(见 §5) |
| `title` | `Agent记忆系统深度拆解(下)…` | 标题(回退用;引擎渲染出的标题更权威,同 SP-5a) |
| `intro` | `AI 记忆系统下集…` | 简介 |
| `cover` | `http://i0.hdslb.com/bfs/...jpg` | 封面 URL(远程,不下载) |
| `duration` | `1497` | 时长(秒) |
| `page` | `1` | 分 P 数 |
| **`fav_time`** | `1776999542` → **2026-04-24 10:59:02** | ⭐⭐ **收藏时间(你把它加入收藏夹的时刻)——这就是 watermark 要的字段** |
| `ctime` | `1776270015` → 2026-04-16 00:20:15 | 视频投稿/创建时间 |
| `pubtime` | `1776270015` → 2026-04-16 00:20:15 | 视频发布时间(本例与 ctime 同) |
| `cnt_info` | `{collect, play, danmaku, reply, view_text_1}` | 计数信息 |
| `upper` | `{mid, name, face}` | UP 主 |
| `ugc` | `{first_cid: 37534961471}` | UGC 信息(含 cid) |
| `link` / `media_list_link` | `bilibili://video/...` | app 内链(不用) |
| `attr` / `season` / `ogv` | `0` / `null` / `null` | 失效标记 / 合集 / 番剧信息 |

### ⭐⭐ 最关键的实证结论:`fav_time` ≠ `pubtime`(SP-5a 的臆断在 B 站不成立)

铁证(media[0]):

```
fav_time = 1776999542  ->  2026-04-24 10:59:02   ← 收藏时间
pubtime  = 1776270015  ->  2026-04-16 00:20:15   ← 视频发布时间
ctime    = 1776270015  ->  2026-04-16 00:20:15
```

两者**相差 8 天**。即:**B 站收藏夹每条都带独立的 `fav_time`,语义就是"收藏时刻",与视频自身的发布时间完全分开。** 这正是 SP-0 §7 的设定、也是你的强先验所指 —— 与知乎当年"凭记忆判定没有可靠收藏时间"的错误结论相反,**B 站这里是真有 `fav_time` 的**。

---

## 4. ⭐ 分页模型 + 一个必须避开的坑

- **页码模型**:`pn`(页号,从 1 起)+ `ps`(每页大小,默认/上限 20)。逐页 `pn += 1`。
- **停止条件 = `data.has_more == False`**。
- ⚠️ **坑(实测亲历)**:`默认收藏夹` `media_count=4`,但 `resource/list` 只返回 **3** 条、且 `has_more=False`。
  → **失效/删除的视频会计入 `media_count` 却不在 `medias[]` 返回。**
  → ⭐ **停止条件必须跟 `has_more`,绝不能用 `len(已收集) >= media_count` 自算停止**——否则会因"永远凑不齐 media_count"而死循环或误判。
  这正是 §知乎链路那条教训(「`offset >= totals` 早停会漏条」)的 B 站翻版:**信 API 给的翻页信号,别自算总数停止。**

---

## 5. ⭐ 排序(`order`)——watermark 早停的前提

实测 `order` 参数改变排序:

```
order=mtime    -> medias 按 fav_time 严格降序:  04-24, 01-23, 2023-12-13   (最新收藏在最前)
order=pubtime  -> 本例同上(小夹里收藏序≈发布序)
order=view     -> 按播放量重排(证明 order 确实控制排序)
```

- ⭐ **`order=mtime` = 按收藏时间倒序(最新收藏在最前)** —— 经实证。
- ⚠️ 注意命名:B 站这里 `mtime`(modify time)对收藏条目而言就是"收藏/移动入夹的时间",**与字段 `fav_time` 同序**;别和"视频修改时间"混。
- 这给了 watermark 早停的可能:`order=mtime` 从 `pn=1` 拉,一旦遇到 `fav_time <= 已存水位` 即可停止本夹(后面全是更早收藏的,已处理过)。

### type 过滤
- 实测样本全是 `type=2`(UGC 视频)。B 站收藏夹理论上可含**音频/番剧/合集**等(type≠2)。引擎是视频转写器(BV→转写),**非 type=2 的条目引擎多半不支持**。
- ⭐ **待你确认**:watcher 是否只处理 `type==2`、其余跳过(我倾向只处理 type=2,把非视频条目 log+skip,不入水位以免噪音)?

---

## 6. 据本文档,我**拟**采用的 watermark 方案(待你批准/修改)

> 这里只是提案,不是已定。你批准后我才写进 design.md。

- **默认:`fav_time` 高水位 + `order=mtime` 早停**(满足 SP-0 §7 + 你的先验)。
  - 每个被监听收藏夹独立存一个水位 = 已成功处理过的最大 `fav_time`。
  - 每轮从 `pn=1` 按 `order=mtime` 拉,遇到 `fav_time <= 水位` 即停本夹(早停,省请求)。
  - 翻页停止仍跟 `has_more`(§4)。
- ⭐ **稳健性加挂(我建议、待你定):** 在 `fav_time` 水位之外,**再叠一个 seen-id 集(keyed on `bvid` 或 `type:id`)**作幂等兜底。理由:
  ① 同秒并列收藏 / 重新收藏会让 `fav_time` 边界处出现等值,纯 `>水位` 可能漏或重;
  ② 失败项不入水位、下轮重试时,seen-set 能防止"水位已前进但某条之前失败"导致的漏处理。
  → 即:**`fav_time` 水位负责"早停省流量",seen-id 负责"绝不重复落盘 / 绝不漏"。** (SP-5a 只有 seen-id;SP-5b 在其上加 `fav_time` 早停。)
  - ⭐ 若你只想要纯 `fav_time` 水位(更简单、接受边界等值的微小风险),也告诉我,我去掉 seen-set。

---

## 7. 留给你拍板的问题(汇总)

1. ⭐ **监听哪些收藏夹**?(全部 22 个 / 指定若干 id+name)
2. ⭐ **watermark 形态**:`fav_time` 水位 + seen-id 兜底(我推荐)/ 纯 `fav_time` 水位 / 纯 seen-id(回退)?
3. ⭐ **type 过滤**:只处理 `type==2`(视频),其余 skip?
4. 上面任何字段含义、坑、排序结论若与你的认知不符,请直接改文档。

---

## 8. 复核

| 检查 | 结果 |
|---|---|
| 实证 vs 臆断 | 全部字段/取值来自 2026-06-10 真实 API 调用,非记忆 |
| `fav_time` 真伪 | ✅ 存在且 ≠ pubtime(铁证 §3) |
| 分页坑 | ✅ media_count 含失效条目,跟 has_more(§4) |
| 排序 | ✅ order=mtime = fav_time 降序(§5) |
| cookie 安全 | SESSDATA 真值未落盘未打印;domain=bilibili.com 无点(credentials.md 权威) |
| 待决项已显式标 ⭐ | §2/§5/§6/§7 |

---

## 9. 用户裁决(2026-06-10,HITL 门已清)

用户认可本文档,据此进 design。§7 三问裁定如下:

1. **监听收藏夹**:先一小撮跑通 —— `AI生成`(id=`2216104467`,41 条)+ `编程折腾`(id=`1195057867`,11 条)。
   其余 20 个以后随时按配置增删。
2. **watermark 形态**:采用 §6 推荐 —— **`fav_time` 高水位(`order=mtime` 早停省请求)+ seen-id 集(keyed `bvid`)幂等兜底**。
   即 fav_time 负责早停、seen-id 负责绝不重复落盘/绝不漏。
3. **type 过滤**:**只处理 `type==2`(UGC 视频)**,非视频条目 log+skip,不入水位(避免噪音)。

这三条是 design.md 的硬输入。
