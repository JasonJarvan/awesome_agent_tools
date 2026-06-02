from zhihu.models import Author, Comment, EmbeddedAnswer, FetchResult, ZhihuType


def test_fetchresult_defaults():
    r = FetchResult(
        url="u",
        type=ZhihuType.ANSWER,
        title="t",
        author=Author(name="a"),
        content_markdown="body",
        metadata={"vote_count": 5},
        fetched_at="2026-06-01T00:00:00Z",
    )
    assert r.answers == []
    assert r.comments == []
    assert r.raw is None
    assert r.type is ZhihuType.ANSWER


def test_comment_is_flat():
    c = Comment(
        id="1",
        parent_id=None,
        author=Author(name="x"),
        content="hi",
        like_count=2,
        created_at="2026-06-01T00:00:00Z",
    )
    child = Comment(
        id="2",
        parent_id="1",
        author=Author(name="y"),
        content="re",
        like_count=0,
        created_at="2026-06-01T00:00:00Z",
        reply_to_author="x",
    )
    assert child.parent_id == "1"
