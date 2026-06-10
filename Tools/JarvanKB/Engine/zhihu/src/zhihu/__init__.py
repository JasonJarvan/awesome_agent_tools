"""Zhihu engine — one URL -> Markdown + metadata."""
from .engine import fetch
from .fetcher import configure
from .models import FetchResult, Author, EmbeddedAnswer, Comment, ZhihuType
from .errors import ZhihuFetchError

__all__ = ["fetch", "configure", "FetchResult", "Author", "EmbeddedAnswer", "Comment",
           "ZhihuType", "ZhihuFetchError"]
