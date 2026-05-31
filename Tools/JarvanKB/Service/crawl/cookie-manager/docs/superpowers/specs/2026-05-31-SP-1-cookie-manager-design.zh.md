# SP-1 CookieManager — 设计

> **中文翻译版**。权威版本为同名英文 `2026-05-31-SP-1-cookie-manager-design.md`（A2A，
> 依 `docs/RepoMem/persist/config.md` 语言策略，agent / writing-plans 消费英文版）。
> 本文件为 H2A 便于用户阅读；两版内容须保持同步（`translation_sync_policy: ask-after-persist-change`）。
> 状态：Stage 1 设计（brainstorming 产出）。临时位置依 handoff §3.B；Stage 3 起 `git mv` 进
> `Service/crawl/cookie-manager/docs/superpowers/specs/`。
> 验证过的协议事实 + 路径分析见 `docs/RepoMem/temp/sp1-cookie-manager/research.md`。
> 上层背景见 `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` §7（SP-1 条目、依赖图）。

## 1. 背景与范围

CookieManager（SP-1）是**所有依赖 cookie 的子项目的硬前置**（SP-3 知乎 Skill、SP-4b B站 Skill、
SP-5a/5b 监听服务——见 SP-0 §7 依赖图）。它接收**未改动的官方 CookieCloud 浏览器扩展**推上来的
cookie，存储它们，并触发用户配置的 hook，使下游爬虫得以刷新 cookie。

### 范围内（v1）

| 交付 | 推迟（v1+） |
|---|---|
| CookieCloud upload-API 兼容接收服务（legacy + aes-128-cbc-fixed 双模式） | WebUI（移动端/iOS fallback） |
| Hook 引擎：T1（cookie 更新）+ T2（cron）触发 → A1（exec shell）+ A3（write_file 模板）动作 | A2 HTTP webhook 动作 |
| CLI：`list` / `show domain=<x>` / `dump` | — |
| Docker compose 部署，**MIT** 许可 | fork / 改浏览器扩展（我们原样复用它） |
| — | 任何 LLM 调用（CookieManager 是纯协议服务） |

### 范围外（禁止 / 非目标）

- 我们**不** fork 或修改浏览器扩展。只实现 CookieCloud HTTP+加密 wire protocol 的**服务器这一半**；
  用户把官方扩展的"服务器地址"指向我们的服务即可。
- 不做多租户账号/鉴权系统。单用户（运维者本人），1..N 个 CookieCloud 箱子。

## 2. 关键决策

| # | 决策 | 理由 |
|---|---|---|
| D1 | **Path B —— 自写 Express 服务**（非 fork easychen/CookieCloud） | 上游是 **GPLv3 copyleft**（由 LICENSE 文件证实——handoff §1 误以为是 MIT），与 SP-1 的 MIT 意图冲突，分发修改版需开源。fork 只省 ~287 LOC 却引入 rebase 负担 + 一个无插件/hook 系统、data_dir 硬编码、无可复用 WebUI 的上游。一个忠实的协议兼容接收服务仅 ~40-70 LOC；复用同款 `crypto-js` 即保证字节级加密兼容。 |
| D2 | **双加密模式**：legacy（默认）+ aes-128-cbc-fixed | legacy 是官方扩展默认（必须）；aes-128-cbc-fixed 仅多 ~10 LOC + 一个 `crypto_type` 分支，为扩展未来版本/配置变化兜底。 |
| D3 | **flat per-hook YAML** 配置（research Option 1） | 对 v1 少量 hook 最易读；每条 hook 自含 trigger + match + action。 |
| D4 | **TypeScript**（非纯 JS） | 互操作失败模式都是静默的（key 取 `[:16]`、Salted__ 默认、body limit、`path.basename`）；编译期类型锁住 config + 协议数据形状。代价：一个 `tsc`/`tsx` 构建步骤。 |
| D5 | **`accounts: [{uuid, password}]`** 映射"箱子 → 解密口令"；cookie 不在 config 里 | cookie 运行时到达（扩展 → `/update`），以密文存进 `data/<uuid>.json`。password 是 CookieCloud **加密口令**（不是网站登录、不是 cookie）；仅在需要解密（domain 匹配 / `{{cookie_json}}` / CLI）时用到。 |
| D6 | **默认单箱**（1 个 account），schema 支持 N | 运维者有一个知乎 + 一个 B站登录，PC/Android 共用 → 单箱，整箱级别的"后写覆盖"始终是一份有效会话。多箱能力保留在 schema 里（`accounts` 是数组）；跨箱同 domain 撞车时，取 `update_time` 最新的那箱，`--uuid` 可覆盖。 |

