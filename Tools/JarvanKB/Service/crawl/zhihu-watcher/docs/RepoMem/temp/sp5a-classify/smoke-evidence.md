---
slug: sp5a-classify
status: active
domains:
  - crawl-pipeline
updated_at: 2026-06-18
task_type: feature
---

# SP-5a v1.2 — live smoke evidence (Task 10)

> Real SP-1 cookies (account, 14 `.zhihu.com` cookies) + real default collection `我的收藏` (id `721323262`) +
> real `mimo` (`mimo-v2.5-pro`). Run from the worktree with worktree `src/` on PYTHONPATH; `.env` +
> `config/llm.yaml` are gitignored → sourced from the MAIN tree (`JARVANKB_LLM_CONFIG` pointed at main).
> Smoke config (gitignored, repo-external): `/tmp/sp5a-classify-smoke/zhihu-watcher.smoke.yaml`
> (`only_after: 2026-06-13` to bound the work to recently-favorited items; output mirrored the real ~32
> category folder names into a /tmp scratch so classification is realistic but the real vault is untouched).

## Acceptance — ALL PASS

| Criterion | Result |
|---|---|
| cookie pull (SP-1) | ✓ 14 `.zhihu.com` cookies |
| list default collection | ✓ 106 items listed (offset paging, plain cookie, no x-zse-96) |
| classify + save into an EXISTING subfolder | ✓ the in-window answer classified into `赚钱-金融市场` / `赚钱-投资分析` (a real category) and saved as `<title>.md` |
| ledger written (success-only) | ✓ `answer:2049194583024722074` → `{classified_folder, local_path, fav_time, classified_at, sync_status: "local-only", sync_attempts: 0}` |
| re-run → 0 re-hit (ledger dedup) | ✓ cycle 2 = "0 new item(s)", 0 LLM calls, ledger unchanged (1 item, same key) |
| vague item Tier-1 → Tier-2 escalation | ✓ the 量化交易 answer was vague at Tier-1 (赚钱-金融市场 vs 赚钱-投资分析 both plausible) → escalated → exactly 2 LLM calls for the 1 item |
| graceful failure path | ✓ (the first run, on an EXPIRED key) did not crash: item NOT ledgered, failure recorded (failures=1), no stub .md, attention = "nothing needs attention" (1 < circuit_break_threshold 10) |

## Notes
- **mimo key expiry (credential, not code):** the first attempt failed with `litellm.AuthenticationError:
  Invalid API Key` — the token-plan `MIMO_API_KEY` had expired (mimo last verified 2026-06-07/06-11). The
  endpoint returned 401 (request reached it; proxy/network fine). User refreshed the key in the main-tree
  `.env`; re-probe returned `ok`; the happy-path then succeeded. This validated the lazy-LLM graceful-skip
  path AND the post-refresh happy path.
- **Classification is mildly non-deterministic** (金融市场 vs 投资分析 across two runs of the same item) — both
  correct buckets; expected for an LLM folder-classifier; acceptable per the "folder-bucket, not summarization"
  design note.
- **Scope:** smoke bounded to `only_after ≥ 2026-06-13` (1 item, which happened to exercise the vague→Tier-2
  path). The full-inbox first-run back-fill (109+ items) is the deployment session's job (Dashboard UN-047,
  WatcherDeploy) against the real vault output dir.
- **Offline regression:** jarvankb_common 22 + zhihu-crawl 27 (SP-3 regression) + zhihu-watcher 78 = 127 green
  (run per-package; a single combined pytest invocation hits a test_classify.py basename clash — harness artifact).
