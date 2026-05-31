---
from: sp1impler
to: orchestrator
type: milestone-done
slug: sp1-cookie-manager
status: open
created: 2026-05-31
lifecycle: burn after orche reads + runs Step 8 (RepoMem.merge) + burns toSP1Impler/handoff.md
---

# SP-1 CookieManager — DONE (Stages 1–7 complete)

The v2 pipeline steps 1–7 are complete and the branch is finished. **Step 8 (RepoMem.merge, HITL) is yours.**

## Outcome

Self-written Node.js/TypeScript + Express service speaking the CookieCloud upload-API protocol
(the official browser extension pushes to it unchanged). Hook engine (T1 cookie-update + T2 cron →
A1 exec + A3 write_file), CLI (list/show/dump), Docker compose, MIT.

- **Merged** into `feat/agentcrawl-bootstrap` (merge commit `b84ee0f`, `--no-ff`). Worktree removed,
  branch `sp1-cookie-manager` deleted. **No push** (handoff §5). Clean 3-way merge — zero file overlap
  with your concurrent commit `c7b5d8e`.
- Code at `Service/crawl/cookie-manager/` (10 src + 9 test files + config/docker/docs).

## Verification evidence (verification-before-completion gate passed)

- `npx tsc --noEmit` clean + `npx vitest run` → **40 tests passed** (re-confirmed on the merged tree in the main checkout).
- **Crypto correctness cross-validated** by independent `node:crypto` OpenSSL oracles (a different
  implementation than crypto-js) for BOTH legacy and aes-128-cbc-fixed — guards against self-consistent-but-wrong.
- **Manual smoke passed**: started the service, pushed a fake cookie via a crypto-js client, observed the
  hook fire and write the domain-narrowed cookies (`[{"name":"z_c0","value":"SMOKE",...}]`) end-to-end; CLI show/list verified.
- Final code review (opus) → CHANGES_REQUESTED (2 Important + minors), all addressed in `2c3488a`; re-verified.

## Pipeline trace

1 RepoMem.read ✓ · 2 brainstorming (compressed, 3 decisions + 1 clarification, all via direct chat) ✓ ·
3 RepoMem.capture (`research.md`) ✓ · 4 writing-plans (11 TDD tasks, self-reviewed) ✓ ·
5 worktree + executing-plans + TDD (12 tasks, subagent-driven) ✓ · 6 verification ✓ ·
7 requesting-code-review + finishing-a-development-branch (merged) ✓.

## Key decisions (full log: `Service/crawl/cookie-manager/docs/RepoMem/decisions.md`)

- **D1 Path B (self-write, NOT fork).** Material correction: easychen/CookieCloud is **GPLv3, not MIT**
  (handoff §1 assumed MIT). Fork would impose copyleft; self-write keeps MIT + full control.
- D2 dual crypto mode; D3 flat YAML hooks; D4 TypeScript; D5/D6 accounts=passphrase-only, single-box (schema supports N).

## For your Step 8 (RepoMem.merge, HITL)

- **Candidate for global promotion:** the GPLv3 finding + the "reimplement-the-protocol over fork" pattern,
  since SP-2/SP-3/SP-4b/SP-5a/SP-5b all reference SP-1's protocol contract. Module decisions.md flags it.
- **SP-1 protocol contract is now frozen** at `Service/crawl/cookie-manager/docs/interface.md` — this satisfies
  the SP-2 entry condition "SP-1 协议敲定". Downstream cookie-consumers integrate against that file.
- Deferred (documented in decisions.md, non-blocking): uuid match is exact-or-`*` not full glob; no
  write-then-read-back byte-compare (writeFileSync throws on failure).

## Loose ends / notes

- `from-sp1impler-plan-ready.md` (this mailbox) can be burned alongside this letter.
- UN-005 (AgentCrawl→JarvanKB rename) completed mid-flight; SP-1 design.md was salvaged byte-identical
  into JarvanKB and the orphan `Tools/AgentCrawl/` was removed (verified zero unique content) — already handled.
- Dashboard SP-1 row set to ⚫ done in the same commit as this letter.

## Next SPs unblocked

SP-2 (Zhihu Engine — needs SP-0 done ✓ + SP-1 协议敲定 ✓), and the cookie-consuming SP-3/4b/5a/5b once their
own engine prerequisites land.
