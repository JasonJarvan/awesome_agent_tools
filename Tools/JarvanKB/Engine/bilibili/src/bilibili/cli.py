"""Thin CLI for manual testing: resolve a video → transcribe → print or write Markdown."""
from __future__ import annotations
import argparse
import os
import sys
from typing import Optional

from .engine import transcribe
from .models import BilibiliCredential, RenderOptions


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="bilibili-engine", description="Transcribe a Bilibili video.")
    p.add_argument("video", help="BV id / bilibili.com URL / av id")
    p.add_argument("--out", default=None, help="output directory (default: print to stdout)")
    p.add_argument("--no-transcript", action="store_true", help="omit the transcript body")
    p.add_argument("--timestamps", action="store_true", help="render [mm:ss] timestamped lines")
    p.add_argument("--split", action="store_true", help="write transcript to a separate file")
    p.add_argument("--slug", default=None, help="override output basename (default: bvid)")
    p.add_argument("--sessdata", default=None, help="SESSDATA cookie (or set BILI_SESSDATA)")
    p.add_argument("--bili-jct", default=None)
    p.add_argument("--buvid3", default=None)
    return p


def _credential_from_args(args) -> Optional[BilibiliCredential]:
    sessdata = args.sessdata or os.getenv("BILI_SESSDATA")
    if not sessdata:
        return None
    return BilibiliCredential(sessdata=sessdata, bili_jct=args.bili_jct, buvid3=args.buvid3)


def run(argv: Optional[list] = None) -> int:
    args = build_parser().parse_args(argv)
    cred = _credential_from_args(args)
    result = transcribe(args.video, cred)
    opts = RenderOptions(
        include_transcript=not args.no_transcript,
        include_timestamps=args.timestamps,
        split_transcript=args.split,
        slug=args.slug,
    )
    rendered = result.render(opts)
    if not args.out:
        sys.stdout.write(rendered.main_markdown)
        return 0
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, rendered.suggested_names["main"]), "w", encoding="utf-8") as f:
        f.write(rendered.main_markdown)
    if rendered.transcript_markdown:
        with open(os.path.join(args.out, rendered.suggested_names["transcript"]), "w", encoding="utf-8") as f:
            f.write(rendered.transcript_markdown)
    return 0


def main() -> None:  # console_scripts entry point
    raise SystemExit(run())
