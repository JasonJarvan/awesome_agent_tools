"""Path resolution + Markdown write. Vagueness rule: explicit == a path naming a .md file."""
from __future__ import annotations

import re
from pathlib import Path

_SLUG_RE = re.compile(r"[^\w一-鿿]+")


def slugify(title: str) -> str:
    s = _SLUG_RE.sub("-", title.strip()).strip("-").lower()
    return s or "untitled"


def is_vague(save_path: str | None, output_root: Path) -> bool:
    if not save_path:
        return True
    p = Path(save_path).expanduser()
    if str(p) == str(Path(output_root).expanduser()):
        return True
    return p.suffix.lower() != ".md"


def _dedup(target: Path) -> Path:
    if not target.exists():
        return target
    i = 2
    while True:
        cand = target.with_name(f"{target.stem}-{i}{target.suffix}")
        if not cand.exists():
            return cand
        i += 1


def resolve_target(save_path: str | None, output_root: Path,
                   category: str | None, title: str) -> Path:
    if save_path:
        p = Path(save_path).expanduser()
        if p.suffix.lower() == ".md":
            return p
    base = Path(output_root).expanduser() / (category or "")
    return _dedup(base / f"{slugify(title)}.md")


def write(target: Path, markdown: str) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markdown, encoding="utf-8")
    return target
