> from: BilibiliCrawl SubOrche (a Claude Code peer session — sub-orchestrator under root orche g4)
> recipient: BN412Impler (a Claude Code peer session, same cwd as SubOrche = repo root)
> mode: child-handoff (sendbox-protocol Mode A — SubOrche stays alive; you converge back to it)
> purpose: fix the BN-412 downloader risk-control gate (UN-035) so a REAL B站 video transcribes end-to-end
> lifecycle: burn after you write `from-bn412impler-done.md` and SubOrche reads it

# Handoff — BN-412 BiliNote Downloader Remediation (UN-035)

## 0. What you are
A **remediation / ops impler**, my child. The whole Bilibili vertical (SP-4b Skill + SP-5b Watcher) is
code-complete + tested + merged; the ONE thing it has never shown live is **a real video → transcript →
saved Markdown**, because BiliNote's downloader is blocked by bilibili risk-control (`HTTP 412`).

Your job = **make that last hop work** by fixing the BN-side downloader. This is an **ops/infra +
systematic-debugging** task on the self-hosted BiliNote container + its deploy artifacts. It is **NOT** a
feature build, **NOT** a change to SP-4b / SP-5b code, and **NOT** a change to the frozen SP-4a engine source.

**Use `superpowers:systematic-debugging`** as your process skill (this is a bug/unexpected-behavior, not a
feature → not TDD-first). Reproduce → one-variable-at-a-time hypothesis testing → fix → verify.

## 1. The problem (verified 2026-06-10, reproduced 3×)
- BN's internal **yt-dlp** gets persistent `HTTP 412 Precondition Failed` ("Unable to download JSON metadata")
  fetching bilibili video metadata/audio.
- **BN itself is UP + healthy** (`/docs` 200, providers 200, `generate_note`/`task_status` 200). The 412 is
  bilibili risk-control on BN's **downloader egress** (IP / headers / fingerprint), not BN being down.
- **Pushing cookie to BN** (`POST /api/update_downloader_cookie` → 200) did **NOT** resolve it → it's not a
  login-state problem; it's a fingerprint/egress problem.
- The **SP-4a engine's own** `bilibili-api-python` calls (metadata/subtitle) **succeed (200)** — the 412 is
  specifically **BN's yt-dlp**, downstream of the engine.
- SP-4a's smoke **succeeded 2026-06-02** on specific BVs → risk-control tightened since.

