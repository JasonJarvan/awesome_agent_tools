> from: SP5bImpler (Claude Code peer session, child of BilibiliCrawl SubOrche; cwd = repo root; active 2026-06-10→11)
> recipient: BilibiliCrawl SubOrche (my parent)
> purpose: SP-5b Bilibili Watcher DONE — full v2 pipeline closed (Stage 0 → Step 8). Convergence + Step-8 diff.
> lifecycle: burn after SubOrche reads (rolls SP-5b into the vertical roll-up). My inbox handoff/greenlight burned.
> date: 2026-06-11

# ⚫ SP-5b Bilibili Watcher — DONE (v2 pipeline 1→8 closed, impler-owned merge)

## 1. TL;DR
SP-5b shipped: a 7-component polling daemon, **44 unit+integration tests**, **live pipeline verified**
(incl. the §5 failure-degrade path observed live), merged locally, **Step-8 promotion applied per your
R1-R3** (`5d4a13d`). The one non-green item is the **BN yt-dlp HTTP-412** (transcription can't complete
live) — external to SP-5b, vertical-wide, carried as **UN-035** (you flagged SP-4b hits the same).

## 2. Stage 0 (the reason this SP existed) — vindicated
Empirically crawled the real favorites API with the user's cookie (2026-06-10): **`fav_time` exists and
IS the collected-time, distinct from `pubtime`** (fav 04-24 vs pub 04-16). The user-review gate (UN-029)
ratified it. This is the positive close on SP-5a's armchair "no reliable favorite-time" — exactly what the
Stage-0 gate was designed to catch.

## 3. What shipped (merged `51557db` → local feat/agentcrawl-bootstrap; worktree removed, branch deleted)
- 7 components mirroring SP-5a: `config / cookie_provider / favorites_client / watermark_store / fetcher /
  saver / watcher` + `__main__` (BlockingScheduler, `max_instances=1`, `--once`).
- **Δ1 engine**: pure consumer of the frozen SP-4a engine (`transcribe(bvid).render(...).main_markdown`).
- **Δ2 watermark**: `fav_time` high-watermark (`order=mtime` early-stop) **+ `bvid` seen-set** (idempotency);
  §5 advance rule `min(failed)-1` (retry-safe). Verified LIVE: an engine failure left watermark held below
  the failure, item not seen, daemon survived.
- `type==2` only; cookie active-PULL (`bilibili.com`, no dot, SESSDATA+bili_jct → BilibiliCredential).
- Deploy: Dockerfile + compose (`network_mode: host`) + example config; module docs frozen
  (`docs/interface.md` is the contract) incl. runbook (proxy + 412 gotchas).

## 4. Verification (verification-before-completion)
- **44/44** tests (fresh run on the merge candidate). Subagent-driven: per-cluster two-stage review + final
  holistic review = READY TO MERGE.
- **Live**: cookie pull, favorites list, `fav_time` early-stop, engine invocation — all real, 3× consistent.
- **Blocked live**: a successful transcription → saved Markdown, by **BN yt-dlp `HTTP 412`** (bilibili
  risk-control; pushing cookie to BN didn't help). Frozen-engine + BN + env → **UN-035** (vertical ops gate).
  Per your R3: 412 sits below the engine; engine-side rate-limiting wouldn't fix it; SP-5b adds none and
  degrades gracefully (confirmed).

## 5. Step 8 RepoMem.merge (impler-owned closure) — applied per your R1-R3
- **Promoted to `crawl-pipeline.md §B站链路`** (`5d4a13d`): (Part 1) NEW favorites-API sub-section
  (endpoints / no-signing / `fav_time`≠`pubtime` / `order=mtime` DESC early-stop / `has_more`-not-`media_count`
  paging) + R1 closing line → `memory/empirical-api-first.md`. (Part 2a) unset-`ALL_PROXY` deploy rule with the
  root-cause reframed as a **SP-4a engine fix candidate** (you escalated to root; mechanism not promoted).
  (Part 2b) BN-412 as a **hazard + mitigations + arch note**, current state cross-ref'd to **UN-035** (not
  persist-as-state).
- Module specifics (D1–D8) live in `bilibili-watcher/docs/RepoMem/decisions.md` (merged in `51557db`).
- `temp/sp5b-bilibili-watcher/` **pruned**.
- **Diff for your verification: `5d4a13d`** (27 insertions, §B站链路 only).

## 6. Convergence
SP-5b status-board cell flipped ⚫ done. I burned my inbox `handoff.md` + your `…-greenlight.md` (lifecycles
satisfied) and my superseded `…-plan-ready.md` / `…-blocker-fav-api-review.md`. **Kept**
`…-blocker-bn412-downloader.md** (open gate, feeds your vertical roll-up + UN-035). No push; engine untouched.
Ready for your `from-bilibilicrawlorche-vertical-done.md` roll-up (SP-4b ⚫ + SP-5b ⚫; UN-035 carried open).
