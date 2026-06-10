import httpx
import pytest
from datetime import datetime
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


def test_parses_favorited_at_and_excerpt_per_type():
    page = {"data": [
        {"created": "2026-05-23T09:00:04+08:00",
         "content": {"type": "article", "id": "a1", "url": "https://zhuanlan.zhihu.com/p/a1",
                     "title": "T", "excerpt_title": "lead &#34;quoted&#34; body"}},
        {"created": "2026-05-13T13:13:03+08:00",
         "content": {"type": "answer", "id": "q1", "url": "https://www.zhihu.com/question/1/answer/q1",
                     "question": {"title": "Q"}, "excerpt": "answer lead"}},
    ], "paging": {"totals": 2, "is_end": True}}
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=page)))
    items = FavoritesClient(http_client=client).list_items("c", {})
    assert items[0].favorited_at == datetime.fromisoformat("2026-05-23T09:00:04+08:00")
    assert items[0].excerpt == 'lead "quoted" body'        # excerpt_title, html-unescaped
    assert items[1].excerpt == "answer lead"               # answer uses content.excerpt
    assert items[1].favorited_at == datetime.fromisoformat("2026-05-13T13:13:03+08:00")


from zhihu_watcher.favorites_client import UserCollection

def _coll(cid, title, is_default=False, item_count=10):
    return {"id": cid, "title": title, "is_default": is_default, "item_count": item_count}

def test_list_user_collections_pages_and_parses():
    pages = {
        0: {"data": [_coll(721323262, "我的收藏", is_default=True, item_count=109),
                     _coll(865315034, "技术-AI生成", item_count=94)],
            "paging": {"totals": 3, "is_end": False}},
        20: {"data": [_coll(630144608, "赚钱-金融市场", item_count=212)],
             "paging": {"totals": 3, "is_end": True}},
    }
    def handler(request):
        assert "x-zse-96" not in {k.lower() for k in request.headers}
        assert request.url.path == "/api/v4/people/zhao-cheng-57-99-79/collections"
        return httpx.Response(200, json=pages[int(dict(request.url.params)["offset"])])
    fc = FavoritesClient(http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    cols = fc.list_user_collections("zhao-cheng-57-99-79", {"z_c0": "x"})
    assert [(c.id, c.title, c.is_default, c.item_count) for c in cols] == [
        ("721323262", "我的收藏", True, 109),
        ("865315034", "技术-AI生成", False, 94),
        ("630144608", "赚钱-金融市场", False, 212),
    ]

def test_list_user_collections_non_200_raises():
    fc = FavoritesClient(http_client=httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(403, json={}))))
    with pytest.raises(ZhihuApiError):
        fc.list_user_collections("zhao-cheng-57-99-79", {})


def test_get_current_url_token():
    def handler(request):
        assert request.url.path == "/api/v4/me"
        return httpx.Response(200, json={"url_token": "zhao-cheng-57-99-79", "name": "晓日晨"})
    fc = FavoritesClient(http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    assert fc.get_current_url_token({"z_c0": "x"}) == "zhao-cheng-57-99-79"

def test_get_current_url_token_non_200_raises():
    fc = FavoritesClient(http_client=httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(401, json={}))))
    with pytest.raises(ZhihuApiError):
        fc.get_current_url_token({})
