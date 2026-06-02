from zhihu.parsers.html_scrape import scrape_body


def test_scrape_answer_richcontent():
    html = '<div class="RichContent-inner"><p>Scraped answer</p></div>'
    assert "Scraped answer" in scrape_body(html)


def test_scrape_article_post_richtext():
    html = '<div class="Post-RichText"><p>Scraped article</p></div>'
    assert "Scraped article" in scrape_body(html)


def test_scrape_returns_none_when_no_match():
    assert scrape_body("<div>nothing useful</div>") is None
