from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from .markdown import render_frontmatter


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
        if not with_frontmatter:
            return self.content_markdown
        meta = {
            "title": self.title,
            "author": self.author.name if self.author else None,
            "url": self.url,
            "type": self.type.value,
            "vote_count": self.metadata.get("vote_count"),
            "comment_count": self.metadata.get("comment_count"),
            "created_at": self.metadata.get("created_at"),
            "updated_at": self.metadata.get("updated_at"),
            "fetched_at": self.fetched_at,
            "source": "zhihu",
        }
        return render_frontmatter(meta) + "\n" + self.content_markdown
