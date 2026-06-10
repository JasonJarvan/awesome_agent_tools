import httpx
from pathlib import Path
from datetime import datetime, timezone
from zhihu_watcher.config import WatcherConfig, CookieSource, CollectionConfig, UserTarget
from zhihu_watcher.favorites_client import CollectionItem, FavoritesClient
from zhihu_watcher.watermark_store import WatermarkStore
from zhihu_watcher.failure_store import FailureStore
from zhihu_watcher.fetcher import FetchedDoc
from zhihu_watcher.watcher import Watcher
from zhihu_watcher.resolver import TargetResolver

def _config(tmp_path, **over):
    base = dict(
        poll_interval_minutes=45, output_dir=str(tmp_path / "out"), state_dir=str(tmp_path / "state"),
        cookie_source=CookieSource("http://x", "u", "p"),
        targets=[CollectionConfig(id="c1", name="Box1")],
    )
    base.update(over)
    return WatcherConfig(**base)

class _FakeCookies:
    def get_cookies(self): return {"z_c0": "x"}

class _FakeResolver:
    def __init__(self, cols): self._c = cols
    def resolve(self, targets, cookies): return self._c

class _FakeFavorites:
    def __init__(self, items): self._items = items; self.calls = 0
    def list_items(self, cid, cookies): self.calls += 1; return self._items

def _build(cfg, items, fetch_fn, *, cols=None, now=None):
    store = WatermarkStore(cfg.state_dir)
    fs = FailureStore(cfg.state_dir, now_fn=(lambda: now) if now is not None else __import__("time").time)
    w = Watcher(cfg, _FakeCookies(), _FakeFavorites(items), fetch_fn, store,
                resolver=_FakeResolver(cols or [CollectionConfig("c1", "Box1")]),
                failure_store=fs,
                now_fn=(lambda: datetime.fromtimestamp(now, tz=timezone.utc)) if now is not None
                       else (lambda: datetime.now(timezone.utc)))
    return w, store, fs


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
    w, store, _ = _build(cfg, items, fake_fetch)

    # First cycle: both items new -> fetched + saved
    w.run_cycle()
    out = Path(cfg.output_dir) / "Box1"
    saved = sorted(p.name for p in out.glob("*.md"))
    assert saved == ["T-11.md", "T-12.md"]
    assert len(fetch_calls) == 2

    # Second cycle: nothing new -> no extra fetches, no extra files (THE dedup invariant)
    w.run_cycle()
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
    w, store, _ = _build(cfg, items, flaky_fetch, now=None)

    w.run_cycle()              # fails -> not marked seen
    assert store.load("c1") == set()
    assert not (Path(cfg.output_dir) / "Box1").exists()

    w.run_cycle()              # retried -> succeeds
    assert store.load("c1") == {"answer:9"}
    assert (Path(cfg.output_dir) / "Box1" / "Nine.md").exists()


def test_cookie_failure_skips_cycle_without_crashing(tmp_path):
    class _BoomCookies:
        def get_cookies(self):
            raise RuntimeError("SP-1 down")

    cfg = _config(tmp_path)
    favorites = _FakeFavorites([])
    store = WatermarkStore(cfg.state_dir)
    fs = FailureStore(cfg.state_dir)
    watcher = Watcher(cfg, _BoomCookies(), favorites, lambda u, c: None, store,
                      resolver=_FakeResolver([CollectionConfig("c1", "Box1")]),
                      failure_store=fs)
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
    w, store, _ = _build(cfg, items, fetch_fn)

    w.run_cycle()              # must NOT raise despite item 1 blowing up
    # item 1 (raised) not marked seen; item 2 still processed
    assert store.load("c1") == {"answer:2"}
    assert (Path(cfg.output_dir) / "Box1" / "Two.md").exists()
    assert not (Path(cfg.output_dir) / "Box1" / "One.md").exists()


def test_corrupt_seen_file_skips_collection_without_crashing(tmp_path):
    items = [CollectionItem(key="answer:1", url="https://www.zhihu.com/answer/1",
                            content_type="answer", title="One")]
    fetch_calls = []

    def fetch_fn(url, cookies):
        fetch_calls.append(url)
        return FetchedDoc(title="One", content_markdown="ok")

    cfg = _config(tmp_path)
    # pre-write a corrupt state file for collection c1
    state = Path(cfg.state_dir)
    state.mkdir(parents=True, exist_ok=True)
    (state / "seen-c1.json").write_text("{not valid json", encoding="utf-8")

    w, _, _ = _build(cfg, items, fetch_fn)
    w.run_cycle()                 # must NOT raise despite the corrupt state file
    assert fetch_calls == []            # collection skipped -> nothing fetched
    assert not (Path(cfg.output_dir) / "Box1").exists()


