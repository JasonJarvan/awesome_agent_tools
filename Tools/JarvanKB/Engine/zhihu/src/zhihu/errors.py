from __future__ import annotations


class ZhihuFetchError(Exception):
    """Raised when all body-fetch fallbacks fail. Carries diagnostics, never a silent sentinel."""

    def __init__(
        self,
        message: str,
        *,
        url: str,
        attempts: list[str] | None = None,
        status: int | None = None,
    ) -> None:
        super().__init__(message)
        self.url = url
        self.attempts = attempts or []
        self.status = status
