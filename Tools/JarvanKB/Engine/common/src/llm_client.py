"""LLMClient — uniform LLM dispatcher with litellm backend.

Design reference: docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md §8.

Status: skeleton only. Body NotImplementedError until first consumer sub-project
(SP-3, SP-6, or SP-7) brings in actual usage. The interface signatures below are
the stable v1 contract — implement against these.
"""

from __future__ import annotations
from typing import Any, Iterator


class LLMClient:
    """Uniform LLM client. Internally uses litellm to route to any provider.

    Use:
        from Engine.common.src.llm_client import LLMClient
        client = LLMClient(profile="default")
        text = client.complete([{"role": "user", "content": "hello"}])
    """

    def __init__(self, profile: str = "default") -> None:
        self.profile = profile
        # Configuration loading happens in first consumer's brainstorming.
        # See config/llm.yaml.example for the schema.

    def complete(self, messages: list[dict], **kwargs: Any) -> str:
        """Single-shot completion. Returns assistant text."""
        raise NotImplementedError(
            "LLMClient.complete pending first consumer implementation. "
            "See SP-3 / SP-6 / SP-7 brainstorming."
        )

    def stream(self, messages: list[dict], **kwargs: Any) -> Iterator[str]:
        """Streaming completion. Yields text chunks."""
        raise NotImplementedError(
            "LLMClient.stream pending first consumer implementation."
        )

    def to_opencode(self) -> Any:
        """v1+ escape hatch: convert to opencode agent loop. Not implemented in v1."""
        raise NotImplementedError("opencode integration planned for v1.x")
