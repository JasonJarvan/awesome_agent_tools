from pathlib import Path
from zhihu_watcher.saver import save, sanitize_title


def test_sanitize_title_rules():
    assert sanitize_title('a/b\\c"d<e>f|g') == "a b c d e f g"
    assert sanitize_title("what?") == "what？"
    assert sanitize_title("ratio 1:2") == "ratio 1：2"
    assert sanitize_title("   ") == "untitled"


def test_save_writes_url_prefixed_markdown_no_frontmatter(tmp_path):
    path = save(str(tmp_path), "AI-papers", "Hello World",
                "https://www.zhihu.com/question/1/answer/2", "# body\ntext")
    p = Path(path)
    assert p == tmp_path / "AI-papers" / "Hello World.md"
    content = p.read_text(encoding="utf-8")
    assert content.startswith("> https://www.zhihu.com/question/1/answer/2\n")
    assert "# body\ntext" in content
    assert not content.startswith("---")   # no YAML frontmatter


def test_collision_appends_url_id(tmp_path):
    save(str(tmp_path), "c", "Dup", "https://www.zhihu.com/answer/100", "first")
    second = save(str(tmp_path), "c", "Dup", "https://www.zhihu.com/answer/200", "second")
    assert Path(second).name == "Dup_200.md"
    assert (tmp_path / "c" / "Dup.md").read_text(encoding="utf-8").endswith("first\n") or \
           "first" in (tmp_path / "c" / "Dup.md").read_text(encoding="utf-8")


def test_remote_image_urls_preserved(tmp_path):
    body = "![pic](https://pic.zhimg.com/x.jpg)"
    path = save(str(tmp_path), "c", "WithImg", "https://www.zhihu.com/p/1", body)
    assert "https://pic.zhimg.com/x.jpg" in Path(path).read_text(encoding="utf-8")
