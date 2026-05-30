# User Now — Pending Actions

> Single source of truth for "what the user needs to do next" in AgentCrawl.
> Authors: any agent session may append. Reader: user.
> Protocol contract: `~/.claude/skills/cc-dashboard/SKILL.md`
> Repo-local hook (language policy, mark-done owner, triggers): `docs/HarnessStack/hooks/cc-dashboard.md`

## Active

| ID | Type | Action | Where (detail) | Blocker for | Since | Status |
|---|---|---|---|---|---|---|
| UN-003 | B | 起新 orchestrator 会话，按 handoff §7 提交当前状态 + 开 Phase 2 OpenSpec change `bilibili-audio-mvp` | `docs/sendbox/toOrchestrator/handoff.md` | Phase 2 开工（B站音频→OSS→Tingwu 最小链路） | 2026-05-30 | open |
| UN-004 | F | 确认已开通：阿里云 AK/SK + Tingwu 服务 + OSS bucket（同区域，私有，prefix `agent-crawl/` 24h 生命周期） | `docs/RepoMem/persist/memory/runbook.md` §1–2 | UN-003 步骤 3（`/opsx:propose` 之前的凭据 pre-flight） | 2026-05-30 | open |

## Archive

| ID | Action | Done | By |
|---|---|---|---|
| UN-001 | 授权全局安装 OpenSpec CLI（`npm i -g @fission-ai/openspec` → v1.3.1） | 2026-05-27 | bootstrap session |
| UN-002 | 把 handoff 带到 `~/Codes/AgentCrawlers/` 起 ruflo 会话 — **obsoleted**：2026-05-30 决定继续在当前 repo 开发，迁移取消 | 2026-05-30 | bootstrap session |
