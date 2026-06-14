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
