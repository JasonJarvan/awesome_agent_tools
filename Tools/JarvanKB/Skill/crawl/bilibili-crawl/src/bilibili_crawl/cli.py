"""Thin CLI over save_bilibili. `--json` prints a machine-readable SaveResult for any calling agent."""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys

from bilibili import BilibiliEngineError, BiliNoteUnavailable

from .api import save_bilibili


def _build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="bilibili-crawl",
                                 description="Transcribe a Bilibili video via the frozen engine and save Markdown.")
    ap.add_argument("ref", help="video ref: BV id / bilibili.com URL / av id")
    ap.add_argument("--out", dest="save_path", default=None,
                    help="save path; a .md file = explicit, a dir/omitted = vague (LLM classify)")
    ap.add_argument("--json", dest="as_json", action="store_true", help="print JSON SaveResult")
    ap.add_argument("--profile", default=None, help="LLM profile override (default: config)")
    ap.add_argument("--config", dest="config_path", default=None, help="path to config.yaml")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        result = save_bilibili(
            args.ref, args.save_path,
            profile=args.profile, config_path=args.config_path,
        )
    except BiliNoteUnavailable as e:   # subclass of BilibiliEngineError — catch first
        print(f"BiliNote unavailable (is the container up?): {e}", file=sys.stderr)
        return 3
    except BilibiliEngineError as e:
        print(f"transcription failed: {e}", file=sys.stderr)
        return 2
    except Exception as e:  # noqa: BLE001
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.as_json:
        print(json.dumps(dataclasses.asdict(result), ensure_ascii=False))
    else:
        cat = ""
        if result.category:
            cat = f"  category: {result.category}" + (" (new)" if result.proposed_new else "")
        extra = f"\n  transcript: {result.transcript_path}" if result.transcript_path else ""
        print(f"saved: {result.path}\n  title: {result.title}  source: {result.transcript_source}{cat}{extra}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
