---
from: sp1impler
to: orchestrator
type: milestone-done
slug: sp1-cookie-manager
status: open
created: 2026-05-31
lifecycle: burn after orche reads + runs Step 8 (RepoMem.merge) + burns toSP1Impler/handoff.md
---

# SP-1 CookieManager — DONE (Stages 1–8 complete)

The v2 pipeline steps **1–8** are complete and the branch is finished. Step 8 (RepoMem.merge) was
**executed by the impler** within its lifecycle (user-directed, HITL-approved) — see the Step 8 section below.

> **📥 ACTIONS FOR ORCHE (please read this letter, then):**
> 1. **Post-SP-1 housekeeping** — burn this letter + `docs/sendbox/toFRPS/handoff.md` (both resolved);
>    optional `RepoMem.prune`/`split`. (Step 8 merge already done — do NOT redo.)
> 2. **Amend the merge-ownership norm** — the handoff-template/pipeline rule that says Step 8 is orche-only
>    is wrong per the user. See **"Process feedback for orche"** below.

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

## Step 8 (RepoMem.merge) — UPDATE: EXECUTED by sp1impler (2026-05-31, HITL-approved by user)

Per the user's explicit instruction, the impler drove RepoMem.merge to completion within its own
lifecycle (rather than leaving it as an orche TODO). Done: **activated the reserved `credentials` domain**
(`docs/RepoMem/persist/architecture/credentials.md` + domain map flipped to 活跃); promoted the GPLv3/path-B
decision + the "reimplement-protocol-over-fork" pattern + the downstream protocol-contract pointer. Module
implementation details (crypto modes, YAML hooks, TS, accounts) were NOT promoted (stay module-local).
`temp/sp1-cookie-manager/research.md` retained (not pruned). **Orche: no need to redo; prune/split at
your discretion.** Original promotion candidates (now done) below for reference.

## Process feedback for orche — amend the merge-ownership norm (user-directed)

The user has ruled that **`RepoMem.merge` (Step 8) must close within the impler's OWN lifecycle**: the impler
drives it to completion (HITL), delegating *execution* to orche only if explicitly chosen — never
fire-and-forget. The SP-1 handoff **§3.F ("Step 8: NOT YOUR JOB — orche runs it")** directly contradicts this
and caused the impler to initially defer the merge.

**Action for orche — fix the norm so this does not recur:**
- In the **impler-handoff template** (the block you write into each SP handoff as §3.F): replace the
  "NOT YOUR JOB" framing with → "**You (impler) own RepoMem.merge closure** — after
  `finishing-a-development-branch`, run it (HITL) yourself, or delegate execution to orche but track it to
  completion before reporting done."
- If Step-8 ownership is codified in `docs/HarnessStack/longterm.md` §Pipeline v2 (or `CLAUDE.md` §3 step 8,
  which currently names no owner), align it to make the **impler the owner** of merge closure.
- (Standing lesson also captured in the impler session memory `impler-owns-repomem-merge`.)

## For your Step 8 (RepoMem.merge, HITL) — original candidates (now executed above)

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

## Addendum — post-merge follow-ups (2026-05-31, on user request; all on feat/agentcrawl-bootstrap, 45 tests green)

- **Port 8088 → 48088** (JarvanKB **48xxx** port convention; recorded in host ops `rules.md`; commit `a382452`).
- **Public frp exposure — verified end-to-end** (public HTTPS push → store → hook): `https://www.zhaoricheng.fun:48098`
  (Nginx TLS) + direct `http://101.35.46.114:48088`. frps needed no allowPorts change. `docs/sendbox/toFRPS/handoff.md`
  resolved (frps-side AI added the Nginx 48098→48088 SSL proxy). frpc recorded in ops `manual-software.txt`.
- **Optional shared-secret header auth** (`server.auth_token` → `X-CookieCloud-Token`, 401 except `/health`; commit `2f39367`).
- **`config/cookie-manager.yaml` gitignored** (secrets); a placeholder-only copy was briefly committed then untracked (`debf429`, no real secret leaked).
- Full module decision log (incl. these): `Service/crawl/cookie-manager/docs/RepoMem/decisions.md` (top entry) — fold into Step 8 RepoMem.merge.
