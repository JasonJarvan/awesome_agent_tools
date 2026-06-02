# Zhihu Engine v1.1 — Full Comment-Tree Crawl Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** For each root comment, fetch ALL child replies (not just the inline `child_comments` preview the root response ships), still flattened two-layer.

**Architecture:** Add a module-level `fetch_child_comments(root_comment_id, ...)` that paginates `/api/v4/comment_v5/comment/{cid}/child_comment` by following `paging.next` VERBATIM (never constructing `offset` — immune to the D3 offset-poison). In `fetch_comments`, after collecting root pages, replace each root's `child_comments` with the full fetched set when `child_comment_count > len(inline)`, then reuse the unchanged `flatten_comments`. Bound by `comment_limit`, loop-guarded.

**Tech Stack:** Python 3.13, httpx (`trust_env=False`), pytest + pytest-httpx 0.36.

> Design rationale + the open empirical question (child pagination model) live in
> `../../RepoMem/temp/zhihu-engine-comment-tree/architecture.md`. Module gotchas D1–D6 in `../../RepoMem/decisions.md`.

---

### Task 1: `fetch_child_comments` — paginate the full child set via `paging.next`

**Files:**
- Modify: `Engine/zhihu/src/zhihu/comments.py` (add `fetch_child_comments`)
- Test: `Engine/zhihu/tests/test_comments.py`

- [ ] **Step 1: Write the failing test**

```python
def test_fetch_child_comments_paginates_via_next(httpx_mock):
    page0 = {"data": [{"id": "c1", "content": "child 1", "like_count": 0, "created_time": 1700000000,
                       "author": {"name": "U1", "url_token": "u1"}, "reply_comment_id": "r1"}],
             "paging": {"is_end": False,
                        "next": "https://www.zhihu.com/api/v4/comment_v5/comment/r1/child_comment?order_by=ts&limit=20&offset=O2"}}
    page1 = {"data": [{"id": "c2", "content": "child 2", "like_count": 0, "created_time": 1700000001,
                       "author": {"name": "U2", "url_token": "u2"}, "reply_comment_id": "c1"}],
             "paging": {"is_end": True, "next": None}}
    httpx_mock.add_response(
        url="https://www.zhihu.com/api/v4/comment_v5/comment/r1/child_comment?order_by=ts&limit=20",
        json=page0)
    httpx_mock.add_response(
        url="https://www.zhihu.com/api/v4/comment_v5/comment/r1/child_comment?order_by=ts&limit=20&offset=O2",
        json=page1)
    from zhihu.comments import fetch_child_comments
    out = fetch_child_comments("r1", cookies={"d_c0": "x"}, limit=None)
    assert [c["id"] for c in out] == ["c1", "c2"]   # raw dicts, both pages, follows next verbatim
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_comments.py::test_fetch_child_comments_paginates_via_next -v`
Expected: FAIL — `ImportError: cannot import name 'fetch_child_comments'`

- [ ] **Step 3: Write minimal implementation** (add to `comments.py`)

```python
def fetch_child_comments(root_comment_id: str, *, cookies: dict, limit: int | None,
                         headers: dict | None = None, page_size: int = 20,
                         max_pages: int = 50) -> list[dict]:
    """Paginate ALL child replies of one root comment, following `paging.next` VERBATIM.

    We never construct `offset` ourselves: doing so on `root_comment` caused the empty-data /
    self-referential-cursor hang (decisions.md D3). Following `next` works whether the server's
    model is cursor- or offset-based (the URL embeds whatever it needs), so this is immune to that
    poison. Returns raw child-comment dicts in the same schema as the inline `child_comments`
    preview, so `flatten_comments` consumes them unchanged. Same loop guard as `fetch_comments`.
    """
    url = (f"https://www.zhihu.com/api/v4/comment_v5/comment/{root_comment_id}/child_comment"
           f"?order_by=ts&limit={page_size}")
    out: list[dict] = []
    seen_next: set[str] = set()
    for _ in range(max_pages):
        resp = httpx.get(url, cookies=cookies, headers=headers or {}, timeout=30.0,
                         follow_redirects=True, trust_env=False)
        resp.raise_for_status()
        page = resp.json()
        data = page.get("data", [])
        out.extend(data)
        paging = page.get("paging", {})
        nxt = paging.get("next")
        if paging.get("is_end") or not data or not nxt or nxt in seen_next:
            break
        if limit is not None and len(out) >= limit:
            break
        seen_next.add(nxt)
        url = nxt
    return out[:limit] if limit is not None else out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_comments.py::test_fetch_child_comments_paginates_via_next -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add Engine/zhihu/src/zhihu/comments.py Engine/zhihu/tests/test_comments.py
git commit -m "feat(zhihu): fetch_child_comments paginates full child set via paging.next"
```

