from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ZhihuType(str, Enum):
    ANSWER = "answer"
    ARTICLE = "article"
    QUESTION = "question"


@dataclass
class Author:
    name: str
    url: str | None = None
    headline: str | None = None


@dataclass
class EmbeddedAnswer:
    answer_id: str
    author: Author | None
    vote_count: int
    comment_count: int
    created_at: str | None
    updated_at: str | None
    url: str
    content_markdown: str  # FULL content when initialData carries it; "" otherwise


@dataclass
class Comment:
    id: str
    parent_id: str | None  # None = top-level
    author: Author | None
    content: str
    like_count: int
    created_at: str | None
    reply_to_author: str | None = None


@dataclass
class FetchResult:
    url: str
    type: ZhihuType
    title: str
    author: Author | None
    content_markdown: str
    metadata: dict
    fetched_at: str
    answers: list[EmbeddedAnswer] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)
    raw: dict | None = None

    def to_markdown(self, with_frontmatter: bool = True) -> str:
        # Implemented in a later task (8b) once render_frontmatter exists; placeholder raises until then.
        raise NotImplementedError
