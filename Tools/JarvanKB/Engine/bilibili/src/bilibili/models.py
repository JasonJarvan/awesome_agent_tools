"""Dataclasses for the Bilibili engine. All field names here are the frozen v1 contract."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class BilibiliCredential:
    sessdata: str
    bili_jct: Optional[str] = None
    buvid3: Optional[str] = None

    def to_cookie_string(self) -> str:
        parts = [f"SESSDATA={self.sessdata}"]
        if self.bili_jct:
            parts.append(f"bili_jct={self.bili_jct}")
        if self.buvid3:
            parts.append(f"buvid3={self.buvid3}")
        return "; ".join(parts)


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str


@dataclass
class Transcript:
    source: Literal["subtitle", "asr"]
    language: Optional[str]
    full_text: str
    segments: list[TranscriptSegment]


@dataclass
class BilibiliMetadata:
    bvid: str
    aid: int
    cid: int
    title: str
    up: str
    up_mid: int
    duration: int
    pubdate: int
    cover: Optional[str]
    url: str


@dataclass
class EngineConfig:
    bn_base_url: str
    provider_id: str
    model_name: str
    poll_interval_s: int = 3
    poll_timeout_s: int = 600
    style: str = "summary"


@dataclass
class RenderOptions:
    include_transcript: bool = True
    include_timestamps: bool = False
    split_transcript: bool = False
    slug: Optional[str] = None


@dataclass
class RenderedOutput:
    main_markdown: str
    transcript_markdown: Optional[str]
    suggested_names: dict


@dataclass
class BilibiliResult:
    metadata: BilibiliMetadata
    transcript: Transcript
    summary_markdown: Optional[str]

    def render(self, options: Optional[RenderOptions] = None) -> RenderedOutput:
        from .render import render_result
        return render_result(self, options or RenderOptions())

    def to_markdown(self, options: Optional[RenderOptions] = None) -> str:
        return self.render(options).main_markdown
