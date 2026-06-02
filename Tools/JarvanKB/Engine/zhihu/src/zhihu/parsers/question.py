from __future__ import annotations
from ..models import FetchResult, ZhihuType, EmbeddedAnswer
from ..markdown import html_to_markdown
from .._entities import entities, epoch_to_iso, parse_author


def parse_question(initial_data: dict, ids: dict, *, url: str) -> FetchResult | None:
    ent = entities(initial_data)
    qid = str(ids.get("question_id"))
    raw = ent.get("questions", {}).get(qid)
    if not raw:
        return None
    answers = _embedded_answers(ent.get("answers", {}), qid)
    return FetchResult(
        url=url,
        type=ZhihuType.QUESTION,
        title=raw.get("title", ""),
        author=parse_author(raw.get("author")),
        content_markdown=html_to_markdown(raw.get("detail", "")),
        metadata={
            "answer_count": raw.get("answerCount", raw.get("answer_count", 0)),
            "follow_count": raw.get("followerCount", raw.get("follower_count", 0)),
            "view_count": raw.get("visitCount", raw.get("visit_count", 0)),
        },
        fetched_at="",
        answers=answers,
        raw=raw,
    )


def _embedded_answers(answers_ent: dict, qid: str) -> list[EmbeddedAnswer]:
    items = []
    for aid, a in answers_ent.items():
        if str((a.get("question") or {}).get("id")) != qid:
            continue
        items.append(EmbeddedAnswer(
            answer_id=str(a.get("id", aid)),
            author=parse_author(a.get("author")),
            vote_count=a.get("voteup_count", 0),
            comment_count=a.get("comment_count", 0),
            created_at=epoch_to_iso(a.get("created_time")),
            updated_at=epoch_to_iso(a.get("updated_time")),
            url=f"https://www.zhihu.com/question/{qid}/answer/{a.get('id', aid)}",
            content_markdown=html_to_markdown(a.get("content", "")),
        ))
    items.sort(key=lambda x: x.vote_count, reverse=True)
    return items