---

### Task 2: `fetch_child_comments` loop guards (empty-data + self-referential next)

**Files:**
- Test: `Engine/zhihu/tests/test_comments.py`
- (No impl change — guards already written in Task 1; these tests pin them.)

- [ ] **Step 1: Write the failing tests**

```python
def test_fetch_child_comments_no_hang_on_empty_data(httpx_mock):
    httpx_mock.add_response(
        url="https://www.zhihu.com/api/v4/comment_v5/comment/r9/child_comment?order_by=ts&limit=20",
        json={"data": [], "paging": {"is_end": False,
              "next": "https://www.zhihu.com/api/v4/comment_v5/comment/r9/child_comment?order_by=ts&limit=20&offset=SAME"}})
    from zhihu.comments import fetch_child_comments
    out = fetch_child_comments("r9", cookies={"d_c0": "x"}, limit=None)
    assert out == []   # empty data breaks immediately, no second request, no hang

def test_fetch_child_comments_breaks_on_self_referential_next(httpx_mock):
    selfref = "https://www.zhihu.com/api/v4/comment_v5/comment/r8/child_comment?order_by=ts&limit=20&offset=STUCK"
    httpx_mock.add_response(
        url="https://www.zhihu.com/api/v4/comment_v5/comment/r8/child_comment?order_by=ts&limit=20",
        json={"data": [{"id": "c1", "content": "x", "like_count": 0, "created_time": 1,
                        "author": {"name": "U", "url_token": "u"}}],
              "paging": {"is_end": False, "next": selfref}})
    httpx_mock.add_response(
        url=selfref,
        json={"data": [{"id": "c2", "content": "y", "like_count": 0, "created_time": 2,
                        "author": {"name": "U", "url_token": "u"}}],
              "paging": {"is_end": False, "next": selfref}})  # next loops to itself
    from zhihu.comments import fetch_child_comments
    out = fetch_child_comments("r8", cookies={"d_c0": "x"}, limit=None)
    assert [c["id"] for c in out] == ["c1", "c2"]   # 2 requests then seen-set breaks, no hang
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/test_comments.py -k "child_comments_no_hang or self_referential" -v`
Expected: PASS (guards from Task 1 cover these). If either hangs/fails, the guard is wrong — fix in `comments.py`.

- [ ] **Step 3: Commit**

```bash
git add Engine/zhihu/tests/test_comments.py
git commit -m "test(zhihu): pin child_comment loop guards (empty-data, self-ref next)"
```

---

### Task 3: `fetch_comments` orchestration — replace inline preview with full child set

**Files:**
- Modify: `Engine/zhihu/src/zhihu/comments.py` (`fetch_comments`)
- Test: `Engine/zhihu/tests/test_comments.py`

- [ ] **Step 1: Write the failing test**

