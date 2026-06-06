"""Pull the latest .zhihu.com cookies from SP-1 CookieManager and decrypt them in memory.

Cookies are NEVER written to disk; only returned as a transient dict for fetch(cookies=...).
Mirrors the CookieCloud crypto protocol documented in
Service/crawl/cookie-manager/docs/interface.md §3.
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging

import httpx
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

from .config import CookieSource

log = logging.getLogger("zhihu_watcher.cookie_provider")


def derive_key(uuid: str, password: str) -> str:
    """the_key = md5(uuid + '-' + password).hex[:16] (UTF-8, literal hyphen)."""
    return hashlib.md5(f"{uuid}-{password}".encode("utf-8")).hexdigest()[:16]


def _evp_bytes_to_key(pw: bytes, salt: bytes, key_len: int, iv_len: int) -> tuple[bytes, bytes]:
    """OpenSSL EVP_BytesToKey with MD5 (1 iteration), as crypto-js / OpenSSL use."""
    d = b""
    prev = b""
    while len(d) < key_len + iv_len:
        prev = hashlib.md5(prev + pw + salt).digest()
        d += prev
    return d[:key_len], d[key_len:key_len + iv_len]


def _aes_cbc_decrypt(key: bytes, iv: bytes, ct: bytes) -> bytes:
    decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    padded = decryptor.update(ct) + decryptor.finalize()
    unpadder = PKCS7(128).unpadder()
    return unpadder.update(padded) + unpadder.finalize()


def decrypt_legacy(encrypted: str, the_key: str) -> dict:
    """OpenSSL 'Salted__' envelope + EVP_BytesToKey(MD5) + AES-256-CBC + PKCS7."""
    raw = base64.b64decode(encrypted)
    if raw[:8] != b"Salted__":
        raise ValueError("legacy ciphertext is not a 'Salted__' envelope")
    salt = raw[8:16]
    ct = raw[16:]
    key, iv = _evp_bytes_to_key(the_key.encode("utf-8"), salt, 32, 16)
    return json.loads(_aes_cbc_decrypt(key, iv, ct).decode("utf-8"))


def decrypt_fixed(encrypted: str, the_key: str) -> dict:
    """aes-128-cbc-fixed: 16-byte key = the_key UTF-8, zero IV, AES-128-CBC + PKCS7, bare base64."""
    ct = base64.b64decode(encrypted)
    key = the_key.encode("utf-8")
    iv = b"\x00" * 16
    return json.loads(_aes_cbc_decrypt(key, iv, ct).decode("utf-8"))


def decrypt_payload(encrypted: str, crypto_type: str, uuid: str, password: str) -> dict:
    the_key = derive_key(uuid, password)
    if crypto_type == "legacy":
        return decrypt_legacy(encrypted, the_key)
    if crypto_type == "aes-128-cbc-fixed":
        return decrypt_fixed(encrypted, the_key)
    raise ValueError(f"unknown crypto_type: {crypto_type!r}")


def extract_zhihu_cookies(payload: dict) -> dict[str, str]:
    """Merge cookies from every domain whose key ends with 'zhihu.com'."""
    out: dict[str, str] = {}
    for domain, cookies in (payload.get("cookie_data") or {}).items():
        if str(domain).endswith("zhihu.com"):
            for c in cookies:
                out[c["name"]] = c["value"]
    return out


class CookieProvider:
    def __init__(self, cookie_source: CookieSource, http_client: httpx.Client | None = None):
        self._src = cookie_source
        # trust_env=False: SP-1 is a local/mainland service reached direct — do NOT pick up the
        # host's overseas proxy env (ALL_PROXY/HTTP_PROXY). Same stance as favorites_client + §知乎链路.
        self._client = http_client or httpx.Client(timeout=30.0, trust_env=False)

    def get_cookies(self) -> dict[str, str]:
        url = f"{self._src.base_url.rstrip('/')}/get/{self._src.uuid}"
        resp = self._client.get(url)
        resp.raise_for_status()
        body = resp.json()
        payload = decrypt_payload(
            body["encrypted"],
            body.get("crypto_type", "legacy"),
            self._src.uuid,
            self._src.password,
        )
        cookies = extract_zhihu_cookies(payload)
        log.info("pulled %d .zhihu.com cookies from SP-1", len(cookies))
        return cookies
