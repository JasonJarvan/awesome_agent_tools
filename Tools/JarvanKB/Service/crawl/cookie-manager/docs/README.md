# cookie-manager

> **SP-1 CookieManager**
> Status: **implemented** (v1, 2026-05-31). Path B — 自写 Express 服务复刻 CookieCloud 协议（非 fork）。

## What this does

复刻 CookieCloud upload-API 协议的接收服务 + hook 引擎（T1 cookie-update / T2 cron → A1 exec / A3 write_file）
+ CLI（list/show/dump）。复用现成官方 CookieCloud 浏览器扩展（不 fork、不改），把扩展服务器地址指向本服务即可。

## Kind

service（Node.js + TypeScript + Express，MIT 许可，Docker compose 部署）

## See also

- 使用说明 / 部署（人类可读）：模块根 `README.md`
- 对外契约（下游集成）：`docs/interface.md`
- 架构概览：`docs/architecture.md`
- 内部设计 / 决策：`docs/RepoMem/{architecture,decisions}.md`
- 权威设计：`docs/superpowers/specs/2026-05-31-SP-1-cookie-manager-design.md`（+ `.zh.md`）
- 实现计划：`docs/superpowers/plans/2026-05-31-SP-1-cookie-manager-plan.md`
- 顶层定位：`<root>/docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` §7
