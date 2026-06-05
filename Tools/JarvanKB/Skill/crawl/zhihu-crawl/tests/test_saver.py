from pathlib import Path

from zhihu_crawl.saver import is_vague, resolve_target, slugify, write


def test_is_vague_rules(tmp_path):
    root = tmp_path / "KB"
    assert is_vague(None, root) is True
    assert is_vague("", root) is True
    assert is_vague(str(root), root) is True              # equals output_root
    assert is_vague(str(root / "tech"), root) is True      # a directory / no .md
    assert is_vague(str(root / "tech" / "note.md"), root) is False  # explicit .md


def test_slugify_keeps_cjk_and_hyphenates():
    assert slugify("  Hello World!  ") == "hello-world"
    assert slugify("知乎 答案 / Test") == "知乎-答案-test"
    assert slugify("") == "untitled"


def test_resolve_target_explicit_md_is_verbatim(tmp_path):
    root = tmp_path / "KB"
    p = resolve_target(str(tmp_path / "x" / "note.md"), root, None, "Some Title")
    assert p == (tmp_path / "x" / "note.md")


def test_resolve_target_vague_uses_category_and_slug(tmp_path):
    root = tmp_path / "KB"
    p = resolve_target(None, root, "tech", "My Answer")
    assert p == root / "tech" / "my-answer.md"


def test_resolve_target_dedups_existing(tmp_path):
    root = tmp_path / "KB"
    (root / "tech").mkdir(parents=True)
    (root / "tech" / "my-answer.md").write_text("x")
    p = resolve_target(None, root, "tech", "My Answer")
    assert p == root / "tech" / "my-answer-2.md"


def test_write_creates_parents(tmp_path):
    target = tmp_path / "a" / "b" / "c.md"
    out = write(target, "# hi")
    assert out.read_text() == "# hi"
