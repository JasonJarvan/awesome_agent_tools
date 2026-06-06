> from: root orchestrator generation 4 (Claude Opus 4.8 1M, active 2026-06-07 →)
> recipient: ZhihuArticleImpler (a new Claude Code peer session you are about to become)
> mode: child-handoff (sendbox-protocol Mode A — root stays alive; you converge back to `toOrchestrator/`)
> purpose: fix a cross-SP Engine gap — 专栏/ARTICLE 403 has no unsigned `/api/v4` fallback, so BOTH the
>   Zhihu Skill (SP-3) and the Zhihu Watcher (SP-5a) fail on `zhuanlan.zhihu.com/p/<id>` articles
> lifecycle: burn this letter after root reads your `from-zhihuarticleimpler-done.md` (your milestone-done)
> date: 2026-06-07

# Handoff — ZhihuArticleImpler (SP-2 Engine v1.2: ARTICLE api-fallback)

## 0. What you are

You are a **bounded engine impler** (a direct child of root orche g4), modeled on the `zhihucommentimpler`
engine-extension pattern that landed SP-2 v1.1 (comment full-tree, merge `9081cbc`). You add **one new
internal fallback branch** to the frozen SP-2 Zhihu Engine (`Engine/zhihu/`). Root stays alive; you do the
work end-to-end (v2 8-step pipeline, including your own compressed brainstorm + TDD + your own Step-8
`RepoMem.merge` closure), then report `from-zhihuarticleimpler-done.md` to root and disappear.

This is **SP-2 v1.2** — a non-breaking engine extension. The frozen `fetch()` contract
(`Engine/zhihu/docs/interface.md`) must **not** change shape: same signature, same `FetchResult`. You are
adding a fallback path that today raises `ZhihuFetchError`.

## 1. The subtask scope (success criteria)

**Add an unsigned `/api/v4` article fallback for `ZhihuType.ARTICLE`, mirroring the existing ANSWER one.**

Success =
1. A `zhuanlan.zhihu.com/p/<id>` article whose navigation GET returns 403 is recovered via the API fallback
   and rendered to Markdown (same `FetchResult` shape consumers already rely on).
2. Existing 200-path article fetch and the ANSWER fallback are untouched (no regressions).
3. **40→N unit tests** still green + new tests for the article-fallback branch (TDD — test first).
4. **One live smoke** against a real 专栏 URL that currently 403s, producing readable prose Markdown.

## 2. The gap (line-level — grounded, read these yourself before brainstorming)

`Engine/zhihu/src/zhihu/engine.py:63` — the unsigned fallback fires **only for ANSWER**:

```python
if result is None and status == 403 and ztype is ZhihuType.ANSWER:
    attempts.append("api-fallback")
    result = _from_api_answer(url, ids, jar, timeout)   # engine.py:94
```

An `ARTICLE` (`zhuanlan.zhihu.com/p/<id>`) that 403s on its nav GET falls straight through to
`engine.py:73` → `raise ZhihuFetchError("All fallbacks failed")`. There is **no article-side fallback**.
The id is already in hand: `url_router.py:23` classifies it as `ZhihuType.ARTICLE` with `{"article_id": ...}`.

**Both consumers are affected** (this is why the fix is in the Engine, not per-consumer — patching it in the
watcher or the skill would be wrong-layer duplication across two callers of the same frozen `fetch()`):
- **SP-5a Watcher**: live 2026-06-07 — 28/168 favorites items failed, all 专栏 ARTICLE (degraded gracefully,
  no crash; already recorded in `crawl-pipeline.md §知乎链路` + the watcher's `decisions.md`).
- **SP-3 Skill**: any `zhuanlan.zhihu.com/p/...` URL → `save_zhihu` will fail identically the moment the
  article page 403s (same `fetch()` → `ZhihuFetchError`). Not yet live-hit, same root cause.

## 3. Recommended fix (mirror the ANSWER path exactly)

The ANSWER path is your template — copy its shape:
- `fetcher.get_api_answer` (`fetcher.py:34`): `GET https://www.zhihu.com/api/v4/answers/{id}?include=content`,
  uses `API_HEADERS` (`fetcher.py:18` — **unsigned**, plain cookie, `trust_env=False`), `raise_for_status()`.
- `_from_api_answer` (`engine.py:94`): calls the helper, builds `FetchResult` from `title`/`content`(→
  `html_to_markdown`)/`author`(→`parse_author`)/vote+comment counts.

Add the article analogs:
1. **`engine.py`** new branch after the ANSWER one:
   `if result is None and status == 403 and ztype is ZhihuType.ARTICLE: result = _from_api_article(...)`
   (wrap in the same `try/except httpx.HTTPError` → `ZhihuFetchError` as the ANSWER branch at :67).
2. **`_from_api_article(url, ids, jar, timeout)`** in `engine.py`: requires `ids["article_id"]`; calls the
   helper; builds `FetchResult(type=ZhihuType.ARTICLE, title=..., author=parse_author(...),
   content_markdown=html_to_markdown(data["content"]), metadata={vote/comment counts}, raw=data)`.
   Cross-check field names against the article API JSON during your live probe (don't assume the answer
   schema 1:1 — articles expose `title` top-level, not under `question`).
3. **`fetcher.get_api_article(article_id, *, cookies, timeout)`** beside `get_api_answer`:
   `GET https://www.zhihu.com/api/v4/articles/{article_id}?include=content`, same `API_HEADERS`,
   `trust_env=False`, `raise_for_status()`.

## 4. Residual risk — resolve by LIVE PROBE, do NOT pre-engineer

**Whether the articles API needs `x-zse-96` signing and the exact `include=` fields is unknown until probed.**
The `§知乎链路` idiom (collections, people/collections, the answer-fallback — all plain-cookie / unsigned)
makes "no signing needed" the **likely** case, and v1's whole charter is **no signer** (D1: zse-96
sidestepped). So:
- Probe one real 专栏 article-id against `/api/v4/articles/{id}?include=content` with plain cookie first.
- If it returns 200 with content → done, mirror the answer path.
- If it **unexpectedly demands a signature** → **STOP, write `from-zhihuarticleimpler-blocker-zse96.md` to
  `toOrchestrator/`** with options. Do **NOT** introduce an `x-zse-96` signer unilaterally — that is a
  separate, deferred decision (the RSSHub-MIT-signer route noted in `§知乎链路`). Signing changes the
  engine's "no browser, no signer" charter and is root's call, not yours.