## 3. CookieCloud 协议（我们要实现的契约）

权威 + verifier 确认的细节见 `research.md`。要点：

- **上传：** `POST {endpoint}/update`，body `{uuid, encrypted, crypto_type?}`。同时接受
  `application/json` 与 `application/x-www-form-urlencoded`。缺 `uuid`/`encrypted` → `400`。
  成功返回 `{"action":"done"}`。
- **下载：** `GET|POST {endpoint}/get/:uuid` —— 请求体带 `password` 则返回解密后的 JSON，否则
  返回原样存储的 `{encrypted, crypto_type}`。
- **密钥派生（两种模式通用）：** `the_key = md5(uuid + "-" + password).hex[:16]`（UTF-8 字符串
  `uuid + "-" + password` 的 32 位小写十六进制 MD5 的**前 16 个字符**；字面连字符 `-`）。
- **legacy（默认）：** `the_key` 作为**字符串口令**传给 crypto-js → OpenSSL 模式：随机 8 字节 salt，
  EVP_BytesToKey（迭代 MD5）→ 32 字节 AES-256 key + 16 字节 IV，AES-256-CBC + PKCS7，
  输出 `base64("Salted__" + salt + 密文)`。
- **aes-128-cbc-fixed：** `the_key` 的 16 个 UTF-8 字节直接当 AES-128 key，固定全零 IV，
  AES-128-CBC + PKCS7，裸 base64（无 `Salted__`）。
- **内层明文：** `{ cookie_data, local_storage_data, update_time }`；`cookie_data` = `domain ->
  [cookie 对象]` 的映射。
- **Node 解密：** 用 `crypto-js`（`CryptoJS.AES.decrypt(encrypted, the_key_string)`）；legacy 模式
  它自动解析 `Salted__` 信封。aes-128-cbc-fixed 则显式解析 16 字节 key + 零 IV。

## 4. 模块分解

每个单元：单一职责、接口清晰、可独立测试。

```
src/
  config.ts      载入 + 校验 config/cookie-manager.yaml（zod）-> 类型化 Config。
                 暴露 loadConfig(path): Config。拥有 YAML schema。
  crypto.ts      ★ 正确性命脉。纯函数，无 IO。
                 cookieDecrypt(uuid, encrypted, password, cryptoType): InnerPayload
                 cookieEncrypt(uuid, payload, password, cryptoType): string  （测试/smoke client 用）
                 deriveKey(uuid, password): string
  store.ts       文件持久化；path.basename(uuid) 防穿越；data_dir 可配。
                 save(uuid, {encrypted, crypto_type}); load(uuid); list(): StoredMeta[]
  server.ts      Express app 工厂。路由：POST /update、GET|POST /get/:uuid、GET /health。
                 body 解析（json + urlencoded，limit 可配）。发出 'cookie-update' 事件。
                 依赖 store、config；以事件（非直接调用）通知 hooks.engine。
  hooks/
    engine.ts    编排：订阅 T1 事件 + 注册 T2 cron；触发时解密(取 password) -> 按 match 过滤 -> 跑 action。
    triggers.ts  T1 = 对 'cookie-update' 的 EventEmitter 订阅；T2 = node-cron 调度器。
    actions.ts   A1 = exec（child_process，超时，env 注入）；A3 = write_file（渲染模板）。
    template.ts  interpolate(template, vars) 处理 {{var}}；matchHook(match, ctx) 处理 uuid glob + domain。
  cli.ts         命令：list | show domain=<x> | dump [--uuid=<u>]。经 store + crypto 读取。
  index.ts       Bootstrap：loadConfig -> store init -> 启动 server -> engine.register(hooks) ->
                 优雅 SIGTERM/SIGINT 退出。
tests/
  crypto.test.ts store.test.ts server.test.ts hooks.test.ts cli.test.ts  + fixtures/
config/cookie-manager.example.yaml
Dockerfile  docker-compose.yml  package.json  tsconfig.json  vitest.config.ts  LICENSE(MIT)
```

