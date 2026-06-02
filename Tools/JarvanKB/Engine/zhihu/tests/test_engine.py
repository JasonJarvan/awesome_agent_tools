import pytest
from conftest import load_fixture
from zhihu import fetch, FetchResult, ZhihuFetchError
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


def test_fetch_css_scrape_fallback(httpx_mock):
    html = '<html><body><div class="RichContent-inner"><p>CSS body</p></div></body></html>'
    httpx_mock.add_response(url="https://www.zhihu.com/answer/77", text=html, status_code=200)
    r = fetch("https://www.zhihu.com/answer/77", cookies={"d_c0": "x"})
    assert "CSS body" in r.content_markdown


def test_fetch_raises_on_non_200_non_403(httpx_mock):
    httpx_mock.add_response(url="https://www.zhihu.com/answer/500", status_code=500, text="err")
    with pytest.raises(ZhihuFetchError):
        fetch("https://www.zhihu.com/answer/500", cookies={"d_c0": "x"})


def test_fetch_with_comments_answer(httpx_mock):
    httpx_mock.add_response(url="https://www.zhihu.com/question/123/answer/456",
                            text=load_fixture("answer_page.html"), status_code=200)
    httpx_mock.add_response(
        url="https://www.zhihu.com/api/v4/comment_v5/answers/456/root_comment?order_by=score&limit=20",
        json={"data": [{"id": "k1", "content": "nice", "like_count": 2, "created_time": 1700000000,
                        "author": {"name": "Carol", "url_token": "carol"},
                        "child_comments": []}],
              "paging": {"is_end": True, "next": None}})
    r = fetch("https://www.zhihu.com/question/123/answer/456", cookies={"d_c0": "x"}, with_comments=True)
    assert len(r.comments) == 1
    assert r.comments[0].content == "nice"
    assert r.comments[0].parent_id is None


def test_fetch_question_via_initialdata(httpx_mock):
    html = ('<html><body><script id="js-initialData" type="text/json">'
            '{"initialState":{"entities":{'
            '"questions":{"123":{"id":123,"title":"Why?","detail":"<p>detail</p>",'
            '"answerCount":1,"followerCount":3,"visitCount":9}},'
            '"answers":{"456":{"id":456,"content":"<p>ans</p>","voteup_count":5,"comment_count":0,'
            '"created_time":1700000000,"updated_time":1700000000,'
            '"author":{"name":"Al","url_token":"al"},"question":{"id":123}}}}}}'
            '</script></body></html>')
    httpx_mock.add_response(url="https://www.zhihu.com/question/123", text=html, status_code=200)
    r = fetch("https://www.zhihu.com/question/123", cookies={"d_c0": "x"})
    assert r.type is ZhihuType.QUESTION
    assert r.title == "Why?"
    assert r.metadata["answer_count"] == 1
    assert [a.answer_id for a in r.answers] == ["456"]
    assert "ans" in r.answers[0].content_markdown
