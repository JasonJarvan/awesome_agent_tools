# MiroMindAI 全家桶解读 + 给 MiroThinker 加反爬的可行路径

> 写给:Jarvan(订阅用户视角)
> 日期:2026-06-12
> 来源:`github.com/MiroMindAI` 各 repo README、`platform.miromind.ai/docs/chat-completions`、MiroFlow `main` 分支实际代码、MiroResearch skill。
> 结论先行(已用 key 实测,2026-06-12 更新):
> - **方案 B(自部署 MiroFlow 大脑指向订阅)已实测判死刑** —— 托管 mirothinker **无视调用方声明的 `tools`、从不返回 `tool_calls`、全部服务器端自己搜**,所以你挂在 MiroFlow 里的反爬工具**永远不触发**。比"重复"更糟,直接不可用。
> - **方案 A(托管 + `mcp_servers` 挂自己工具)是用订阅 + 加反爬的唯一官方通道,但你当前 key 实测被拒** —— `mcp_servers_not_allowed`,要找 MiroMind 开 beta。
> - **当下想立刻有反爬,只能走方案 C(自部署 + 第三方/开源权重大脑 + 反爬 MCP),但那不消耗订阅。**
> - 订阅本身可用,内置 google_search + fetch 已经能抓不少(实测能拿到带引用的实时数据),只是**改不动它的抓取层**。

---

## Part 1 — MiroMindAI 下每个 repo 是干嘛的(人话版)

MiroMind 这家做的是"深度研究 agent"(deep research agent):你丢一个问题,它自己上网搜、读网页、必要时跑代码,最后给你一份带引用的报告。围绕这件事,他们开源了一整条流水线——**训练 → 模型 → 跑模型的框架 → 评测**。

| Repo | Star | 一句话是什么 | 跟你有没有关系 |
|---|---|---|---|
| **MiroThinker** | ⭐8.3k | **旗舰"研究员模型"本体**。给一个问题,它会自己规划→网搜→读页面→(可选)跑代码→产出带引用的报告。最新 MiroThinker-1.7 在 BrowseComp / BrowseComp-Zh 上拿到 74.0 / 75.3。**既有开源权重,也有官方托管 API**。 | **直接相关**:你的 `MiroResearch` skill、你的订阅,背后调的就是它。 |
| **MiroFlow** | ⭐3.0k | **开源的"跑 agent 的框架/脚手架"(harness)**。负责多轮对话、分层子 agent 编排、工具接入(搜索/读取/代码/视觉/音频,全部走 MCP server)。**后端大脑可换**:MiroThinker / Claude / Kimi / OpenAI / Gemini / DeepSeek 都行,还带 Web UI。 | **直接相关**:想"自部署 + 加反爬",就是改它。 |
| **MiroRL** | ⭐246 | "MCP 优先"的**强化学习训练框架**,专门训 deep research agent——教模型怎么用工具。 | 间接:训练用,你跑研究用不上。 |
| **MiroTrain** | ⭐140 | "算法优先"的**高效训练框架**(SFT 那一层),和 MiroRL 配合把模型练出来。 | 间接:训练用。 |
| **MiroMind-M1** | ⭐279 | 完全开源的**数学推理 LLM 系列**,基于 Qwen-2.5,专攻数学推理。和上面那条"研究 agent"线是**相对独立的另一条产品线**。 | 基本无关:你要的是研究/抓取,不是解数学题。 |
| **MiroEval** | ⭐40 | deep research agent 的**基准 + 评测框架**:100 个任务(70 文本 + 30 多模态),从合成质量 / 事实性 / 研究过程三个维度评了 13 个系统。 | 间接:想客观比较"加了反爬前后效果"时可以拿来打分。 |
| **miromindai.github.io** | ⭐4 | 纯**资源/素材托管**仓库(网站 assets),没有功能代码。 | 无关。 |

> 另外常被一起提到的 **MiroVerse**(147k 条训练数据集)**不是这个 GitHub org 下的代码仓库**,它是放在 HuggingFace 上的数据集,训练用。

**三条线一眼记住:**
- 想**用**:`MiroThinker`(模型/能力)+ `MiroFlow`(把它跑起来的框架)。
- 想**训**:`MiroTrain` + `MiroRL`(+ `MiroVerse` 数据)。
- 想**评 / 看别的模型**:`MiroEval` + `MiroMind-M1`。

