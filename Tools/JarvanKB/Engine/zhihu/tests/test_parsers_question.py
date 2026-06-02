from zhihu.parsers.question import parse_question
from zhihu.models import ZhihuType

INITIAL = {
    "initialState": {"entities": {
        "questions": {"123": {
            "id": 123, "title": "Why sky blue?",
            "detail": "<p>Question detail</p>",
            "answerCount": 2, "followerCount": 50, "visitCount": 999,
        }},
        "answers": {
            "456": {"id": 456, "content": "<p>Rayleigh</p>", "voteup_count": 9,
                    "comment_count": 1, "created_time": 1700000000, "updated_time": 1700000000,
                    "author": {"name": "Alice", "url_token": "alice"},
                    "question": {"id": 123, "title": "Why sky blue?"}},
            "457": {"id": 457, "content": "<p>Scatter</p>", "voteup_count": 4,
                    "comment_count": 0, "created_time": 1700000001, "updated_time": 1700000001,
                    "author": {"name": "Bob", "url_token": "bob"},
                    "question": {"id": 123, "title": "Why sky blue?"}},
            "999": {"id": 999, "content": "<p>Other</p>", "question": {"id": 555}},
        },
    }}
}

def test_parse_question():
    r = parse_question(INITIAL, {"question_id": "123"}, url="https://www.zhihu.com/question/123")
    assert r.type is ZhihuType.QUESTION
    assert r.title == "Why sky blue?"
    assert "Question detail" in r.content_markdown
    assert r.metadata["answer_count"] == 2
    assert r.metadata["follow_count"] == 50
    assert [a.answer_id for a in r.answers] == ["456", "457"]
    assert "Rayleigh" in r.answers[0].content_markdown
    assert r.answers[0].vote_count == 9
    assert r.answers[0].url == "https://www.zhihu.com/question/123/answer/456"
