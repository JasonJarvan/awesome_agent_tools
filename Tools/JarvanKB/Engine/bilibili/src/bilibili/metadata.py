"""Fetch + parse video metadata via bilibili-api-python.

Split into a pure parser (parse_info) and a thin async-wrapping fetch (_get_info_raw),
so the field mapping is unit-tested without network.
"""
from __future__ import annotations
import asyncio
from typing import Optional

from .errors import CredentialError, InvalidVideoRef
from .models import BilibiliCredential, BilibiliMetadata
from .url_parser import VideoRef


def parse_info(raw: dict) -> BilibiliMetadata:
    """Map the Bilibili `view` API `data` dict to BilibiliMetadata (pure)."""
    owner = raw.get("owner") or {}
    bvid = raw["bvid"]
    return BilibiliMetadata(
        bvid=bvid,
        aid=int(raw.get("aid", 0)),
        cid=int(raw["cid"]),
        title=raw.get("title", ""),
        up=owner.get("name", ""),
        up_mid=int(owner.get("mid", 0)),
        duration=int(raw.get("duration", 0)),
        pubdate=int(raw.get("pubdate", 0)),
        cover=raw.get("pic"),
        url=f"https://www.bilibili.com/video/{bvid}",
    )


def _build_credential(cred: Optional[BilibiliCredential]):
    from bilibili_api import Credential
    if cred is None:
        return None
    return Credential(sessdata=cred.sessdata, bili_jct=cred.bili_jct, buvid3=cred.buvid3)


def _get_info_raw(ref: VideoRef, cred: Optional[BilibiliCredential]) -> dict:
    """Thin wrapper around bilibili-api-python's async get_info. Returns the `data` dict.

    NOTE: confirmed at smoke time against a real public BV id that the returned dict
    contains bvid/aid/cid/title/owner/duration/pubdate/pic; if a key differs in the
    installed library version, update parse_info + the fixture together.
    """
    from bilibili_api import video

    async def _run():
        credential = _build_credential(cred)
        if ref.bvid:
            v = video.Video(bvid=ref.bvid, credential=credential)
        else:
            v = video.Video(aid=ref.aid, credential=credential)
        return await v.get_info()

    return asyncio.run(_run())


def fetch_metadata(ref: VideoRef, cred: Optional[BilibiliCredential]) -> BilibiliMetadata:
    if not ref.bvid and not ref.aid:
        raise InvalidVideoRef("VideoRef has neither bvid nor aid")
    try:
        raw = _get_info_raw(ref, cred)
    except Exception as e:
        msg = str(e).lower()
        if "credential" in msg or "登录" in str(e) or "-101" in msg:
            raise CredentialError(f"metadata fetch rejected (check SESSDATA): {e}") from e
        raise
    return parse_info(raw)
