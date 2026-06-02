from __future__ import annotations
from ..models import FetchResult, ZhihuType
from ..markdown import html_to_markdown
from .._entities import entities, epoch_to_iso, parse_author


def parse_answer(initial_data: dict, ids: dict, *, url: str) -> FetchResult | None:
    ent = entities(initial_data).get("answers", {})
    raw = ent.get(str(ids.get("answer_id")))
    if not raw:
        return None
    question = raw.get("question") or {}
    return FetchResult(
        url=url,
        type=ZhihuType.ANSWER,
        title=question.get("title", ""),
        author=parse_author(raw.get("author")),
        content_markdown=html_to_markdown(raw.get("content", "")),
        metadata={
            "vote_count": raw.get("voteup_count", 0),
            "comment_count": raw.get("comment_count", 0),
            "created_at": epoch_to_iso(raw.get("created_time")),
            "updated_at": epoch_to_iso(raw.get("updated_time")),
        },
        fetched_at="",  # set by engine
        raw=raw,
    )
