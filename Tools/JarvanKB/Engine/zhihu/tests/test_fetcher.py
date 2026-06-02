from zhihu.fetcher import get_page, get_api_answer, NAV_HEADERS, API_HEADERS

def test_nav_and_api_headers_have_no_signature():
    assert "x-zse-96" not in {k.lower() for k in NAV_HEADERS}
    assert "User-Agent" in NAV_HEADERS
    assert API_HEADERS["x-requested-with"] == "fetch"

def test_get_page_returns_status_and_text(httpx_mock):
    httpx_mock.add_response(url="https://www.zhihu.com/answer/1", text="<html>hi</html>", status_code=200)
    status, text = get_page("https://www.zhihu.com/answer/1", cookies={"d_c0": "x"})
    assert status == 200
    assert "hi" in text

def test_get_api_answer(httpx_mock):
    httpx_mock.add_response(
        url="https://www.zhihu.com/api/v4/answers/1?include=content",
        json={"id": 1, "content": "<p>api body</p>"})
    data = get_api_answer("1", cookies={"d_c0": "x"})
    assert data["content"] == "<p>api body</p>"
