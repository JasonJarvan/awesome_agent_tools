from __future__ import annotations
import httpx
from .models import Comment, Author
from ._entities import epoch_to_iso
from .markdown import html_to_markdown

_TYPE_PATH = {"answer": "answers", "article": "articles"}


def _author(raw: dict | None) -> Author | None:
    if not raw:
        return None
    token = raw.get("url_token") or raw.get("urlToken")
    return Author(name=raw.get("name", ""),
                  url=f"https://www.zhihu.com/people/{token}" if token else None,
                  headline=raw.get("headline") or None)


def flatten_comments(root_pages: list[dict]) -> list[Comment]:
    """Flatten root comments + their inline child replies into a two-layer flat list.

    Real comment_v5 schema: author is inline (`author.name`/`url_token`); child replies live in
    `child_comments`; a child's reply target is `reply_comment_id` (resolved to a display name via an
    id->name map built across all collected comments). parent_id = the root comment id.
    """
    name_by_id: dict[str, str] = {}
    for page in root_pages:
        for c in page.get("data", []):
            name_by_id[str(c.get("id"))] = (c.get("author") or {}).get("name", "")
            for ch in c.get("child_comments", []):
                name_by_id[str(ch.get("id"))] = (ch.get("author") or {}).get("name", "")

    out: list[Comment] = []
    for page in root_pages:
        for c in page.get("data", []):
            root_id = str(c.get("id"))
            out.append(Comment(
                id=root_id, parent_id=None, author=_author(c.get("author")),
                content=html_to_markdown(c.get("content", "")), like_count=c.get("like_count", 0),
                created_at=epoch_to_iso(c.get("created_time")),
            ))
            for ch in c.get("child_comments", []):
                reply_cid = ch.get("reply_comment_id")
                reply_to = name_by_id.get(str(reply_cid)) if reply_cid else None
                out.append(Comment(
                    id=str(ch.get("id")), parent_id=root_id,
                    author=_author(ch.get("author")), content=html_to_markdown(ch.get("content", "")),
                    like_count=ch.get("like_count", 0),
                    created_at=epoch_to_iso(ch.get("created_time")),
                    reply_to_author=reply_to,
                ))
    return out


def fetch_comments(item_type: str, item_id: str, *, cookies: dict, limit: int | None,
                   headers: dict | None = None, page_size: int = 20,
                   max_pages: int = 50) -> list[Comment]:
    """Paginate comment_v5 root_comment via the `paging.next` CURSOR (plain cookies, no signature).

    IMPORTANT: this endpoint is cursor-paginated. Passing `offset` returns empty data and a
    self-referential cursor (observed live) — so the first call sends only `order_by`+`limit` and we
    then follow `paging.next` verbatim. Guarded against the empty-data / non-advancing-cursor infinite
    loop (max_pages + a seen-cursor set + empty-data break). 403 here would mean signing is enforced —
    it is NOT (verified at smoke).
    """
    if item_type not in _TYPE_PATH:
        raise ValueError(f"Unsupported comment item_type: {item_type!r} (expected one of {sorted(_TYPE_PATH)})")
    path = _TYPE_PATH[item_type]
    url = (f"https://www.zhihu.com/api/v4/comment_v5/{path}/{item_id}/root_comment"
           f"?order_by=score&limit={page_size}")
    pages: list[dict] = []
    collected = 0
    seen_next: set[str] = set()
    for _ in range(max_pages):
        resp = httpx.get(url, cookies=cookies, headers=headers or {}, timeout=30.0,
                         follow_redirects=True, trust_env=False)
        resp.raise_for_status()
        page = resp.json()
        data = page.get("data", [])
        pages.append(page)
        collected += len(data)
        paging = page.get("paging", {})
        nxt = paging.get("next")
        if paging.get("is_end") or not data or not nxt or nxt in seen_next:
            break
        if limit is not None and collected >= limit:
            break
        seen_next.add(nxt)
        url = nxt

    # Expand each root's inline child PREVIEW into its FULL child set (v1.1). A root response ships
    # only a truncated `child_comments` preview + a `child_comment_count` total; when the total
    # exceeds the preview, paginate the child endpoint and REPLACE the preview with the full set so
    # `flatten_comments` (which reads each root's `child_comments`) emits the whole two-layer tree.
    collected_total = 0
    for page in pages:
        for c in page.get("data", []):
            collected_total += 1  # the root comment itself
            inline = c.get("child_comments", [])
            count = c.get("child_comment_count")
            need_more = count is not None and count > len(inline)
            if need_more and (limit is None or collected_total < limit):
                child_budget = None if limit is None else max(0, limit - collected_total)
                full = fetch_child_comments(str(c.get("id")), cookies=cookies, limit=child_budget,
                                            headers=headers, page_size=page_size, max_pages=max_pages)
                c["child_comments"] = full
                collected_total += len(full)
            else:
                collected_total += len(inline)

    flat = flatten_comments(pages)
    return flat[:limit] if limit is not None else flat


def fetch_child_comments(root_comment_id: str, *, cookies: dict, limit: int | None,
                         headers: dict | None = None, page_size: int = 20,
                         max_pages: int = 50) -> list[dict]:
    """Paginate ALL child replies of one root comment, following `paging.next` VERBATIM.

    We never construct `offset` ourselves: doing so on `root_comment` caused the empty-data /
    self-referential-cursor hang (decisions.md D3). Following `next` works whether the server's model
    is cursor- or offset-based (the `next` URL embeds whatever it needs), so this is immune to that
    poison. Returns raw child-comment dicts in the SAME schema as the inline `child_comments` preview,
    so `flatten_comments` consumes them unchanged. Same loop guard as `fetch_comments`.
    """
    url = (f"https://www.zhihu.com/api/v4/comment_v5/comment/{root_comment_id}/child_comment"
           f"?order_by=ts&limit={page_size}")
    out: list[dict] = []
    seen_next: set[str] = set()
    for _ in range(max_pages):
        resp = httpx.get(url, cookies=cookies, headers=headers or {}, timeout=30.0,
                         follow_redirects=True, trust_env=False)
        resp.raise_for_status()
        page = resp.json()
        data = page.get("data", [])
        out.extend(data)
        paging = page.get("paging", {})
        nxt = paging.get("next")
        if paging.get("is_end") or not data or not nxt or nxt in seen_next:
            break
        if limit is not None and len(out) >= limit:
            break
        seen_next.add(nxt)
        url = nxt
    return out[:limit] if limit is not None else out
