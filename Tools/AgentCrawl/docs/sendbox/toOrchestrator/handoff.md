> from: bootstrap-orchestrator (sessions 2026-05-26 → 2026-05-30)
> recipient: next orchestrator session for AgentCrawl
> mode: inheritance
> purpose: hand over full orchestrator responsibility; no convergence back
> lifecycle: persist until inheritor logs first `milestone-done.md`, then burn

# AgentCrawl Orchestrator — Inheritance Handoff

## 1. Identity statement

You are the **AgentCrawl orchestrator**, inheriting full responsibility for
this repo (`~/Codes/awesome_agent_tools/Tools/AgentCrawl/`). Scope:
deliver a Python tool collection that lets caller agents crawl Zhihu URLs
and Bilibili videos and save markdown+json locally. HarnessStack recipe
`openspec-superpowers-repomem-sendbox-dashboard` is active. There is no
parent session to report back to.

## 2. Status snapshot

| Layer | Status | Evidence |
|---|---|---|
| HarnessStack bootstrap | **done** | `docs/HarnessStack/{README,longterm,_toUser/README}.md` user-authored; CLAUDE.md distilled |
| RepoMem persist scaffold | **done** | `docs/RepoMem/persist/{config,version-plan}.md` + `architecture/` + `memory/` populated |
| RepoMem `harness-bootstrap` task docs | **merged** | `docs/RepoMem/temp/harness-bootstrap/{init-proposal,init-conflicts}.md` (status: merged); NO formal `RepoMem.merge` HITL was run because nothing in `temp/` was promotion-worthy |
| OpenSpec CLI install | **done** | v1.3.1 global via npm (`~/.nvm/.../bin/openspec`); root symlink `openspec → docs/openspec` |
| OpenSpec workspace | **empty** | `docs/openspec/changes/` + `specs/` exist; no change proposed yet |
| Skills installed | **done** | `~/.claude/skills/{repo-mem,sendbox-protocol,cc-dashboard}` symlinks; `.claude/skills/openspec-*` per-repo; `.claude/commands/opsx/*` per-repo |
| cc-dashboard | **active** | `docs/Dashboard/index.md` seeded; hook config `docs/HarnessStack/hooks/cc-dashboard.md` (mark-done=option-a, language=zh for Action column) |
| sendbox tree | **active** | only `toAgent/handoff.md` (placeholder caller contract) + this letter |
| Phase 2 code | **not started** | no `scripts/` directory exists |
| Git | **uncommitted** | branch `main` of parent repo `awesome_agent_tools`; everything under `Tools/AgentCrawl/` is untracked. **Commit early** before doing real work — see §6 |

Counts: 14 RepoMem docs + 1 dashboard + 1 hook + 2 sendbox letters + CLAUDE/README + 4 OpenSpec skills + 4 opsx commands + `openspec/` workspace dirs.

## 3. Must-read list (in this order)

