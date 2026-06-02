from __future__ import annotations
import httpx

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

NAV_HEADERS = {
    "User-Agent": _UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.zhihu.com/",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Upgrade-Insecure-Requests": "1",
}

API_HEADERS = {
    "User-Agent": _UA,
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.zhihu.com/",
    "x-requested-with": "fetch",
}


def get_page(url: str, *, cookies: dict, timeout: float = 30.0) -> tuple[int, str]:
    """GET a Zhihu page as a browser navigation. Returns (status_code, text). Does not raise on 4xx."""
    resp = httpx.get(url, cookies=cookies, headers=NAV_HEADERS, timeout=timeout,
                     follow_redirects=True, trust_env=False)
    return resp.status_code, resp.text


def get_api_answer(answer_id: str, *, cookies: dict, timeout: float = 30.0) -> dict:
    """Unsigned /api/v4 answer fallback. Raises on non-2xx."""
    url = f"https://www.zhihu.com/api/v4/answers/{answer_id}?include=content"
    resp = httpx.get(url, cookies=cookies, headers=API_HEADERS, timeout=timeout,
                     follow_redirects=True, trust_env=False)
    resp.raise_for_status()
    return resp.json()
