"""save_zhihu — orchestrate cookie pull -> frozen zhihu engine fetch -> markdown -> resolve path -> write.

Module-level `fetch` and `LLMClient` are imported so tests can monkeypatch them.
"""
from __future__ import annotations

from dataclasses import dataclass

from jarvankb_common import LLMClient
from zhihu import fetch

from . import classify, cookie, saver
from . import config as cfgmod


@dataclass
class SaveResult:
    path: str
    title: str
    type: str
    url: str
    category: str | None
    was_vague: bool
    proposed_new: bool


def save_zhihu(url: str, save_path: str | None = None, *,
               with_comments: bool = False, comment_limit: int | None = None,
               profile: str | None = None, config_path: str | None = None) -> SaveResult:
    cfg = cfgmod.load_config(config_path)
    cookies = cookie.pull(cfg.cookie)
    result = fetch(url, cookies=cookies, with_comments=with_comments, comment_limit=comment_limit)
    markdown = result.to_markdown()

    vague = saver.is_vague(save_path, cfg.output_root)
    category: str | None = None
    proposed_new = False
    if vague:
        client = LLMClient(profile=profile or cfg.llm_profile)
        cat = classify.classify(result, cfg.output_root, client)
        category, proposed_new = cat.name, cat.is_new

    target = saver.resolve_target(save_path, cfg.output_root, category, result.title)
    written = saver.write(target, markdown)
    return SaveResult(
        path=str(written),
        title=result.title,
        type=getattr(result.type, "value", str(result.type)),
        url=result.url,
        category=category,
        was_vague=vague,
        proposed_new=proposed_new,
    )
