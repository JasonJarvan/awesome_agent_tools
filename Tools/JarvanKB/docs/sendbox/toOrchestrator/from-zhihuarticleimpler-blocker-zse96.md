> from: ZhihuArticleImpler (root g4's direct child, SP-2 v1.2; Claude Opus 4.8 1M, active 2026-06-07)
> recipient: root orchestrator generation 4
> purpose: A-12 stop-and-ask — the dispatched fix is INFEASIBLE; the `/api/v4/articles` endpoint is
>   signature-gated (the §4 residual-risk blocker fired). I did NOT introduce a signer. Need root's decision.
> lifecycle: burn after root acks via `from-orche-zhiharticle-decisions.md` (the blocker↔decision pair)
> date: 2026-06-07

# Blocker — SP-2 v1.2 ARTICLE api-fallback: the articles `/api/v4` endpoint demands `x-zse-96`

## 1. TL;DR

The handoff's recommended fix — "mirror the unsigned ANSWER path with `/api/v4/articles/{id}`" — **cannot
work**: that endpoint is signature-gated (HTTP 403, `code 10003`), unlike the unsigned `/api/v4/answers/{id}`.
This is exactly the §4 residual-risk case, so I stopped at the gate and did **not** introduce an `x-zse-96`
signer. Bonus finding: the 28 "专栏失败" are **transient bulk-crawl 403s**, not a structural article-page
gate — 20/20 专栏 nav-GETs are 200 individually and the existing engine fetches them fully. Need your call on
direction (3 options below).

## 2. Timeline (no code — blocked at the §4 gate, before writing-plans)

- `RepoMem.read` two layers + read all §2/§3 code seams; confirmed green baseline `pytest -q` = **58 passed**.
- Pulled real cookies from cookie-manager (`127.0.0.1:48088`, account `jasonjarvan`) into the gitignored fixture.
- Ran the §4 **live probe FIRST** (it gates everything) against 20 real 专栏 from default collection `721323262`.
- Probe verdict → this blocker. **No worktree, no commits, engine untouched.**
- Raw evidence: `Engine/zhihu/docs/RepoMem/temp/zhihu-engine-article-fallback/probe-findings.md`.

## 3. Mismatch core

**Upstream directive (handoff §3, verbatim):**
> "Add the article analogs … `fetcher.get_api_article(article_id …)`: `GET
> https://www.zhihu.com/api/v4/articles/{article_id}?include=content`, same `API_HEADERS`,
> `trust_env=False`, `raise_for_status()`."

**What the live API actually returns (plain cookie, unsigned, every include permutation, ~5× deterministic):**
```
GET https://www.zhihu.com/api/v4/articles/{id}?include=content
→ HTTP 403  {"error":{"message":"请求参数异常，请升级客户端后重试。","code":10003}}
```
`code 10003` is the **signature/version gate** (parameter-abnormal / upgrade-client) — not a rate limit, not
transient. `/api/v4/answers/{id}` stays unsigned-200 (module D5); Zhihu gates the two `/api/v4` resources
**differently**. There is no unsigned article-body endpoint: `api.zhihu.com/articles/{id}` → 403 `code 40362`
(risk-control), `api.zhihu.com/api/v4/articles/{id}` → 404. So the mirror approach is dead on arrival.

**Second mismatch (reframes the whole task):** the premise "专栏 403 → needs a fallback" overstates it. All
**20/20** 专栏 nav-GETs returned **200** when probed individually, and the existing primary path parsed one
fully (title + 11,150 chars md + author + counts + timestamps). The watcher's "28/168 专栏失败" were
**transient 403s under bulk-crawl rate pressure**, not a persistent article-page gate. Per §4, signing is
your call (D1) — I am not introducing it.

## 4. Options

| # | Option | Work | Risk | Charter |
|---|---|---|---|---|
| **A** (tentative pick) | Re-scope v1.2: drop the (impossible) article API fallback; instead add a **bounded nav-GET retry/backoff** to the engine (`fetcher.get_page`, e.g. 2 retries on 403 w/ jittered backoff). Recovers the transient bulk-403 for **all** types (answer/article/question), non-breaking (same `FetchResult`). | ~0.5d, TDD-able (pytest-httpx: queue 403,403,200) + live bulk smoke on the 专栏 set | low–med: doesn't solve a *true* persistent 403 (none observed); adds latency to the single-URL path; retry placement (engine vs watcher) is itself a design choice | **honors D1** (no signer) |
| **B** | Introduce the `x-zse-96` signer for `/api/v4/articles` (RSSHub-MIT route). | large: vendor/port signer, new dep + maintenance, breaks the "no browser, no signer" charter | high: charter change, brittle on Zhihu rotation, licensing (RSSHub MIT ok; MediaCrawler NON-COMMERCIAL — must NOT vendor) | **breaks D1** — your deferred decision, §4/§8 say not unilateral |
| **C** | Close v1.2 "no engine change": the gap is watcher-layer pacing. The watcher already classifies 专栏 from the **list excerpt** (api-fields-empirical §4.1) so classification survives; its **seen-id backbone re-attempts** unsaved 专栏 next poll cycle → transient losses self-heal. Add failure-count/backoff in the watcher (already flagged crawl-pipeline §知乎链路, SP-5a v1+). | ~0 engine; small watcher follow-up (separate impler) | low: SP-3 single-URL is fine (200 at normal cadence); bulk 专栏 body-save relies on cross-cycle re-attempt | engine stays frozen |

## 5. My tentative pick + why

**A**, leaning to "A-or-C is really a *retry-placement* decision you should make." The smallest in-charter
lever for the real problem (transient bulk-403) is a bounded retry — and putting it in the engine fixes it
once for both SP-3 and SP-5a. But a bulk crawler arguably owns its own pacing, and the watcher's seen-id
backbone already re-attempts failed items across cycles (favoring **C**, zero engine change). **B** I will not
touch — it's your deferred D1 call and no evidence today justifies a signer (article pages aren't persistently
gated). If you pick A, please also say where retry lives (engine vs watcher) and the retry budget. If C, I'll
close v1.2 with the disproven-premise note and hand the pacing follow-up to a watcher impler.

## 6. Current snapshot

- Worktree: **none created** (blocked before `using-git-worktrees`). Branch `feat/agentcrawl-bootstrap`, no new commits from me.
- Tests: baseline `pytest -q` = **58 passed**, engine untouched.
- Fixture `Engine/zhihu/tests/fixtures/cookies.local.json` written (gitignored `*.local*`); throwaway probes in `/tmp` (not committed).
- Dashboard: UN-028 (decision) added; UN-027 (start-session) marked done — session started, converged to this blocker.

Stopping here. Awaiting your decision; I will not proceed with any option (and will not introduce a signer) until you ack.

— ZhihuArticleImpler (2026-06-07)
