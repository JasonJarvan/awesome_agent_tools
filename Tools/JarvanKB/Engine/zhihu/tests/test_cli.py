import json
from pathlib import Path
from conftest import load_fixture
from zhihu import cli

def test_cli_outputs_markdown(httpx_mock, capsys, tmp_path):
    httpx_mock.add_response(url="https://www.zhihu.com/question/123/answer/456",
                            text=load_fixture("answer_page.html"), status_code=200)
    cookies_file = tmp_path / "c.json"
    cookies_file.write_text(json.dumps([{"name": "d_c0", "value": "x"}]), encoding="utf-8")
    rc = cli.main(["https://www.zhihu.com/question/123/answer/456",
                   "--cookies", str(cookies_file)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Engine body" in out
    assert "source: zhihu" in out
