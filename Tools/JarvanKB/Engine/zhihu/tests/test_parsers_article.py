from zhihu.parsers.article import parse_article
from zhihu.models import ZhihuType

INITIAL = {
    "initialState": {"entities": {"articles": {"789": {
        "id": 789,
        "title": "My Article",
        "content": "<p>Article body</p>",
        "voteup_count": 7,
        "comment_count": 1,
        "created": 1700000000,
        "updated": 1700000100,
        "author": {"name": "Bob", "url_token": "bob"},
    }}}}
}

def test_parse_article():
    r = parse_article(INITIAL, {"article_id": "789"}, url="https://zhuanlan.zhihu.com/p/789")
    assert r.type is ZhihuType.ARTICLE
    assert r.title == "My Article"
    assert r.author.name == "Bob"
    assert "Article body" in r.content_markdown
    assert r.metadata["vote_count"] == 7

def test_parse_article_missing_returns_none():
    assert parse_article({"initialState": {"entities": {"articles": {}}}},
                         {"article_id": "0"}, url="u") is None

def test_parse_article_camelcase_initialdata():
    initial = {"initialState": {"entities": {"articles": {"5": {
        "id": 5, "title": "T", "content": "<p>b</p>", "voteupCount": 9, "commentCount": 2,
        "created": 1700000000, "updated": 1700000100,
        "author": {"name": "Au", "urlToken": "au"}}}}}}
    r = parse_article(initial, {"article_id": "5"}, url="u")
    assert r.metadata["vote_count"] == 9
    assert r.metadata["created_at"].startswith("20")