单元间接口是值/事件，而非共享可变状态：`server` 发出 `cookie-update {uuid, encrypted, crypto_type}`；
`engine` 消费它并从 `config.accounts` 取 password。`crypto` 与 `template` 是纯函数。`store` 是 cookie
数据唯一的文件系统拥有者。

## 5. 数据流

```
[上传]  官方扩展 --加密--> POST /update {uuid, encrypted, crypto_type?}
   server：校验（缺字段 -> 400）-> store.save（原样存密文）-> 回读字节比对
        -> 立即返回 {action:'done'}（不让 hook 阻塞扩展）
        -> (异步) 发 'cookie-update' -> engine：
              按 uuid 查 account.password -> crypto.decrypt -> 算 domains
              -> 对每条 match 命中的 T1 hook -> 用插值变量跑 A1/A3
[定时]  node-cron 触发 T2 hook -> engine：载入最新存储的 cookie -> 解密 -> 跑 A1/A3
[CLI]   store.load + crypto.decrypt -> 打印（list / show domain= / dump）
```

异步 hook 的理由：慢的 exec hook 绝不能拖住扩展的上传请求（否则扩展会报同步失败）。hook 结果进日志。

## 6. 配置 schema（flat per-hook YAML）

```yaml
server:
  host: 0.0.0.0          # 局域网/Android 推送用 0.0.0.0；仅同机用 127.0.0.1
  port: 48088             # CookieCloud 习惯端口
  data_dir: ./data
  body_limit: 50mb       # 默认 100kb 会静默截断真实 cookie dump
accounts:                # 箱子 -> 解密口令；cookie 不在这里（经 /update 到达）
  - uuid: "your-uuid"    # 你在扩展里设的随机 id
    password: "your-pw"  # 你在扩展里设的加密口令（不是网站登录）
hooks:
  - id: refresh-zhihu
    on: cookie-update                 # T1
    match: { uuid: "*", domain: ".zhihu.com" }
    action: exec                       # A1
    command: "/opt/crawl/refresh.sh"
    args: ["--uuid", "{{uuid}}", "--domain", "{{domain}}"]
    env: { COOKIE_JSON: "{{cookie_json}}" }   # 大 JSON 走 env，不走 argv
    timeout_ms: 30000
  - id: snapshot
    on: cron                           # T2
    schedule: "*/15 * * * *"
    match: { uuid: "*" }
    action: write_file                 # A3
    path: "./snapshots/{{uuid}}-{{ts}}.json"
    template: '{"uuid":"{{uuid}}","cookies":{{cookie_json}},"at":"{{ts}}"}'
```

模板变量：`{{uuid}} {{domain}} {{cookie_json}} {{encrypted}} {{crypto_type}} {{update_time}} {{ts}}`。
`{{cookie_json}}` 注入裸 JSON 值（不带引号）。未知变量 -> 空串。`match.domain` 把 T1 过滤到解密后
`cookie_data` 的键上；省略则每次更新都触发。某 account 未配 password 时：带 domain 匹配的 hook 记
warning 并跳过（只有基于 `{{encrypted}}` 的 hook 能跑）。

## 7. CLI 接口

