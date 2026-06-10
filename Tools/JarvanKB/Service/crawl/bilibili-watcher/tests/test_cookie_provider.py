import base64, hashlib, json
import httpx
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

from bilibili_watcher.cookie_provider import (
    derive_key, decrypt_payload, extract_bilibili_cookies, CookieProvider,
)
from bilibili_watcher.config import CookieSource


def _evp(pw, salt, klen, ivlen):
    d = b""; prev = b""
    while len(d) < klen + ivlen:
        prev = hashlib.md5(prev + pw + salt).digest(); d += prev
    return d[:klen], d[klen:klen + ivlen]


def _enc_legacy(plaintext: dict, the_key: str) -> str:
    salt = b"12345678"
    key, iv = _evp(the_key.encode(), salt, 32, 16)
    enc = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    pad = PKCS7(128).padder()
    body = pad.update(json.dumps(plaintext).encode()) + pad.finalize()
    ct = enc.update(body) + enc.finalize()
    return base64.b64encode(b"Salted__" + salt + ct).decode()


def test_derive_key():
    assert derive_key("u", "p") == hashlib.md5(b"u-p").hexdigest()[:16]


def test_decrypt_legacy_roundtrip():
    payload = {"cookie_data": {"bilibili.com": [{"name": "SESSDATA", "value": "abc"}]}}
    the_key = derive_key("u", "p")
    enc = _enc_legacy(payload, the_key)
    assert decrypt_payload(enc, "legacy", "u", "p") == payload


def test_extract_bilibili_cookies_no_dot():
    payload = {"cookie_data": {
        "bilibili.com": [{"name": "SESSDATA", "value": "s"}, {"name": "bili_jct", "value": "j"}],
        ".bilibili.com": [{"name": "OTHER", "value": "x"}],   # leading-dot domain must be IGNORED
        "zhihu.com": [{"name": "z_c0", "value": "z"}],
    }}
    out = extract_bilibili_cookies(payload)
    assert out == {"SESSDATA": "s", "bili_jct": "j"}


def test_provider_pulls_and_sends_auth_token():
    payload = {"cookie_data": {"bilibili.com": [{"name": "SESSDATA", "value": "s"}]}}
    enc = _enc_legacy(payload, derive_key("u", "p"))
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["token"] = request.headers.get("X-CookieCloud-Token")
        seen["path"] = request.url.path
        return httpx.Response(200, json={"encrypted": enc, "crypto_type": "legacy"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    src = CookieSource(base_url="http://box", uuid="u", password="p", auth_token="tok")
    cp = CookieProvider(src, http_client=client)
    assert cp.get_cookies() == {"SESSDATA": "s"}
    assert seen["token"] == "tok"
    assert seen["path"] == "/get/u"