1. `CLAUDE.md` — always-loaded contract (recipe, 13-step pipeline, hard invariants, Where-to-Look table)
2. `docs/HarnessStack/longterm.md` — authoritative pipeline / merge gates / cross-method invariants
3. `docs/HarnessStack/_toUser/README.md` — Day-One Init usage, per-task loop description
4. `docs/RepoMem/persist/architecture/crawl-pipeline.md` — full data flow + fallback chains for both pipelines
5. `docs/RepoMem/persist/memory/runbook.md` — env vars + cookies + OSS bucket + **§0 OpenSpec symlink note (don't delete it)**
6. `docs/RepoMem/persist/memory/pre-openspec-decisions.md` — D1–D7 frozen decisions (subtitle vs ASR, Tingwu choice, no-parsevideo, etc.)
7. `docs/RepoMem/persist/version-plan.md` — phase plan (Phase 2 is next)
8. `docs/Dashboard/index.md` — current pending user actions
9. `docs/sendbox/toAgent/handoff.md` — caller-agent contract placeholder (Phase 2 must fill it)

Skip the contents of `docs/RepoMem/temp/harness-bootstrap/` (merged, historical only).

## 4. Pending decisions you must finalize

Four were left open at bootstrap close. Resolve when relevant; do not block on them now:

1. **Concurrency / queueing** — single-shot CLI or background worker? Depends on caller (Hermes) call pattern.
2. **Result caching** — should re-fetching a URL hit a local cache? Probably yes for Zhihu (by URL hash); B站 subtitle/ASR results are expensive to redo.
3. **Cookie rotation cadence** — Phase 4 design implied but not specified (the `cookies/refresh_chrome_cdp.py` story).
4. **Output file granularity** — single combined `{platform}_{id}.md` or split into transcript/summary/keyframes?

These should be settled inside the OpenSpec change that first touches each concern, not preemptively.

## 5. Active relationships

- **Caller agents** (Hermes Agent v0.14.0 at `~/.hermes/hermes-agent/`, plus any other) — they read `docs/sendbox/toAgent/handoff.md`. That handoff is currently a placeholder; **Phase 2's deliverable includes filling it with real I/O contracts**.
- **Parent repo** `~/Codes/awesome_agent_tools/` — this directory is a subtree, not a submodule. Top-level `AGENT.md` describes the umbrella project; conventions apply.
- **No active subagent sessions** at handoff time. No `from-<x>-*.md` letters pending response.
- **`toRufloAgent/` was deleted** by the operator on 2026-05-30 after deciding against the ruflo migration. Its `handoff.md` (RufloAgent letter) used to exist; ignore any stale references.

## 6. Env / tool state

- Branch: `main` of parent repo `awesome_agent_tools`
- Working tree: **all of `Tools/AgentCrawl/` is untracked**. Nothing is committed yet. **Recommended first commit**: `git add Tools/AgentCrawl/ && git commit -m "feat(AgentCrawl): scaffold HarnessStack bootstrap + RepoMem + OpenSpec workspace"` — atomic checkpoint before Phase 2 starts.
- Submodule `gstack` shows `M` in `git status` — pre-existing, unrelated, do not touch.
- `~/.nvm/.../bin/openspec` v1.3.1 installed globally; `which openspec` should resolve.
- `openspec list` from repo root works via the symlink — verify before first `/opsx:propose`.
- **Do not delete the root `openspec` symlink.** It is the only way OpenSpec CLI discovers `docs/openspec/`. See `runbook.md §0` for the technical reason (CLI's `OPENSPEC_DIR_NAME` is hardcoded).

## 7. Recommended next action (Phase 2 kickoff)

Per `version-plan.md`, Phase 2 = "minimum viable pipeline": `scripts/bilibili_audio.py` + `oss_upload.py` + `tingwu_transcribe.py` + `save_local.py`.

The 13-step pipeline for this Phase 2 task:

```
0. (this letter) — you've inherited; commit current state first
1. RepoMem.read bilibili-audio-mvp
2. Superpowers.brainstorming — likely SKIP, intent is `clear` per persist docs
3. /opsx:propose bilibili-audio-mvp "B站 BV → 字幕优先 → 无字幕走 yt-dlp -x m4a → OSS → Tingwu URL → 落地 output/bilibili_{bvid}.{md,json}"
4. RepoMem.capture bilibili-audio-mvp  (open temp/<slug>/{requirements,architecture}.md)
5. Superpowers.writing-plans — consume OpenSpec specs/tasks
6. using-git-worktrees + executing-plans + TDD
7. RepoMem.capture (continuous)
8. verification-before-completion + /opsx:verify
9. /requesting-code-review (ask-first)
10. finishing-a-development-branch (ask-first)
11. /opsx:archive bilibili-audio-mvp (ask-first; half-irreversible)
12. RepoMem.merge bilibili-audio-mvp (HITL)
```

Slug: `bilibili-audio-mvp` (proposed; the three-way identifier `<task>=change-id=<slug>` will all be this string).

**Before step 3**, confirm the operator has acquired Aliyun AK/SK + activated Tingwu service + created OSS bucket (these are credentials prerequisites listed in `runbook.md`). If missing → write a `from-orche-blocker-credentials.md` to `toUser/` and add a dashboard row, do not proceed.

## 8. Landmines (top of mind)

- **Tingwu rejects `bilibili.com` domain URLs.** Always go via yt-dlp → OSS. (D3 in `pre-openspec-decisions.md`.)
- **Audio only, never full video.** Hardware budget. (D4.)
- **Local ASR is fallback only.** GTX 860M + 7.6 GB RAM can't carry it. (D3.)
- **Errors return, never raise** past the public function boundary. (D7.)
- **Bilibili needs `SESSDATA` cookie** for high-quality audio + AI subtitles.
- **Zhihu primary path = Playwright CDP** to a manually-started Chrome on `127.0.0.1:9222`. Verify the operator's Chrome is running with that flag before Phase 3.
- **OpenSpec symlink is fragile.** Don't delete it; if you re-run `openspec init`, it may be overwritten — restore with `rm -rf openspec && ln -s docs/openspec openspec`. Cross-platform clone (Windows) will lose the symlink.
- **`openspec update` may re-write `.claude/skills/openspec-*`** — your custom edits in those skill files would be lost. Don't customize them.

## 9. Sendbox & dashboard state at handoff

| Item | Current value | Disposition |
|---|---|---|
| `toAgent/handoff.md` | placeholder caller contract | persist; fill during Phase 2 |
| `toOrchestrator/handoff.md` (this letter) | active | persist until your first `milestone-done.md`, then burn |
| Dashboard UN-001 (OpenSpec install) | Archive | done; ignore |
| Dashboard UN-002 (RufloAgent migration) | Active but **obsolete** — letter target was deleted | **You should mark done and move to Archive with note "obsoleted, migration cancelled 2026-05-30"** |
| Dashboard UN-003 (this handoff's start-session) | will be added below | open until you log first commit + first `/opsx:propose` |

## 10. Lifecycle of this letter

`persist` until you produce a `from-orche-bilibili-audio-mvp-done.md` (or equivalent first milestone) confirming inheritance worked. At that point: `git rm docs/sendbox/toOrchestrator/handoff.md` and commit. The milestone letter implicitly ratifies the inheritance.