---

## Part 2 — 你的真实问题:MiroThinker 现在没有反爬,怎么补?

### 先说清楚一个结构性事实(这决定了所有方案)

你的订阅买的是**官方托管的 mirothinker 深度研究 agent**。它的"上网搜 / 抓页面 / 跑代码"这些动作**全部在 MiroMind 的服务器上执行**(`web_search` / `fetch_url_content` / `execute_python` 都是 server-side reasoning step)。你只发一个 prompt,收一份报告。

也就是说:**它内置的抓取器抓不动的页面(JS 重渲染 / 要登录 / 被 Cloudflare 之类反爬挡住),你没法从外面直接"塞一个更强的抓取器进它肚子里"——除非官方给口子。**

而官方确实给了口子,而且自部署框架也把抓取层完全交到你手里。所以下面按你的优先级("用订阅 > 自部署也用订阅 > 第三方模型 fallback")给三档。

---

### 方案 A(最省事、最不浪费订阅):托管 API + `mcp_servers` 把你自己的抓取工具挂上去

**这是官方文档里明写的机制。** `POST https://api.miromind.ai/v1/chat/completions` 接受一个 `mcp_servers` 数组参数,让你给托管的 mirothinker 注册外部 MCP 工具。模型在内置抓取失败时,会调用你提供的工具。

```jsonc
// 伪示意:OpenAI 兼容,直接用 openai SDK 或 curl
{
  "model": "mirothinker-1-7-deepresearch",
  "messages": [{"role": "user", "content": "研究 XXX,需要访问 <某站点>"}],
  "mcp_servers": [
    {
      "name": "my_browser",
      "url": "https://你公网可达的MCP服务/mcp",   // 关键:必须 MiroMind 服务器能访问到
      "access_token": "..."                        // 或 headers / oauth
    }
  ]
}
```

- **谁做反爬**:你那台 MCP server。里面可以包一个**合规的渲染/抓取后端**——Playwright 真实浏览器、或托管抓取服务(Jina Reader / Firecrawl / Browserbase / ScrapingBee / Bright Data / ZenRows 这类专门处理 JS 渲染 + 反爬挑战的商业服务),并带上**你本人有权使用的登录态 / cookie**。
- **优点**:订阅 100% 用上(大脑还是托管 mirothinker),你几乎不用自己跑重东西,只维护一个 MCP 抓取服务。这就是字面意义的"给 mirothinker API 加反爬"。
- **拦路虎(实测确认)**:
  1. `mcp_servers` **目前对你账号是关的**——实测 `POST /v1/chat/completions` 带 `mcp_servers` 直接返回 `{"error":{"code":"mcp_servers_not_allowed","message":"mcp_servers is not enabled for this account"}}`。**必须先找 MiroMind 申请开通 beta**,否则此方案无法启动。
  2. 你的 MCP server 得**公网可达**(MiroMind 服务器要能回连),内网得开隧道(ngrok / cloudflared 之类)。
  3. 你现在用的 `MiroResearch` skill 走的是 **Responses API**(文档明说不支持 tools)。要用这个口子,得改走 **chat-completions 接口 + `mcp_servers`**,不是现成 skill。

> **判断:这是用订阅 + 加反爬的唯一官方路径,首选——但被 beta 权限卡住。当务之急是去开通 `mcp_servers`。**

---

### 方案 B(❌ 已实测判死刑,不要走):自部署 MiroFlow,大脑指向你的订阅

> **实测结论:此路不通。** 思路本身很美(订阅当大脑 + 本地反爬工具),但托管 mirothinker 的接口行为让它无法成立——见下方"要命的事"。保留此节是为了让你知道**为什么**不能这么干,别再绕回来试。

**为什么能用订阅?** MiroFlow 里 MiroThinker 的后端类 `MiroThinkerSGLangClient` 本质就是个 OpenAI 兼容客户端:

```python
# src/llm/providers/mirothinker_sglang_client.py(节选)
AsyncOpenAI(
    api_key=self.cfg.llm.oai_mirothinker_api_key,     # ← 改成你的 sk_live_...
    base_url=self.cfg.llm.oai_mirothinker_base_url,   # ← 默认 localhost:61005,改成托管地址
)
```

