from pathlib import Path
from bilibili_watcher.config import (
    WatcherConfig, CookieSource, EngineConfig, RenderConfig, FolderConfig,
)
from bilibili_watcher.favorites_client import BiliFavItem
from bilibili_watcher.watermark_store import WatermarkStore
from bilibili_watcher.fetcher import FetchedDoc
from bilibili_watcher.watcher import Watcher


def _config(tmp_path):
    return WatcherConfig(
        poll_interval_minutes=20,
        output_dir=str(tmp_path / "out"),
        state_dir=str(tmp_path / "state"),
        cookie_source=CookieSource("http://x", "u", "p"),
        engine=EngineConfig("b", "pid", "m"),
        render=RenderConfig(),
        folders=[FolderConfig(id="f1", name="Box1")],
    )


class _FakeCookies:
    def get_cookies(self):
        return {"SESSDATA": "s", "bili_jct": "j"}


class _FakeFavorites:
    def __init__(self, items):
        self._items = items
        self.calls = []

    def list_items(self, fid, cookies, since_fav_time=0):
        self.calls.append(since_fav_time)
        # emulate fav_time early-stop against the watermark passed in
        return [i for i in self._items if i.fav_time > since_fav_time]


def _item(bvid, ft):
    return BiliFavItem(bvid=bvid, fav_time=ft, title="T-" + bvid)


def test_full_cycle_then_second_is_noop_and_passes_watermark(tmp_path):
    items = [_item("BV1", 300), _item("BV2", 200)]
    fetch_calls = []

    def fake_fetch(bvid, cred):
        fetch_calls.append(bvid)
        return FetchedDoc(title="T-" + bvid, markdown="body\n")

    cfg = _config(tmp_path)
    fav = _FakeFavorites(items)
    store = WatermarkStore(cfg.state_dir)
    w = Watcher(cfg, _FakeCookies(), fav, fake_fetch, store)

    w.run_cycle()
    out = Path(cfg.output_dir) / "Box1"
    assert sorted(p.name for p in out.glob("*.md")) == ["T-BV1.md", "T-BV2.md"]
    assert fetch_calls == ["BV1", "BV2"]
    st = store.load("f1")
    assert st.watermark == 300 and st.seen == {"BV1", "BV2"}

    # second cycle: watermark 300 passed in -> fake returns nothing new -> no fetch, no file
    w.run_cycle()
    assert fav.calls == [0, 300]
    assert fetch_calls == ["BV1", "BV2"]


def test_fetch_failure_holds_watermark_below_failure_and_retries(tmp_path):
    items = [_item("BV1", 300), _item("BV2", 200)]
    attempts = {"BV2": 0}

    def flaky_fetch(bvid, cred):
        if bvid == "BV2":
            attempts["BV2"] += 1
            if attempts["BV2"] == 1:
                return None                       # BV2 fails first cycle
        return FetchedDoc(title="T-" + bvid, markdown="ok\n")

    cfg = _config(tmp_path)
    store = WatermarkStore(cfg.state_dir)
    w = Watcher(cfg, _FakeCookies(), _FakeFavorites(items), flaky_fetch, store)

    w.run_cycle()
    st = store.load("f1")
    assert st.seen == {"BV1"}                      # BV2 not saved
    assert st.watermark == 199                     # held below the failure (200-1) per §5
    assert (Path(cfg.output_dir) / "Box1" / "T-BV1.md").exists()

    w.run_cycle()                                  # re-lists fav_time>199 -> BV1(seen,skip)+BV2(retry)
    st = store.load("f1")
    assert st.seen == {"BV1", "BV2"}
    assert st.watermark == 300


def test_no_sessdata_skips_cycle(tmp_path):
    class _NoSess:
        def get_cookies(self):
            return {"bili_jct": "j"}              # no SESSDATA

    cfg = _config(tmp_path)
    fav = _FakeFavorites([_item("BV1", 1)])
    Watcher(cfg, _NoSess(), fav, lambda b, c: None, WatermarkStore(cfg.state_dir)).run_cycle()
    assert fav.calls == []                          # never listed


