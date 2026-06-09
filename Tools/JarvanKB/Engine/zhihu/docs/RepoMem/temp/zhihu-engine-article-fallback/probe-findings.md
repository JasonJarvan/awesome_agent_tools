---
slug: zhihu-engine-article-fallback
status: active
domains:
  - crawl-pipeline
updated_at: 2026-06-09
task_type: feature
---

> **UNBLOCKED 2026-06-09 (user chose A + extras).** Root/user acked the blocker: do **NOT** add the
> (infeasible) article API fallback and do **NOT** add a signer (B rejected). Instead **re-scope v1.2 to an
> engine-side rate-limit hardening**: a **proactive rate-limiter (pacing)** to avoid tripping risk-control AND
> a **reactive backoff/retry** on 403/429. See §"Rate-limit characterization (2026-06-09)" + §"v1.2 design"
> below. The original mirror-ANSWER premise stays dead (Findings 1–3 unchanged, kept for the record).

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

## Rate-limit characterization (2026-06-09 — safe, measurement-only probe)

Throwaway `/tmp/zhihu_ratelimit_probe.py` (not committed). Safe-by-design: sequential, single-threaded,
STOP at first 403, hard cap 60, dump 403 headers if any.

**Result: 60/60 consecutive nav-GETs returned 200 — zero throttle.** Each request carries ~350–800ms of
full-page (~180 KB) download latency, so 60 back-to-back ran at **~2 req/s for ~30s with no block**.

**Inference — the throttle is BURST/CONCURRENCY-sensitive, not cumulative-count-based:**
- A gentle sequential cadence (~2 req/s, self-paced by download latency) is **safe well past 60 requests**.
- The watcher's "28 专栏失败" (and the answer nav-GETs that 403'd and were rescued via api-fallback) were
  caused by an **aggressive cadence** — likely concurrency / no inter-request gap / multiple requests per
  item (nav-GET + api-fallback + comments). The trip condition is instantaneous rate, not total volume.
- This tells the proactive limiter exactly what to control: **smooth bursts / cap the rate**, not "count
  requests." A conservative ~2 req/s ceiling is empirically safe; we default below that with jitter.

**No 403 headers captured** (never tripped). Deliberately did NOT force a trip via a concurrent burst:
(a) it would throttle the real account and could disrupt the SP-5a watcher service if it is polling, and
(b) the only payoff is confirming a `Retry-After` header, which the reactive backoff handles defensively
regardless (honor `Retry-After` if present, else exponential backoff + jitter). Cost > benefit on a live,
shared account — characterized from the safe direction instead.

## v1.2 design (re-scoped — proactive limiter + reactive backoff, no signer)

1. **Proactive rate-limiter** — a module-level shared limiter (min-interval-with-jitter or token bucket)
   wrapping **all** outbound httpx calls (`get_page`, `get_api_answer`, future `get_api_*`, comments). Shared
   process-wide so a **bulk** consumer (watcher: many `fetch()` calls in one process) is auto-paced, while a
   **single-URL** consumer (SP-3) is ~unaffected (one request never waits). Conservative configurable default
   (below the ~2 req/s safe ceiling, e.g. min-interval ≈ 0.4–0.6s + jitter); can be tuned/disabled.
2. **Reactive backoff/retry** — on **403/429**, retry up to N (default ~3) with exponential backoff + jitter;
   **honor `Retry-After`** if the response carries it, else backoff. Retries exhausted → preserve current
   behavior (the 403 falls through to `ZhihuFetchError` as today). Network errors: optional same treatment.
3. **Contract: non-breaking (handoff §8 still binds).** No change to `fetch()` signature or `FetchResult`.
   Limiter/retry are module-level configurable (e.g. `zhihu.configure(...)`) with safe defaults — existing
   callers get the hardening for free, no code change. `interface.md` gains a "built-in pacing + 403/429
   backoff" note (behavior add, not a breaking change).

## Status / next

- UNBLOCKED → implementing A. No worktree/commits yet for the impl. Baseline `pytest -q` = 58 passed.
- Plan: `Engine/zhihu/docs/superpowers/plans/2026-06-09-zhihu-ratelimit-hardening-plan.md` (writing-plans).
- Then worktree + TDD (limiter unit tests w/ injectable clock; retry tests w/ pytest-httpx queued 403→200;
  Retry-After honor test) → verify (full suite + a gentle live smoke confirming pacing holds) → finish (ask-first)
  → Step-8 merge: promote the BURST-sensitive-throttle gotcha + "answers unsigned / articles signature-gated"
  asymmetry to global `crawl-pipeline.md §知乎链路` (cross-SP reusable); keep limiter mechanism in module + code.
