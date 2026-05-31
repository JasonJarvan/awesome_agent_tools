# cookie-manager — 对外契约（Interface）

> SP-1 CookieManager 的稳定公开接口。下游需要 cookie 的子项目（SP-3 知乎 Skill、SP-4b B站 Skill、
> SP-5a/5b 监听服务）按本文件集成，不要依赖内部实现细节。
> 权威设计：`docs/superpowers/specs/2026-05-31-SP-1-cookie-manager-design.md`（及 `.zh.md`）。

## 1. 它是什么

一个自写的 Node.js/TypeScript + Express 服务，**复刻 CookieCloud 的 upload-API 协议**——所以**现成的
官方 CookieCloud 浏览器扩展不改、不 fork**，把扩展里的"服务器地址"指向本服务即可把 cookie 推上来。
服务负责：接收并存储（密文）、按 hook 规则触发下游动作、提供 CLI 查看 cookie。

## 2. HTTP 接口

| 方法 + 路径 | 入参 | 行为 / 出参 |
|---|---|---|
| `POST /update` | body（接受 `application/json` 与 `application/x-www-form-urlencoded`）：`uuid`(string)、`encrypted`(string, base64 密文)、可选 `crypto_type`(`legacy`\|`aes-128-cbc-fixed`，默认 `legacy`) | 存储密文原样到 `data/<uuid>.json`；返回 `{"action":"done"}`。缺 `uuid`/`encrypted` 或 `crypto_type` 非法 → `400`。响应**先于** hook 执行返回（不阻塞扩展）。|
| `GET\|POST /get/:uuid` | 路径参数 `uuid` | 返回原样存储的 `{encrypted, crypto_type}`；不存在 → `404`。（v1 不做服务端按 password 解密返回；消费端自行解密。）|
| `GET /health` | — | `200 {"status":"ok"}` |

## 3. 加密协议（消费端如需自行解密）

- key 派生（两模式通用）：`the_key = md5(uuid + "-" + password).hex[:16]`（UTF-8 字符串、字面连字符、取前 16 个十六进制字符）。
- **legacy（默认）**：`the_key` 作为**字符串口令**喂给 crypto-js → OpenSSL `Salted__` 信封 + EVP_BytesToKey(迭代 MD5) → AES-256-CBC + PKCS7。Node 解密直接用 `crypto-js`：`CryptoJS.AES.decrypt(encrypted, the_key).toString(CryptoJS.enc.Utf8)`。
- **aes-128-cbc-fixed**：`the_key` 的 16 个 UTF-8 字节直接作 AES-128 key，固定全零 IV，AES-128-CBC + PKCS7，裸 base64（无 `Salted__`）。
- 内层明文：`{ cookie_data, local_storage_data, update_time }`；`cookie_data` 是 `domain -> cookie 对象数组` 的映射。

## 4. CLI

| 命令 | 行为 |
|---|---|
| `cookie-manager list` | 列出已存 uuid + crypto_type + domain 数 + update_time |
| `cookie-manager show domain=<x>` | 解密并打印某 domain 的 cookie 数组（撞车取最新箱） |
| `cookie-manager dump [--uuid=<u>]` | 解密并打印全部（或指定 uuid）的 cookie |

> 运行时需 `COOKIE_MANAGER_CONFIG` 指向配置文件（默认 `config/cookie-manager.yaml`），以取得解密 password。

## 5. 配置（flat per-hook YAML）

见 `config/cookie-manager.example.yaml`。要点：
- `server`: `host`/`port`(默认 48088)/`data_dir`/`body_limit`(默认 50mb)。
- `accounts: [{uuid, password}]`: 箱子 → 解密口令（**cookie 不写这里**）。
- `hooks[]`: 每条含 `id`、`on`(`cookie-update`\|`cron`，cron 需 `schedule`)、`match`(`uuid` glob `*`/精确 + 可选 `domain`)、`action`(`exec`\|`write_file`)。
  - `exec`: `command` + `args[]` + `env{}` + `timeout_ms`。
  - `write_file`: `path` + `template` + 可选 `mode`。

## 6. Hook 触发模型（供下游设计联动）

- **T1 `cookie-update`**：每次 `POST /update` 成功后异步触发，命中 `match` 的 hook 执行。
- **T2 `cron`**：按 `schedule` 定时，对 store 内所有账号跑（无叠加：上一轮未完则跳过本轮）。
- **A1 `exec`**：跑 shell 命令；大 JSON 建议经 `env` 传（不拼进 shell）。
- **A3 `write_file`**：按 `template` 渲染写文件。
- 模板变量：`{{uuid}} {{domain}} {{cookie_json}} {{encrypted}} {{crypto_type}} {{update_time}} {{ts}}`。
  - **注意** `{{cookie_json}}`：当 `match.domain` 设置时是**该 domain 的 cookie 数组**；否则是**完整 `cookie_data` 映射**。`{{cookie_json}}` 注入裸 JSON（不加引号）。

## 7. 下游典型用法

需要某站 cookie 的子项目两条路：
1. **被动**：配一条 `cookie-update` + `match.domain=<目标站>` 的 hook，触发时 `exec` 调你的刷新脚本 / `write_file` 落地 cookie，供爬虫读取。
2. **主动**：调 `cookie-manager show domain=<目标站>` 或读 `GET /get/:uuid` 自行解密，按需取 cookie。

## 8. 部署与安全

Docker compose（见根 `README.md`）。协议仅靠 uuid+password 模糊保护——**务必跑在局域网/VPN/反向代理后，勿暴露公网**。