| 命令 | 行为 |
|---|---|
| `cookie-manager list` | 列出已存 uuid + `update_time` + 每个 uuid 的 domain 数 |
| `cookie-manager show domain=<x>` | 解密并展示 domain `<x>` 的 cookie（撞车时取最新箱） |
| `cookie-manager dump [--uuid=<u>]` | 解密并 dump 全部 cookie（或指定 uuid） |

## 8. 错误处理与安全

- 缺 `uuid`/`encrypted` -> 400；body 超限 -> 413；文件 IO 错 -> 500。
- 解密失败（密码错 / 密文损坏）-> 记日志 + 跳过该 hook，**绝不崩溃**；CLI 报错退出。
- exec hook：可配 `timeout_ms`，超时杀进程；cron hook 若上一轮仍在跑则跳过本轮（不叠加）。
- **安全：**
  - 构造文件路径前 `path.basename(uuid)`（防路径穿越）。
  - exec 命令来自**可信的本地 config**（运维者自己的）；`{{cookie_json}}` 走 env，绝不拼进 shell 字符串。
  - 协议本身只靠 uuid+password 模糊保护（同上游）。README 必须提示跑在局域网/VPN/反向代理后；
    不要把端口暴露到公网。

## 9. 测试策略（TDD —— 先红）

- **crypto.ts（最重）：**（1）round-trip encrypt->decrypt；（2）一个硬编码的**已知向量** fixture，
  对照参考实现交叉验证（防"自洽但错误"的代码）；（3）两种 `crypto_type` 分支都覆盖。
- **store：** save/load/list；`../` 穿越被拒。
- **server：** supertest —— `POST /update` 用 json 和 urlencoded 两种；400 用例；大 body；`GET /get/:uuid`。
- **hooks：** `matchHook`（uuid glob + domain）；模板插值；A3 write_file（临时目录）；A1 exec（`echo`）；
  cron 触发用假定时器。
- **cli：** 对种子 store 跑 list/show/dump。
- **手动 smoke（verification-before-completion 闸门，handoff §3.E —— 强制）：** 启动服务，用一个
  PyCookieCloud 式小 client（node + crypto-js）推一条 fake cookie，观察 hook 触发并写出文件。

## 10. 部署

`Dockerfile` + `docker-compose.yml`（service + data volume + 挂载 config）+ `LICENSE`（MIT）+ README
（装官方扩展 -> 把服务器地址指向本服务 -> 设 uuid/password -> 配 hook）。我们**产出** compose 文件但
**不**起 docker（handoff §5：部署是运维者的操作）。

## 11. 未决项 / 风险

- **R1（低）：** 官方扩展 POST /update 的确切 `Content-Type` —— research 指出扩展发 JSON 而
  PyCookieCloud 发 urlencoded；通过两者都接受来缓解。
- **R2（低）：** 整箱级"后写覆盖"在某设备未登录某站却最后同步时可能丢掉那个 domain。运维者单箱、
  两端都登两个站 -> 非问题；README 写明。
- **R3（中）：** `crypto-js` 上游处于维护-only 模式。v1 可接受；解密路径很小，将来需要可改用
  `node:crypto` 重写。

## 12. 自审报告

- **占位符扫描：** 无 TBD/TODO 残留。各节均具体。
- **内部一致性：** D5/D6（accounts 模型、单箱默认）与 §6 config + §7 CLI 撞车规则一致；§3 协议与
  `research.md`（verifier 确认）一致；§4 模块接口与 §5 数据流一致（server 发事件，engine 消费 + 从
  config 取 password）。
- **范围：** 单模块，单一实现计划；v1/v1+ 划分在 §1 明确。
- **歧义已消解：** "撞车取最新箱"锁定到 `update_time` + `--uuid` 覆盖（D6）；异步 hook 顺序锁定在 §5
  （先回复再跑 hook）；双 Content-Type 锁定在 §3。
- **残留风险**记录在 §11（R1-R3），均为低/中且有缓解措施。
