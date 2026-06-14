# credentials domain — cookie / session credential lifecycle

> Global architecture memory for the `credentials` domain. Activated 2026-05-31 by
> `RepoMem.merge` of `sp1-cookie-manager`. Concise summary + pointers only — module docs hold the
> detail (no-duplication invariant). Audience: A2A (English per `config.md`; new persist files are A2A).

## Scope

Lifecycle + refresh of the browser credentials (cookies / SESSDATA / site tokens) that the crawl SPs
consume. (Aliyun AK / OSS credentials are out of v1 scope — R5 switched ASR to BiliNote + bcut; see
`version-plan.md`.)

## SP-1 CookieManager — the cookie source of truth

- **What:** a self-written Node.js/TypeScript Express service speaking the **CookieCloud upload-API
  protocol**, so the *unmodified* official CookieCloud browser extension pushes cookies to it.
  Module: `Service/crawl/cookie-manager/`.
- **Why self-write, not fork (reusable pattern):** easychen/CookieCloud is **GPLv3 (copyleft), not MIT**.
  → **When an upstream you would fork is copyleft and its wire protocol is small (~tens of LOC),
  reimplement the protocol instead of forking** — keeps license freedom + full control; byte-for-byte
  compatibility is guaranteed by reusing the same `crypto-js` the extension uses.
- **Integration contract (downstream entry point):** `Service/crawl/cookie-manager/docs/interface.md`.
  Cookie-consuming SPs (SP-3 Zhihu Skill, SP-4b Bilibili Skill, SP-5a/5b watchers) integrate by **active
  PULL** (`cookie-manager show domain=<x>` / `GET /get/:uuid` then client-side decrypt per interface §3).
  **Decision (user-ratified 2026-06-02, cross-vertical — all crawl consumers): PULL is the sole delivery
  path; the SP-1 _push_ delivery path** (a `cookie-update`/`cron` hook landing plaintext cookies for
  consumers to read) **is permanently cancelled** — push left plaintext cookies on disk + a standing
  cross-module config dep, while pull decrypts transiently in-memory and keeps each consumer
  self-contained. SP-1's general hook engine (`exec`/`write_file`) stays as-is but **latent** (a future
  non-decrypting consumer would be a config entry, not new code — nothing removed from SP-1). This satisfies
  the consumers' "SP-1 协议敲定" entry condition.
- **Flow:** extension → `POST /update {uuid, encrypted, crypto_type?}` (AES; `legacy` = CryptoJS
  passphrase/`Salted__`, or `aes-128-cbc-fixed`) → file-per-uuid store → hook engine + CLI + `/get`.
- **Deployment / exposure:** local `127.0.0.1:48088` (JarvanKB **48xxx** service-port convention);
  public via frp → **`https://www.zhaoricheng.fun:48098`** (Nginx TLS, Let's Encrypt) + direct
  `http://101.35.46.114:48088`. Optional shared-secret header auth (`server.auth_token` →
  `X-CookieCloud-Token`). Real config `config/cookie-manager.yaml` holds secrets → gitignored.

### Host service-port convention — **48xxx** (ratified by root g4, 2026-06-14)

The canonical JarvanKB **listening**-service port block is **48000–48999**. (The user's literal ask was
"45xxx"; per the user's own fallback rule "if occupied, find another 4yxxx band", 45xxx is excluded —
`127.0.0.1:45397` is held by a foreign `node` listener — so 48xxx stands: it's the pre-existing convention,
zero-migration.) Binds **listening** services only; **watchers (SP-5a/5b) do NOT listen** (outbound pollers,
`network_mode: host`, no port map). Sub-allocation:

| Band | Layer | Used / planned |
|---|---|---|
| 48000–48099 | crawl | cookie-manager `48088` (local) + `48098` (frp public) — existing |
| 48100–48199 | engine | LLMService v2; BiliNote host-map optionally relocate `3015`→`481xx` (low-pri) |
| 48200–48299 | ingester / **mcp** | SP-6/SP-7 + the `Service/mcp/` façade, if they expose control/health |
| 48300–48399 | router/search | SP-8 |
| 48900–48999 | reserved / experimental | — |

ops-doc (`~/.ops-doc-maintainer-docs/hosts/<host>/rules.md`) already carries the 48xxx rule; the
sub-allocation table above is the formalized version (WatcherDeploy/ops impler may sync it there).

## Pointers

- Module decision log (full): `Service/crawl/cookie-manager/docs/RepoMem/decisions.md`
- Design: `Service/crawl/cookie-manager/docs/superpowers/specs/2026-05-31-SP-1-cookie-manager-design.md` (+ `.zh.md`)
- Verified protocol reference: `Service/crawl/cookie-manager/docs/RepoMem/temp/sp1-cookie-manager/research.md`
- Host ops (48xxx port rule, frp/frpc record): `~/.ops-doc-maintainer-docs/hosts/<host>/rules.md` + `manual-software.txt`

## Bilibili (SP-4a engine) — verified 2026-06-02

- **Cookie domain is `bilibili.com` (NO leading dot)** in the SP-1 cookie-manager store, NOT
  `.bilibili.com` as earlier assumed. Verified from the live store: the box holds `SESSDATA` + `bili_jct`
  (no `buvid3`). **Downstream SP-4b Skill / SP-5b Watcher must query `cookie-manager show domain=bilibili.com`**
  (or `GET /get/:uuid` then pick the `bilibili.com` entry) — `.bilibili.com` returns nothing.
- **What needs the cookie:** `bilibili-api-python.get_subtitle(cid)` requires `SESSDATA` (it *raises*
  `CredentialNoSessdataException` without one — does not return empty). `get_info` (metadata) works
  **without** any credential for public videos. So SP-4a's engine is usable cookie-less on public videos
  (metadata + bcut ASR); the subtitle-first path only engages when a valid SESSDATA is injected.
- **Engine contract:** SP-4a takes a structured `BilibiliCredential(sessdata, bili_jct?, buvid3?)` as
  INPUT (it never fetches cookies itself); SP-4b/5b inject it. See `Engine/bilibili/docs/interface.md`.

## Consumer-side decrypt — verified Python reference impl (SP-3, 2026-06-07)

The pull + client-side decrypt protocol (interface §3) now has a verified Python reference:
`Skill/crawl/zhihu-crawl/src/zhihu_crawl/cookie.py` — `the_key = md5(f"{uuid}-{password}").hexdigest()[:16]`;
`legacy` = OpenSSL `Salted__` + EVP_BytesToKey(MD5) → AES-256-CBC; `aes-128-cbc-fixed` = 16-byte key + zero
IV; cookies decrypted **in memory only, never persisted**. The `legacy` path is tested against real `openssl`
(interop). SP-4b/SP-5b reuse it with `domain=bilibili.com`; minor per-SP duplication of this small routine
is accepted in v1.

## Open / future

- Credential **refresh / keep-alive** strategy (handling cookie expiry) is deferred until the watchers
  (SP-5a/5b) run — pull-on-demand cadence is theirs to set (the push path is cancelled; see Integration contract above).
- Aliyun / OSS credentials: out of v1.
