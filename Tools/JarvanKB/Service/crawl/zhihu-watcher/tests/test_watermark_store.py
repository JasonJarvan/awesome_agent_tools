from zhihu_watcher.watermark_store import WatermarkStore


def test_empty_when_no_file(tmp_path):
    store = WatermarkStore(str(tmp_path))
    assert store.load("c1") == set()


def test_save_and_reload(tmp_path):
    store = WatermarkStore(str(tmp_path))
    store.save("c1", {"answer:1", "article:2"})
    # a fresh instance must read the same data (survives "restart")
    reloaded = WatermarkStore(str(tmp_path)).load("c1")
    assert reloaded == {"answer:1", "article:2"}


def test_collections_isolated(tmp_path):
    store = WatermarkStore(str(tmp_path))
    store.save("c1", {"answer:1"})
    store.save("c2", {"answer:2"})
    assert store.load("c1") == {"answer:1"}
    assert store.load("c2") == {"answer:2"}


def test_save_is_atomic_no_partial_file(tmp_path):
    store = WatermarkStore(str(tmp_path))
    store.save("c1", {"answer:1"})
    # no leftover temp files
    leftovers = [p.name for p in tmp_path.iterdir() if p.name.endswith(".tmp")]
    assert leftovers == []
