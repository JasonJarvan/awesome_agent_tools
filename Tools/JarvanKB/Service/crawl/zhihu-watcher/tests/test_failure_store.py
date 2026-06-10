from zhihu_watcher.failure_store import FailureStore


def test_cooldown_after_n_failures_then_skip(tmp_path):
    clock = {"t": 1000.0}
    fs = FailureStore(str(tmp_path), now_fn=lambda: clock["t"])
    # 2 failures, N=3 -> not yet skipping
    fs.record_failure("c1", "article:1", max_failures=3, cooldown_seconds=100)
    fs.record_failure("c1", "article:1", max_failures=3, cooldown_seconds=100)
    assert fs.should_skip("c1", "article:1") is False
    # 3rd failure -> cooldown set to now+100
    fs.record_failure("c1", "article:1", max_failures=3, cooldown_seconds=100)
    assert fs.should_skip("c1", "article:1") is True
    # after the window -> no longer skipped (retried once)
    clock["t"] = 1101.0
    assert fs.should_skip("c1", "article:1") is False


def test_clear_resets(tmp_path):
    fs = FailureStore(str(tmp_path), now_fn=lambda: 0.0)
    fs.record_failure("c1", "k", max_failures=1, cooldown_seconds=100)
    assert fs.should_skip("c1", "k") is True
    fs.clear("c1", "k")
    assert fs.should_skip("c1", "k") is False


def test_persists_across_reload(tmp_path):
    fs1 = FailureStore(str(tmp_path), now_fn=lambda: 0.0)
    fs1.record_failure("c1", "k", max_failures=1, cooldown_seconds=100)
    fs2 = FailureStore(str(tmp_path), now_fn=lambda: 0.0)
    assert fs2.should_skip("c1", "k") is True


def test_unknown_key_not_skipped(tmp_path):
    fs = FailureStore(str(tmp_path), now_fn=lambda: 0.0)
    assert fs.should_skip("c1", "never-seen") is False
