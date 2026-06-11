from bilibili_watcher.watermark_store import WatermarkStore, FolderState, next_watermark


def test_load_empty(tmp_path):
    st = WatermarkStore(str(tmp_path)).load("f1")
    assert st.watermark == 0 and st.seen == set()


def test_save_and_reload(tmp_path):
    store = WatermarkStore(str(tmp_path))
    store.save("f1", FolderState(watermark=300, seen={"BV1", "BV2"}))
    reloaded = WatermarkStore(str(tmp_path)).load("f1")
    assert reloaded.watermark == 300
    assert reloaded.seen == {"BV1", "BV2"}


def test_folders_isolated(tmp_path):
    store = WatermarkStore(str(tmp_path))
    store.save("f1", FolderState(10, {"BV1"}))
    store.save("f2", FolderState(20, {"BV2"}))
    assert WatermarkStore(str(tmp_path)).load("f1").seen == {"BV1"}
    assert WatermarkStore(str(tmp_path)).load("f2").watermark == 20


def test_atomic_no_leftover_tmp(tmp_path):
    WatermarkStore(str(tmp_path)).save("f1", FolderState(1, {"BV1"}))
    assert [p.name for p in tmp_path.iterdir() if p.name.endswith(".tmp")] == []


def test_next_watermark_no_failures_advances_to_newest():
    # listed fav_times newest-first; no failures -> advance to max
    assert next_watermark(prev=100, listed=[300, 250, 110], failed=[]) == 300


def test_next_watermark_no_new_items_keeps_prev():
    assert next_watermark(prev=100, listed=[], failed=[]) == 100


def test_next_watermark_failure_holds_below_oldest_failure():
    # BV at 250 failed; 300 saved. Must keep failed item listable next cycle => 250-1
    assert next_watermark(prev=100, listed=[300, 250], failed=[250]) == 249


def test_next_watermark_multiple_failures_uses_min():
    assert next_watermark(prev=100, listed=[300, 250, 180], failed=[250, 180]) == 179
