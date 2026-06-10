from pathlib import Path
import pytest

FIXTURES = Path(__file__).parent / "fixtures"

@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES

def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.fixture(autouse=True)
def _reset_engine_pacing(monkeypatch):
    # Default OFF in tests: no real sleeps, no cross-test limiter state. Tests that exercise
    # pacing/retry opt back in via fetcher.configure(enabled=True, ...) + their own monkeypatch.
    from zhihu import fetcher
    monkeypatch.setattr(fetcher, "_sleep", lambda s: None)
    fetcher._limiter._last = 0.0
    saved = fetcher._cfg
    fetcher._cfg = fetcher._Config(enabled=False)
    yield
    fetcher._cfg = saved
