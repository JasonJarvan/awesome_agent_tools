from __future__ import annotations
import argparse
import json
import sys
from .engine import fetch


def _load_cookies(path: str | None) -> dict | None:
    if not path:
        return None
    raw = json.loads(open(path, encoding="utf-8").read())
    if isinstance(raw, list):  # browser-export form [{name, value}, ...]
        return {c["name"]: c["value"] for c in raw}
    return raw  # already a dict


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="zhihu", description="Fetch one Zhihu URL -> Markdown")
    parser.add_argument("url")
    parser.add_argument("--cookies", help="path to cookies.json (browser-export list or dict)")
    parser.add_argument("--comments", action="store_true")
    parser.add_argument("--no-frontmatter", action="store_true")
    args = parser.parse_args(argv)

    result = fetch(args.url, cookies=_load_cookies(args.cookies), with_comments=args.comments)
    print(result.to_markdown(with_frontmatter=not args.no_frontmatter))
    return 0


if __name__ == "__main__":
    sys.exit(main())
