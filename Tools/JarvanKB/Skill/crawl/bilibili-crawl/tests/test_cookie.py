import base64
import json
import subprocess

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from bilibili_crawl.cookie import CookieSource, build_credential, decrypt, pull, _the_key


UUID = "test-uuid"
PW = "test-password"
PLAINTEXT = {
    "cookie_data": {"bilibili.com": [
        {"name": "SESSDATA", "value": "SSS"},
        {"name": "bili_jct", "value": "JJJ"},
    ]},
    "local_storage_data": {},
    "update_time": "2026-06-07T00:00:00Z",
}


def _enc_fixed(plaintext: bytes, the_key: str) -> str:
    key = the_key.encode("utf-8")[:16]
    ct = AES.new(key, AES.MODE_CBC, b"\x00" * 16).encrypt(pad(plaintext, 16))
    return base64.b64encode(ct).decode()


def _enc_legacy_via_openssl(plaintext: bytes, the_key: str) -> str:
    out = subprocess.run(
        ["openssl", "enc", "-aes-256-cbc", "-md", "md5", "-salt",
         "-pass", f"pass:{the_key}", "-base64", "-A"],
        input=plaintext, capture_output=True, check=True,
    ).stdout
    return out.decode().strip()


def test_decrypt_fixed_roundtrip():
    the_key = _the_key(UUID, PW)
    enc = _enc_fixed(json.dumps(PLAINTEXT).encode(), the_key)
    assert decrypt(enc, "aes-128-cbc-fixed", UUID, PW) == PLAINTEXT


def test_decrypt_legacy_against_openssl():
    the_key = _the_key(UUID, PW)
    enc = _enc_legacy_via_openssl(json.dumps(PLAINTEXT).encode(), the_key)
    assert decrypt(enc, "legacy", UUID, PW) == PLAINTEXT


def test_pull_picks_bilibili_dot_com_no_dot(monkeypatch):
    the_key = _the_key(UUID, PW)
    enc = _enc_fixed(json.dumps(PLAINTEXT).encode(), the_key)

    class FakeResp:
        def raise_for_status(self): pass
        def json(self): return {"encrypted": enc, "crypto_type": "aes-128-cbc-fixed"}

    class FakeClient:
        def get(self, url): assert url.endswith("/get/test-uuid"); return FakeResp()

    src = CookieSource(base_url="http://127.0.0.1:48088", uuid=UUID, password=PW)
    cookies = pull(src, client=FakeClient())   # default domain == "bilibili.com"
    assert cookies == {"SESSDATA": "SSS", "bili_jct": "JJJ"}


def test_build_credential_maps_sessdata():
    cred = build_credential({"SESSDATA": "SSS", "bili_jct": "JJJ"})
    assert cred is not None
    assert cred.sessdata == "SSS"
    assert cred.bili_jct == "JJJ"
    assert cred.buvid3 is None


def test_build_credential_none_without_sessdata():
    assert build_credential({"bili_jct": "JJJ"}) is None
    assert build_credential({}) is None
