"""List items in one Bilibili favorite folder via the public resource/list API.

Endpoint: GET https://api.bilibili.com/x/v3/fav/resource/list?media_id=&pn=&ps=20&order=mtime
Plain cookie (SESSDATA) + browser headers, NO signing (Stage-0 verified 2026-06-10). Direct connect
(trust_env=False; bilibili is a mainland site). order=mtime => medias sorted by fav_time DESC, so we
early-stop once an item's fav_time <= since_fav_time. Paging stops on data.has_more==False (NEVER on
media_count — it counts deleted/invalid items not returned; Stage-0 gotcha). Only type==2 (UGC video).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

log = logging.getLogger("bilibili_watcher.favorites_client")

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.bilibili.com/",
}


@dataclass
class BiliFavItem:
    bvid: str       # fed to engine.transcribe(bvid, ...)
    fav_time: int   # the collected-time (Stage-0: distinct from pubtime); watermark axis
    title: str      # fallback title (engine's metadata.title is authoritative)


class BilibiliFavApiError(Exception):
    def __init__(self, status: int, code, url: str):
        super().__init__(f"Bilibili fav API status={status} code={code} for {url}")
        self.status = status
        self.code = code
        self.url = url


def folder_id_from_url(url_or_id: str) -> str:
    # accepts a raw media_id or a .../fid<id> / ?fid= URL; config normally gives the bare id
    s = url_or_id.split("?")[0].rstrip("/").split("/")[-1]
    return s.replace("fid", "") if s.startswith("fid") else s


class FavoritesClient:
    def __init__(self, http_client: httpx.Client | None = None, page_size: int = 20):
        self._client = http_client or httpx.Client(
            trust_env=False, headers=_BROWSER_HEADERS, timeout=30.0
        )
        self._ps = page_size

    def list_items(
        self, folder_id_or_url: str, cookies: dict[str, str], since_fav_time: int = 0
    ) -> list[BiliFavItem]:
        folder_id = folder_id_from_url(folder_id_or_url)
        items: list[BiliFavItem] = []
        pn = 1
        while True:
            url = "https://api.bilibili.com/x/v3/fav/resource/list"
            params = {"media_id": folder_id, "pn": pn, "ps": self._ps,
                      "order": "mtime", "type": 0, "platform": "web"}
            resp = self._client.get(url, params=params, cookies=cookies)
            if resp.status_code != 200:
                raise BilibiliFavApiError(resp.status_code, None, str(resp.url))
            body = resp.json()
            if body.get("code") != 0:
                raise BilibiliFavApiError(resp.status_code, body.get("code"), str(resp.url))
            data = body.get("data") or {}
            medias = data.get("medias") or []
            for m in medias:
                ft = m.get("fav_time")
                bvid = m.get("bvid") or m.get("bv_id")
                if ft is None or not bvid:
                    continue                                  # malformed -> skip (don't stop)
                if ft <= since_fav_time:
                    log.info("folder %s: early-stop at fav_time=%s <= watermark=%s",
                             folder_id, ft, since_fav_time)
                    return items                              # all further items are older
                if m.get("type") != 2:
                    continue                                  # only UGC video
                items.append(BiliFavItem(bvid=bvid, fav_time=ft, title=str(m.get("title") or bvid)))
            if not data.get("has_more"):
                break
            pn += 1
        log.info("folder %s: listed %d new video item(s)", folder_id, len(items))
        return items
