"""Active cookie pull from SP-1 cookie-manager + in-memory client-side decrypt.

Pull-only (SP-1 push permanently cancelled). Plaintext cookies live only in memory; never written to disk.
Decrypt protocol: Service/crawl/cookie-manager/docs/interface.md §3.
"""
from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass

import httpx
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


@dataclass
class CookieSource:
    base_url: str
    uuid: str
    password: str


def _the_key(uuid: str, password: str) -> str:
    return hashlib.md5(f"{uuid}-{password}".encode("utf-8")).hexdigest()[:16]


def _evp_bytes_to_key(passphrase: bytes, salt: bytes, key_len: int = 32, iv_len: int = 16):
    data = b""
    prev = b""
    while len(data) < key_len + iv_len:
        prev = hashlib.md5(prev + passphrase + salt).digest()
        data += prev
    return data[:key_len], data[key_len:key_len + iv_len]


def _decrypt_legacy(b64: str, the_key: str) -> bytes:
    raw = base64.b64decode(b64)
    if raw[:8] != b"Salted__":
        raise ValueError("legacy ciphertext missing OpenSSL Salted__ header")
    salt, ct = raw[8:16], raw[16:]
    key, iv = _evp_bytes_to_key(the_key.encode("utf-8"), salt)
    return unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(ct), AES.block_size)


def _decrypt_fixed(b64: str, the_key: str) -> bytes:
    key = the_key.encode("utf-8")[:16]
    ct = base64.b64decode(b64)
    return unpad(AES.new(key, AES.MODE_CBC, b"\x00" * 16).decrypt(ct), AES.block_size)


def decrypt(encrypted: str, crypto_type: str, uuid: str, password: str) -> dict:
    the_key = _the_key(uuid, password)
    if crypto_type == "aes-128-cbc-fixed":
        plaintext = _decrypt_fixed(encrypted, the_key)
    else:  # "legacy" (default)
        plaintext = _decrypt_legacy(encrypted, the_key)
    return json.loads(plaintext)


def pull(source: CookieSource, domain: str = ".zhihu.com", *, client: httpx.Client | None = None) -> dict[str, str]:
    url = f"{source.base_url.rstrip('/')}/get/{source.uuid}"
    owns = client is None
    c = client or httpx.Client(timeout=15.0)
    try:
        resp = c.get(url)
        resp.raise_for_status()
        blob = resp.json()
    finally:
        if owns:
            c.close()
    data = decrypt(blob["encrypted"], blob.get("crypto_type", "legacy"), source.uuid, source.password)
    cookies = data.get("cookie_data", {}).get(domain, [])
    return {ck["name"]: ck["value"] for ck in cookies}
