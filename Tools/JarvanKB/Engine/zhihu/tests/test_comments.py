from zhihu.comments import flatten_comments, fetch_comments

ROOT_PAGE = {
    "data": [
        {"id": "r1", "content": "top one", "like_count": 5, "created_time": 1700000000,
         "author": {"name": "Alice", "url_token": "alice", "headline": "dev"},
         "child_comments": [
             {"id": "r1a", "content": "reply", "like_count": 1, "created_time": 1700000001,
              "author": {"name": "Bob", "url_token": "bob"},
              "reply_comment_id": "r1", "reply_root_comment_id": "r1", "reply_to_author": None},
         ]},
    ],
    "paging": {"is_end": True, "next": None},
}

def test_flatten_two_layer_real_schema():
    out = flatten_comments([ROOT_PAGE])
    assert [c.id for c in out] == ["r1", "r1a"]
    assert out[0].parent_id is None
    assert out[0].author.name == "Alice"
    assert out[0].author.url == "https://www.zhihu.com/people/alice"
    assert out[1].parent_id == "r1"            # child linked to its root
    assert out[1].author.name == "Bob"
    assert out[1].reply_to_author == "Alice"   # resolved from reply_comment_id -> id->name map


def test_flatten_converts_comment_html_to_markdown():
    page = {"data": [{"id": "x", "content": "see <a href=\"https://z.cn\">link</a> and <strong>bold</strong>",
                      "like_count": 0, "created_time": 1700000000,
                      "author": {"name": "A", "url_token": "a"}, "child_comments": []}],
            "paging": {"is_end": True, "next": None}}
    out = flatten_comments([page])
    assert "**bold**" in out[0].content        # HTML converted to Markdown
    assert "<strong>" not in out[0].content
    assert "https://z.cn" in out[0].content

def test_fetch_comments_cursor_pagination(httpx_mock):
    page0 = {"data": [{"id": "a", "content": "c-a", "like_count": 0, "created_time": 1700000000,
                       "author": {"name": "A", "url_token": "a"}, "child_comments": []}],
             "paging": {"is_end": False,
                        "next": "https://www.zhihu.com/api/v4/comment_v5/answers/9/root_comment?order_by=score&limit=20&cursor=C2"}}
    page1 = {"data": [{"id": "b", "content": "c-b", "like_count": 0, "created_time": 1700000001,
                       "author": {"name": "B", "url_token": "b"}, "child_comments": []}],
             "paging": {"is_end": True, "next": None}}
    httpx_mock.add_response(
        url="https://www.zhihu.com/api/v4/comment_v5/answers/9/root_comment?order_by=score&limit=20",
        json=page0)
    httpx_mock.add_response(
        url="https://www.zhihu.com/api/v4/comment_v5/answers/9/root_comment?order_by=score&limit=20&cursor=C2",
        json=page1)
    out = fetch_comments("answer", "9", cookies={"d_c0": "x"}, limit=None)
    assert [c.id for c in out] == ["a", "b"]

def test_fetch_comments_no_infinite_loop_on_empty_data(httpx_mock):
    # data=[] + is_end False + a next cursor: MUST break on empty data, not keep requesting.
    httpx_mock.add_response(
        url="https://www.zhihu.com/api/v4/comment_v5/answers/7/root_comment?order_by=score&limit=20",
        json={"data": [], "paging": {"is_end": False,
              "next": "https://www.zhihu.com/api/v4/comment_v5/answers/7/root_comment?order_by=score&limit=20&cursor=SAME"}})
    out = fetch_comments("answer", "7", cookies={"d_c0": "x"}, limit=None)
    assert out == []   # returns immediately, no hang, no second request

def test_fetch_comments_bad_type_raises():
    import pytest
    with pytest.raises(ValueError):
        fetch_comments("video", "1", cookies={}, limit=None)


# --- v1.1: full child-comment tree -------------------------------------------------

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


def test_fetch_child_comments_no_hang_on_empty_data(httpx_mock):
    # data=[] + is_end False + a next: MUST break on empty data (not keep requesting -> would exhaust
    # the single mocked response and raise; the guard returns [] after one request instead).
    httpx_mock.add_response(
        url="https://www.zhihu.com/api/v4/comment_v5/comment/r9/child_comment?order_by=ts&limit=20",
        json={"data": [], "paging": {"is_end": False,
              "next": "https://www.zhihu.com/api/v4/comment_v5/comment/r9/child_comment?order_by=ts&limit=20&offset=SAME"}})
    from zhihu.comments import fetch_child_comments
    out = fetch_child_comments("r9", cookies={"d_c0": "x"}, limit=None)
    assert out == []   # one request, empty-data break, no hang


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
    assert [c["id"] for c in out] == ["c1", "c2"]   # 2 requests, then seen-next breaks, no hang


