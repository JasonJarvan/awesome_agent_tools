import json
import pathlib
from unittest.mock import patch
from bilibili.metadata import parse_info, fetch_metadata
from bilibili.models import BilibiliCredential, BilibiliMetadata
from bilibili.url_parser import VideoRef

FIX = pathlib.Path(__file__).parent / "fixtures" / "view_info.json"


def test_parse_info_maps_fields():
    raw = json.loads(FIX.read_text(encoding="utf-8"))
    meta = parse_info(raw)
    assert isinstance(meta, BilibiliMetadata)
    assert meta.bvid == raw["bvid"]
    assert meta.cid == raw["cid"]
    assert meta.aid == raw["aid"]
    assert meta.title == raw["title"]
    assert meta.up == raw["owner"]["name"]
    assert meta.up_mid == raw["owner"]["mid"]
    assert meta.duration == raw["duration"]
    assert meta.pubdate == raw["pubdate"]
    assert meta.cover == raw["pic"]
    assert meta.url == f"https://www.bilibili.com/video/{raw['bvid']}"


def test_fetch_metadata_uses_parser():
    raw = json.loads(FIX.read_text(encoding="utf-8"))
    ref = VideoRef(bvid=raw["bvid"], aid=None, part=None)
    with patch("bilibili.metadata._get_info_raw", return_value=raw) as m:
        meta = fetch_metadata(ref, BilibiliCredential(sessdata="SS"))
    m.assert_called_once()
    assert meta.bvid == raw["bvid"]


def test_get_info_raw_routes_through_paced(monkeypatch):
    from bilibili import metadata, ratelimit
    seen = {}
    def fake_paced(fn):
        seen["ok"] = True                    # routed through paced; fn() never run -> no network
        return {"bvid": "BV1x", "aid": 1, "cid": 1, "owner": {}}
    monkeypatch.setattr(ratelimit, "paced", fake_paced)
    out = metadata._get_info_raw(VideoRef(bvid="BV1x", aid=None, part=None), None)
    assert seen.get("ok") is True and out["bvid"] == "BV1x"