默认它指向本地 sglang(自己起开源权重),但 base_url / api_key 都可配。**把它指到官方托管接口,大脑就是你订阅的 mirothinker,但整个 harness + 工具层跑在你本地、由你掌控。**

具体改两处:

```yaml
# 复制 config/agent_llm_mirothinker.yaml,改 llm 段:
main_agent:
  llm:
    provider_class: "MiroThinkerSGLangClient"        # 也可用 GPTOpenAIClient,二者都是薄封装
    model_name: "mirothinker-1-7-deepresearch"        # 用托管模型名,不再是 DUMMY
    oai_mirothinker_api_key: "${oc.env:OAI_MIROTHINKER_API_KEY}"
    oai_mirothinker_base_url: "${oc.env:OAI_MIROTHINKER_BASE_URL}"
  tool_config:
    - tool-reading
    - tool-searching-serper
    - tool-anticrawl        # ← 你新加的反爬工具(见下)
```

```bash
# .env
OAI_MIROTHINKER_BASE_URL="https://api.miromind.ai/v1"
OAI_MIROTHINKER_API_KEY="sk_live_你的key"
SERPER_API_KEY="..."        # 普通搜索
```

**反爬工具怎么加(关键):** MiroFlow 工具全是 MCP server,配置即插拔。**注意:`config/tool/tool-browsing.yaml` 引用的 `src.tool.mcp_servers.browsing_mcp_server` 这个文件在 `main` 分支里实际不存在**(仓库里只有 `browser_session.py`,是个 Playwright 持久会话的封装,没有完整的 browsing MCP server)。所以 MiroFlow 自带的浏览工具**开箱跑不起来**,你要么自己补这个文件,要么挂一个第三方浏览器 MCP。两条路:

1. **挂现成的浏览器/抓取 MCP**(最快):新建一个 `config/tool/tool-anticrawl.yaml`,`tool_command` 指向 Playwright-MCP、Browserbase MCP、或 Firecrawl MCP 这类,把你的登录态 / 代理配进去。仿照 `tool-searching-serper.yaml` 的写法(它就是 `npx -y serper-search-scrape-mcp-server`)。
2. **自己写** `browsing_mcp_server.py`:照 `contribute_llm_clients.md` 那套 MCP server 模板,内部用 Playwright 渲染 + 你的 cookie/代理 + 限速/缓存,返回结构化结果。

- **本来想要的优点**:订阅当大脑、反爬本地可控、不等 beta。
- **要命的事(已用 key 实测,2026-06-12)**:MiroFlow 靠"声明本地工具(OpenAI `tools` 参数)→ 模型返回 `tool_calls` → MiroFlow 本地执行"驱动工具。但托管 mirothinker 的 chat-completions 接口实测:
  - **收下 `tools` 参数却完全无视**——我声明了一个 `get_weather` 函数,模型在 `reasoning_steps` 里明说它看到的只有自己的 `web-processing.google_search`,根本不知道我的工具存在;
  - **`finish_reason` 返回 `stop` 而非 `tool_calls`**,消息里没有 `tool_calls` 数组——它自顾自服务器端搜完,直接把最终答案 + 引用还回来,**从不把执行权交回给调用方**。
  - 后果:把它当 MiroFlow 大脑,**你挂的反爬 MCP 一次都不会被调用**,模型永远用它那个无反爬的内置搜索。这不是"重复",是"你的工具是死的"。**所以方案 B 不成立。**

**方案 B′(不省钱但最干净):** 不想用托管、有 GPU(README 说一张 RTX 4090 即可)的话,把 MiroThinker-1.7 开源权重用 sglang/vLLM 起在本地 `localhost:61005`,`OAI_MIROTHINKER_BASE_URL` 指本地。完全自主、推理免费,但**不消耗你的订阅**,且要自己养 GPU。

---

### 方案 C(fallback):自部署 MiroFlow + 第三方大脑 + 反爬工具

最省心、最不依赖 MiroMind 的路。直接用 MiroFlow 现成的 `agent_quickstart_search.yaml`(大脑是 Claude 3.7,走 OpenRouter),换成你想要的 Claude / GPT / Gemini,再把方案 B 里那套反爬 MCP 工具挂上。

