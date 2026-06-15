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


def test_circuit_break_sets_permanent_skip_and_records_display_fields(tmp_path):
    from zhihu_watcher.failure_store import FailureStore
    clock = [1000.0]
    fs = FailureStore(str(tmp_path), now_fn=lambda: clock[0])
    for _ in range(3):
        fs.record_failure("c1", "article:12", url="https://zhuanlan.zhihu.com/p/12",
                          title="T12", excerpt="lead...", max_failures=3,
                          circuit_break_threshold=3, cooldown_seconds=60)
    assert fs.should_skip("c1", "article:12") is True   # circuit-broken -> always skip
    clock[0] += 10_000                                   # even far past any cooldown
    assert fs.should_skip("c1", "article:12") is True
    broken = fs.circuit_broken_items("c1")
    assert len(broken) == 1
    assert broken[0]["key"] == "article:12"
    assert broken[0]["url"] == "https://zhuanlan.zhihu.com/p/12"
    assert broken[0]["title"] == "T12"
    assert broken[0]["failures"] == 3


def test_below_circuit_break_still_clears_on_success(tmp_path):
    from zhihu_watcher.failure_store import FailureStore
    fs = FailureStore(str(tmp_path), now_fn=lambda: 1000.0)
    fs.record_failure("c1", "answer:11", max_failures=3, circuit_break_threshold=10, cooldown_seconds=60)
    fs.clear("c1", "answer:11")
    assert fs.should_skip("c1", "answer:11") is False
    assert fs.circuit_broken_items("c1") == []


def test_circuit_broken_items_empty_when_none(tmp_path):
    from zhihu_watcher.failure_store import FailureStore
    fs = FailureStore(str(tmp_path))
    assert fs.circuit_broken_items("c1") == []
