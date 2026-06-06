> from: SP3Impler (Claude Code peer session, cwd = repo root)
> recipient: ZhihuCrawl SubOrche (parent)
> type: milestone-done
> lifecycle: burn after SubOrche reads (then SubOrche may burn `toSP3Impler/handoff.md` per its §8)
> date: 2026-06-07

# SP-3 Zhihu Skill — DONE (v1, live-verified, merged)

## What landed
`Skill/crawl/zhihu-crawl/` (dist `zhihu-crawl`): `URL → SP-1 cookie pull+decrypt (in-memory) → frozen SP-2
engine fetch → to_markdown → explicit-.md-path verbatim write OR vague-path LLM classification into an
output_root subfolder`. Surfaces: importable `zhihu_crawl.save_zhihu` + thin `zhihu-crawl` CLI (`--json`) +
**one agentskills.io `SKILL.md`** (Claude Code/Codex/OpenClaw/Hermes) + `scripts/sync-skill.sh`.
Plus the shared piece: **`Engine/common` packaged as `jarvankb-common` with the real `LLMClient` litellm body**.

## Verification (evidence)
- **40 unit tests** green (Engine/common 10 + zhihu-crawl 30), all network/LLM/cookie boundaries mocked.
- Offline integration smoke: explicit + vague paths through the real engine `to_markdown()` seam.
- **LIVE vague_path smoke** passed: `mimo-v2.5-pro` over the OpenAI protocol classified a sample → `机器学习`.
- Code review (opus reviewer): verdict "merge with fixes"; 2 Important fixed (parse robustness, category
  path-traversal slug) + stream no-replay, 3 Minor deferred (recorded in module decisions).

## Branch / merge
Worked in worktree `.worktrees/sp3-zhihu-skill`; **fast-forward merged into local `feat/agentcrawl-bootstrap`**
(functional tip `c500119`, + Step-8 doc commits). Worktree removed, branch deleted. Local only — no push.

## Step-8 RepoMem.merge (impler-owned, HITL-approved) — promotions
- `persist/architecture/credentials.md` ← verified Python cookie pull+decrypt reference (`cookie.py`); SP-4b/5b reuse with `domain=bilibili.com`.
- `persist/memory/llm-shared-layer.md` (new) ← LLMClient real-impl (import/config/custom-provider) + agentskills.io single-`SKILL.md` packaging. **SP-4b/SP-6/SP-7 reuse — do not reimplement.**
- `persist/version-plan.md` ← LLMClient v1 landed + LLMService v2 roadmap.
- Dashboard SP-3 → ⚫ done. Module decisions condensed; temp `sp3-zhihu-skill/` pruned.

## Heads-up for you / root (cross-vertical)
- **LLMService = a v2 platform-level SP** (user decision 2026-06-05 "不扩": v1 stays a library). It is
  non-breaking (frozen `LLMClient` interface). Please track for root/SubOrche scheduling; affects SP-4b/6/7.
- **LLM provider configured** = `mimo-v2.5-pro` (xiaomi token-plan, OpenAI protocol) via gitignored
  `config/llm.yaml` + `.env`; key never in repo. SP-4b can reuse the same `mimo` profile.
- **v1.1 candidate:** have the SP-2 engine expose Zhihu 话题/topics so classification can prefer them
  (cheaper/more accurate, possibly LLM-free). Not in SP-3 scope.

SP-3 closed. Ready for SubOrche convergence.
