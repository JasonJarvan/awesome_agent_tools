import json
import httpx
import pytest
from bilibili.bilinote_client import BiliNoteClient
from bilibili.errors import BiliNoteUnavailable, TranscriptionFailed, TranscriptionTimeout


def _client(handler):
    transport = httpx.MockTransport(handler)
    http = httpx.Client(transport=transport, base_url="http://bn")
    return BiliNoteClient(base_url="http://bn", provider_id="pid", model_name="m",
                          poll_interval_s=0, poll_timeout_s=5, http=http)


def test_health_ok():
    def h(req):
        assert req.url.path == "/api/sys_check"
        return httpx.Response(200, json={"code": 0, "msg": "ok", "data": None})
    _client(h).health_check()


def test_health_unavailable_on_connect_error():
    def h(req):
        raise httpx.ConnectError("refused", request=req)
    with pytest.raises(BiliNoteUnavailable):
        _client(h).health_check()


def test_generate_note_returns_task_id():
    def h(req):
        assert req.url.path == "/api/generate_note"
        body = json.loads(req.content)
        assert body["platform"] == "bilibili"
        assert body["provider_id"] == "pid"
        assert body["quality"] == "fast"
        return httpx.Response(200, json={"code": 0, "data": {"task_id": "T1"}})
    assert _client(h).generate_note("https://www.bilibili.com/video/BV1x") == "T1"


def test_generate_note_includes_prefetched_when_given():
    seen = {}
    def h(req):
        seen["body"] = json.loads(req.content)
        return httpx.Response(200, json={"code": 0, "data": {"task_id": "T2"}})
    pf = {"language": "zh", "full_text": "hi", "segments": [{"start": 0, "end": 1, "text": "hi"}]}
    _client(h).generate_note("u", prefetched_transcript=pf)
    assert seen["body"]["prefetched_transcript"] == pf


def test_poll_success_returns_result():
    note = {"markdown": "## S", "transcript": {"language": "zh", "full_text": "hi",
            "segments": [{"start": 0, "end": 1, "text": "hi"}]}, "audio_meta": {}}
    def h(req):
        return httpx.Response(200, json={"code": 0, "data": {"status": "SUCCESS", "result": note}})
    assert _client(h).poll("T1")["markdown"] == "## S"


def test_poll_failed_raises():
    def h(req):
        return httpx.Response(200, json={"code": 0, "data": {"status": "FAILED", "message": "boom"}})
    with pytest.raises(TranscriptionFailed):
        _client(h).poll("T1")


def test_poll_timeout_raises():
    def h(req):
        return httpx.Response(200, json={"code": 0, "data": {"status": "TRANSCRIBING"}})
    with pytest.raises(TranscriptionTimeout):
        _client(h).poll("T1")


def test_transcribe_orchestrates_and_returns_transcript_and_summary():
    note = {"markdown": "## S", "transcript": {"language": "zh", "full_text": "hi",
            "segments": [{"start": 0, "end": 1, "text": "hi"}]}, "audio_meta": {}}
    def h(req):
        if req.url.path == "/api/sys_check":
            return httpx.Response(200, json={"code": 0, "data": None})
        if req.url.path == "/api/generate_note":
            return httpx.Response(200, json={"code": 0, "data": {"task_id": "T1"}})
        return httpx.Response(200, json={"code": 0, "data": {"status": "SUCCESS", "result": note}})
    transcript, summary = _client(h).transcribe("u")
    assert summary == "## S"
    assert transcript["full_text"] == "hi"