- **优点**:成熟、文档全、`.env` 只要一个 `OPENROUTER_API_KEY` 就能起。
- **代价**:**完全不用 MiroMind 订阅**,只把 MiroFlow 当 harness 用。仅当方案 A/B 都不顺时才退到这。

---

## Part 3 — 推荐路线 + 现在就能做的事

**实测后的真实排序(2026-06-12):**

1. **方案 A —— 用订阅 + 反爬的唯一官方路径,但当前被 `mcp_servers_not_allowed` 卡住。** → **最高杠杆的动作:去找 MiroMind 申请开通 `mcp_servers` beta。** 一旦开通,这就是首选,运维最轻、订阅全用上。
2. **方案 B —— ❌ 已实测不成立,从清单划掉。**
3. **方案 C —— 当下想立刻有反爬的唯一可落地路径。** 自部署 MiroFlow + 第三方大脑(Claude/GPT/Gemini)+ 反爬 MCP。代价:**完全不用订阅**。在 beta 开通前用它顶着。
4. **方案 B′(可选)**——有 GPU 又想自主可控,本地起 MiroThinker 开源权重 + 反爬 MCP;同样不用订阅。
5. **订阅照常用**——对那些"内置搜索就够、不需要登录态/反爬"的研究任务,直接用现成 `MiroResearch` skill,别浪费。

> 一句话:**你想要的"用订阅 + 加反爬"现在被一道账号权限挡着(`mcp_servers` beta)。开通前,有反爬的活只能用第三方模型顶;开通后,方案 A 一步到位。**

**合规边界(说一次):** 上面所有"反爬"都指**合规手段**——用你**本人有权访问**的登录态、真实浏览器渲染 JS 重页面、商业抓取服务、限速 + 缓存 + 来源标注、优先用站点官方 API。**不包括**:破解 CAPTCHA、绕过访问控制、轮换身份规避封禁、违反站点 ToS。遇到验证码/访问墙的正确做法是"人工接管 + 标记 needs_human_action",不是硬绕。

**当下要做的事:**

1. **去开通 `mcp_servers` beta(最高优先)。** 这是方案 A 的唯一闸门,实测你账号现在被拒。给 MiroMind 发邮件/工单,问法别提"反爬绕过",就说:"需要给托管 mirothinker 挂自定义的、用户授权的浏览/抓取 MCP 连接器(authenticated / JS-heavy / 人工接管式浏览支持)"。

2. **key 已验证可用,但注意载入方式 + 安全。** 实测这把 key 能正常调 `/v1/models` 和 `/v1/chat/completions`。但本仓库环境里 `MIROMIND_API_KEY` 仍未设、repo 根目录无 `.env`——程序只读 `os.environ`,跑前要 `export`:
   ```bash
   export MIROMIND_API_KEY="sk-..."     # MiroResearch skill 用(本文不落盘明文 key)
   ```
   key 是明文贴进对话的,**建议用完轮换一次**。

3. **在 beta 开通前,要反爬就先搭方案 C**:MiroFlow + 第三方大脑 + 一个反爬 MCP(Playwright-MCP / Firecrawl / Browserbase),订阅那部分先放着。

---

## Part 4 — 现在可用的方案(综合 MiroThinker 调研回执 + 二次核实,2026-06-12)

> 来源:把前面的调研 prompt 喂给 MiroMind API(mirothinker deep research)拿回的报告 + 我对它承重事实的**独立复核**(`gh api` 直查仓库)。报告整体可信、合规 framing 也对,但它的部分源链接来自二手博客和一个 PR 分支,下面区分"已核实为真 / 仍是推测"。

### 4.1 报告关键论断的核实结论

