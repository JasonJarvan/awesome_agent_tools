from unittest.mock import patch, MagicMock
from bilibili.engine import BilibiliEngine
from bilibili.models import (
    EngineConfig, BilibiliCredential, BilibiliMetadata, Transcript, TranscriptSegment,
)

CFG = EngineConfig(bn_base_url="http://bn", provider_id="pid", model_name="m")
META = BilibiliMetadata(bvid="BV1x", aid=1, cid=2, title="T", up="U", up_mid=9,
                        duration=10, pubdate=1610000000, cover=None,
                        url="https://www.bilibili.com/video/BV1x")
SUBT = Transcript(source="subtitle", language="zh", full_text="hi",
                  segments=[TranscriptSegment(0, 1, "hi")])


def _engine(bn):
    e = BilibiliEngine(CFG)
    e._bn = bn
    return e


def test_subtitle_path_feeds_prefetched_and_keeps_source_subtitle():
    bn = MagicMock()
    bn.transcribe.return_value = (None, "## Summary")
    with patch("bilibili.engine.fetch_metadata", return_value=META), \
         patch("bilibili.engine.fetch_subtitle", return_value=SUBT):
        res = _engine(bn).transcribe("BV1GJ411x7h7", BilibiliCredential(sessdata="SS"))
    _, kwargs = bn.transcribe.call_args
    assert kwargs["prefetched_transcript"]["full_text"] == "hi"
    bn.push_cookie.assert_not_called()
    assert res.transcript.source == "subtitle"
    assert res.summary_markdown == "## Summary"


def test_asr_path_pushes_cookie_and_sets_source_asr():
    asr = {"language": "zh", "full_text": "world", "segments": [{"start": 0, "end": 1, "text": "world"}]}
    bn = MagicMock()
    bn.transcribe.return_value = (asr, "## Summary")
    with patch("bilibili.engine.fetch_metadata", return_value=META), \
         patch("bilibili.engine.fetch_subtitle", return_value=None):
        res = _engine(bn).transcribe("BV1GJ411x7h7", BilibiliCredential(sessdata="SS"))
    bn.push_cookie.assert_called_once()
    _, kwargs = bn.transcribe.call_args
    assert kwargs["prefetched_transcript"] is None
    assert res.transcript.source == "asr"
    assert res.transcript.full_text == "world"


def test_asr_path_cookie_push_failure_is_best_effort():
    asr = {"language": "zh", "full_text": "x", "segments": [{"start": 0, "end": 1, "text": "x"}]}
    bn = MagicMock()
    bn.push_cookie.side_effect = Exception("cookie store down")
    bn.transcribe.return_value = (asr, None)
    with patch("bilibili.engine.fetch_metadata", return_value=META), \
         patch("bilibili.engine.fetch_subtitle", return_value=None):
        res = _engine(bn).transcribe("BV1GJ411x7h7", BilibiliCredential(sessdata="SS"))
    assert res.transcript.source == "asr"
