from bilibili.models import (
    BilibiliMetadata, Transcript, TranscriptSegment, BilibiliResult, RenderOptions,
)
from bilibili.render import render_result, format_timestamp


def _result(source="subtitle", summary="## Summary\n\nhi"):
    meta = BilibiliMetadata(
        bvid="BV1x", aid=1, cid=2, title="T", up="U", up_mid=9,
        duration=125, pubdate=1610000000, cover="http://c", url="https://www.bilibili.com/video/BV1x",
    )
    tr = Transcript(source=source, language="zh", full_text="你好世界",
                    segments=[TranscriptSegment(0, 1, "你好"), TranscriptSegment(75, 76, "世界")])
    return BilibiliResult(metadata=meta, transcript=tr, summary_markdown=summary)


def test_format_timestamp():
    assert format_timestamp(75) == "01:15"
    assert format_timestamp(3725) == "1:02:05"


def test_default_inline_has_frontmatter_summary_and_prose():
    out = render_result(_result(), RenderOptions())
    assert out.transcript_markdown is None
    md = out.main_markdown
    assert md.startswith("---\n")
    assert "bvid: BV1x" in md
    assert "transcript_source: subtitle" in md
    assert "## Summary" in md
    assert "你好世界" in md
    assert "[00:00]" not in md


def test_timestamps_mode_lists_segments():
    out = render_result(_result(), RenderOptions(include_timestamps=True))
    assert "[00:00] 你好" in out.main_markdown
    assert "[01:15] 世界" in out.main_markdown


def test_include_transcript_false_omits_body():
    out = render_result(_result(), RenderOptions(include_transcript=False))
    assert "你好世界" not in out.main_markdown
    assert "## Summary" in out.main_markdown
    assert out.transcript_markdown is None


def test_split_emits_two_documents_and_link():
    out = render_result(_result(), RenderOptions(split_transcript=True))
    assert out.transcript_markdown is not None
    assert "你好世界" in out.transcript_markdown
    assert "你好世界" not in out.main_markdown
    assert "[全文转录](./BV1x.transcript.md)" in out.main_markdown
    assert out.suggested_names == {"main": "BV1x.md", "transcript": "BV1x.transcript.md"}


def test_slug_override_drives_names_and_link():
    out = render_result(_result(), RenderOptions(split_transcript=True, slug="custom"))
    assert "[全文转录](./custom.transcript.md)" in out.main_markdown
    assert out.suggested_names["transcript"] == "custom.transcript.md"