def test_fetch_comments_fetches_full_child_tree(httpx_mock):
    root_page = {"data": [
        {"id": "r1", "content": "root", "like_count": 9, "created_time": 1700000000,
         "author": {"name": "Root", "url_token": "root"},
         "child_comments": [   # only a 1-item inline PREVIEW
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


def test_fetch_comments_skips_child_fetch_when_preview_complete(httpx_mock):
    root_page = {"data": [
        {"id": "r1", "content": "root", "like_count": 0, "created_time": 1700000000,
         "author": {"name": "Root", "url_token": "root"},
         "child_comments": [
             {"id": "c1", "content": "only child", "like_count": 0, "created_time": 1700000001,
              "author": {"name": "U1", "url_token": "u1"}, "reply_comment_id": "r1"}],
         "child_comment_count": 1}],   # preview already complete -> no child request
        "paging": {"is_end": True, "next": None}}
    httpx_mock.add_response(
        url="https://www.zhihu.com/api/v4/comment_v5/answers/6/root_comment?order_by=score&limit=20",
        json=root_page)
    # NO child-endpoint mock: if the code calls it, pytest-httpx raises on the unmatched request.
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


def test_fetch_comments_multiple_roots_each_fetch_children(httpx_mock):
    # Two roots, each with a full child set on its OWN child endpoint. Pins per-root URL
    # construction, collected_total accumulation across roots, and no id->name collision.
    root_page = {"data": [
        {"id": "r1", "content": "root1", "like_count": 0, "created_time": 1700000000,
         "author": {"name": "Root1", "url_token": "root1"},
         "child_comments": [], "child_comment_count": 2},
        {"id": "r2", "content": "root2", "like_count": 0, "created_time": 1700000010,
         "author": {"name": "Root2", "url_token": "root2"},
         "child_comments": [], "child_comment_count": 2}],
        "paging": {"is_end": True, "next": None}}
    r1_children = {"data": [
        {"id": "a1", "content": "a1", "like_count": 0, "created_time": 1700000001,
         "author": {"name": "A1", "url_token": "a1"}, "reply_comment_id": "r1"},
        {"id": "a2", "content": "a2", "like_count": 0, "created_time": 1700000002,
         "author": {"name": "A2", "url_token": "a2"}, "reply_comment_id": "a1"}],
        "paging": {"is_end": True, "next": None}}
    r2_children = {"data": [
        {"id": "b1", "content": "b1", "like_count": 0, "created_time": 1700000011,
         "author": {"name": "B1", "url_token": "b1"}, "reply_comment_id": "r2"},
        {"id": "b2", "content": "b2", "like_count": 0, "created_time": 1700000012,
         "author": {"name": "B2", "url_token": "b2"}, "reply_comment_id": "b1"}],
        "paging": {"is_end": True, "next": None}}
    httpx_mock.add_response(
        url="https://www.zhihu.com/api/v4/comment_v5/answers/9/root_comment?order_by=score&limit=20",
        json=root_page)
    httpx_mock.add_response(
        url="https://www.zhihu.com/api/v4/comment_v5/comment/r1/child_comment?order_by=ts&limit=20",
        json=r1_children)
    httpx_mock.add_response(
        url="https://www.zhihu.com/api/v4/comment_v5/comment/r2/child_comment?order_by=ts&limit=20",
        json=r2_children)
    out = fetch_comments("answer", "9", cookies={"d_c0": "x"}, limit=None)
    assert [c.id for c in out] == ["r1", "a1", "a2", "r2", "b1", "b2"]   # each root's full set, in order
    by_id = {c.id: c for c in out}
    assert by_id["a1"].parent_id == "r1" and by_id["a2"].parent_id == "r1"
    assert by_id["b1"].parent_id == "r2" and by_id["b2"].parent_id == "r2"
    assert by_id["a2"].reply_to_author == "A1"   # resolved within r1's set
    assert by_id["b2"].reply_to_author == "B1"   # resolved within r2's set, no cross-root collision
