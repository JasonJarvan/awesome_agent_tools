import httpx
from zhihu.comments import flatten_comments, fetch_comments

ROOT_PAGE = {
    "data": [
        {"id": "c1", "content": "top one", "like_count": 5, "created_time": 1700000000,
         "author": {"member": {"name": "Alice", "url_token": "alice"}},
         "child_comments": [
             {"id": "c1a", "content": "reply", "like_count": 1, "created_time": 1700000001,
              "author": {"member": {"name": "Bob", "url_token": "bob"}},
              "reply_to_author": {"member": {"name": "Alice"}}},
         ]},
    ],
    "paging": {"is_end": True},
}

def test_flatten_two_layer():
    out = flatten_comments([ROOT_PAGE])
    assert [c.id for c in out] == ["c1", "c1a"]
    assert out[0].parent_id is None
    assert out[1].parent_id == "c1"
    assert out[1].reply_to_author == "Alice"
    assert out[0].author.name == "Alice"

def test_fetch_comments_paginates(httpx_mock):
    httpx_mock.add_response(
        url="https://www.zhihu.com/api/v4/comment_v5/answers/456/root_comment?order_by=score&limit=20&offset=0",
        json=ROOT_PAGE)
    out = fetch_comments("answer", "456", cookies={"d_c0": "x"}, limit=None)
    assert len(out) == 2

PAGE0 = {
    "data": [{"id": "r0", "content": "p0", "like_count": 0, "created_time": 1700000000,
              "author": {"member": {"name": "A", "url_token": "a"}}, "child_comments": []}],
    "paging": {"is_end": False},
}
PAGE1 = {
    "data": [{"id": "r1", "content": "p1", "like_count": 0, "created_time": 1700000001,
              "author": {"member": {"name": "B", "url_token": "b"}}, "child_comments": []}],
    "paging": {"is_end": True},
}

def test_fetch_comments_multi_page(httpx_mock):
    httpx_mock.add_response(
        url="https://www.zhihu.com/api/v4/comment_v5/answers/9/root_comment?order_by=score&limit=20&offset=0",
        json=PAGE0)
    httpx_mock.add_response(
        url="https://www.zhihu.com/api/v4/comment_v5/answers/9/root_comment?order_by=score&limit=20&offset=20",
        json=PAGE1)
    out = fetch_comments("answer", "9", cookies={"d_c0": "x"}, limit=None)
    assert [c.id for c in out] == ["r0", "r1"]

def test_fetch_comments_bad_type_raises():
    import pytest
    with pytest.raises(ValueError):
        fetch_comments("video", "1", cookies={}, limit=None)
