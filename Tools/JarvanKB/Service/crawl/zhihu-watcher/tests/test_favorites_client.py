import httpx
import pytest
from zhihu_watcher.favorites_client import (
    FavoritesClient,
    CollectionItem,
    ZhihuApiError,
    collection_id_from_url,
)


def test_collection_id_from_url():
    assert collection_id_from_url("https://www.zhihu.com/collection/630144608") == "630144608"
    assert collection_id_from_url("https://www.zhihu.com/collection/630144608?x=1") == "630144608"
    assert collection_id_from_url("630144608") == "630144608"


def _page(items, totals, is_end):
    return {"data": items, "paging": {"totals": totals, "is_end": is_end}}


def _answer_item(cid):
    return {"content": {"type": "answer", "id": cid,
                        "url": f"https://www.zhihu.com/question/1/answer/{cid}",
                        "question": {"title": f"Q{cid}"}}}


def _article_item(cid):
    return {"content": {"type": "article", "id": cid,
                        "url": f"https://zhuanlan.zhihu.com/p/{cid}", "title": f"Art{cid}"}}


def test_paging_walks_all_pages_and_parses_items():
    pages = {
        0: _page([_answer_item("11"), _article_item("12")], totals=3, is_end=False),
        20: _page([_answer_item("13")], totals=3, is_end=True),
    }

    def handler(request: httpx.Request) -> httpx.Response:
        # no signing header must be present
        assert "x-zse-96" not in {k.lower() for k in request.headers}
        offset = int(dict(request.url.params)["offset"])
        return httpx.Response(200, json=pages[offset])

    client = httpx.Client(transport=httpx.MockTransport(handler))
    fc = FavoritesClient(http_client=client)
    items = fc.list_items("630144608", {"z_c0": "x"})
    assert [i.key for i in items] == ["answer:11", "article:12", "answer:13"]
    assert items[0].title == "Q11"          # answer title comes from content.question.title
    assert items[1].title == "Art12"        # article title comes from content.title
    assert items[0].url.endswith("/answer/11")


def test_stops_on_offset_reaching_totals_without_is_end():
    pages = {
        0: _page([_answer_item("1")], totals=1, is_end=False),  # is_end stays False
    }

    def handler(request: httpx.Request) -> httpx.Response:
        offset = int(dict(request.url.params)["offset"])
        return httpx.Response(200, json=pages[offset])

    client = httpx.Client(transport=httpx.MockTransport(handler))
    fc = FavoritesClient(http_client=client)
    items = fc.list_items("c", {})
    assert [i.key for i in items] == ["answer:1"]   # stopped because offset(20) >= totals(1)


def test_non_200_raises():
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(403, json={})))
    fc = FavoritesClient(http_client=client)
    with pytest.raises(ZhihuApiError) as exc:
        fc.list_items("c", {})
    assert exc.value.status == 403


def test_skips_malformed_items():
    page = {"data": [{"content": {"type": "answer"}}, _answer_item("9")],
            "paging": {"totals": 2, "is_end": True}}
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=page)))
    fc = FavoritesClient(http_client=client)
    items = fc.list_items("c", {})
    assert [i.key for i in items] == ["answer:9"]   # item missing id/url dropped
