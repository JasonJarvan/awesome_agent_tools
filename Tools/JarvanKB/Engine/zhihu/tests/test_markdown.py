from zhihu.markdown import html_to_markdown, render_frontmatter

def test_basic_conversion():
    md = html_to_markdown("<p>Hello <strong>world</strong></p>")
    assert "Hello **world**" in md

def test_image_keeps_remote_url_no_download():
    md = html_to_markdown('<img src="https://pic.zhimg.com/x.jpg" alt="cap">')
    assert "https://pic.zhimg.com/x.jpg" in md
    assert "![" in md  # standard markdown image, not Obsidian embed
    assert "![[" not in md

def test_style_tags_stripped():
    md = html_to_markdown("<style>.x{}</style><p>kept</p>")
    assert ".x{}" not in md
    assert "kept" in md

def test_render_frontmatter():
    fm = render_frontmatter({"title": "T", "type": "answer", "source": "zhihu"})
    assert fm.startswith("---\n")
    assert "title: T" in fm
    assert fm.rstrip().endswith("---")
