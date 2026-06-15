from datetime import datetime, timezone

from zhihu_watcher.ledger_store import LedgerStore


def _dt(s):
    return datetime.fromisoformat(s)


def test_record_then_has(tmp_path):
    led = LedgerStore(str(tmp_path))
    assert led.has("c1", "answer:11") is False
    led.record("c1", "answer:11", "机器学习", "/o/机器学习/x.md",
               _dt("2026-05-23T09:00:04+08:00"), _dt("2026-06-14T08:00:00+00:00"))
    assert led.has("c1", "answer:11") is True
    assert led.has("c1", "answer:99") is False
    assert led.has("c2", "answer:11") is False   # per-collection isolation


def test_record_persists_schema(tmp_path):
    import json
    led = LedgerStore(str(tmp_path))
    led.record("c1", "article:12", "历史", "/o/历史/y.md",
               _dt("2026-05-01T00:00:00+08:00"), _dt("2026-06-14T08:00:00+00:00"))
    data = json.loads((tmp_path / "ledger-c1.json").read_text(encoding="utf-8"))
    rec = data["article:12"]
    assert rec["classified_folder"] == "历史"
    assert rec["local_path"] == "/o/历史/y.md"
    assert rec["fav_time"] == "2026-05-01T00:00:00+08:00"
    assert rec["sync_status"] == "local-only"
    assert rec["sync_attempts"] == 0


def test_record_handles_none_fav_time(tmp_path):
    led = LedgerStore(str(tmp_path))
    led.record("c1", "answer:11", "tech", "/o/tech/x.md", None, _dt("2026-06-14T08:00:00+00:00"))
    assert led.has("c1", "answer:11") is True


def test_load_corrupt_file_is_empty(tmp_path):
    (tmp_path / "ledger-c1.json").write_text("{ broken", encoding="utf-8")
    led = LedgerStore(str(tmp_path))
    assert led.has("c1", "answer:11") is False   # corrupt -> treated as empty, never crashes
