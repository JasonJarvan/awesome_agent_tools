import pytest
from bilibili.errors import (
    BilibiliEngineError, InvalidVideoRef, CredentialError,
    BiliNoteUnavailable, TranscriptionFailed, TranscriptionTimeout,
)

@pytest.mark.parametrize("cls", [
    InvalidVideoRef, CredentialError, BiliNoteUnavailable,
    TranscriptionFailed, TranscriptionTimeout,
])
def test_all_subclass_base(cls):
    assert issubclass(cls, BilibiliEngineError)
    with pytest.raises(BilibiliEngineError):
        raise cls("boom")
