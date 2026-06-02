"""Exception hierarchy. All engine failures subclass BilibiliEngineError."""


class BilibiliEngineError(Exception):
    """Base for all engine errors."""


class InvalidVideoRef(BilibiliEngineError):
    """The input could not be resolved to a Bilibili video id."""


class CredentialError(BilibiliEngineError):
    """Credentials missing or rejected where required (metadata/subtitle)."""


class BiliNoteUnavailable(BilibiliEngineError):
    """The BiliNote instance is unreachable (the Stage-3 gate)."""


class TranscriptionFailed(BilibiliEngineError):
    """BiliNote reported task status FAILED."""


class TranscriptionTimeout(BilibiliEngineError):
    """Polling BiliNote exceeded the configured timeout."""
