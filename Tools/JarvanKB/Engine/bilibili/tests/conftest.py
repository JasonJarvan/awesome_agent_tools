import pytest
from bilibili import ratelimit


@pytest.fixture(autouse=True)
def _reset_engine_pacing(monkeypatch):
    # default OFF in tests: no real sleeps, no cross-test limiter state; tests that exercise
    # pacing/retry opt back in via ratelimit.configure(enabled=True, ...) + their own monkeypatch.
    monkeypatch.setattr(ratelimit, "_sleep", lambda s: None)
    ratelimit._limiter._last = 0.0
    saved = ratelimit._cfg
    ratelimit._cfg = ratelimit._Config(enabled=False)
    yield
    ratelimit._cfg = saved
