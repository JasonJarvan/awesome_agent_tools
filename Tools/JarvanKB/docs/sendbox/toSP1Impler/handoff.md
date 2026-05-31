> from: orchestrator session (Claude Opus 4.7, 2026-05-31)
> recipient: SP1Impler (a Claude Code peer session in same cwd)
> mode: child-handoff
> purpose: execute the full v2 8-step pipeline for SP-1 (CookieManager) — brainstorming → design → writing-plans → execute → verify → done. Runs in PARALLEL with SP-0 impler; only the execute stage is gated on SP-0 completion.
> lifecycle: burn after impler writes `from-sp1impler-sp1-done.md` and orche reads it

# SP-1 Handoff — CookieManager service

## 0. What this letter is

A **child-handoff** under sendbox-protocol (see `~/.claude/skills/sendbox-protocol/SKILL.md`). You are a peer Claude Code session; the orchestrator stays alive while you run. Three-stage life:

| Stage | Scope | Parallel with SP-0? | Convergence |
|---|---|---|---|
| **Stage 1: design** | brainstorming (likely auto-skip per `clear intent`, see §3.A) → design.md | ✅ yes | direct chat with user for clarifying Q&A; write design.md to root path (see §5) |
| **Stage 2: plan** | writing-plans skill → plan.md | ✅ yes | write `from-sp1impler-plan-ready.md` to `toOrchestrator/` |
| **Stage 3: execute** | git worktree + TDD + verification-before-completion → done | ❌ **HARD-GATED** on SP-0 completion (need `Service/crawl/cookie-manager/` dir) | write `from-sp1impler-sp1-done.md` to `toOrchestrator/` |

Between Stage 2 and Stage 3 you **MUST** verify SP-0 is done (see §3.D check).

## 1. Subtask scope

Deliver **SP-1: CookieManager service** end-to-end through the v2 pipeline.

**v1 范围（user-confirmed in earlier brainstorming）**:
- ✅ 实现 **CookieCloud upload API 协议**（让用户复用现成 Chrome 扩展自动推 cookie 上来）—— 协议是 AES-128-CBC + PKCS7 + 共享 password key，公开文档
- ✅ **Hook 机制**：T1（cookie 更新触发）+ T2（定时触发）→ A1（exec shell）+ A3（write_file，按 template 写）
- ✅ 简单 **CLI**：`cookie-manager list / show domain=<x> / dump`
- ❌ **WebUI**（v1+ 推迟，因为 v1 用户只在 PC + Android Kiwi/Yandex 装 CookieCloud 扩展抓取，WebUI 主要是 iOS 移动端 fallback）
- ❌ **HTTP webhook 动作**（A2）—— v1+ 推迟
- ❌ **自带 Chrome 扩展 fork** —— 直接用 CookieCloud 现成扩展，不 fork
- ❌ 不实现 LLM 调用（CookieManager 是纯协议服务）

**部署形式**：Node.js + Express，Docker compose。MIT 许可。

**架构路径决策**：R1 调研推荐两条，**首选 fork CookieCloud** 然后加 WebUI（v1+）+ hook 模块。**备选**：自家服务实现 CookieCloud upload API 协议，复用扩展。两条**都允许，由 brainstorming 阶段定**——确认时考虑：维护负担（fork 跟随上游 vs 自家代码全权控制），代码量（fork ~80% reusable vs 自写 ~150 行核心），未来 WebUI 集成路径。

## 2. Inputs (minimum set — do NOT load anything else)