def test_cookie_failure_skips_without_crashing(tmp_path):
    class _Boom:
        def get_cookies(self):
            raise RuntimeError("SP-1 down")

    cfg = _config(tmp_path)
    fav = _FakeFavorites([_item("BV1", 1)])
    Watcher(cfg, _Boom(), fav, lambda b, c: None, WatermarkStore(cfg.state_dir)).run_cycle()
    assert fav.calls == []


def test_listing_error_skips_folder_without_crashing(tmp_path):
    class _BoomFav:
        calls = []

        def list_items(self, fid, cookies, since_fav_time=0):
            raise RuntimeError("403")

    cfg = _config(tmp_path)
    Watcher(cfg, _FakeCookies(), _BoomFav(), lambda b, c: None, WatermarkStore(cfg.state_dir)).run_cycle()
    # must not raise; nothing saved
    assert not (Path(cfg.output_dir) / "Box1").exists()


def test_unexpected_fetch_exception_does_not_crash_cycle(tmp_path):
    items = [_item("BV1", 300), _item("BV2", 200)]

    def fetch_fn(bvid, cred):
        if bvid == "BV1":
            raise RuntimeError("engine leaked a non-BilibiliEngineError")
        return FetchedDoc(title="T-BV2", markdown="ok\n")

    cfg = _config(tmp_path)
    store = WatermarkStore(cfg.state_dir)
    Watcher(cfg, _FakeCookies(), _FakeFavorites(items), fetch_fn, store).run_cycle()
    st = store.load("f1")
    assert st.seen == {"BV2"}                       # BV1 (raised) not seen
    assert st.watermark == 299                      # next_watermark(0,[300,200],[300])=min([300])-1=299
    assert (Path(cfg.output_dir) / "Box1" / "T-BV2.md").exists()
    assert not (Path(cfg.output_dir) / "Box1" / "T-BV1.md").exists()


def test_corrupt_state_file_skips_folder(tmp_path):
    cfg = _config(tmp_path)
    state = Path(cfg.state_dir)
    state.mkdir(parents=True, exist_ok=True)
    (state / "state-f1.json").write_text("{bad json", encoding="utf-8")
    fetch_calls = []
    Watcher(cfg, _FakeCookies(), _FakeFavorites([_item("BV1", 1)]),
            lambda b, c: fetch_calls.append(b), WatermarkStore(cfg.state_dir)).run_cycle()
    assert fetch_calls == []                          # folder skipped


def test_main_once_runs_single_cycle(monkeypatch):
    import bilibili_watcher.__main__ as m
    calls = {"n": 0}

    class _W:
        def run_cycle(self):
            calls["n"] += 1

    monkeypatch.setattr(m, "build_watcher", lambda cfg: _W())
    monkeypatch.setattr(m, "load_config", lambda path: object())
    m.main(["--once", "--config", "irrelevant.yaml"])
    assert calls["n"] == 1


def test_main_default_schedules_interval_job(monkeypatch):
    import types as _t
    import bilibili_watcher.__main__ as m
    cycles = {"n": 0}

    class _W:
        def run_cycle(self):
            cycles["n"] += 1

    captured = {}

    class _FakeScheduler:
        def add_job(self, func, **kwargs):
            captured["kwargs"] = kwargs

        def start(self):
            captured["started"] = True

        def shutdown(self):
            pass

    fake_cfg = _t.SimpleNamespace(poll_interval_minutes=20, folders=[1, 2])
    monkeypatch.setattr(m, "load_config", lambda path: fake_cfg)
    monkeypatch.setattr(m, "build_watcher", lambda cfg: _W())
    monkeypatch.setattr(m, "BlockingScheduler", lambda: _FakeScheduler())
    m.main([])
    assert cycles["n"] == 1
    assert captured.get("started") is True
    assert captured["kwargs"]["trigger"] == "interval"
    assert captured["kwargs"]["minutes"] == 20
    assert captured["kwargs"]["max_instances"] == 1
