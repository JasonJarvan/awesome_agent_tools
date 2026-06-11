#!/usr/bin/env python3
"""BN-412 prevention: sync the bilibili cookie from SP-1 cookie-manager into BiliNote.

Why this exists (BN-412, 2026-06-11): bilibili's playurl API returns HTTP 412 for
anonymous (cookie-less) requests, and BiliNote's BilibiliDownloader is an import-time
singleton that reads its cookie store ONCE at process start — so a rotated SESSDATA
never reaches the live process until the container restarts. This script closes the
loop from the host (SP-1 runs in docker without docker.sock and cannot reach BN's
host-loopback port, so an SP-1 exec hook structurally cannot do this).

Run from host cron (the BN-owner host). Idempotent: compares the pulled SESSDATA
against BiliNote's stored one and exits silently when unchanged. Only the SESSDATA
VALUE is compared — the frozen engine best-effort re-pushes the cookie in its own
format on every ASR run, so comparing the full cookie string would flap.

Never logs cookie values.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request

import yaml

REPO_ROOT = "/home/shenzhou/Codes/awesome_agent_tools/Tools/JarvanKB"
CM_CONFIG = os.path.join(REPO_ROOT, "Service/crawl/cookie-manager/config/cookie-manager.yaml")
CM_BASE_URL = "http://127.0.0.1:48088"
BN_BASE_URL = "http://127.0.0.1:3015"
BN_CONTAINER = "jarvankb-bilinote"
BN_STORE = "/app/backend/config/downloader.json"
COOKIE_KEYS = ["SESSDATA", "bili_jct", "buvid3", "DedeUserID", "DedeUserID__ckMd5"]
HEALTH_TIMEOUT_S = 60

sys.path.insert(0, os.path.join(REPO_ROOT, "Skill/crawl/bilibili-crawl/src"))


def log(msg: str) -> None:
    print(f"{time.strftime('%Y-%m-%dT%H:%M:%S%z')} {msg}", flush=True)


def pull_cookies() -> dict[str, str]:
    from bilibili_crawl.cookie import CookieSource, pull  # PyCryptodome decrypt, in-memory only
    with open(CM_CONFIG, encoding="utf-8") as f:
        acct = yaml.safe_load(f)["accounts"][0]
    return pull(CookieSource(base_url=CM_BASE_URL, uuid=acct["uuid"], password=acct["password"]))


def bn_stored_sessdata() -> str | None:
    out = subprocess.run(
        ["docker", "exec", BN_CONTAINER, "cat", BN_STORE],
        capture_output=True, text=True, timeout=30,
    )
    if out.returncode != 0:
        log(f"WARN cannot read BN store: {out.stderr.strip()[:200]}")
        return None
    cookie = json.loads(out.stdout).get("bilibili", {}).get("cookie", "")
    for pair in cookie.split("; "):
        if pair.startswith("SESSDATA="):
            return pair.split("=", 1)[1]
    return None


def push_cookie(cookie_str: str) -> None:
    req = urllib.request.Request(
        f"{BN_BASE_URL}/api/update_downloader_cookie",
        data=json.dumps({"platform": "bilibili", "cookie": cookie_str}).encode(),
        headers={"Content-Type": "application/json"},
    )
    body = json.load(urllib.request.urlopen(req, timeout=15))
    if body.get("code") != 0:
        raise RuntimeError(f"BN cookie push rejected: {body}")


def restart_bn() -> None:
    subprocess.run(["docker", "restart", BN_CONTAINER], check=True, capture_output=True, timeout=120)
    deadline = time.time() + HEALTH_TIMEOUT_S
    while time.time() < deadline:
        try:
            body = json.load(urllib.request.urlopen(f"{BN_BASE_URL}/api/sys_check", timeout=5))
            if body.get("code") == 0:
                log("BN restarted and healthy")
                return
        except Exception:
            pass
        time.sleep(3)
    raise RuntimeError(f"BN not healthy {HEALTH_TIMEOUT_S}s after restart")


def main() -> int:
    force = "--force" in sys.argv
    # Local services only — never let a host SOCKS/HTTP proxy intercept loopback calls.
    for var in ("ALL_PROXY", "all_proxy", "HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy"):
        os.environ.pop(var, None)

    cookies = pull_cookies()
    fresh = cookies.get("SESSDATA")
    if not fresh:
        log("WARN SP-1 has no bilibili SESSDATA; leaving BN untouched")
        return 1

    stored = bn_stored_sessdata()
    if fresh == stored and not force:
        return 0  # silent no-op: nothing rotated

    cookie_str = "; ".join(f"{k}={cookies[k]}" for k in COOKIE_KEYS if cookies.get(k))
    log(f"SESSDATA {'forced resync' if fresh == stored else 'rotation detected'}; pushing to BN + restarting")
    push_cookie(cookie_str)
    restart_bn()
    return 0


if __name__ == "__main__":
    sys.exit(main())
