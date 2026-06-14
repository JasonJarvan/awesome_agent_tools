---
slug: sp5a-classify
status: active
domains:
  - crawl-pipeline
  - credentials
updated_at: 2026-06-14
task_type: feature
---

# SP-5a v1.2 — requirements & acceptance (task-scoped)

> Design narrative is in `docs/superpowers/specs/2026-06-14-SP-5a-v1.2-default-collection-classify-design.md`.
> This file holds ONLY the acceptance criteria + the verification checklist (no design duplication).

## Acceptance criteria (verification-before-completion gate)

- [ ] `jarvankb_common.classify` exists: `classify(title, lead_text, existing_subfolders, client, *, allow_new=True) -> Classification(folder, is_new, vague)` + `lead_text`, `existing_subfolders` re-exported from `jarvankb_common`.
- [ ] SP-3 `zhihu_crawl/classify.py` is a thin adapter; `api.py` + `saver.py` unchanged; **full SP-3 suite green after the move** (regression gate).
- [ ] Watcher `classifier.py`: Tier-1 (200) → vague → Tier-2 (1000); never full text; off-list-after-Tier-2 (`is_new` True, `allow_new=False`) → `ClassifyError`.
- [ ] `ledger_store.py`: success-only; classify targets dedup via ledger (NOT seen-set); `sync_status="local-only"`/`sync_attempts=0` written, never read.
- [ ] `FailureStore` extended: `circuit_break_threshold` (default 10) terminal state + url/title/excerpt capture.
- [ ] Attention surface: `<output_dir>/_zhihu-watcher-attention.md`, integral overwrite each cycle from FailureStore JSON authority; `✓ nothing needs attention` when empty.
- [ ] Config: per-target `classify: bool=false`; `classify:` block (`llm_profile`, `tier1_chars`, `tier2_chars`, `allow_new_folders`); top-level `circuit_break_threshold`.
- [ ] No-LLM default preserved: no `classify: true` target ⇒ `LLMClient` never constructed (test asserts this).
- [ ] Daemon-never-crashes invariant holds for all new failure paths (ClassifyError, LLM exception, render failure).

## Live smoke (real creds, real default collection `我的收藏` / 721323262, mimo-v2.5-pro)

- [ ] `.env` loaded into env first (jarvankb_common reads os.environ — see global memory `llm-env-not-autoloaded`).
- [ ] classify + save into existing subfolders + ledger written.
- [ ] re-run `--once` → **0 re-hit** (dedup via ledger).
- [ ] at least one vague item escalating Tier-1 → Tier-2 (observe two LLM calls in logs).

## Out of scope (forward-compat hook only)

- v1.3 Zhihu write-API sync (only `sync_status` hook here). Promote v1.3 roadmap + `x-zse-96` signing-risk to `version-plan.md` at Step 8.
