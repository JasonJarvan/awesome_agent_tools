from zhihu._entities import entities, epoch_to_iso, parse_author

def test_entities_safe_on_none():
    assert entities(None) == {}
    assert entities({"initialState": {"entities": {"x": 1}}}) == {"x": 1}

def test_epoch_to_iso_valid_and_invalid():
    assert epoch_to_iso(1700000000).startswith("20")
    assert epoch_to_iso(1700000000).endswith("Z")
    assert epoch_to_iso(0) is None
    assert epoch_to_iso(None) is None
    assert epoch_to_iso("not-a-number") is None

def test_parse_author_url_and_headline():
    a = parse_author({"name": "Alice", "url_token": "alice", "headline": "dev"})
    assert a.name == "Alice"
    assert a.url == "https://www.zhihu.com/people/alice"
    assert a.headline == "dev"

def test_parse_author_none_and_no_token():
    assert parse_author(None) is None
    a = parse_author({"name": "NoToken"})
    assert a.url is None
    assert a.headline is None
