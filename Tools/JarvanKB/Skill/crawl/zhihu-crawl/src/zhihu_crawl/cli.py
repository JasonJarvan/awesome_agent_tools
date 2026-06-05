"""Thin CLI over save_zhihu. `--json` prints a machine-readable SaveResult for any calling agent."""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys

from zhihu import ZhihuFetchError

from .api import save_zhihu


def _build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="zhihu-crawl",
                                 description="Fetch a Zhihu URL via the frozen engine and save Markdown.")
    ap.add_argument("url", help="Zhihu URL (answer / article / question)")
    ap.add_argument("--out", dest="save_path", default=None,
                    help="save path; a .md file = explicit, a dir/omitted = vague (LLM classify)")
    ap.add_argument("--comments", action="store_true", help="also fetch comments")
    ap.add_argument("--comment-limit", type=int, default=None, help="max comments (default: all)")
    ap.add_argument("--json", dest="as_json", action="store_true", help="print JSON SaveResult")
    ap.add_argument("--profile", default=None, help="LLM profile override (default: config)")
    ap.add_argument("--config", dest="config_path", default=None, help="path to config.yaml")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        result = save_zhihu(
            args.url, args.save_path,
            with_comments=args.comments, comment_limit=args.comment_limit,
            profile=args.profile, config_path=args.config_path,
        )
    except ZhihuFetchError as e:
        print(f"fetch failed: {e}", file=sys.stderr)
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
        print(f"saved: {result.path}\n  title: {result.title}  type: {result.type}{cat}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
