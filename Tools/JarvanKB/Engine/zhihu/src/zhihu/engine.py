from __future__ import annotations
from datetime import datetime, timezone
from http.cookies import SimpleCookie
import httpx

from .url_router import classify
from .models import ZhihuType, FetchResult, Author
from .errors import ZhihuFetchError
from .initialdata import extract_initial_data
from .markdown import html_to_markdown
from . import fetcher, comments as comments_mod
from .parsers.answer import parse_answer
from .parsers.article import parse_article
from .parsers.question import parse_question
from .parsers.html_scrape import scrape_body

_PARSERS = {ZhihuType.ANSWER: parse_answer, ZhihuType.ARTICLE: parse_article,
            ZhihuType.QUESTION: parse_question}
_COMMENTABLE = {ZhihuType.ANSWER: "answer", ZhihuType.ARTICLE: "article"}


def _normalize_cookies(cookies: dict | str | None) -> dict:
    if cookies is None:
        return {}
    if isinstance(cookies, dict):
        return cookies
    jar = SimpleCookie()
    jar.load(cookies)
    return {k: m.value for k, m in jar.items()}


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")


def fetch(url: str, cookies: dict | str | None = None, *, with_comments: bool = False,
          comment_limit: int | None = None, timeout: float = 30.0) -> FetchResult:
    ztype, ids = classify(url)
    jar = _normalize_cookies(cookies)
    attempts: list[str] = []

    status, text = fetcher.get_page(url, cookies=jar, timeout=timeout)
    result: FetchResult | None = None

    if status == 200:
        attempts.append("html-initialdata")
        data = extract_initial_data(text)
        if data is not None:
            result = _PARSERS[ztype](data, ids, url=url)

    if result is None and status == 200:
        attempts.append("html-css-scrape")
        body = scrape_body(text)
        if body:
            result = FetchResult(
                url=url, type=ztype, title="", author=None,
                content_markdown=body, metadata={}, fetched_at="", raw=None)

    if result is None and status == 403 and ztype is ZhihuType.ANSWER:
        attempts.append("api-fallback")
        try:
            result = _from_api_answer(url, ids, jar, timeout)
        except httpx.HTTPStatusError as e:
            raise ZhihuFetchError(
                f"API fallback failed for {url}", url=url, attempts=attempts,
                status=e.response.status_code) from e

    if result is None:
        raise ZhihuFetchError(
            f"All fallbacks failed for {url}", url=url, attempts=attempts, status=status)

    result.fetched_at = _now_iso()

    if with_comments and ztype in _COMMENTABLE:
        item_id = ids.get("answer_id") or ids.get("article_id")
        result.comments = comments_mod.fetch_comments(
            _COMMENTABLE[ztype], item_id, cookies=jar, limit=comment_limit,
            headers=fetcher.API_HEADERS)

    return result


def _from_api_answer(url: str, ids: dict, jar: dict, timeout: float) -> FetchResult:
    answer_id = ids.get("answer_id")
    if not answer_id:
        raise ZhihuFetchError("API fallback requires an answer_id", url=url, attempts=["api-fallback"])
    data = fetcher.get_api_answer(answer_id, cookies=jar, timeout=timeout)
    author = data.get("author") or {}
    question = data.get("question") or {}
    return FetchResult(
        url=url, type=ZhihuType.ANSWER, title=question.get("title", ""),
        author=Author(name=author.get("name", "")) if author else None,
        content_markdown=html_to_markdown(data.get("content", "")),
        metadata={"vote_count": data.get("voteup_count", 0),
                  "comment_count": data.get("comment_count", 0)},
        fetched_at="", raw=data)
