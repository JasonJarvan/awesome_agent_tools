import base64
import json
import subprocess

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from zhihu_crawl.cookie import CookieSource, decrypt, pull, _the_key


UUID = "test-uuid"
PW = "test-password"
PLAINTEXT = {
    "cookie_data": {".zhihu.com": [
        {"name": "z_c0", "value": "ZZZ"},
        {"name": "d_c0", "value": "DDD"},
    ]},
    "local_storage_data": {},
    "update_time": "2026-06-05T00:00:00Z",
}


def _enc_fixed(plaintext: bytes, the_key: str) -> str:
    key = the_key.encode("utf-8")[:16]
    ct = AES.new(key, AES.MODE_CBC, b"\x00" * 16).encrypt(pad(plaintext, 16))
    return base64.b64encode(ct).decode()


def _enc_legacy_via_openssl(plaintext: bytes, the_key: str) -> str:
    # Reference encryptor = OpenSSL, matching CryptoJS Salted__ + EVP_BytesToKey(MD5).
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


def test_pull_returns_name_value_dict(monkeypatch):
    the_key = _the_key(UUID, PW)
    enc = _enc_fixed(json.dumps(PLAINTEXT).encode(), the_key)

    class FakeResp:
        def raise_for_status(self): pass
        def json(self): return {"encrypted": enc, "crypto_type": "aes-128-cbc-fixed"}

    class FakeClient:
        def get(self, url): assert url.endswith("/get/test-uuid"); return FakeResp()

    src = CookieSource(base_url="http://127.0.0.1:48088", uuid=UUID, password=PW)
    cookies = pull(src, client=FakeClient())
    assert cookies == {"z_c0": "ZZZ", "d_c0": "DDD"}