| 报告论断 | 复核结果 | 依据 |
|---|---|---|
| MiroFlow 有 `src/tool/manager.py`(ToolManager,MCP 协议接入) | ✅ **真** | `gh api .../contents/src/tool` 见 `manager.py` |
| MCP server 是标准做法,已有 reading/searching/python server | ✅ **真** | `src/tool/mcp_servers/` 下确有这些 |
| 官方通过 YAML 组合 MCP 工具集 | ✅ **真** | MiroThinker `apps/miroflow-agent/conf/agent/*.yaml`(default/single_agent/multi_agent/mirothinker_v*)、`assets/LOCAL-TOOL-DEPLOYMENT.md`、`libs/miroflow-tools/README.md` 均存在 |
| 浏览 MCP(`browsing_mcp_server.py`)缺失,只有 `browser_session.py` | ✅ **真,且比想的更彻底** | **main、PR 分支 `zxz-pr/miroflow-v0.3`、MiroThinker 仓库三处全缺**,只有 `browser_session.py`(Playwright 会话封装)。不是"还没合到 main",是各分支都没成品 |
| 托管 `tools` 被忽略、`mcp_servers` 私测 403 | ✅ **真** | 我方实测(Part 2 / 实测记录表) |
| `mcp_servers` 的 schema(`type:http/stdio/sse`、url、auth)、可达性要求(公网/TLS/IP 白名单) | ⚠️ **推测,未证实** | 报告按 Claude/Gemini 惯例推断,官方无公开文档。**别照这个 schema 提前写死代码** |
| 托管内置 fetch 对 Cloudflare/Turnstile/hCaptcha 的上限 | ❓ **未知** | 需对你的目标站逐个 A/B 实测 |

### 4.2 现在可用的方案(一张表看清"今天能跑 / 等什么 / 别依赖")

| 方案 | 用订阅? | 现在能跑? | 反爬挂在哪 | 闸门 |
|---|---|---|---|---|
| 订阅原样用(现成 skill) | ✅ 全用 | ✅ 是 | 改不了(只有内置 fetch) | 强反爬站会失败 |
| **方案 C:自部署 MiroFlow + 第三方大脑 + 浏览 MCP** | ❌ 不用 | ✅ **是(架构已核实就绪)** | **本地工具层,你自己挂** | 仅缺"浏览 MCP"本体,你来供 |
| 方案 B′:同上但大脑=本地开源权重 | ❌ 不用 | ✅ 是 | 同上 | 需 GPU |
| 方案 A:托管 + `mcp_servers` 挂你的浏览 MCP | ✅ 全用 | ❌ **否** | 你的远程 MCP | `mcp_servers` beta(403,待申请);schema 未公开 |
| 方案 B:MiroFlow 大脑=托管订阅 | — | ❌ **死** | — | 托管模型不调用方工具 |

**今天就能落地的只有一条:方案 C(或 B′)。** 调研复核证实 MiroFlow 的工具层是 MCP 原生 + YAML 组合,加一个浏览工具是它**设计内的标准操作**——你只需:① 部署一个浏览 MCP;② 在 agent YAML 里注册一条指向它的 entry(仿 `searching`/`reading` server 的写法,补上 main 里那个缺失的 `browsing` 引用);③ ToolManager 就会让模型调用它。**唯一"缺件"是浏览 MCP 本体,而这正好就是给 orchestrator 的 Item 2——把本仓库已有的 zhihu/bilibili 反爬抓取封成 MCP。建这个 MCP 是无悔的第一步:方案 C 今天用它,方案 A 将来(beta 开通后)也用它。**

### 4.3 浏览 MCP 的选型 + 内部合规设计(无论 A/C 都套用)

**候选浏览/抓取 MCP**(挑一个,或用 FastMCP 聚合多个到单入口):
- **Playwright MCP**(`microsoft/playwright-mcp`)—— 真实浏览器、多会话、持久上下文,最通用。
- **Browser Use MCP**(`browser-use/browser-use`、`Saik0s/mcp-browser-use`)—— 适合复杂 UI 交互(点击/表单/JS)。
- **Browserbase MCP**(`browserbase/mcp-server-browserbase`)—— 托管浏览器服务,省运维。
- **Firecrawl MCP**(`firecrawl/firecrawl`)—— 偏"搜索+抓取+JS 渲染"的文本提取,交互弱但简单。
- 本仓库自有抓取(zhihu/bilibili)封成 MCP —— **首选**,复用已验证的反爬逻辑(= Item 2)。

