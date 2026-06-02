from __future__ import annotations
import httpx
from .models import Comment, Author
from ._entities import epoch_to_iso

_TYPE_PATH = {"answer": "answers", "article": "articles"}


def _author(raw: dict | None) -> Author | None:
    member = (raw or {}).get("member") or {}
    if not member:
        return None
    token = member.get("url_token")
    return Author(name=member.get("name", ""),
                  url=f"https://www.zhihu.com/people/{token}" if token else None)


def flatten_comments(root_pages: list[dict]) -> list[Comment]:
    """Flatten root comments + their inline child replies into a two-layer flat list."""
    out: list[Comment] = []
    for page in root_pages:
        for c in page.get("data", []):
            out.append(Comment(
                id=str(c.get("id")), parent_id=None, author=_author(c.get("author")),
                content=c.get("content", ""), like_count=c.get("like_count", 0),
                created_at=epoch_to_iso(c.get("created_time")),
            ))
            for ch in c.get("child_comments", []):
                reply_to = ((ch.get("reply_to_author") or {}).get("member") or {}).get("name")
                out.append(Comment(
                    id=str(ch.get("id")), parent_id=str(c.get("id")),
                    author=_author(ch.get("author")), content=ch.get("content", ""),
                    like_count=ch.get("like_count", 0),
                    created_at=epoch_to_iso(ch.get("created_time")),
                    reply_to_author=reply_to,
                ))
    return out


def fetch_comments(item_type: str, item_id: str, *, cookies: dict, limit: int | None,
                   headers: dict | None = None, page_size: int = 20) -> list[Comment]:
    """Paginate comment_v5 root_comment (plain cookies, no signature) and flatten.

    NOTE: if Zhihu returns 403 here, comment signing is hard-enforced — see design.md §9
    and the smoke gate; this function will need the RSSHub-MIT signer branch.
    """
    if item_type not in _TYPE_PATH:
        raise ValueError(f"Unsupported comment item_type: {item_type!r} (expected one of {sorted(_TYPE_PATH)})")
    path = _TYPE_PATH[item_type]
    pages: list[dict] = []
    offset, collected = 0, 0
    while True:
        url = (f"https://www.zhihu.com/api/v4/comment_v5/{path}/{item_id}/root_comment"
               f"?order_by=score&limit={page_size}&offset={offset}")
        resp = httpx.get(url, cookies=cookies, headers=headers or {}, timeout=30.0,
                        trust_env=False)
        resp.raise_for_status()
        page = resp.json()
        pages.append(page)
        collected += len(page.get("data", []))
        offset += page_size
        if page.get("paging", {}).get("is_end", True) or (limit is not None and collected >= limit):
            break
    flat = flatten_comments(pages)
    return flat[:limit] if limit is not None else flat
