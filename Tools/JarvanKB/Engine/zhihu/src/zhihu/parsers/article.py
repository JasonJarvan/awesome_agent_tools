from __future__ import annotations
from ..models import FetchResult, ZhihuType
from ..markdown import html_to_markdown
from .._entities import entities, epoch_to_iso, parse_author


def parse_article(initial_data: dict, ids: dict, *, url: str) -> FetchResult | None:
    ent = entities(initial_data).get("articles", {})
    raw = ent.get(str(ids.get("article_id")))
    if not raw:
        return None
    return FetchResult(
        url=url,
        type=ZhihuType.ARTICLE,
        title=raw.get("title", ""),
        author=parse_author(raw.get("author")),
        content_markdown=html_to_markdown(raw.get("content", "")),
        metadata={
            "vote_count": raw.get("voteup_count", 0),
            "comment_count": raw.get("comment_count", 0),
            "created_at": epoch_to_iso(raw.get("created")),
            "updated_at": epoch_to_iso(raw.get("updated")),
        },
        fetched_at="",
        raw=raw,
    )