```python
def test_fetch_comments_fetches_full_child_tree(httpx_mock):
    root_page = {"data": [
        {"id": "r1", "content": "root", "like_count": 9, "created_time": 1700000000,
         "author": {"name": "Root", "url_token": "root"},
         "child_comments": [   # only 1-item inline PREVIEW
             {"id": "c1", "content": "inline preview", "like_count": 0, "created_time": 1700000001,
              "author": {"name": "U1", "url_token": "u1"}, "reply_comment_id": "r1"}],
         "child_comment_count": 3}],
        "paging": {"is_end": True, "next": None}}
    child_page = {"data": [   # the FULL set of 3 children
        {"id": "c1", "content": "full 1", "like_count": 0, "created_time": 1700000001,
         "author": {"name": "U1", "url_token": "u1"}, "reply_comment_id": "r1"},
        {"id": "c2", "content": "full 2", "like_count": 0, "created_time": 1700000002,
         "author": {"name": "U2", "url_token": "u2"}, "reply_comment_id": "c1"},
        {"id": "c3", "content": "full 3", "like_count": 0, "created_time": 1700000003,
         "author": {"name": "U3", "url_token": "u3"}, "reply_comment_id": "r1"}],
        "paging": {"is_end": True, "next": None}}
    httpx_mock.add_response(
        url="https://www.zhihu.com/api/v4/comment_v5/answers/5/root_comment?order_by=score&limit=20",
        json=root_page)
    httpx_mock.add_response(
        url="https://www.zhihu.com/api/v4/comment_v5/comment/r1/child_comment?order_by=ts&limit=20",
        json=child_page)
    out = fetch_comments("answer", "5", cookies={"d_c0": "x"}, limit=None)
    assert [c.id for c in out] == ["r1", "c1", "c2", "c3"]    # root + ALL 3, not the 1-item preview
    assert out[0].parent_id is None
    assert all(c.parent_id == "r1" for c in out if c.id != "r1")   # two-layer flatten
    by_id = {c.id: c for c in out}
    assert by_id["c1"].reply_to_author == "Root"   # c1 -> r1 -> Root
    assert by_id["c2"].reply_to_author == "U1"     # c2 -> c1 -> U1, resolved across the FULL set
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_comments.py::test_fetch_comments_fetches_full_child_tree -v`
Expected: FAIL — v1 returns only `["r1", "c1"]` (inline preview), and `pytest-httpx` errors that the child-endpoint response was never requested.

- [ ] **Step 3: Write minimal implementation** — in `fetch_comments`, between the root loop and `flatten_comments(pages)`, insert:

```python
    # Expand each root's inline child preview into its FULL child set.
    collected_total = 0
    for page in pages:
        for c in page.get("data", []):
            collected_total += 1  # the root comment itself
            inline = c.get("child_comments", [])
            count = c.get("child_comment_count")
            need_more = count is not None and count > len(inline)
            if need_more and (limit is None or collected_total < limit):
                child_budget = None if limit is None else max(0, limit - collected_total)
                full = fetch_child_comments(str(c.get("id")), cookies=cookies, limit=child_budget,
                                            headers=headers, page_size=page_size, max_pages=max_pages)
                c["child_comments"] = full
                collected_total += len(full)
            else:
                collected_total += len(inline)
```

(Leave the existing `flat = flatten_comments(pages)` / `return flat[:limit] ...` lines unchanged.)

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_comments.py::test_fetch_comments_fetches_full_child_tree -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add Engine/zhihu/src/zhihu/comments.py Engine/zhihu/tests/test_comments.py
git commit -m "feat(zhihu): fetch_comments expands inline preview into full child tree"
```

---

### Task 4: Don't over-fetch — skip child call when preview is complete; `comment_limit` caps total

**Files:**
- Test: `Engine/zhihu/tests/test_comments.py`
- (No impl change expected — Task 3 logic covers both; these tests pin the behavior.)

- [ ] **Step 1: Write the failing tests**

```python
def test_fetch_comments_skips_child_fetch_when_preview_complete(httpx_mock):
    root_page = {"data": [
        {"id": "r1", "content": "root", "like_count": 0, "created_time": 1700000000,
         "author": {"name": "Root", "url_token": "root"},
         "child_comments": [
             {"id": "c1", "content": "only child", "like_count": 0, "created_time": 1700000001,
              "author": {"name": "U1", "url_token": "u1"}, "reply_comment_id": "r1"}],
         "child_comment_count": 1}],   # preview already complete
        "paging": {"is_end": True, "next": None}}
    httpx_mock.add_response(
        url="https://www.zhihu.com/api/v4/comment_v5/answers/6/root_comment?order_by=score&limit=20",
        json=root_page)
    # NO child-endpoint mock: if code calls it, pytest-httpx raises on the unmatched request.
    out = fetch_comments("answer", "6", cookies={"d_c0": "x"}, limit=None)
    assert [c.id for c in out] == ["r1", "c1"]

