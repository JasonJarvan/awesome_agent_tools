---
slug: zhihu-engine-article-fallback
status: blocked
domains:
  - crawl-pipeline
updated_at: 2026-06-07
task_type: feature
---

# SP-2 v1.2 — ARTICLE api-fallback: live-probe findings (GATE — handoff §4)

> **Verdict: the dispatched fix is INFEASIBLE.** The `/api/v4/articles/{id}` endpoint is
> **signature-gated** (HTTP 403, code 10003), unlike the unsigned `/api/v4/answers/{id}` the handoff
> told me to mirror. Per handoff §4/§8 + module D1, I did NOT introduce an `x-zse-96` signer; I
> stopped at the gate and escalated to root (`docs/sendbox/toOrchestrator/from-zhihuarticleimpler-blocker-zse96.md`).
> This doc is the raw empirical record backing that blocker. No code was written; baseline 58 tests still green.

## Provenance

Live crawl 2026-06-07, real SP-1 cookies (account `jasonjarvan`, pulled from cookie-manager
`127.0.0.1:48088`, 15 meaningful `.zhihu.com` cookies incl. `d_c0`/`z_c0`/`__zse_ck`), direct connect
(`trust_env=False`), plain cookie + the engine's exact `API_HEADERS`/`NAV_HEADERS`, **NO `x-zse-96`**.
Throwaway probes `/tmp/zhihu_article_probe.py` + `_probe2.py` (NOT committed). 20 real 专栏 articles from
the default collection `我的收藏` (id `721323262`).

## Finding 1 — the articles `/api/v4` endpoint is signature-gated (the blocker)

`GET https://www.zhihu.com/api/v4/articles/{id}?include=content` (plain cookie, unsigned) →

```
HTTP 403  {"error":{"message":"请求参数异常，请升级客户端后重试。","code":10003}}
```

Reproduced deterministically across **every** include permutation (none, `?include=content`,
`?include=data[*].content,comment_count,voteup_count`) for article id `2044156343825826178`, ~5×.
`code 10003` ("请求参数异常，请升级客户端" = parameter-abnormal / upgrade-client) is the **signature/version
gate**, NOT a rate limit — it is immediate, deterministic, and does not escalate to a throttle.

**Asymmetry vs ANSWER (the whole premise of the handoff):** `/api/v4/answers/{id}` is unsigned-200 (module
D5, and the watcher rescued 140 answers through it on 2026-06-07). `/api/v4/articles/{id}` is NOT — Zhihu
gates the two `/api/v4` resources differently. "Mirror the unsigned ANSWER path" therefore cannot work for
articles.

## Finding 2 — no unsigned article API alternative exists

| Endpoint | Result | Note |
|---|---|---|
| `www.zhihu.com/api/v4/articles/{id}?include=content` | 403 code 10003 | signature gate |
| `www.zhihu.com/api/v4/articles/{id}` (no include) | 403 code 10003 | signature gate |
| `www.zhihu.com/api/v4/articles/{id}?include=data[*].content,…` | 403 code 10003 | signature gate |
| `api.zhihu.com/articles/{id}` (mobile host) | 403 code **40362** | risk-control block ("暂时限制本次访问") |
| `api.zhihu.com/api/v4/articles/{id}` | 404 | wrong path |

No unsigned `/api/v4` article body endpoint was found. The mobile host (`api.zhihu.com`) is itself gated by
risk-control (code 40362, a different error than the signature gate).

## Finding 3 — 专栏 nav GET returns 200; the existing primary path already fetches articles fine

All **20/20** 专栏 articles from the default collection returned **HTTP 200 on the nav GET** when probed
individually (not under bulk load). The existing engine primary path (`get_page` → `extract_initial_data` →
`parse_article`) fetched article `2044156343825826178` perfectly:

```
type=ARTICLE  title='Agent IAM 系列（三）：Agent IAM 不能后补'  md_len=11150
author='模安局管铭'  meta={vote_count:2, comment_count:0, created_at:'2026-05-30…', updated_at:'…'}
```

**Implication:** the watcher's "28 专栏失败" (crawl-pipeline.md §知乎链路, 168-item bulk run) were **transient
nav-GET 403s under bulk-crawl rate pressure**, NOT a structural article-page gate. When fetched at a normal
cadence the article pages are 200 and the engine recovers full content with no fallback at all. The premise
"专栏 403 needs an unsigned API fallback like ANSWER" is disproven on two counts: (a) no such unsigned
endpoint exists, and (b) the article PAGE isn't persistently gated — only transiently throttled in bulk.

## What this means for the fix (full options → blocker letter)

The real, in-charter lever for the transient bulk-403 is **bounded retry/backoff on the nav GET** (helps ALL
types — answer/article/question — within D1 "no signer"), NOT an article API fallback. A true persistent
article-API need would require the `x-zse-96` signer (D1's deferred RSSHub-MIT route) — root's call, not mine.
Options + tentative pick are in the blocker letter; this doc holds only the raw evidence (no duplication).

## Status / next

- BLOCKED awaiting root's decision (blocker letter + Dashboard UN-028).
- No worktree, no commits. Baseline `pytest -q` = 58 passed.
- On unblock: if "retry/backoff" → re-scope to TDD a retry on `fetcher.get_page` (test-first) + live smoke;
  if "signer" → separate task, out of this impler's charter; if "no engine change" → close v1.2, watcher owns pacing.
