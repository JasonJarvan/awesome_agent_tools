import pytest
from bilibili.url_parser import parse_video_ref, VideoRef
from bilibili.errors import InvalidVideoRef


def test_bare_bvid():
    assert parse_video_ref("BV1GJ411x7h7") == VideoRef(bvid="BV1GJ411x7h7", aid=None, part=None)


def test_full_url_with_part():
    assert parse_video_ref("https://www.bilibili.com/video/BV1GJ411x7h7?p=2&t=10") == \
        VideoRef(bvid="BV1GJ411x7h7", aid=None, part=2)


def test_url_without_part_defaults_none():
    assert parse_video_ref("https://www.bilibili.com/video/BV1GJ411x7h7/").part is None


def test_av_id():
    assert parse_video_ref("av170001") == VideoRef(bvid=None, aid=170001, part=None)


@pytest.mark.parametrize("bad", ["", "not a video", "https://b23.tv/abc", "https://youtube.com/x"])
def test_invalid(bad):
    with pytest.raises(InvalidVideoRef):
        parse_video_ref(bad)
