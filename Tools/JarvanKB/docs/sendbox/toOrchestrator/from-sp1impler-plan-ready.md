---
from: sp1impler
to: orchestrator
type: plan-ready
slug: sp1-cookie-manager
status: open
created: 2026-05-31
lifecycle: burn after orche reads + SP-1 Stage 3 greenlit
---

# SP-1 CookieManager — plan-ready (Stage 2 complete)

Stages 1 + 2 of the v2 pipeline are done. **Stopping at the Stage 2→3 gate per handoff §3.D.**

## Step checklist (pipeline 1–7; 8 is orche's)

- [x] 1. RepoMem.read (global persist + module two-layer)
- [x] 2. brainstorming (compressed) — 3 decisions confirmed with user + 1 follow-up clarification
- [x] 3. RepoMem.capture — `docs/RepoMem/temp/sp1-cookie-manager/research.md` (6-agent verified research)
- [x] 4. writing-plans — plan.md written + self-reviewed
- [ ] 5–7. execute / verify / finish — **GATED** (this letter)

## Artifacts (temp root location per handoff §3.B/§3.C; `git mv` into module at Stage 3 start)

- Design (EN canonical): `docs/superpowers/specs/2026-05-31-SP-1-cookie-manager-design.md`
- Design (ZH, H2A): `docs/superpowers/specs/2026-05-31-SP-1-cookie-manager-design.zh.md`
- Plan: `docs/superpowers/plans/2026-05-31-SP-1-cookie-manager-plan.md`
- Research capture: `docs/RepoMem/temp/sp1-cookie-manager/research.md`

## Key decisions (user-confirmed)

- **D1 Path B — self-write Express service, NOT fork.** Material finding: easychen/CookieCloud is
  **GPLv3, not MIT** (handoff §1 assumed MIT). Fork buys ~287 LOC but adds copyleft + rebase friction +
  an unextensible upstream. Self-write ≈40-70 LOC, MIT, crypto-compat via reused `crypto-js`.
- **D2 Dual crypto mode**: legacy (default, official extension) + aes-128-cbc-fixed.
- **D3 Flat per-hook YAML** config (research Option 1).
- **D4 TypeScript** (silent interop failure modes → compile-time shape locking).
- **D5/D6 accounts model**: `accounts: [{uuid, password}]` (passphrase only; cookies arrive via /update,
  not config). **Single box** for v1 (one Zhihu + one Bilibili login shared PC/Android), schema supports N.

## Items needing ack / greenlight

1. **Stage 3 greenlight (UN-012).** Gate = SP-0 done ✅ (`from-sp0impler-sp0-done.md` + module dir exist)
   AND orche/user greenlight. The user is driving the SP1Impler session directly, so a direct "go" in chat
   satisfies the greenlight (no `from-orche-sp1-greenlight.md` needed unless orche prefers the letter path).
2. **Execution mode** (writing-plans handoff): subagent-driven (recommended) vs inline.
3. **License intent confirmed MIT** — flagging because handoff §1 said MIT while the path-A target was GPLv3;
   path B keeps us MIT-clean. No conflict, just recording the correction.

## Risk signals

- R1 (low): exact extension Content-Type — mitigated (accept json + urlencoded).
- R2 (low): whole-blob last-write-wins across devices — non-issue for single-box-both-logins; README notes it.
- R3 (med): `crypto-js` is maintenance-only upstream — acceptable for v1; decrypt path is small + replaceable.
- Process note: UN-005 (AgentCrawl→JarvanKB rename) completed mid-flight; SP-1 design.md was salvaged
  byte-identical into JarvanKB and the orphan `Tools/AgentCrawl/` was removed (verified zero unique content).

## Next action when greenlit

`git mv` design/plan/research-temp into `Service/crawl/cookie-manager/...`, commit, create worktree, then
execute the plan task-by-task (TDD) → verification-before-completion (incl. mandatory manual smoke) →
requesting-code-review + finishing-a-development-branch (both ask-first) → `from-sp1impler-sp1-done.md`.
