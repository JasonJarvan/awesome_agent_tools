"""LLMClient — uniform LLM dispatcher with a litellm backend.

Design reference: Skill/crawl/zhihu-crawl/docs/superpowers/specs/2026-06-02-SP-3-zhihu-skill-design.md §7
(real impl landed in SP-3; first consumer = zhihu-crawl vague_path classification).

Public signatures (frozen v1 contract): __init__(profile), complete(messages, **kwargs) -> str,
stream(messages, **kwargs) -> Iterator[str], to_opencode().
"""
from __future__ import annotations

from typing import Any, Iterator

import litellm

from .llm_config import resolve_candidates


class LLMClient:
    """Uniform LLM client. Routes to any provider via litellm; provider switches by config alone."""

    def __init__(self, profile: str = "default", config_path: str | None = None) -> None:
        self.profile = profile
        self._candidates = resolve_candidates(profile, config_path=config_path)
        if not self._candidates:
            raise RuntimeError(
                f"No available LLM profile for {profile!r}. Set the api_key_env credentials in your "
                f"environment (.env) for one of the configured profiles."
            )

    def complete(self, messages: list[dict], **kwargs: Any) -> str:
        last_err: Exception | None = None
        for cfg in self._candidates:
            try:
                resp = litellm.completion(
                    model=cfg.model, messages=messages,
                    api_key=cfg.api_key, api_base=cfg.api_base, **kwargs,
                )
                return resp.choices[0].message.content
            except Exception as e:  # noqa: BLE001 — provider-agnostic fallthrough
                last_err = e
        raise RuntimeError(f"All LLM profiles failed for {self.profile!r}") from last_err

    def stream(self, messages: list[dict], **kwargs: Any) -> Iterator[str]:
        last_err: Exception | None = None
        for cfg in self._candidates:
            try:
                stream = litellm.completion(
                    model=cfg.model, messages=messages,
                    api_key=cfg.api_key, api_base=cfg.api_base, stream=True, **kwargs,
                )
                for chunk in stream:
                    piece = chunk.choices[0].delta.content
                    if piece:
                        yield piece
                return
            except Exception as e:  # noqa: BLE001
                last_err = e
        raise RuntimeError(f"All LLM profiles failed for {self.profile!r}") from last_err

    def to_opencode(self) -> Any:
        """v1+ escape hatch: convert to opencode agent loop. Not implemented in v1."""
        raise NotImplementedError("opencode integration planned for v1.x")
