from unittest.mock import patch
from bilibili.cli import build_parser, run
from bilibili.models import (
    BilibiliMetadata, Transcript, TranscriptSegment, BilibiliResult,
)

META = BilibiliMetadata(bvid="BV1x", aid=1, cid=2, title="T", up="U", up_mid=9,
                        duration=10, pubdate=1610000000, cover=None,
                        url="https://www.bilibili.com/video/BV1x")
RES = BilibiliResult(metadata=META,
                     transcript=Transcript("subtitle", "zh", "hi", [TranscriptSegment(0, 1, "hi")]),
                     summary_markdown="## S")


def test_parser_defaults():
    args = build_parser().parse_args(["BV1x"])
    assert args.video == "BV1x"
    assert args.split is False
    assert args.timestamps is False
    assert args.no_transcript is False


def test_run_prints_markdown(capsys):
    with patch("bilibili.cli.transcribe", return_value=RES), \
         patch("bilibili.cli._credential_from_args", return_value=None):
        rc = run(["BV1x", "--sessdata", "SS"])
    assert rc == 0
    assert "## S" in capsys.readouterr().out


def test_run_split_writes_files(tmp_path):
    out = tmp_path / "out"
    with patch("bilibili.cli.transcribe", return_value=RES), \
         patch("bilibili.cli._credential_from_args", return_value=None):
        rc = run(["BV1x", "--split", "--out", str(out)])
    assert rc == 0
    assert (out / "BV1x.md").exists()
    assert (out / "BV1x.transcript.md").exists()
