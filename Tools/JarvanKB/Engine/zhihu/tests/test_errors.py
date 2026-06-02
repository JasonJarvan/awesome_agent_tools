from zhihu.errors import ZhihuFetchError


def test_error_carries_diagnostics():
    err = ZhihuFetchError(
        "boom",
        url="https://www.zhihu.com/x",
        attempts=["html", "api"],
        status=403
    )
    assert err.url == "https://www.zhihu.com/x"
    assert err.attempts == ["html", "api"]
    assert err.status == 403
    assert "boom" in str(err)
