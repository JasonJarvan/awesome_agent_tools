from pathlib import Path
from bilibili_watcher.saver import save, sanitize_title


def test_sanitize_title():
    assert sanitize_title('a/b\\c"d<e>f|g') == "a b c d e f g"
    assert sanitize_title("what? yes: no") == "what？ yes： no"
    assert sanitize_title("   ") == "untitled"


def test_save_layout_and_content(tmp_path):
    path = save(str(tmp_path), "AI生成", "Hello World", "BV1xx", "## body\n")
    p = Path(path)
    assert p.parent.name == "AI生成"
    assert p.name == "Hello World.md"
    assert p.read_text(encoding="utf-8") == "> https://www.bilibili.com/video/BV1xx\n## body\n"


def test_collision_appends_bvid(tmp_path):
    save(str(tmp_path), "f", "Same", "BV1", "a\n")
    second = save(str(tmp_path), "f", "Same", "BV2", "b\n")
    assert Path(second).name == "Same_BV2.md"