**MCP 内部必须内置的合规闸**(报告这部分建议是对的,采纳):
- 首访某域名先抓 `robots.txt` / 查 ToS,禁止则返回 `disallowed_by_robots` 并让 agent 停手;
- 按域名/会话限速 + 缓存 + 来源标注;
- 检测到 CAPTCHA / 硬访问控制 → **不自动绕过**,返回结构化 `{status: needs_human_action, url, screenshot}`,交人工接管(可配 `wait_for_manual_login_and_resume` 这类工具复用同一浏览器会话);
- 复用持久会话(`browser_session.py` 那套 userDataDir / session_id),减少重复登录——这是"模仿真实用户的连续会话",不是身份轮换。

### 4.4 这次调研没改变的结论

方案 B 仍死、方案 A 仍是用订阅+反爬的唯一官方路径且仍被 beta 卡住。调研的净增量是:**把方案 C 从"fallback"提升为"今天唯一能落地、且架构已核实就绪"的路**,并明确了浏览 MCP 的选型与内部合规设计。Part 3 的推荐据此微调:**别等 beta 才动手——先按 Item 2 把反爬抓取封成 MCP,用方案 C 跑起来;beta 到了再平移到方案 A。**

---

## 附:关键证据出处

- repo 列表 / star / 描述:`gh api orgs/MiroMindAI/repos`(2026-06-12)。
- 托管接口支持 `mcp_servers`(private beta)、OpenAI 兼容、server-side 工具:`platform.miromind.ai/docs/chat-completions`。
- MiroThinker 后端是可改 base_url 的 OpenAI 客户端:`MiroFlow/src/llm/providers/mirothinker_sglang_client.py`、`config/agent_llm_mirothinker.yaml`。
- 浏览工具在 main 缺失:`config/tool/tool-browsing.yaml` 引用 `src.tool.mcp_servers.browsing_mcp_server`,但该文件不在 `src/tool/mcp_servers/`(仅有 `browser_session.py`)。
- 工具即 MCP、配置即插拔:`config/tool/tool-searching-serper.yaml`、`docs/mkdocs/docs/contribute_llm_clients.md`。
- 第三方大脑最小起步:`config/agent_quickstart_search.yaml`、`.env.template`(只要 `OPENROUTER_API_KEY`)。
- ToolManager(MCP 接入层):`MiroFlow/src/tool/manager.py`(`gh api` 核实存在,2026-06-12)。
- 官方 YAML 组合工具 + 本地工具部署文档:MiroThinker `apps/miroflow-agent/conf/agent/*.yaml`、`assets/LOCAL-TOOL-DEPLOYMENT.md`、`libs/miroflow-tools/README.md`(均核实存在)。
- 浏览 MCP 缺口范围:main / PR 分支 `zxz-pr/miroflow-v0.3` / MiroThinker `libs/miroflow-tools/src/miroflow_tools/mcp_servers/` 三处均只有 `browser_session.py`,无 `browsing_mcp_server.py`(`gh api` 核实,2026-06-12)。
- 浏览/抓取 MCP 候选(MiroThinker 调研报告 + 公开项目):`microsoft/playwright-mcp`、`browser-use/browser-use`、`Saik0s/mcp-browser-use`、`browserbase/mcp-server-browserbase`、`firecrawl/firecrawl`。

## 附:实测记录(2026-06-12,用户提供的 key,明文不落盘)

| # | 调用 | 结果 | 推论 |
|---|---|---|---|
| 1 | `GET /v1/models` | 200,返回 `mirothinker-1-7-deepresearch` 与 `-mini`(均 262144 ctx / 16384 max completion) | key 可用,订阅有效 |
| 2 | `POST /v1/chat/completions`,带 OpenAI `tools`(声明 `get_weather`)+ `tool_choice:auto` | 200,但 `reasoning_steps` 显示模型只用自己的 `web-processing.google_search`,**无视 `get_weather`**;`finish_reason:stop`,**无 `tool_calls`**;直接返回带引用的最终答案 | **方案 B 死刑**:托管模型不调用调用方声明的工具,本地反爬 MCP 永不触发 |
| 3 | `POST /v1/chat/completions`,带 `mcp_servers`(探针) | 403 `{"code":"mcp_servers_not_allowed","message":"mcp_servers is not enabled for this account"}` | **方案 A 被账号权限卡住**:须申请 beta |

> 三次调用共同说明:托管 mirothinker 是个"封闭的服务器端 agent",外部加工具的唯一合法入口是 `mcp_servers`(当前对此账号关闭)。