| 文件 / 资源 | 角色 |
|---|---|
| `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` §7 SP-1 entry + §6 recipe v2 pipeline | 子项目定位 + 流水线契约 |
| `CLAUDE.md` §2 + §3 + §4 (v2 已生效) | 治理 + invariants |
| `docs/Dashboard/index.md` §SP Status Board | 自己的状态行（你完成各 stage 时更新） |
| `~/.claude/skills/superpowers/brainstorming/SKILL.md` | brainstorming 流程（你需要时调用 Skill tool） |
| `~/.claude/skills/superpowers/writing-plans/SKILL.md` | writing-plans 流程 |
| `~/.claude/skills/sendbox-protocol/SKILL.md` §A-12 stop-and-ask、§child-handoff | 沟通协议 |
| **CookieCloud 上游**: https://github.com/easychen/CookieCloud README + issue #69 (webhook) + issue #124 (WebUI) | 你需要深读这些来出 design；fork 路径需读 server 端 Express 代码结构 |
| **CookieCloud 协议参考实现**: PyCookieCloud (https://github.com/lupohan44/PyCookieCloud) — AES-128-CBC + PKCS7 解密示例 | 自写路径的协议复刻参考 |

**Do NOT read** unless brainstorming/design 明确需要：
- `docs/RepoMem/persist/architecture/` 全部（与 SP-1 无关）
- `docs/RepoMem/persist/memory/pre-openspec-decisions.md`（已被 R5 部分推翻，且 SP-1 不涉及 ASR/B 站决策）
- SP-0 plan.md（impler 的执行细节，与你无关）
- 其他 SP-X 的任何文档（SP-1 阶段不需要）

## 3. Pipeline execution (v2 8-step)

执行 v2 pipeline 的步骤 1–7，**步骤 8 留给 orche（HITL merge）**。

### 3.A Step 1: RepoMem.read

- **Global persist**（read-only）：`docs/RepoMem/persist/config.md`（语言策略 + grandfather）；`docs/RepoMem/persist/version-plan.md`（A2A 英文，recipe 历史）
- **Module persist**：`Service/crawl/cookie-manager/docs/RepoMem/{architecture,decisions}.md`——**SP-0 完成后才存在**；Stage 1 + Stage 2 期间可忽略，Stage 3 前再读

### 3.B Step 2: Superpowers.brainstorming

**Auto-judge**：intent likely **clear**（§1 v1 scope + R1 调研结论已经把 path A vs B 二选一摆桌上），可以走 brainstorming skill 的 "skip on clear intent" 豁免，**但**：

- 仍需 invoke `superpowers:brainstorming` skill（CLAUDE.md §3 step 2 不能完全 silent skip）
- 走入后**压缩**到：(a) 跟用户确认 path A (fork CookieCloud) vs path B (自写服务) 的选择；(b) 跟用户确认是否要保留 Chrome 扩展的兼容（v1 必须）；(c) 跟用户确认 hook 配置 schema（exec 命令 + write_file template 字段长啥样）
- Brainstorming clarifying Q&A 走**直接 chat**（用户开你这个 session 后直接对话），**不**通过 sendbox letter（高 latency 没必要）
- design.md 落到 `<root>/docs/superpowers/specs/2026-05-31-SP-1-cookie-manager-design.md`（**注意**：因 SP-0 未完成，`Service/crawl/cookie-manager/docs/` 子目录还不存在；落 root 是 temporary location；Stage 3 开始时 `git mv` 进模块目录）

### 3.C Step 3-4: RepoMem.capture + writing-plans

- temp 目录：因 SP-0 未完成，本应在 `Service/crawl/cookie-manager/docs/RepoMem/temp/sp1-cookie-manager/` 的临时 docs **暂时**落到 `<root>/docs/RepoMem/temp/sp1-cookie-manager/`（同样 Stage 3 开始时 `git mv`）
- plan.md 落 `<root>/docs/superpowers/plans/2026-05-31-SP-1-cookie-manager-plan.md`（temporary location，同样 Stage 3 开始时 `git mv`）
- **Stage 2 完成的标志**：plan.md + 跑完 writing-plans skill 的 self-review → 写 plan-ready letter（§4）

### 3.D Stage 2 → Stage 3 gate（**关键 HITL 点**）

Stage 2 写完 plan-ready letter后，**STOP**。等以下任一信号 satisfied:

1. **SP-0 done 信号**：`docs/sendbox/toOrchestrator/from-sp0impler-sp0-done.md` 存在；同时 `Service/crawl/cookie-manager/` 目录存在（`ls Service/crawl/cookie-manager/ 2>&1` 不报错）
2. **Orche greenlight 信号**：`docs/sendbox/toSP1Impler/from-orche-sp1-greenlight.md` 存在（orche 显式说"开跑"）

**两者必须都过**才能开 Stage 3。

Stage 3 开始时**首件事**：
```bash
git mv docs/superpowers/specs/2026-05-31-SP-1-cookie-manager-design.md Service/crawl/cookie-manager/docs/superpowers/specs/
git mv docs/superpowers/plans/2026-05-31-SP-1-cookie-manager-plan.md Service/crawl/cookie-manager/docs/superpowers/plans/
git mv docs/RepoMem/temp/sp1-cookie-manager Service/crawl/cookie-manager/docs/RepoMem/temp/sp1-cookie-manager
git commit -m "chore(SP-1): move design/plan/temp into module dir post-SP-0"
```

### 3.E Step 5-7: execute + verification + finishing-a-development-branch

- 用 `using-git-worktrees` skill 起 worktree（在 `Tools/JarvanKB/.worktrees/sp1-cookie-manager/` 或类似）
- TDD：每个功能模块（cookie store / hook engine / CLI）先写 failing test，再实现
- `Superpowers.verification-before-completion`：单一闸门，必须跑 lint + tests + manual smoke（**手动 smoke 必须**：启动服务、用 PyCookieCloud client 推一条 fake cookie、看 hook 触发并写文件）
- `requesting-code-review` + `finishing-a-development-branch` 都 **ask-first**（写 letter 问 orche 是否进入）

### 3.F Step 8: NOT YOUR JOB

`RepoMem.merge` 是 HITL，orche 在你完成 SP-1 后跑。你只要把 module decisions.md 写好就行。

## 4. Convergence paths

**Parent's cwd**: `/home/shenzhou/Codes/awesome_agent_tools/Tools/JarvanKB/`（你和 orche 同 cwd；用相对路径即可）

| 事件 | 写信地址 |
|---|---|
| Stage 1 design.md 落盘完，求 user review | （直接 chat 或）`docs/sendbox/toOrchestrator/from-sp1impler-design-ready.md` |
| Stage 2 plan-ready | `docs/sendbox/toOrchestrator/from-sp1impler-plan-ready.md`（按 cc-sendbox `plan-ready` 类型：step checklist + plan path + key decisions + items needing ack + risk signals） |
| Blocker（A-12 stop-and-ask） | `docs/sendbox/toOrchestrator/from-sp1impler-blocker-<topic>.md` |
| Code review 需求（Step 7） | `docs/sendbox/toOrchestrator/from-sp1impler-review-request.md` |
| 完成 | `docs/sendbox/toOrchestrator/from-sp1impler-sp1-done.md` |
| Orche 回复（用户回复 orche，orche 写信给你） | `docs/sendbox/toSP1Impler/from-orche-*.md`（greenlight / decisions / questions） |

**用户直接对你说话**：当用户开这个 CC session 时，所有 brainstorming clarifying questions、design review、greenlight 都走直接 chat。Sendbox 用于**跨 session 协调**（orche 不在场时记录决策）和**异步触发**（用户离场时 plan-ready 等通知）。

## 5. Out-of-scope (forbidden actions)

You MUST NOT:

- **Stage 3 开始前**做任何 `Service/crawl/cookie-manager/` 内的写操作（目录尚不存在，SP-0 在跑）
- **碰 SP-0 的 plan / design / temp 文件**（contract not yours）
- **修改 design.md 或 plan.md 已落盘内容**（contract once finalized）—— 如需修改，先写 blocker letter
- 修改 `CLAUDE.md` / `docs/HarnessStack/longterm.md`（治理层，跨模块；要改先 blocker letter 给 orche）
- 修改 `docs/RepoMem/persist/`（global memory）—— 你的 decisions 写到 `<module>/docs/RepoMem/decisions.md` 即可，HITL merge 时 orche 决定是否 promote 到 global
- **`git push`** 或 `git merge to main` 任何分支（local commits only）
- **`git rebase`** 或重写历史
- Spawn 你自己的 sub-impler / sub-orche，**除非** brainstorming/writing-plans 阶段发现 SP-1 需要分解（罕见，先 blocker letter 跟 orche 讨论）
- 安装 Docker / 起 Docker 容器作为 SP-1 一部分（部署是 user 操作；你出 docker-compose.yml 即可）
- 编辑 `docs/sendbox/toOrchestrator/handoff.md`（orche 的入站箱）—— 那是 orche 内部信件
- 编辑 `docs/sendbox/toSP0Impler/handoff.md` 或 SP-0 impler 写的信件（跨 impler 隔离）

You MAY:

- 跑 `git status / log / diff / show / blame`、`ls / find / grep` 任何 read-only 命令
- **WebFetch** 或 **WebSearch**（**优先用 Tavily MCP**，参见 root `CLAUDE.md` 联网规则）查 CookieCloud 源码、协议文档、社区讨论
- 跑 `npm view <pkg>` / `pip show <pkg>` 等 read-only 包查询
- 创建 git worktree（Stage 3 内必须用）
- TaskCreate / TaskUpdate 跟踪你自己的 stage 进度（独立于 orche 任务列表）

## 6. Branch + worktree state at handoff

- Branch: `feat/agentcrawl-bootstrap`（parent repo `awesome_agent_tools` 的）
- HEAD：见 `git log -1 --oneline`；正在并行接收 SP-0 impler 的 commit 流
- 当 Stage 3 启动时，先 `git pull` 或 `git fetch + rebase` 到 SP-0 impler 最新（确保 `Service/crawl/cookie-manager/` 已落地）；然后**起独立 worktree** 跑你的 execute 阶段，避免和 SP-0 impler 共享工作树

## 7. Reporting cadence

| 频率 | 内容 |
|---|---|
| **Stage 1 / 2 内**：每完成一个 milestone（design 落盘、plan-ready）写 letter | 单条 letter，结构化 |
| **Stage 2 → 3 gate 期间**：每 5 min 自检一次 SP-0 done 信号；满足后立即转 Stage 3 | 不写 letter |
| **Stage 3 内**：commit 流即可见状态；卡住才写 blocker | letter 仅在 ask-first / blocker / done 时 |
| 任何阶段：用户在 chat 里问你 → 直接答 | 不走 sendbox |

## 8. Lifecycle of this letter

`burn` after impler 写 `from-sp1impler-sp1-done.md` 并 orche 读到。orche 会在它自己的 SP-1 后处理 commit 里 `git rm` 这封信。

**注意区别 SP-0 模式**：SP-0 是单一 stage（直接 execute），所以 sp0-done letter 直接触发 burn。SP-1 是三 stage 长寿命 impler，handoff letter 在 stage 转换期间 persist，最终在 Stage 3 完成后 burn。

## 9. SP-1 Status Board 更新责任

每当你转 stage 或转状态，**同步更新 `docs/Dashboard/index.md` §SP Status Board** 的 SP-1 行：

| Stage 进入 | Dashboard SP-1 Status | Owner Agent |
|---|---|---|
| Stage 1 start | 🟡 wip | sp1impler |
| Stage 2 done, gate 等待 SP-0 | 🔴 blocked | sp1impler |
| Stage 3 start | 🟡 wip | sp1impler |
| 完成 | ⚫ done | sp1impler |

Dashboard 同行编辑（不写新行）。每次转 stage 一个 commit，commit msg 含 `docs(SP-1):` 前缀。

---

**Begin at Step 1 (RepoMem.read), then proceed to Step 2 (brainstorming, likely compressed).** 用户开你这个 session 后，直接说 hi 然后问 "ready to start SP-1 brainstorming?" 或类似，让用户进入对话。
