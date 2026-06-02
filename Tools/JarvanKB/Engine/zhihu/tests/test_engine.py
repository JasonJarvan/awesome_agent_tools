from conftest import load_fixture
from zhihu import fetch, FetchResult
from zhihu.models import ZhihuType


def test_fetch_answer_via_initialdata(httpx_mock):
    httpx_mock.add_response(url="https://www.zhihu.com/question/123/answer/456",
                            text=load_fixture("answer_page.html"), status_code=200)
    r = fetch("https://www.zhihu.com/question/123/answer/456", cookies={"d_c0": "x"})
    assert isinstance(r, FetchResult)
    assert r.type is ZhihuType.ANSWER
    assert "Engine body" in r.content_markdown
    assert r.metadata["vote_count"] == 8
    assert r.fetched_at != ""  # stamped by engine


def test_fetch_accepts_cookie_string(httpx_mock):
    httpx_mock.add_response(url="https://www.zhihu.com/question/123/answer/456",
                            text=load_fixture("answer_page.html"), status_code=200)
    r = fetch("https://www.zhihu.com/question/123/answer/456", cookies="d_c0=x; z_c0=y")
    assert r.content_markdown


def test_fetch_falls_back_to_api_on_403(httpx_mock):
    httpx_mock.add_response(url="https://www.zhihu.com/question/123/answer/456",
                            status_code=403, text="forbidden")
    httpx_mock.add_response(url="https://www.zhihu.com/api/v4/answers/456?include=content",
                            json={"id": 456, "content": "<p>API fallback body</p>",
                                  "voteup_count": 1, "comment_count": 0,
                                  "author": {"name": "Alice"}, "question": {"title": "Q?"}})
    r = fetch("https://www.zhihu.com/question/123/answer/456", cookies={"d_c0": "x"})
    assert "API fallback body" in r.content_markdown
