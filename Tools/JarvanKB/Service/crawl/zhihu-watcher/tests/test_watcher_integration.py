from pathlib import Path
import types
from zhihu_watcher.config import WatcherConfig, CookieSource, CollectionConfig
from zhihu_watcher.favorites_client import CollectionItem
from zhihu_watcher.watermark_store import WatermarkStore
from zhihu_watcher.fetcher import FetchedDoc
from zhihu_watcher.watcher import Watcher


def _config(tmp_path):
    return WatcherConfig(
        poll_interval_minutes=45,
        output_dir=str(tmp_path / "out"),
        state_dir=str(tmp_path / "state"),
        cookie_source=CookieSource(base_url="http://x", uuid="u", password="p"),
        collections=[CollectionConfig(id="c1", name="Box1")],
    )


class _FakeCookies:
    def get_cookies(self):
        return {"z_c0": "x"}


class _FakeFavorites:
    def __init__(self, items):
        self._items = items
        self.calls = 0

    def list_items(self, cid, cookies):
        self.calls += 1
        return self._items


def test_full_cycle_then_second_cycle_is_noop(tmp_path):
    items = [
        CollectionItem(key="answer:11", url="https://www.zhihu.com/question/1/answer/11",
                       content_type="answer", title="Eleven"),
        CollectionItem(key="article:12", url="https://zhuanlan.zhihu.com/p/12",
                       content_type="article", title="Twelve"),
    ]
    fetch_calls = []

    def fake_fetch(url, cookies):
        fetch_calls.append(url)
        return FetchedDoc(title="T-" + url.split("/")[-1], content_markdown="body")

    cfg = _config(tmp_path)
    favorites = _FakeFavorites(items)
    watcher = Watcher(
        config=cfg,
        cookie_provider=_FakeCookies(),
        favorites_client=favorites,
        fetcher_fn=fake_fetch,
        watermark_store=WatermarkStore(cfg.state_dir),
    )

    # First cycle: both items new -> fetched + saved
    watcher.run_cycle()
    out = Path(cfg.output_dir) / "Box1"
    saved = sorted(p.name for p in out.glob("*.md"))
    assert saved == ["T-11.md", "T-12.md"]
    assert len(fetch_calls) == 2

    # Second cycle: nothing new -> no extra fetches, no extra files (THE dedup invariant)
    watcher.run_cycle()
    assert len(fetch_calls) == 2
    assert sorted(p.name for p in out.glob("*.md")) == ["T-11.md", "T-12.md"]


def test_fetch_failure_does_not_mark_seen(tmp_path):
    items = [CollectionItem(key="answer:9", url="https://www.zhihu.com/answer/9",
                            content_type="answer", title="Nine")]
    attempts = {"n": 0}

    def flaky_fetch(url, cookies):
        attempts["n"] += 1
        if attempts["n"] == 1:
            return None              # first cycle: fetch fails
        return FetchedDoc(title="Nine", content_markdown="ok")

    cfg = _config(tmp_path)
    store = WatermarkStore(cfg.state_dir)
    watcher = Watcher(cfg, _FakeCookies(), _FakeFavorites(items), flaky_fetch, store)

    watcher.run_cycle()              # fails -> not marked seen
    assert store.load("c1") == set()
    assert not (Path(cfg.output_dir) / "Box1").exists()

    watcher.run_cycle()              # retried -> succeeds
    assert store.load("c1") == {"answer:9"}
    assert (Path(cfg.output_dir) / "Box1" / "Nine.md").exists()


def test_cookie_failure_skips_cycle_without_crashing(tmp_path):
    class _BoomCookies:
        def get_cookies(self):
            raise RuntimeError("SP-1 down")

    cfg = _config(tmp_path)
    favorites = _FakeFavorites([])
    watcher = Watcher(cfg, _BoomCookies(), favorites, lambda u, c: None, WatermarkStore(cfg.state_dir))
    watcher.run_cycle()              # must not raise
    assert favorites.calls == 0      # never reached listing


def test_unexpected_fetch_exception_does_not_crash_cycle(tmp_path):
    items = [
        CollectionItem(key="answer:1", url="https://www.zhihu.com/answer/1",
                       content_type="answer", title="One"),
        CollectionItem(key="answer:2", url="https://www.zhihu.com/answer/2",
                       content_type="answer", title="Two"),
    ]

    def fetch_fn(url, cookies):
        if url.endswith("/1"):
            raise RuntimeError("engine leaked a non-ZhihuFetchError")
        return FetchedDoc(title="Two", content_markdown="ok")

    cfg = _config(tmp_path)
    store = WatermarkStore(cfg.state_dir)
    watcher = Watcher(cfg, _FakeCookies(), _FakeFavorites(items), fetch_fn, store)

    watcher.run_cycle()              # must NOT raise despite item 1 blowing up
    # item 1 (raised) not marked seen; item 2 still processed
    assert store.load("c1") == {"answer:2"}
    assert (Path(cfg.output_dir) / "Box1" / "Two.md").exists()
    assert not (Path(cfg.output_dir) / "Box1" / "One.md").exists()
