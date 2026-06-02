from bilibili.models import TranscriptSegment
from bilibili.render import merge_segments_to_prose


def test_zh_segments_join_without_spaces():
    segs = [TranscriptSegment(0, 1, "你好"), TranscriptSegment(1, 2, "世界")]
    assert merge_segments_to_prose(segs) == "你好世界"


def test_en_segments_join_with_space():
    segs = [TranscriptSegment(0, 1, "hello"), TranscriptSegment(1, 2, "world")]
    assert merge_segments_to_prose(segs) == "hello world"


def test_paragraph_break_on_time_gap():
    segs = [
        TranscriptSegment(0, 1, "你好"),
        TranscriptSegment(1, 2, "世界"),
        TranscriptSegment(5, 6, "再见"),
    ]
    assert merge_segments_to_prose(segs, gap_threshold_s=2.0) == "你好世界\n\n再见"


def test_paragraph_break_on_char_budget():
    segs = [TranscriptSegment(i, i + 0.1, "字" * 50) for i in range(4)]
    out = merge_segments_to_prose(segs, char_budget=120)
    assert "\n\n" in out


def test_empty_segments():
    assert merge_segments_to_prose([]) == ""
