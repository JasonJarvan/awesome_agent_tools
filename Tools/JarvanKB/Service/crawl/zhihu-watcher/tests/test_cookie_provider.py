import httpx
import pytest
from zhihu_watcher.cookie_provider import (
    derive_key,
    decrypt_payload,
    extract_zhihu_cookies,
    CookieProvider,
)
from zhihu_watcher.config import CookieSource

# Known vectors (generated 2026-06-02, round-trip verified with `cryptography`).
# uuid="test-box-uuid", password="test-password" -> the_key="7f0b629578cb94ce"
# inner plaintext:
# {"cookie_data":{".zhihu.com":[{"name":"z_c0","value":"ZC0TOKEN"},
#  {"name":"d_c0","value":"DC0DEVID"}]},"local_storage_data":{},
#  "update_time":"2026-06-02T00:00:00Z"}
UUID = "test-box-uuid"
PASSWORD = "test-password"
LEGACY_ENC = (
    "U2FsdGVkX18BAgMEBQYHCKJedRci3iuczFZeVrfBOKug/+Yss9Tg/xdZnSBkCzRwMkYy"
    "rexR5JZr7Olk9bIIS57PteFYfqawOj9KklEJrCukYem2RoRyhh+JKIZGCo1Ou77/yrzF"
    "2z6QaCd0hMvlXRgf14BuLo3/s8//vedmEuVgG1vyIlhzaBKo2ZCFVHa3D/itWb7iet0g"
    "e9446yKImum9etaJ5O1jbSjBAEpPFaCGEttB4mcisg3wMQNqn6Wm"
)
FIXED_ENC = (
    "kyIjmJjByCjZqPaocBuQa8u0ETzs8iT/Ws11uvwGs5BHdY1BeNDQsOWm67tx11IttqpZ"
    "Mee0uoLPf0NFC3mpXsauK5cuccJ4F8y9SbzL3Q725FSzK+gBXyZRitWMaDBOH9d+RWy2"
    "EdLCTp5SVDh33dmWUxwQjsdkRgrxqAI1eFBi+NuuM0gipUx2Ws4P0k9GXFd2Tgn3YrRz"
    "AGJ6WG3DBsOGEuiCopuX3t3BSfv87S8="
)


def test_derive_key():
    assert derive_key(UUID, PASSWORD) == "7f0b629578cb94ce"


def test_decrypt_legacy():
    payload = decrypt_payload(LEGACY_ENC, "legacy", UUID, PASSWORD)
    assert payload["cookie_data"][".zhihu.com"][0]["name"] == "z_c0"


def test_decrypt_fixed():
    payload = decrypt_payload(FIXED_ENC, "aes-128-cbc-fixed", UUID, PASSWORD)
    assert payload["cookie_data"][".zhihu.com"][1]["value"] == "DC0DEVID"


def test_unknown_crypto_type_raises():
    with pytest.raises(ValueError, match="crypto_type"):
        decrypt_payload(FIXED_ENC, "rot13", UUID, PASSWORD)


def test_extract_zhihu_cookies_merges_zhihu_domains():
    payload = {
        "cookie_data": {
            ".zhihu.com": [{"name": "z_c0", "value": "A"}],
            "www.zhihu.com": [{"name": "d_c0", "value": "B"}],
            ".other.com": [{"name": "x", "value": "C"}],
        }
    }
    out = extract_zhihu_cookies(payload)
    assert out == {"z_c0": "A", "d_c0": "B"}


def test_provider_get_cookies_end_to_end():
    src = CookieSource(base_url="http://sp1.local", uuid=UUID, password=PASSWORD)

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == f"/get/{UUID}"
        return httpx.Response(200, json={"encrypted": LEGACY_ENC, "crypto_type": "legacy"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = CookieProvider(src, http_client=client)
    cookies = provider.get_cookies()
    assert cookies == {"z_c0": "ZC0TOKEN", "d_c0": "DC0DEVID"}
