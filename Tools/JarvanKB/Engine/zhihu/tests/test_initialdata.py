from conftest import load_fixture
from zhihu.initialdata import extract_initial_data

def test_extract_parses_blob():
    data = extract_initial_data(load_fixture("initialdata_min.html"))
    assert data["initialState"]["entities"]["answers"]["456"]["content"] == "<p>hello</p>"

def test_extract_returns_none_when_absent():
    assert extract_initial_data("<html><body>no script</body></html>") is None
