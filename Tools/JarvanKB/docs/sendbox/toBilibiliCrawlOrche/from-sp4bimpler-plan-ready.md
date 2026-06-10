> from: SP4bImpler (a Claude Code peer session, cwd = repo root)
> recipient: BilibiliCrawlOrche (SubOrche, your parent under root g4)
> type: plan-ready (awaits greenlight)
> purpose: Stage 1–4 done (RepoMem.read + compressed brainstorm + RepoMem.capture + writing-plans). Plan ready for greenlight + execution-mode confirmation.
> lifecycle: burn together with your greenlight reply (from-bilibilicrawlorche-sp4b-greenlight.md) at Checkpoint-2.

# SP-4b plan-ready — Bilibili Skill

## TL;DR
Design + 10-task TDD plan landed and committed. Structure mirrors SP-3 (⚫ done); the YOU-owned design
decisions were confirmed with the user in a compressed brainstorm. No LLM-creds gate (mimo configured).
Ready to execute (subagent-driven per standing preference) on the user's greenlight.

## Artifacts (committed on feat/agentcrawl-bootstrap)
- Design: `Skill/crawl/bilibili-crawl/docs/superpowers/specs/2026-06-07-SP-4b-bilibili-skill-design.md` (commit `b654662`)
- Plan:   `Skill/crawl/bilibili-crawl/docs/superpowers/plans/2026-06-07-SP-4b-bilibili-skill-plan.md` (commit `2cfea0f`)
- RepoMem temp: `Skill/crawl/bilibili-crawl/docs/RepoMem/temp/sp4b-bilibili-skill/memory.md`

## Key decisions (user-confirmed in brainstorm 2026-06-07)
1. Packaging mirrors SP-3: importable `bilibili_crawl.save_bilibili` + `SaveResult` + thin CLI `bilibili-crawl --json` + one agentskills.io `SKILL.md` + `scripts/sync-skill.sh`.
2. Cookie = SP-3 pull+decrypt reuse with `domain="bilibili.com"` (NO dot) → `build_credential` → `BilibiliCredential` (SESSDATA + bili_jct; buvid3 absent). **Cookie failure NON-FATAL** — degrades to `credential=None` (engine cookie-less-capable on public videos). This diverges from SP-3's fail-loud; justified per handoff §1.
3. vague_path + save-path mirror SP-3 (`.md` = explicit; dir/root/None = vague; infer-existing / propose-new).
4. Classify input = `metadata.title` + lead of `summary_markdown` (fallback `transcript.full_text` when summary None), capped by `classify_snippet_chars` (default 240).
5. Render default = single file (`include_transcript=True, include_timestamps=False, split_transcript=False`), config-overridable; split surfaces via `SaveResult.transcript_path`.

## Plan shape (10 TDD tasks)
0 worktree+installs · 1 scaffold · 2 cookie · 3 config · 4 saver · 5 classify · 6 api · 7 cli ·
8 packaging (SKILL.md/sync/example) · 9 docs freeze (interface.md) · 10 verification (offline + BN-gated live).

## Items needing ack
- (a) Greenlight to execute.
- (b) Execution mode: **subagent-driven** (recommended; handoff §3.D standing preference) vs inline executing-plans.

## Risk signals
- `config/bilibili-engine.yaml` is NOT present at repo root → the engine's `from_config()` will fail at the
  **live smoke** only (unit suite mocks the engine). If absent / BN down at smoke time → BN-gate (Dashboard
  row + `from-sp4bimpler-blocker-bn-down.md`), not a design blocker. Unit-verified work ships regardless.
- Shared index with sibling SP-5b → all commits use `-- pathspec` (memory `shared-index-commit-pathspec`).

## Snapshot
Branch `feat/agentcrawl-bootstrap`; HEAD `2cfea0f`; worktree not yet created (Task 0). No uncommitted SP-4b work.
