from __future__ import annotations
import re
from .models import ZhihuType
from .errors import ZhihuFetchError

_ANSWER_WITH_Q = re.compile(r"/question/(?P<q>\d+)/answer/(?P<a>\d+)")
_ANSWER_BARE = re.compile(r"/answer/(?P<a>\d+)")
_ARTICLE = re.compile(r"/p/(?P<p>\d+)")
_QUESTION = re.compile(r"/question/(?P<q>\d+)/?$")


def classify(url: str) -> tuple[ZhihuType, dict]:
    """Classify a Zhihu URL into (type, ids). Raises ZhihuFetchError on unsupported URLs."""
    url = url.split("?", 1)[0].split("#", 1)[0]
    m = _ANSWER_WITH_Q.search(url)
    if m:
        return ZhihuType.ANSWER, {"answer_id": m.group("a"), "question_id": m.group("q")}
    m = _ANSWER_BARE.search(url)
    if m:
        return ZhihuType.ANSWER, {"answer_id": m.group("a")}
    m = _ARTICLE.search(url)
    if m:
        return ZhihuType.ARTICLE, {"article_id": m.group("p")}
    m = _QUESTION.search(url)
    if m:
        return ZhihuType.QUESTION, {"question_id": m.group("q")}
    raise ZhihuFetchError(f"Unsupported Zhihu URL: {url}", url=url)
