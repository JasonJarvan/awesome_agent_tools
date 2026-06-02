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
