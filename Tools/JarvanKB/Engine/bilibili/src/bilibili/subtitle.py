"""Engine-side subtitle fetch (subtitle-first cascade step 1).

Pure helpers (pick_track / parse_body / normalize_url) are unit-tested; the two thin
wrappers (_get_tracks_raw via bilibili-api-python, _get_body_raw via httpx) carry the
fixture-recording note. Returns a Transcript(source="subtitle") or None when no usable track.
"""
from __future__ import annotations
import asyncio
import logging
from typing import Optional

import httpx

from .models import BilibiliCredential, Transcript, TranscriptSegment

logger = logging.getLogger(__name__)


def normalize_url(url: str) -> str:
    return "https:" + url if url.startswith("//") else url


def _is_zh(track: dict) -> bool:
    lan = (track.get("lan") or "").lower()
    return lan.startswith("zh") or lan == "ai-zh"


def pick_track(tracks: list[dict]) -> Optional[dict]:
    """manual zh (ai_type falsy) > AI zh > any non-empty."""
    if not tracks:
        return None
    for t in tracks:
        if _is_zh(t) and not t.get("ai_type"):
            return t
    for t in tracks:
        if _is_zh(t):
            return t
    return tracks[0]


def parse_body(body: list[dict]) -> list[TranscriptSegment]:
    segs: list[TranscriptSegment] = []
    for item in body or []:
        text = (item.get("content") or "").strip()
        if not text:
            continue
        segs.append(TranscriptSegment(
            start=float(item.get("from", 0)),
            end=float(item.get("to", 0)),
            text=text,
        ))
    return segs


def merge_full_text(segs: list[TranscriptSegment]) -> str:
    return " ".join(s.text for s in segs)


def _build_credential(cred: Optional[BilibiliCredential]):
    from bilibili_api import Credential
    if cred is None:
        return None
    return Credential(sessdata=cred.sessdata, bili_jct=cred.bili_jct, buvid3=cred.buvid3)


def _get_tracks_raw(bvid: str, cid: int, cred: Optional[BilibiliCredential]) -> list[dict]:
    """Thin wrapper: bilibili-api-python get_subtitle(cid) -> list of subtitle tracks.

    NOTE: confirm at smoke time against a real video with subtitles that the returned
    structure yields the track list (the library handles wbi signing). If the library nests
    the list differently, normalize to a list of {lan, ai_type, subtitle_url} dicts here.
    """
    from bilibili_api import video

    async def _run():
        v = video.Video(bvid=bvid, credential=_build_credential(cred))
        data = await v.get_subtitle(cid)
        return (data or {}).get("subtitles", []) or []

    return asyncio.run(_run())


def _get_body_raw(subtitle_url: str, cred: Optional[BilibiliCredential]) -> list[dict]:
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.bilibili.com"}
    if cred and cred.sessdata:
        headers["Cookie"] = cred.to_cookie_string()
    resp = httpx.get(normalize_url(subtitle_url), headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json().get("body") or []


def fetch_subtitle(bvid: str, cid: int, cred: Optional[BilibiliCredential]) -> Optional[Transcript]:
    # Subtitle tracks (incl. AI CC) require a logged-in session — bilibili-api-python's
    # get_subtitle raises CredentialNoSessdataException without one. The subtitle path is
    # best-effort and ASR is the fallback, so a missing credential or ANY subtitle-fetch
    # failure returns None (→ engine takes the ASR path) instead of raising.
    if cred is None or not cred.sessdata:
        return None
    try:
        tracks = _get_tracks_raw(bvid, cid, cred)
    except Exception as e:
        logger.warning("subtitle track fetch failed for %s (cid=%s): %s — falling back to ASR", bvid, cid, e)
        return None
    track = pick_track(tracks)
    if not track or not track.get("subtitle_url"):
        return None
    try:
        body = _get_body_raw(track["subtitle_url"], cred)
    except Exception as e:
        logger.warning("subtitle body fetch failed for %s: %s — falling back to ASR", bvid, e)
        return None
    segs = parse_body(body)
    if not segs:
        return None
    lan = track.get("lan") or "zh"
    return Transcript(
        source="subtitle",
        language=lan,
        full_text=merge_full_text(segs),
        segments=segs,
    )
