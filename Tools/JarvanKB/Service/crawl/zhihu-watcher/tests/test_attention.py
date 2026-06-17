from pathlib import Path

from zhihu_watcher.attention import write_attention

ATT = "_zhihu-watcher-attention.md"


def test_empty_writes_nothing_needs_attention(tmp_path):
    path = write_attention(str(tmp_path), [])
    text = Path(path).read_text(encoding="utf-8")
    assert "nothing needs attention" in text


def test_renders_broken_entries_with_links_and_cause_hint(tmp_path):
    broken = [
        {"collection": "我的收藏", "key": "article:12", "url": "https://zhuanlan.zhihu.com/p/12",
         "title": "专栏标题", "excerpt": "开头…", "failures": 10},
        {"collection": "我的收藏", "key": "answer:11", "url": "https://www.zhihu.com/question/1/answer/11",
         "title": "答案标题", "excerpt": "正文…", "failures": 12},
    ]
    path = write_attention(str(tmp_path), broken)
    text = Path(path).read_text(encoding="utf-8")
    assert "https://zhuanlan.zhihu.com/p/12" in text
    assert "专栏标题" in text and "答案标题" in text
    assert "10" in text and "12" in text             # failure counts shown
    assert "__zse_ck" in text                        # 专栏 cause hint present


def test_overwrites_each_call(tmp_path):
    write_attention(str(tmp_path), [
        {"collection": "x", "key": "answer:1", "url": "u1", "title": "A", "excerpt": "", "failures": 10}])
    path = write_attention(str(tmp_path), [])          # second render: now empty
    text = Path(path).read_text(encoding="utf-8")
    assert "answer:1" not in text                      # integral overwrite, no stale rows
    assert "nothing needs attention" in text
