"""The cascade orchestrator: metadata → subtitle → (prefetched|ASR) BiliNote → BilibiliResult."""
from __future__ import annotations
import logging
from typing import Optional

from .bilinote_client import BiliNoteClient
from .config import load_config, DEFAULT_CONFIG_PATH
from .metadata import fetch_metadata
from .models import (
    BilibiliCredential, BilibiliResult, EngineConfig, Transcript, TranscriptSegment,
)
from .subtitle import fetch_subtitle
from .url_parser import parse_video_ref

logger = logging.getLogger(__name__)


def _transcript_to_prefetched(t: Transcript) -> dict:
    return {
        "language": t.language,
        "full_text": t.full_text,
        "segments": [{"start": s.start, "end": s.end, "text": s.text} for s in t.segments],
    }


class BilibiliEngine:
    def __init__(self, config: EngineConfig):
        self.config = config
        self._bn = BiliNoteClient(
            base_url=config.bn_base_url, provider_id=config.provider_id,
            model_name=config.model_name, poll_interval_s=config.poll_interval_s,
            poll_timeout_s=config.poll_timeout_s, style=config.style,
        )

    @classmethod
    def from_config(cls, path: str = DEFAULT_CONFIG_PATH) -> "BilibiliEngine":
        return cls(load_config(path))

    def transcribe(self, video_ref: str, credential: Optional[BilibiliCredential] = None) -> BilibiliResult:
        ref = parse_video_ref(video_ref)
        meta = fetch_metadata(ref, credential)
        subtitle = fetch_subtitle(meta.bvid, meta.cid, credential)

        if subtitle is not None:
            _, summary = self._bn.transcribe(
                meta.url, prefetched_transcript=_transcript_to_prefetched(subtitle))
            transcript = subtitle
        else:
            if credential and credential.sessdata:
                try:
                    self._bn.push_cookie(credential.to_cookie_string())
                except Exception as e:
                    logger.warning("cookie push to BiliNote failed (best-effort): %s", e)
            asr, summary = self._bn.transcribe(meta.url, prefetched_transcript=None)
            transcript = Transcript(
                source="asr",
                language=asr.get("language"),
                full_text=asr["full_text"],
                segments=[TranscriptSegment(s["start"], s["end"], s["text"]) for s in asr["segments"]],
            )

        return BilibiliResult(metadata=meta, transcript=transcript, summary_markdown=summary)


def transcribe(video_ref: str, credential: Optional[BilibiliCredential] = None,
               config: Optional[EngineConfig] = None) -> BilibiliResult:
    """Convenience: build a default engine (from EngineConfig or config file) and transcribe."""
    engine = BilibiliEngine(config) if config else BilibiliEngine.from_config()
    return engine.transcribe(video_ref, credential)
