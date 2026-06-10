"""Wrap the frozen SP-4a Bilibili engine: (bvid, credential) -> FetchedDoc | None.

build_credential turns the pulled bilibili.com cookies into a BilibiliCredential. make_fetcher binds
an engine instance + render options into a (bvid, cred) closure the watcher calls per item. On any
BilibiliEngineError (BN down / transcription failed / timeout / bad ref) we log + return None so the
daemon degrades gracefully and the item is retried next cycle (not marked seen / not watermarked).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Optional

from bilibili import BilibiliCredential, RenderOptions, BilibiliEngineError

log = logging.getLogger("bilibili_watcher.fetcher")

from .config import RenderConfig

FetcherFn = Callable[[str, BilibiliCredential], Optional["FetchedDoc"]]


@dataclass
class FetchedDoc:
    title: str
    markdown: str


def build_credential(cookies: dict[str, str]) -> BilibiliCredential:
    return BilibiliCredential(sessdata=cookies.get("SESSDATA", ""), bili_jct=cookies.get("bili_jct"))


def make_fetcher(engine, render: RenderConfig) -> FetcherFn:
    ro = RenderOptions(
        include_transcript=render.include_transcript,
        include_timestamps=render.include_timestamps,
        split_transcript=render.split_transcript,
    )

    def fetch(bvid: str, credential: BilibiliCredential) -> Optional[FetchedDoc]:
        try:
            result = engine.transcribe(bvid, credential=credential)
            markdown = result.render(ro).main_markdown
        except BilibiliEngineError as e:
            log.warning("SP-4a engine failed bvid=%s: %s", bvid, e)
            return None
        return FetchedDoc(title=result.metadata.title, markdown=markdown)

    return fetch
