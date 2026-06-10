"""save_bilibili — orchestrate cookie pull -> frozen bilibili engine transcribe -> render -> resolve -> write.

Module-level `transcribe` and `LLMClient` are imported so tests can monkeypatch them. Cookie failure is
NON-FATAL: the engine is cookie-less-capable on public videos, so a missing/expired cookie degrades to
credential=None with a warning rather than crashing.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass

from bilibili import RenderOptions, transcribe
from jarvankb_common import LLMClient

from . import classify, cookie, saver
from . import config as cfgmod


@dataclass
class SaveResult:
    path: str
    transcript_path: str | None
    title: str
    ref: str
    transcript_source: str
    category: str | None
    was_vague: bool
    proposed_new: bool


def save_bilibili(ref: str, save_path: str | None = None, *,
                  profile: str | None = None, config_path: str | None = None) -> SaveResult:
    cfg = cfgmod.load_config(config_path)

    # Cookie is best-effort: engine works cookie-less on public videos (subtitle path needs SESSDATA only).
    try:
        cookies = cookie.pull(cfg.cookie, domain="bilibili.com")
        cred = cookie.build_credential(cookies)
    except Exception as e:  # noqa: BLE001 — never let cookie issues abort a transcribe
        warnings.warn(f"bilibili-crawl: cookie unavailable ({e}); proceeding without credential")
        cred = None

    result = transcribe(ref, credential=cred)

    vague = saver.is_vague(save_path, cfg.output_root)
    category: str | None = None
    proposed_new = False
    if vague:
        client = LLMClient(profile=profile or cfg.llm_profile)
        cat = classify.classify(result, cfg.output_root, client, snippet_chars=cfg.classify_snippet_chars)
        category, proposed_new = cat.name, cat.is_new

    target = saver.resolve_target(save_path, cfg.output_root, category, result.metadata.title)
    rendered = result.render(RenderOptions(
        include_transcript=cfg.render.include_transcript,
        include_timestamps=cfg.render.include_timestamps,
        split_transcript=cfg.render.split_transcript,
        slug=target.stem,
    ))
    main_path = saver.write(target, rendered.main_markdown)
    transcript_path = None
    if cfg.render.split_transcript and rendered.transcript_markdown is not None:
        transcript_path = saver.write(saver.transcript_path_for(target), rendered.transcript_markdown)

    return SaveResult(
        path=str(main_path),
        transcript_path=str(transcript_path) if transcript_path else None,
        title=result.metadata.title,
        ref=ref,
        transcript_source=result.transcript.source,
        category=category,
        was_vague=vague,
        proposed_new=proposed_new,
    )
