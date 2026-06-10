import httpx
import pytest
from bilibili_watcher.favorites_client import (
    FavoritesClient, BiliFavItem, BilibiliFavApiError,
)


def _media(bvid, fav_time, type_=2, title=None):
    return {"bvid": bvid, "fav_time": fav_time, "type": type_, "title": title or bvid}


def _page(medias, has_more, code=0):
    return {"code": code, "message": "0", "data": {"medias": medias, "has_more": has_more,
                                                    "info": {"media_count": len(medias)}}}


def test_pages_until_has_more_false_and_parses():
    pages = {
        1: _page([_media("BV1", 300), _media("BV2", 200)], has_more=True),
        2: _page([_media("BV3", 100)], has_more=False),
    }

    def handler(request: httpx.Request) -> httpx.Response:
        pn = int(dict(request.url.params)["pn"])
        assert dict(request.url.params)["order"] == "mtime"
        return httpx.Response(200, json=pages[pn])

    fc = FavoritesClient(http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    items = fc.list_items("121", {"SESSDATA": "s"})
    assert [(i.bvid, i.fav_time) for i in items] == [("BV1", 300), ("BV2", 200), ("BV3", 100)]


def test_filters_non_type_2():
    page = _page([_media("BV1", 300), _media("AU9", 250, type_=12), _media("BV2", 200)], has_more=False)
    fc = FavoritesClient(http_client=httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=page))))
    items = fc.list_items("121", {"SESSDATA": "s"})
    assert [i.bvid for i in items] == ["BV1", "BV2"]   # type=12 audio dropped


def test_early_stops_on_fav_time_at_or_below_watermark():
    # order=mtime DESC; watermark=200 -> BV1(300) kept, BV2(200) triggers stop (<=200)
    pages = {1: _page([_media("BV1", 300), _media("BV2", 200), _media("BV3", 100)], has_more=True)}
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        pn = int(dict(request.url.params)["pn"])
        return httpx.Response(200, json=pages[pn])

    fc = FavoritesClient(http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    items = fc.list_items("121", {"SESSDATA": "s"}, since_fav_time=200)
    assert [i.bvid for i in items] == ["BV1"]          # stopped at BV2 (fav_time<=200)
    assert calls["n"] == 1                             # did NOT page to page 2 (early-stop)


def test_early_stop_evaluated_before_type_filter():
    # a non-video item at the boundary still triggers stop (ordering is across all types)
    page = _page([_media("BV1", 300), _media("AU0", 200, type_=12), _media("BV9", 150)], has_more=True)
    fc = FavoritesClient(http_client=httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=page))))
    items = fc.list_items("121", {"SESSDATA": "s"}, since_fav_time=200)
    assert [i.bvid for i in items] == ["BV1"]          # AU0 (type 12, fav<=200) stops before BV9


def test_does_not_stop_from_media_count():
    # media_count says 4 but only 3 returned + has_more False (deleted item gotcha) -> must not loop
    page = {"code": 0, "data": {"medias": [_media("BV1", 30), _media("BV2", 20), _media("BV3", 10)],
                                "has_more": False, "info": {"media_count": 4}}}
    fc = FavoritesClient(http_client=httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=page))))
    items = fc.list_items("121", {"SESSDATA": "s"})
    assert [i.bvid for i in items] == ["BV1", "BV2", "BV3"]


def test_non_200_raises():
    fc = FavoritesClient(http_client=httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(412, json={}))))
    with pytest.raises(BilibiliFavApiError) as exc:
        fc.list_items("121", {"SESSDATA": "s"})
    assert exc.value.status == 412


def test_nonzero_code_raises():
    # e.g. -101 not logged in (expired cookie)
    page = {"code": -101, "message": "账号未登录", "data": None}
    fc = FavoritesClient(http_client=httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=page))))
    with pytest.raises(BilibiliFavApiError) as exc:
        fc.list_items("121", {"SESSDATA": "s"})
    assert exc.value.code == -101


def test_skips_malformed_items():
    page = _page([{"type": 2}, _media("BV9", 100)], has_more=False)   # first lacks bvid/fav_time
    fc = FavoritesClient(http_client=httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=page))))
    items = fc.list_items("121", {"SESSDATA": "s"})
    assert [i.bvid for i in items] == ["BV9"]
