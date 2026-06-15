> 给用户的说明信(H2A,中文)
> 主题:MiroThinker 接入**定论**(Miro 团队 2026-06-15 回复 + 官方文档核实)+ 公网 MCP 的 cookie 保护
> 作者:root orche g4 · 建于 2026-06-15 · **2026-06-15 重写**(原稿把 A′ 当近乎可用,经 Miro 回复+文档否定,已纠正)
> lifecycle: persist 到 Path A vs B′ 最终拍板后,折进 `version-plan §MiroThinker` 再 burn

# MiroThinker 接入定论 + 公网 MCP / cookie 保护

## 0. 定论(纠正我前两轮的话)

经 Miro 团队回复 + 官方文档(`/docs/{concepts,chat-completions,responses-api}`)核实:

- **平台不提供「裸模 API」** —— 所以我前两轮说的 **A′(订阅纯模型 + client-side tools + 自建 harness)经 API 这条路不存在**。纠正。
- **client-side tool-call 只能靠自部署开源权重**(= 方案 B′,要 GPU、**不吃订阅**)。
- **Path A = 托管非 `-h` workflow(`apodex-1-0-deepresearch`)+ `mcp_servers`** 是**唯一既用订阅、又官方支持**的接入路。
- 模型:`apodex-1-0-deepresearch-h`(multi-agent,**不**支持 mcp/client-tc)/ `apodex-1-0-deepresearch`(非 `-h`,workflow,支持 `mcp_servers`,需开 user 白名单)/ `-mini`。
  - (注:官方文档里写的是 `mirothinker-1-7-*`,团队回复给的是 `apodex-1-0-*` —— 命名不一致,调用前要确认确切 id。)

**为什么 `-h`(multi-agent)不支持**:tool-call 协议假设"单一可暂停-恢复的循环";multi-agent 是 orchestrator 派生多个并发/嵌套子 agent,没有面向调用方的单一暂停点,client-tc 协议层不兼容,外部 MCP 路由进多层级也最难接 → 故"暂不支持"。单 agent 的非 `-h` workflow 只一条循环,易接 → `mcp_servers` 开在它上面。

## 1. Path A 怎么搭(主路)

```
你的 anti-crawl MCP(公网 + 强鉴权)
        ▲  server-side 调用(Miro 服务器发起)
        │
Miro 托管 workflow(apodex-1-0-deepresearch,非 -h)  ← 请求里带 mcp_servers:[{name,url,access_token}]
        │  内部 deepresearch 循环(规划/搜/读)调用你挂的 MCP tool/resource
        ▼
   带引用的研究报告
```
- 你要跑的:**一个公网可达的 anti-crawl MCP**(= 仓库 `Service/mcp/` 门面 / Item-2 / UN-043)。Miro 帮你跑研究循环。
- 前置:account 开 **workflow toolcall 白名单** + **mcp_servers beta**(团队已答应开)。

## 2. 🔴 公网 MCP 要做什么保护 + 怎么护 cookie(你的核心问题)

**核心原则:cookie 永不进出 MCP 接口面;公网面只暴露"URL→markdown"最小能力;每请求强鉴权;你这边再收一层网络。** 分层:

1. **能力最小化(最重要)**:MCP 只暴露「抓某 URL → 返回 markdown」。**绝不**提供"给我 cookie""用我 cookie 发任意请求""通用代理"这类能力。→ 即使 token 泄露,攻击者**也只能拿到抓取内容,拿不到 cookie、也无法把你的身份指向任意站点**。
2. **cookie 全程内部、绝不回显**:cookie 由 MCP 内部从 **localhost 的 cookie-manager(`127.0.0.1:48088`)** 拉取 → **内存使用** → 用完即弃;**绝不落盘明文、绝不出现在 MCP 的请求/响应里**(沿用仓库既有"主动拉取内存解密"模式再加这条)。**cookie-manager 本身不经公网 MCP 暴露** —— 公网面只有 MCP 的抓取工具。
3. **强鉴权(补 Miro 内测期无 URL 白名单的缺)**:MCP endpoint **仅 HTTPS**;每请求带**强随机 bearer token / OAuth**(填进 `mcp_servers` 的 `access_token`/`headers`);只有持 token 的 Miro 服务器能调;token **可轮换、泄露即吊销**。
4. **你这边收窄可达性**:放在 **Nginx + TLS 之后**(复用 cookie-manager 那套 frp/Nginx 模式,**别裸开端口**);若能拿到 **Miro 出口 IP 段**,在防火墙/反代**只放行 Miro 的 IP**(Miro 不做 URL 白名单,但你可以做 IP 白名单 → 见 §4 待确认)。
5. **域名白名单 + 限流 + 审计**:MCP 只允许抓 `zhihu.com`/`bilibili.com`(cookie 不能被指向任意站);按 token/IP 限流(叠加引擎 v1.2 出站限流);**审计日志**(谁/抓什么/何时)→ 滥用可界定、可发现。
6. **降爆破面(可选纵深)**:用**受限/专用账号**的 cookie 抓取,万一泄露不殃及主号。

**最干净的替代 = B′**:自部署开源权重 + client-side 本地工具 → **MCP/工具根本不上公网,cookie 零公网暴露面**。若 cookie 安全是第一优先,B′ 架构上最安全;Path A 必须把上面 1–5 做齐才可接受。

## 3. 选 Path A 还是 B′?

| | **Path A**(托管 workflow + `mcp_servers`) | **B′**(自部署开源权重 + client-side 工具) |
|---|---|---|
| 用订阅 | ✅ | ❌ |
| 谁跑研究循环 | Miro(现成 deepresearch) | 你(MiroFlow/自写 + 本地权重) |
| 你的 MCP/工具 | **必须上公网**(Miro 调用)→ 须做 §2 全套保护 | **全本地,零公网暴露** ✅ |
| cookie 暴露面 | 公网端点背后(靠 §2 防护) | 无公网面,最安全 |
| 额外成本 | 开两个白名单 + 维护公网 MCP | **GPU(~1×4090)** |

**我的判断**:Path A 省事、用订阅,但要把一个"带你登录态"的端点放公网 + 做齐防护;B′ 对 cookie 最安全但要养 GPU、不吃订阅。**取决于你更在意"用订阅省事"还是"cookie 零公网暴露"。**

## 4. 还没确认的(发 Miro)

1. **命名**:`apodex-1-0-*` vs 文档 `mirothinker-1-7-*` —— 当前确切 id?
2. **两个白名单**:workflow toolcall 白名单 + mcp_servers beta,是否都已为 `jasonjarvan@gmail.com` 开?
3. **mcp 工具是否真被调用**(非 fallback 到内置搜索)?
4. **`mcp_servers` 精确 schema**:transport(公网 → http/SSE)、`access_token`/oauth 怎么填?
5. **Miro 出口 IP 段**(用于你侧 IP 白名单,补无 URL 白名单)。
6. **B′ 取舍**:要本地零暴露就走 B′(GPU + 不吃订阅),确认能接受?

## 5. 对仓库的硬影响

**Item-2(`Service/mcp/` 门面 / UN-043)硬约束:MCP 必须自带鉴权 + 能力最小化 + cookie 绝不进出接口面 + 域名白名单。** 无论最后走 A 还是 B′,门面都建;A 直接公网用(带防护),B′ 本地挂。

— root orche g4
