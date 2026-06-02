"""JarvanKB Bilibili Engine (SP-4a). Frozen public API — see docs/interface.md."""
from .engine import BilibiliEngine, transcribe
from .models import (
    BilibiliCredential, EngineConfig, RenderOptions, RenderedOutput,
    BilibiliResult, BilibiliMetadata, Transcript, TranscriptSegment,
)
from .errors import (
    BilibiliEngineError, InvalidVideoRef, CredentialError,
    BiliNoteUnavailable, TranscriptionFailed, TranscriptionTimeout,
)

__version__ = "0.1.0"

__all__ = [
    "BilibiliEngine", "transcribe",
    "BilibiliCredential", "EngineConfig", "RenderOptions", "RenderedOutput",
    "BilibiliResult", "BilibiliMetadata", "Transcript", "TranscriptSegment",
    "BilibiliEngineError", "InvalidVideoRef", "CredentialError",
    "BiliNoteUnavailable", "TranscriptionFailed", "TranscriptionTimeout",
]
