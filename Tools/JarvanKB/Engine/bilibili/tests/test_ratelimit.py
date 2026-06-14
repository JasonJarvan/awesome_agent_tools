def test_default_config_is_conservative():
    from bilibili import ratelimit
    c = ratelimit._Config()
    assert c.min_interval == 0.3 and c.jitter == 0.2
    assert c.max_retries == 3 and c.backoff_base == 0.5
    assert c.throttle_codes == frozenset({-509, -799})
    assert c.retry_http_statuses == (429,)
    assert c.enabled is True


def test_configure_updates_and_restores():
    from bilibili import ratelimit
    from bilibili import configure
    saved = (ratelimit._cfg.min_interval, ratelimit._cfg.max_retries, ratelimit._cfg.enabled)
    try:
        configure(min_interval=1.25, max_retries=5, enabled=False)
        assert ratelimit._cfg.min_interval == 1.25
        assert ratelimit._cfg.max_retries == 5
        assert ratelimit._cfg.enabled is False
        configure(throttle_codes=[-509, -799, -412])
        assert ratelimit._cfg.throttle_codes == frozenset({-509, -799, -412})
    finally:
        ratelimit._cfg.min_interval, ratelimit._cfg.max_retries, ratelimit._cfg.enabled = saved
        ratelimit._cfg.throttle_codes = frozenset({-509, -799})


def test_rate_limiter_paces_second_call(monkeypatch):
    from bilibili import ratelimit
    clock = {"t": 1000.0}
    slept = []
    monkeypatch.setattr(ratelimit, "_now", lambda: clock["t"])
    monkeypatch.setattr(ratelimit, "_sleep", lambda s: (slept.append(s), clock.__setitem__("t", clock["t"] + s)))
    monkeypatch.setattr(ratelimit, "_rand", lambda a, b: 0.0)   # zero jitter -> deterministic
    lim = ratelimit._RateLimiter()
    lim.acquire(min_interval=0.5, jitter=0.0)   # first call: last=0 -> target far in past -> no sleep
    assert slept == []
    lim.acquire(min_interval=0.5, jitter=0.0)   # immediate second call -> must wait the full interval
    assert slept == [0.5]


def test_rate_limiter_no_wait_when_enough_time_elapsed(monkeypatch):
    from bilibili import ratelimit
    clock = {"t": 1000.0}
    slept = []
    monkeypatch.setattr(ratelimit, "_now", lambda: clock["t"])
    monkeypatch.setattr(ratelimit, "_sleep", lambda s: slept.append(s))
    monkeypatch.setattr(ratelimit, "_rand", lambda a, b: 0.0)
    lim = ratelimit._RateLimiter()
    lim.acquire(0.5, 0.0)
    clock["t"] += 2.0          # 2s passes (e.g. a slow get_info) -> already past interval
    lim.acquire(0.5, 0.0)
    assert slept == []         # no extra pacing when the call itself was slow enough
