from zhihu.parsers.answer import parse_answer
from zhihu.models import ZhihuType

INITIAL = {
    "initialState": {"entities": {"answers": {"456": {
        "id": 456,
        "content": "<p>Answer body</p>",
        "voteup_count": 12,
        "comment_count": 3,
        "created_time": 1700000000,
        "updated_time": 1700000100,
        "author": {"name": "Alice", "url_token": "alice", "headline": "dev"},
        "question": {"id": 123, "title": "Why?"},
    }}}}
}

def test_parse_answer():
    r = parse_answer(INITIAL, {"answer_id": "456", "question_id": "123"},
                     url="https://www.zhihu.com/question/123/answer/456")
    assert r.type is ZhihuType.ANSWER
    assert r.title == "Why?"
    assert r.author.name == "Alice"
    assert "Answer body" in r.content_markdown
    assert r.metadata["vote_count"] == 12
    assert r.metadata["comment_count"] == 3
    assert r.metadata["created_at"].startswith("20")

def test_parse_answer_missing_entity_returns_none():
    assert parse_answer({"initialState": {"entities": {"answers": {}}}},
                        {"answer_id": "999"}, url="u") is None

def test_parse_answer_camelcase_initialdata():
    initial = {"initialState": {"entities": {"answers": {"5": {
        "id": 5, "content": "<p>body</p>", "voteupCount": 42, "commentCount": 7,
        "createdTime": 1700000000, "updatedTime": 1700000100,
        "author": {"name": "Cami", "urlToken": "cami"},
        "question": {"id": 9, "title": "Q"}}}}}}
    r = parse_answer(initial, {"answer_id": "5"}, url="u")
    assert r.metadata["vote_count"] == 42
    assert r.metadata["comment_count"] == 7
    assert r.metadata["created_at"].startswith("20")
    assert r.author.url == "https://www.zhihu.com/people/cami"