- `QUESTION` 403: live data only showed ARTICLE failing. Keep **ARTICLE the focus**; treat a QUESTION
  fallback as an optional maybe only if it's trivially symmetric — do not scope-creep.

## 5. Inputs (minimum set — re-fetch the rest as needed)

| Need | Path |
|---|---|
| The gap + ANSWER template | `Engine/zhihu/src/zhihu/{engine.py,fetcher.py}` (lines cited above) |
| Frozen contract you must NOT break | `Engine/zhihu/docs/interface.md` |
| Module memory (two layers — read on RepoMem.read) | global `docs/RepoMem/persist/` + module `Engine/zhihu/docs/RepoMem/{architecture,decisions}.md` |
| The §知乎链路 gotchas (unsigned endpoints, offset-poison, camelCase, trust_env) | `docs/RepoMem/persist/architecture/crawl-pipeline.md §知乎链路` |
| Engine decisions (your new ones land as **D8+**) | `Engine/zhihu/docs/RepoMem/decisions.md` (D1–D7 exist; D1 = zse-96 sidestepped — honor it) |
| Test layout + how to run | `Engine/zhihu/tests/{test_engine.py,test_fetcher.py}`; `pytest` from `Engine/zhihu/` (`.venv` present, `pytest-httpx` for mocking) |
| Engine-extension precedent (model your task/plan on this) | `Engine/zhihu/docs/superpowers/plans/2026-06-02-zhihu-comment-tree-plan.md` |

## 6. Convergence path (you report to ROOT — you are root's direct child, NOT under a SubOrche)

- **Parent cwd (absolute):** `/home/shenzhou/Codes/awesome_agent_tools/Tools/JarvanKB/`
- **Done →** write `docs/sendbox/toOrchestrator/from-zhihuarticleimpler-done.md` (milestone-done: acceptance
  table w/ evidence — test count, live-smoke URL + result, commit list, Step-8 promotions).
- **Blocked →** `docs/sendbox/toOrchestrator/from-zhihuarticleimpler-blocker-<topic>.md` (2–3 options, your
  tentative pick; stop and wait). The signing case in §4 is the most likely blocker.
- **Only if you change the `fetch()` contract** (you should NOT) → also ping `toZhihuWatcherV11Impler/`. A new
  internal fallback branch returning the same `FetchResult` requires **no** consumer change — don't expect to.

## 7. Worktree / branch / commit discipline

- Work in a git worktree off the **local** `feat/agentcrawl-bootstrap` branch (NOT `origin/main` — that loses
  local commits). Use `superpowers:using-git-worktrees`; base = current local branch.
- **Local commits only — no `git push`, no merge to `main`.** Fast-forward / merge into local
  `feat/agentcrawl-bootstrap` when done (the comment-tree precedent).
- **Multiple sessions share the main tree** → scope every commit with explicit pathspec; expect "modified
  since read" on shared files (Dashboard) — re-read + retry. Uncommitted in-flight files outside
  `Engine/zhihu/` belong to other sessions (SP-4b/5b implers are active) — **don't touch them**, don't touch
  `gstack`.

## 8. Out of scope (do NOT do)

- No `x-zse-96` signer (blocker-and-escalate instead — §4).
- No changes to the `fetch()` signature or `FetchResult` shape (non-breaking extension only).
- No comment-tree work (separate, already done v1.1), no SP-5a v1.1 work (a different impler owns UN-024).
- No QUESTION fallback unless trivially symmetric and live-confirmed needed.
- Don't redo anyone else's RepoMem.merge; **you own YOUR Step-8 closure** (HITL) — promote
  cross-SP-reusable article-fallback gotchas to `crawl-pipeline.md §知乎链路` (global), keep code-mechanism
  in the module. Then prune your temp.

## 9. Day-1 checklist

1. `RepoMem.read` — global persist + `Engine/zhihu/docs/RepoMem/` (two layers).
2. Read §2/§3 code seams yourself; run `pytest` in `Engine/zhihu/` to confirm the green baseline.
3. Compressed brainstorm (scope is locked above — confirm, don't re-open) → writing-plans → worktree+TDD.
4. **Live-probe the articles API early** (§4) — it gates the whole approach (unsigned vs blocker).
5. verification-before-completion (tests + live smoke evidence) → finish branch (ask-first) → Step-8 merge.
6. Report `from-zhihuarticleimpler-done.md` to `toOrchestrator/`.

— root orche g4 (2026-06-07)
