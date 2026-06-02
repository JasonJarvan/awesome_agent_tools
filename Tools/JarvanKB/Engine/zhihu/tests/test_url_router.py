import pytest
from zhihu.url_router import classify
from zhihu.models import ZhihuType
from zhihu.errors import ZhihuFetchError

@pytest.mark.parametrize("url,expected_type,expected_ids", [
    ("https://www.zhihu.com/question/123/answer/456", ZhihuType.ANSWER, {"answer_id": "456", "question_id": "123"}),
    ("https://www.zhihu.com/answer/456", ZhihuType.ANSWER, {"answer_id": "456"}),
    ("https://zhuanlan.zhihu.com/p/789", ZhihuType.ARTICLE, {"article_id": "789"}),
    ("https://www.zhihu.com/p/789", ZhihuType.ARTICLE, {"article_id": "789"}),
    ("https://www.zhihu.com/question/123", ZhihuType.QUESTION, {"question_id": "123"}),
])
def test_classify(url, expected_type, expected_ids):
    t, ids = classify(url)
    assert t is expected_type
    for k, v in expected_ids.items():
        assert ids[k] == v

def test_classify_rejects_unknown():
    with pytest.raises(ZhihuFetchError):
        classify("https://www.zhihu.com/people/someone")