def test_fetch_comments_comment_limit_caps_total(httpx_mock):
    root_page = {"data": [
        {"id": "r1", "content": "root", "like_count": 0, "created_time": 1700000000,
         "author": {"name": "Root", "url_token": "root"},
         "child_comments": [], "child_comment_count": 5}],
        "paging": {"is_end": True, "next": None}}
    child_page = {"data": [
        {"id": f"c{i}", "content": f"child {i}", "like_count": 0, "created_time": 1700000000 + i,
         "author": {"name": f"U{i}", "url_token": f"u{i}"}, "reply_comment_id": "r1"}
        for i in range(1, 6)],
        "paging": {"is_end": True, "next": None}}
    httpx_mock.add_response(
        url="https://www.zhihu.com/api/v4/comment_v5/answers/8/root_comment?order_by=score&limit=20",
        json=root_page)
    httpx_mock.add_response(
        url="https://www.zhihu.com/api/v4/comment_v5/comment/r1/child_comment?order_by=ts&limit=20",
        json=child_page)
    out = fetch_comments("answer", "8", cookies={"d_c0": "x"}, limit=2)
    assert [c.id for c in out] == ["r1", "c1"]   # total capped at 2 (root + 1 child)
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/test_comments.py -k "skips_child_fetch or comment_limit_caps" -v`
Expected: PASS. If `skips_child_fetch` fails with an unmatched-request error, the `need_more` guard is wrong. If `comment_limit_caps` returns >2 items, the early-stop / `flat[:limit]` cap is wrong.

- [ ] **Step 3: Commit**

```bash
git add Engine/zhihu/tests/test_comments.py
git commit -m "test(zhihu): pin no-over-fetch + comment_limit total cap for child tree"
```

---

### Task 5: Full unit suite green + MANDATORY live smoke (the verification gate)

**Files:**
- Possibly Modify: `Engine/zhihu/src/zhihu/comments.py` (only IF smoke reveals the child endpoint has NO usable `paging.next` and needs server-offset handling — see architecture.md)
- Smoke script (throwaway, NOT committed): ad-hoc under `Engine/zhihu/` using gitignored `tests/fixtures/cookies.local.json`

- [ ] **Step 1: Full unit suite**

Run: `pytest -q` (from `Engine/zhihu/`)
Expected: all green (the 51 baseline + the new child-tree tests).

- [ ] **Step 2: Pull cookies (consumer path) into gitignored fixture**

```bash
# from Service/crawl/cookie-manager (service on 127.0.0.1:48088); box jasonjarvan; NEVER commit
COOKIE_MANAGER_CONFIG=config/cookie-manager.yaml node_modules/.bin/tsx src/cli.ts show domain=zhihu.com
# write d_c0 / z_c0 / __zse_ck into Engine/zhihu/tests/fixtures/cookies.local.json (matches *.local* gitignore)
```

- [ ] **Step 3: Live smoke — verify the open empirical question**

Pick a real answer with a root comment having > `page_size` children. Run `fetch_comments("answer", <id>, cookies=<live>, limit=None)`. CONFIRM:
- child endpoint pagination model — does following `paging.next` reach `is_end`? (record cursor vs offset in architecture.md / decisions.md)
- child data field names are snake_case as assumed (`id`/`content`/`like_count`/`created_time`/`author.name`/`reply_comment_id`)
- count of fetched children for that root == its `child_comment_count`
- NO hang; flattened two-layer with correct `parent_id` / `reply_to_author`
- still 200 with plain cookies (no `x-zse-96`) — re-confirm D5 for the child endpoint

- [ ] **Step 4: If smoke contradicts the design**, fix `fetch_child_comments` (e.g. add server-offset fallback) and re-run Steps 1+3 until green. Record the actual model in `architecture.md` smoke-findings + a new decision in `decisions.md`.

- [ ] **Step 5: Commit any smoke-driven fix**

```bash
git add Engine/zhihu/src/zhihu/comments.py
git commit -m "fix(zhihu): align child_comment pagination with live behavior"   # only if a fix was needed
```
