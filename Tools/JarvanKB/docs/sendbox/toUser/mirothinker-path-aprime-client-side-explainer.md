> 给用户的说明信(H2A,中文)
> 主题:MiroThinker 接入的 **Path A′ —— 非 `-h` 模型 + client-side tool call + 自建 harness**
> 作者:root orche g4 · 2026-06-15
> lifecycle: persist 到 A/A′/B 路径最终敲定后,折进 `version-plan §MiroThinker` 再 burn

# Path A′ 详解:订阅当大脑,你自建 agent workflow

## 0. 你的理解对不对?

**对。** Path A′ = MiroMind 订阅只给你**单纯的模型推理能力**(那个支持 client-side tool call 的「非 `-h`」模型),**agent 的循环 / harness / workflow 由你自建**,工具在**你这边本地执行**。

唯一前提(待 Miro 确认 = 追问 Q1b/Q2):非 `-h` 模型确实是「纯 tool-calling 模型」——它把 `tool_calls` 交回给你、**不**在服务端自己跑搜索循环。Miro 说它「支持 client-side tool call」基本就是这个意思,但要它一锤定音。

> 对照:`-h`/deepresearch 那个是**完整 workflow agent**(官方文档原话:"A Workflow ... manages the entire lifecycle";工具是**服务端** Step、由它自己的 Agent 执行)。它不把控制权交给你,所以只能用 `mcp_servers`(把你的公网 MCP 注入它的服务端循环)。那是 Path A,不是 A′。

## 1. client-side tool call 一句话

你调模型时带上 `tools`(工具的 schema)→ 模型不直接答,而是返回 **`tool_calls`**(要调哪个工具+参数)→ **你的程序本地执行**那个工具 → 把结果发回 → 模型继续。**循环你掌控,工具在你本地跑,模型只负责"决定调谁"**。

## 2. 你要跑哪些服务(A′ 的完整栈)

| 角色 | 是什么 | A′ 里要不要你跑 |
|---|---|---|
| **大脑(LLM)** | MiroMind 非 `-h` 模型,走官方 API(订阅) | ❌ **不用你跑**,远程托管,你只 `chat/completions` 调它 |
| **harness / agent 循环** ⭐ | 发对话+`tools`→收 `tool_calls`→分发→喂回结果→循环;管规划/子agent/记忆/停止条件 | ✅ **这是 A′ 唯一真正新增要跑的东西**(见 §4 选型) |
| **工具:反爬抓取** ⭐ | 本仓库 `Service/mcp/` crawl 门面(= Item-2/UN-043),封装 zhihu-crawl/bilibili-crawl+引擎,**本地** MCP | ✅ 要(就是 UN-043,要先建) |
| 工具:通用网页抓取(可选) | Playwright-MCP / Firecrawl 之类,补非知乎/B站的页面 | 可选 |
| **cookie-manager** | `127.0.0.1:48088`,抓取工具按需拉 cookie | ✅ 已在跑,复用 |
| **BiliNote** | `127.0.0.1:3015`,B站转写 | ✅ 已在跑(做B站才需要) |

**A′ 明确不需要的**(这正是它的好处):
- ❌ **不需要把 MCP 暴露到公网**(工具全程本地;对比 Path A 必须公网可达)。
- ❌ **不需要 GPU**(大脑是托管 API;对比 B′ 自起开源权重要 GPU)。
- ❌ **不需要等 `mcp_servers` beta**(那是 Path A 的事)。

## 3. 一次请求怎么流转(具体)

1. 你的 **harness** 发:研究目标 + `tools=[crawl_zhihu, crawl_bilibili, web_fetch, …]` 给非 `-h` 模型。
2. 模型规划 → 返回 `tool_calls: [crawl_zhihu(url=…)]`。
3. harness **本地执行** `crawl_zhihu`:从 cookie-manager(48088)拉 cookie → 走知乎引擎抓取(带 v1.2 主动限流)→ 得到 markdown。
4. harness 把结果作为 `tool` 消息发回模型。
5. 模型读结果 → 可能再调更多工具 → 最后产出带引用的报告。
6. **整个循环在你这边、工具本地执行,只有模型推理是远程(吃订阅)。**

## 4. harness 选谁(三选一,推荐第一个)

1. **自托管 MiroFlow ⭐(= 报告里"复活的方案 B")** —— MiroFlow 本就是开源的 research harness(多轮、分层子 agent、工具走 MCP、带 Web UI),把它的「大脑」配成非 `-h` 官方 API、把 `Service/mcp/` 反爬 MCP 挂上即可。**复用现成、最省построй。** 前提=非 `-h` 模型确实触发本地工具(Miro Q2)。
2. **Hermes / OpenClaw** —— 若你要"定时自治研究"那条线(= 我们 version-plan 里的 **auto-researcher / Feature A**),harness 就是 Hermes,工具同样是 `Service/mcp/` 那套。
3. **自写轻量循环** —— 只要标准 OpenAI tool-calling round-trip,几十行也能跑,完全可控。

## 5. 跟本仓库怎么接(其实零散件都已就位)

- **工具层** = `Service/mcp/` crawl 门面(**Item-2 / UN-043**)。我已定它"**同一套 crawl 逻辑既出 MCP server、也出 OpenAI tool-schema**"——所以 A(挂公网 MCP)/A′(本地 client-side tools)/复活B 全通吃,不返工。
- **harness 层** = MiroFlow(复活B)或 **auto-researcher / Feature A**(UN-040,Hermes)。
- **大脑** = MiroMind 非 `-h` API(订阅);也可随时换任何 tool-calling LLM。
- **底座** = cookie-manager + BiliNote + 引擎(全 done)。

一句话:**A′ ≈ 你的 auto-researcher 愿景的具体落法** —— MCP 门面供工具、自建/MiroFlow 供循环、订阅模型供大脑。

## 6. 还没确认的(决定 A′ 能否成立)

发给 Miro 的追问(尤其):
- **Q1b** 非 `-h` 模型确切 model id?它是纯 tool-calling、还是仍跑服务端循环?
- **Q2** 自托管 MiroFlow + 非 `-h` API 当大脑,`tools`/`tool_calls` 能**端到端触发我本地的工具**吗?(= 方案 B 是否真复活)
- **Q3** 这种用法是否正常计订阅。

Q2 = 真。→ A′(及其 MiroFlow 形态)成立。Q2 = 假(非 `-h` 也无视工具)→ A′ 倒,退回 Path A(公网 MCP)或 C(第三方大脑)。

## 7. A vs A′ 速比

| | **Path A**(`mcp_servers`,服务端) | **Path A′**(client-side,自建 harness) |
|---|---|---|
| 谁跑研究循环 | Miro(现成 deepresearch harness) | 你(MiroFlow/Hermes/自写) |
| 你的反爬工具在哪 | **公网 MCP**(Miro 调用)→ 安全/合规面 | **本地**(零公网暴露)→ 对带 cookie 抓取更干净 ✅ |
| 用订阅 | ✅ | ✅ |
| 依赖 | 等 beta(已答应开) | 等确认非 `-h` 行为(Q2) |
| 省事度 | 高(Miro 帮你跑循环) | 中(循环你建,但复用 MiroFlow 也不重) |

**我的倾向**:对一个**带授权 cookie 的反爬抓取器**,A′ 在安全面上明显更优(工具不上公网);且它顺势就是 auto-researcher 的落法。但最终取决于 Miro 对 Q2 的回答 + 你要不要 Miro 现成的 deepresearch 循环。

— root orche g4
