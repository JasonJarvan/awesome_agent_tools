"""Pure resolution of a video reference (BV id / bilibili.com URL / av id) to ids."""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse, parse_qs

from .errors import InvalidVideoRef

_BVID_RE = re.compile(r"(BV[0-9A-Za-z]{10})")
_AV_RE = re.compile(r"^av(\d+)$", re.IGNORECASE)


@dataclass(frozen=True)
class VideoRef:
    bvid: Optional[str]
    aid: Optional[int]
    part: Optional[int]


def parse_video_ref(ref: str) -> VideoRef:
    if not ref or not ref.strip():
        raise InvalidVideoRef("empty reference")
    ref = ref.strip()

    m = _AV_RE.match(ref)
    if m:
        return VideoRef(bvid=None, aid=int(m.group(1)), part=None)

    if ref.startswith("http://") or ref.startswith("https://"):
        parsed = urlparse(ref)
        if "bilibili.com" not in parsed.netloc:
            raise InvalidVideoRef(f"unsupported host: {parsed.netloc}")
        bm = _BVID_RE.search(parsed.path)
        if not bm:
            raise InvalidVideoRef(f"no BV id in URL path: {parsed.path}")
        part = None
        p = parse_qs(parsed.query).get("p")
        if p and p[0].isdigit():
            part = int(p[0])
        return VideoRef(bvid=bm.group(1), aid=None, part=part)

    bm = _BVID_RE.fullmatch(ref) or _BVID_RE.fullmatch(ref.replace("/", ""))
    if bm:
        return VideoRef(bvid=bm.group(1), aid=None, part=None)

    raise InvalidVideoRef(f"unrecognized reference: {ref!r}")