def test_main_once_runs_single_cycle(tmp_path, monkeypatch):
    import zhihu_watcher.__main__ as m

    calls = {"n": 0}

    class _W:
        def run_cycle(self):
            calls["n"] += 1

    monkeypatch.setattr(m, "build_watcher", lambda cfg: _W())
    monkeypatch.setattr(m, "load_config", lambda path: object())

    m.main(["--once", "--config", "irrelevant.yaml"])
    assert calls["n"] == 1   # exactly one cycle, no scheduler started


def test_main_default_schedules_unpaused_interval_job(tmp_path, monkeypatch):
    import types as _t
    import zhihu_watcher.__main__ as m

    cycles = {"n": 0}

    class _W:
        def run_cycle(self):
            cycles["n"] += 1

    captured = {}

    class _FakeScheduler:
        def add_job(self, func, **kwargs):
            captured["kwargs"] = kwargs

        def start(self):
            captured["started"] = True  # no-op so the test does not block

        def shutdown(self):
            pass

    fake_cfg = _t.SimpleNamespace(poll_interval_minutes=45, targets=[1, 2])
    monkeypatch.setattr(m, "load_config", lambda path: fake_cfg)
    monkeypatch.setattr(m, "build_watcher", lambda cfg: _W())
    monkeypatch.setattr(m, "BlockingScheduler", lambda: _FakeScheduler())

    m.main([])  # default mode (no --once)

    assert cycles["n"] == 1                                  # immediate run happened once
    assert captured.get("started") is True                  # scheduler was started
    assert captured["kwargs"]["trigger"] == "interval"
    assert captured["kwargs"]["minutes"] == 45
    assert captured["kwargs"]["max_instances"] == 1
    # paused-job guard: next_run_time must NOT be explicitly None (that would pause the job)
    assert captured["kwargs"].get("next_run_time", "absent") is not None


def test_first_run_baseline_skips_old_favorites(tmp_path):
    old = CollectionItem("answer:old", "https://www.zhihu.com/answer/old", "answer", "Old",
                         favorited_at=datetime(2020, 1, 1, tzinfo=timezone.utc))
    new = CollectionItem("answer:new", "https://www.zhihu.com/answer/new", "answer", "New",
                         favorited_at=datetime(2026, 6, 9, tzinfo=timezone.utc))
    fetched = []
    def fake_fetch(url, c): fetched.append(url); return FetchedDoc("T", "body")
    cfg = _config(tmp_path)
    w, store, _ = _build(cfg, [old, new], fake_fetch, now=datetime(2026, 6, 8, tzinfo=timezone.utc).timestamp())
    w.run_cycle()
    assert fetched == ["https://www.zhihu.com/answer/new"]
    assert store.load("c1") == {"answer:new"}

def test_item_in_cooldown_is_skipped(tmp_path):
    item = CollectionItem("article:1", "https://zhuanlan.zhihu.com/p/1", "article", "A",
                          favorited_at=datetime(2026, 6, 9, tzinfo=timezone.utc))
    cfg = _config(tmp_path, backfill_on_first_run=True, max_consecutive_failures=1)
    calls = []
    def failing_fetch(url, c): calls.append(url); return None  # always fails
    w, _, fs = _build(cfg, [item], failing_fetch, now=1000.0)
    w.run_cycle()
    assert fs.should_skip("c1", "article:1") is True
    w.run_cycle()
    assert calls == ["https://zhuanlan.zhihu.com/p/1"]


def test_full_cycle_with_real_resolver_and_user_target(tmp_path):
    def handler(request):
        path = request.url.path
        if path == "/api/v4/me":
            return httpx.Response(200, json={"url_token": "zhao"})
        if path == "/api/v4/people/zhao/collections":
            return httpx.Response(200, json={"data": [
                {"id": 721, "title": "我的收藏", "is_default": True, "item_count": 5},
                {"id": 865, "title": "技术-AI生成", "is_default": False, "item_count": 2},
            ], "paging": {"totals": 2, "is_end": True}})
        if path == "/api/v4/collections/865/items":
            return httpx.Response(200, json={"data": [
                {"content": {"type": "answer", "id": "a1",
                             "url": "https://www.zhihu.com/question/1/answer/a1",
                             "question": {"title": "Q1"}, "excerpt": "lead"}},
            ], "paging": {"totals": 1, "is_end": True}})
        raise AssertionError(f"unexpected path {path}")

    fc = FavoritesClient(http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    cfg = _config(tmp_path, targets=[UserTarget(url_token="me")], backfill_on_first_run=True)
    store = WatermarkStore(cfg.state_dir)
    fs = FailureStore(cfg.state_dir, now_fn=lambda: 0.0)
    saved = []
    def fake_fetch(url, cookies):
        saved.append(url)
        return FetchedDoc("Q1", "body")
    w = Watcher(cfg, _FakeCookies(), fc, fake_fetch, store,
                resolver=TargetResolver(fc), failure_store=fs)
    w.run_cycle()
    # default 我的收藏 (721) skipped; only 技术-AI生成 (865) polled + saved
    assert saved == ["https://www.zhihu.com/question/1/answer/a1"]
    assert (Path(cfg.output_dir) / "技术-AI生成" / "Q1.md").exists()
