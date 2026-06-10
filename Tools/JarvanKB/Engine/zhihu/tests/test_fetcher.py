from zhihu.fetcher import get_page, get_api_answer, NAV_HEADERS, API_HEADERS

def test_nav_and_api_headers_have_no_signature():
    assert "x-zse-96" not in {k.lower() for k in NAV_HEADERS}
    assert "User-Agent" in NAV_HEADERS
    assert API_HEADERS["x-requested-with"] == "fetch"
    assert "x-zse-96" not in {k.lower() for k in API_HEADERS}

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


# --- v1.2 rate-limit hardening ---

def test_configure_updates_defaults_and_resets():
    from zhihu import fetcher
    saved = fetcher._cfg.min_interval, fetcher._cfg.max_retries, fetcher._cfg.enabled
    try:
        from zhihu import configure
        configure(min_interval=1.25, max_retries=5, enabled=False)
        assert fetcher._cfg.min_interval == 1.25
        assert fetcher._cfg.max_retries == 5
        assert fetcher._cfg.enabled is False
    finally:
        fetcher._cfg.min_interval, fetcher._cfg.max_retries, fetcher._cfg.enabled = saved


def test_default_config_is_conservative():
    from zhihu import fetcher
    c = fetcher._Config()
    assert c.min_interval == 0.3 and c.jitter == 0.2
    assert c.max_retries == 3 and c.backoff_base == 0.5
    assert c.retry_statuses == (403, 429) and c.enabled is True


def test_rate_limiter_paces_second_call(monkeypatch):
    from zhihu import fetcher
    clock = {"t": 1000.0}
    slept = []
    monkeypatch.setattr(fetcher, "_now", lambda: clock["t"])
    monkeypatch.setattr(fetcher, "_sleep", lambda s: (slept.append(s), clock.__setitem__("t", clock["t"] + s)))
    monkeypatch.setattr(fetcher, "_rand", lambda a, b: 0.0)   # zero jitter -> deterministic
    lim = fetcher._RateLimiter()
    lim.acquire(min_interval=0.5, jitter=0.0)   # first call: last=0 -> target far in past -> no sleep
    assert slept == []
    lim.acquire(min_interval=0.5, jitter=0.0)   # immediate second call -> must wait the full interval
    assert slept == [0.5]


def test_rate_limiter_no_wait_when_enough_time_elapsed(monkeypatch):
    from zhihu import fetcher
    clock = {"t": 1000.0}
    slept = []
    monkeypatch.setattr(fetcher, "_now", lambda: clock["t"])
    monkeypatch.setattr(fetcher, "_sleep", lambda s: slept.append(s))
    monkeypatch.setattr(fetcher, "_rand", lambda a, b: 0.0)
    lim = fetcher._RateLimiter()
    lim.acquire(0.5, 0.0)
    clock["t"] += 2.0          # 2s passes (e.g. a slow nav-GET download) -> already past interval
    lim.acquire(0.5, 0.0)
    assert slept == []         # no extra pacing when the request itself was slow enough


def test_request_retries_403_then_succeeds(httpx_mock, monkeypatch):
    from zhihu import fetcher
    monkeypatch.setattr(fetcher, "_sleep", lambda s: None)          # no real waiting
    monkeypatch.setattr(fetcher, "_rand", lambda a, b: 0.0)
    monkeypatch.setattr(fetcher._limiter, "_last", 0.0, raising=False)
    httpx_mock.add_response(url="https://www.zhihu.com/answer/9", status_code=403, text="no")
    httpx_mock.add_response(url="https://www.zhihu.com/answer/9", status_code=200, text="yes")
    fetcher.configure(min_interval=0.0, jitter=0.0, max_retries=3, enabled=True)
    r = fetcher._request("https://www.zhihu.com/answer/9", cookies={"d_c0": "x"},
                         headers=fetcher.NAV_HEADERS, timeout=5.0)
    assert r.status_code == 200 and r.text == "yes"


def test_request_honors_retry_after_header(httpx_mock, monkeypatch):
    from zhihu import fetcher
    waits = []
    monkeypatch.setattr(fetcher, "_sleep", lambda s: waits.append(s))
    monkeypatch.setattr(fetcher, "_rand", lambda a, b: 0.0)
    httpx_mock.add_response(url="https://www.zhihu.com/answer/7", status_code=429,
                            headers={"Retry-After": "12"}, text="slow down")
    httpx_mock.add_response(url="https://www.zhihu.com/answer/7", status_code=200, text="ok")
    fetcher.configure(min_interval=0.0, jitter=0.0, max_retries=3, backoff_base=0.5, enabled=True)
    r = fetcher._request("https://www.zhihu.com/answer/7", cookies={"d_c0": "x"},
                         headers=fetcher.API_HEADERS, timeout=5.0)
    assert r.status_code == 200
    assert 12 in waits            # honored Retry-After, not the 0.5 backoff


def test_request_gives_up_after_max_retries(httpx_mock, monkeypatch):
    from zhihu import fetcher
    monkeypatch.setattr(fetcher, "_sleep", lambda s: None)
    monkeypatch.setattr(fetcher, "_rand", lambda a, b: 0.0)
    for _ in range(4):            # initial + 3 retries
        httpx_mock.add_response(url="https://www.zhihu.com/answer/5", status_code=403, text="nope")
    fetcher.configure(min_interval=0.0, jitter=0.0, max_retries=3, enabled=True)
    r = fetcher._request("https://www.zhihu.com/answer/5", cookies={"d_c0": "x"},
                         headers=fetcher.NAV_HEADERS, timeout=5.0)
    assert r.status_code == 403   # returns the last response; caller decides (raise / fallback)
