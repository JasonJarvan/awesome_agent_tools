import json
import pathlib
from unittest.mock import patch
from bilibili.subtitle import pick_track, parse_body, normalize_url, fetch_subtitle
from bilibili.models import Transcript, BilibiliCredential

FX = pathlib.Path(__file__).parent / "fixtures"


def test_pick_prefers_manual_zh():
    tracks = [
        {"lan": "en", "ai_type": 0, "subtitle_url": "//a"},
        {"lan": "ai-zh", "ai_type": 1, "subtitle_url": "//b"},
        {"lan": "zh-CN", "ai_type": 0, "subtitle_url": "//c"},
    ]
    assert pick_track(tracks)["subtitle_url"] == "//c"


def test_pick_falls_back_to_ai_zh_then_any():
    assert pick_track([{"lan": "ai-zh", "ai_type": 1, "subtitle_url": "//b"}])["lan"] == "ai-zh"
    assert pick_track([{"lan": "fr", "ai_type": 0, "subtitle_url": "//x"}])["lan"] == "fr"
    assert pick_track([]) is None


def test_normalize_url():
    assert normalize_url("//x/y.json") == "https://x/y.json"
    assert normalize_url("https://x/y.json") == "https://x/y.json"


def test_parse_body_filters_empty_and_maps_times():
    body = [{"from": 0.0, "to": 1.5, "content": "你好"}, {"from": 1.5, "to": 2.0, "content": "  "}]
    segs = parse_body(body)
    assert len(segs) == 1
    assert segs[0].start == 0.0 and segs[0].end == 1.5 and segs[0].text == "你好"


def test_fetch_subtitle_returns_transcript():
    tracks = json.loads((FX / "subtitle_tracks.json").read_text(encoding="utf-8"))
    body = json.loads((FX / "subtitle_body.json").read_text(encoding="utf-8"))
    with patch("bilibili.subtitle._get_tracks_raw", return_value=tracks), \
         patch("bilibili.subtitle._get_body_raw", return_value=body["body"]):
        tr = fetch_subtitle(bvid="BV1x", cid=2, cred=BilibiliCredential(sessdata="SS"))
    assert isinstance(tr, Transcript)
    assert tr.source == "subtitle"
    assert tr.full_text and len(tr.segments) >= 1


def test_fetch_subtitle_none_when_no_tracks():
    with patch("bilibili.subtitle._get_tracks_raw", return_value=[]):
        assert fetch_subtitle(bvid="BV1x", cid=2, cred=BilibiliCredential(sessdata="SS")) is None


def test_fetch_subtitle_none_without_credential_skips_network():
    # No SESSDATA → subtitle path skipped entirely (no track fetch); engine will use ASR.
    with patch("bilibili.subtitle._get_tracks_raw") as m:
        assert fetch_subtitle(bvid="BV1x", cid=2, cred=None) is None
        assert fetch_subtitle(bvid="BV1x", cid=2, cred=BilibiliCredential(sessdata="")) is None
    m.assert_not_called()


def test_fetch_subtitle_falls_back_to_none_on_track_fetch_error():
    # get_subtitle raising (e.g. CredentialNoSessdataException / network) must NOT crash the
    # engine — return None so the cascade falls through to ASR.
    with patch("bilibili.subtitle._get_tracks_raw", side_effect=Exception("CredentialNoSessdataException")):
        assert fetch_subtitle(bvid="BV1x", cid=2, cred=BilibiliCredential(sessdata="SS")) is None


def test_fetch_subtitle_falls_back_to_none_on_body_fetch_error():
    tracks = [{"lan": "ai-zh", "ai_type": 1, "subtitle_url": "//x/sub.json"}]
    with patch("bilibili.subtitle._get_tracks_raw", return_value=tracks), \
         patch("bilibili.subtitle._get_body_raw", side_effect=Exception("timeout")):
        assert fetch_subtitle(bvid="BV1x", cid=2, cred=BilibiliCredential(sessdata="SS")) is None


def test_get_tracks_raw_routes_through_paced(monkeypatch):
    from bilibili import subtitle, ratelimit
    seen = {}
    def fake_paced(fn):
        seen["ok"] = True
        return [{"lan": "ai-zh", "subtitle_url": "//x"}]
    monkeypatch.setattr(ratelimit, "paced", fake_paced)
    out = subtitle._get_tracks_raw("BV1x", 2, None)
    assert seen.get("ok") is True and out[0]["lan"] == "ai-zh"


def test_get_body_raw_retries_transient_429(monkeypatch):
    import httpx as _httpx
    from bilibili import subtitle, ratelimit
    ratelimit._limiter._last = 0.0
    monkeypatch.setattr(ratelimit, "_sleep", lambda s: None)
    monkeypatch.setattr(ratelimit, "_rand", lambda a, b: 0.0)
    ratelimit.configure(min_interval=0.0, jitter=0.0, max_retries=2, enabled=True)
    req = _httpx.Request("GET", "https://x/sub.json")
    responses = [
        _httpx.Response(429, request=req),
        _httpx.Response(200, json={"body": [{"from": 0.0, "to": 1.0, "content": "你好"}]}, request=req),
    ]
    monkeypatch.setattr(subtitle.httpx, "get", lambda *a, **k: responses.pop(0))
    body = subtitle._get_body_raw("//x/sub.json", None)
    assert body == [{"from": 0.0, "to": 1.0, "content": "你好"}]   # 429 retried -> recovered