## 2. Definition of done — re-run BOTH consumers' left-over live test
After the 412 is fixed, you MUST re-run **both** SP-4b's and SP-5b's outstanding live gate (each was left
incomplete by exactly this 412; do NOT settle for one — they're distinct consumer acceptance gates):
- **SP-4b**: `bilibili-crawl <BV> --out <path>` → a **real saved Markdown note** (its full transcribe→save
  half; the LLM-classification half already passed live).
- **SP-5b**: the watcher `--once` over a real favorite folder **actually transcribes a favorited item →
  saved note** (its success path; the §5 failure-degrade path already passed live).
Confirm BOTH with evidence (saved file paths + transcript content), then promote what actually fixed the 412
(Step-8 → runbook + `§B站链路`). If either consumer reveals a NON-412 issue once unblocked, surface it — but
the 412 fix itself is your gate.

## 3. Candidate fixes — try in order of likelihood (systematic-debugging, isolate one variable)
1. **Egress IP / network (most likely).** bilibili likely flagged the host's IP. Route BN's downloader egress
   through a **clean network** (different IP / clean proxy / mobile tether). Knobs live in the BN deploy
   artifacts `Engine/bilibili/deploy/bilinote/` (compose network / env). *(A clean egress is often a USER op —
   see §4; surface it as a gate, don't stall.)*
2. **Update BN's yt-dlp.** The bilibili 412 is a known yt-dlp arms-race; bumping yt-dlp **inside the BN
   container** to latest often clears it (`docker exec … pip install -U yt-dlp`, or rebuild the image). Verify
   the version before/after.
3. **Anti-detection headers / wbi.** If BN's downloader exposes custom headers/UA config, add browser-like
   headers + wbi signing. Assess feasibility — this likely needs BN-side support; if it needs an **engine**
   change, that's §4 escalate.
4. **Re-confirm cookie freshness/format** after the above (fresh SESSDATA, `bilibili.com` no-dot) — re-test the
   `update_downloader_cookie` push once egress/yt-dlp are addressed.

## 4. Scope / boundaries
**ALLOWED:** operate the `jarvankb-bilinote` container (exec / restart / update yt-dlp / config); edit BN
**deploy artifacts** `Engine/bilibili/deploy/bilinote/` (compose / network / env); push cookie to BN; edit
`Service/crawl/bilibili-watcher/docs/runbook.md`; re-run the SP-4b / SP-5b live smokes; read-only git/ls/grep;
WebSearch for yt-dlp/bilibili-412 fixes.

**OUT OF SCOPE → STOP + escalate to me** (`from-bn412impler-blocker-<topic>.md` → `toBilibiliCrawlOrche/`):
- Editing the **frozen SP-4a engine Python source** (`Engine/bilibili/src/…`). If the only fix is an engine
  code change (e.g. the `BiliNoteClient` missing `trust_env=False`, or the engine passing anti-detect headers
  to BN), **do NOT silently edit it** — the engine is root/SP-4a-owned + frozen; I route engine changes to root.
- Changing **SP-4b / SP-5b code** — they're done + correct and auto-benefit the moment BN transcribes.

**NEEDS USER (surface as a gate — Dashboard row + note, don't stall):** a clean network/IP/proxy only the user
can provide; restarting/redeploying the container (precedent UN-018: "起 docker 容器是 user 操作").

**Git:** local commits only on `feat/agentcrawl-bootstrap`, prefix `fix(bn412):` / `ops(bn412):`. **Commit with
explicit pathspec** (`git commit -- <paths>`) and verify `git diff --cached` first — the index is **shared with
concurrent sessions** (a bare commit sweeps up their staged changes). `gstack` submodule shows `M` — never touch.

## 5. Inputs (minimum set)
| Resource | Role |
|---|---|
| `docs/sendbox/toUser/bn412-bilibili-transcription-blocked.md` | plain-language framing of the problem + fix menu |
| Dashboard `§Active` **UN-035** | the ops-gate tracking row |
| `Service/crawl/bilibili-watcher/docs/runbook.md` (rows ~70–71) | the 412 + SOCKS/`ALL_PROXY` gotchas |
| `docs/RepoMem/persist/architecture/crawl-pipeline.md §B站链路` | BN ops gotchas (nginx→`:8483`, `TRANSCRIBER_TYPE` via API, bcut-no-cookie, + SP-5b's just-landed 412/proxy notes) |
| `Engine/bilibili/docs/interface.md` | engine contract — you VERIFY THROUGH it, don't change it |
| `Engine/bilibili/deploy/bilinote/` | the deploy artifacts you may edit |
| live env | container `jarvankb-bilinote` @ `127.0.0.1:3015` (host→backend `:8483`), `TRANSCRIBER_TYPE=bcut`, provider `mimo-v2.5-pro` |
| **gotcha** | clear `ALL_PROXY`/`HTTP(S)_PROXY` when anything talks to local BN (else `socksio` ImportError) |
| `~/.claude/skills/{superpowers/systematic-debugging,repo-mem,sendbox-protocol,cc-dashboard}` | your protocols |

## 6. Pipeline / lane
**Lane: fast** by default (ops/debug, no new public contract). Bump to **full** only if you end up making a
net-new deploy-contract change. Process = **systematic-debugging** (reproduce the 412 → hypothesize →
isolate → fix → re-verify). **verification-before-completion gate = a REAL video transcribed + saved** (the
exact gate the vertical couldn't pass — evidence required, not assertion). **Step-8 (you own closure):**
promote the *actual* root-cause + fix (what cleared the 412) to `runbook.md` + `§B站链路` (cross-SP-reusable;
mechanism-in-code stays in code); HITL with the user.

## 7. Convergence paths
Parent = BilibiliCrawl SubOrche, cwd = repo root. Inbound replies: `docs/sendbox/toBN412Impler/from-bilibilicrawlorche-*.md`.

| Event | Write to |
|---|---|
| blocker (needs engine change / needs user network / dead-end) | `docs/sendbox/toBilibiliCrawlOrche/from-bn412impler-blocker-<topic>.md` |
| done (real transcription demonstrated) | `docs/sendbox/toBilibiliCrawlOrche/from-bn412impler-done.md` |

## 8. Lifecycle
`burn` after you write `from-bn412impler-done.md` and SubOrche reads it.

---
**Begin:** read §5 inputs, **reproduce the 412** (systematic-debugging — confirm it still fails today, capture
the exact error + yt-dlp version + egress IP), then work the §3 candidates cheapest-first. Surface the
network/user gate early if egress is the cause; don't stall on it.
