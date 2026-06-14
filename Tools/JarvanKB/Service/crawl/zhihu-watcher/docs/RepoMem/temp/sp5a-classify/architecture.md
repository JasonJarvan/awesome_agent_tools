---
slug: sp5a-classify
status: active
domains:
  - crawl-pipeline
updated_at: 2026-06-14
task_type: feature
---

# SP-5a v1.2 — implementation working notes (task-scoped)

> Concrete codegraph blast radius + file-change map the impl needs. Design rationale stays in the spec.

## Codegraph blast radius (verified 2026-06-14)

**SP-3 classifier symbols to MOVE → `jarvankb_common/classify.py`:**
- `Skill/crawl/zhihu-crawl/src/zhihu_crawl/classify.py`: `_lead_text`, `existing_subfolders`, `_build_prompt`,
  `_parse`, `Category`, `classify(result, output_root, client, *, snippet_chars=240)`.
- Callers of SP-3 `classify`: `zhihu_crawl/api.py:40` (`classify.classify(result, ...)` → `cat.name, cat.is_new`).
  Keep `api.py` unchanged by returning a `Category(name, is_new)` from the adapter.
- SP-3 `existing_subfolders` has 2 callers inside `classify.py` (now internal to the shared module).
- `bilibili-crawl` has its OWN copy of these symbols — **NOT in scope**, do not touch.

**Watcher symbols (already present — no parse change needed):**
- `favorites_client.CollectionItem` ALREADY carries `title` + `excerpt` (html-unescaped) + `favorited_at` +
  `content_type` + `key` + `url`. Attention render + dedup key are ready; `_build_item` parses excerpt per type
  (answer→`excerpt`, article→`excerpt_title`). No favorites_client change required.
- `watcher.Watcher._poll_collection` is the integration point: branch dedup + post-success record on the
  per-target `classify` flag. The existing broad `except Exception` already catches ClassifyError/LLM errors.
- `config.CollectionConfig(id, name)` → add `classify: bool = False`. `TargetResolver.resolve` sets
  `classify=False` for user-discovered collections (named-collection classify out of scope).
- `FailureStore` (state_dir JSON, `failures-{coll}.json`) → extend record with url/title/excerpt + a
  `circuit_break_threshold` terminal state (`should_skip` already gates on `skip_until`; add a permanent flag).
- `WatermarkStore` seen-set untouched for non-classify targets.

## File-change map

| File | Change |
|---|---|
| `Engine/common/src/jarvankb_common/classify.py` | NEW — shared classifier (self-contained `_slugify`/`_parse`/prompt) |
| `Engine/common/src/jarvankb_common/__init__.py` | export `classify`, `Classification`, `lead_text`, `existing_subfolders` |
| `Engine/common/tests/test_classify.py` | NEW — migrated SP-3 classify tests + vague/allow_new cases |
| `Skill/crawl/zhihu-crawl/src/zhihu_crawl/classify.py` | SHRINK to adapter (import shared; return `Category`) |
| `Skill/crawl/zhihu-crawl/tests/test_classify.py` | trim to a delegation test (internals now tested in common) |
| `Service/.../zhihu_watcher/classifier.py` | NEW — Tier-1→Tier-2 wrapper + `ClassifyError` |
| `Service/.../zhihu_watcher/ledger_store.py` | NEW — `ledger-{coll}.json`, success-only, has/record |
| `Service/.../zhihu_watcher/failure_store.py` | EXTEND — circuit_break_threshold + url/title/excerpt |
| `Service/.../zhihu_watcher/attention.py` | NEW — render `_zhihu-watcher-attention.md` (integral overwrite) |
| `Service/.../zhihu_watcher/config.py` | ADD `classify` flag on CollectionConfig + `ClassifyConfig` + `circuit_break_threshold` |
| `Service/.../zhihu_watcher/watcher.py` | branch `_poll_collection` on `classify`; lazy LLMClient once/cycle; render attention at cycle end |
| `Service/.../zhihu_watcher/__main__.py` / `build_watcher` | wire ledger + classifier + attention |
| `Service/.../config/zhihu-watcher.example.yaml` | add classify block + a `我的收藏` classify target example |
| watcher tests | new: classifier, ledger_store, attention; extend failure_store + integration |

## Gotchas to carry into impl

- **`.env` not auto-loaded** (global memory `llm-env-not-autoloaded`): live smoke must `set -a; source .env`
  or equivalent before running — `jarvankb_common` only reads `os.environ`.
- **Shared index commit needs pathspec** (global memory `shared-index-commit-pathspec`): a bare `git commit`
  swept another session's staged changes once — always commit with explicit pathspec.
- **`__zse_ck` freshness gate** (global `crawl-pipeline.md §知乎链路`): 专栏 nav-GET 403 is intermittent and
  cured by a fresh browser cookie, NOT by retry — this is why the circuit-breaker hint distinguishes
  stale-cookie vs permanently-unreachable.
- **slug vs raw folder names**: `existing_subfolders` returns raw CJK names; the classifier slugs the model's
  pick; `_slugify` preserves CJK so `is_new = slug(folder) ∉ raw_subs` is consistent for CJK folders.
