from bilibili.models import (
    BilibiliCredential, TranscriptSegment, Transcript, BilibiliMetadata,
    BilibiliResult, EngineConfig, RenderOptions, RenderedOutput,
)


def test_credential_defaults_and_cookie_string():
    c = BilibiliCredential(sessdata="SS")
    assert c.bili_jct is None and c.buvid3 is None
    assert c.to_cookie_string() == "SESSDATA=SS"
    c2 = BilibiliCredential(sessdata="SS", bili_jct="JCT", buvid3="BV3")
    assert c2.to_cookie_string() == "SESSDATA=SS; bili_jct=JCT; buvid3=BV3"


def test_render_options_defaults():
    o = RenderOptions()
    assert o.include_transcript is True
    assert o.include_timestamps is False
    assert o.split_transcript is False
    assert o.slug is None


def test_engine_config_defaults():
    cfg = EngineConfig(bn_base_url="http://x", provider_id="p", model_name="m")
    assert cfg.poll_interval_s == 3
    assert cfg.poll_timeout_s == 600
    assert cfg.style == "summary"


def test_transcript_holds_segments():
    t = Transcript(source="subtitle", language="zh", full_text="hi",
                   segments=[TranscriptSegment(0.0, 1.0, "hi")])
    assert t.source == "subtitle"
    assert t.segments[0].text == "hi"
