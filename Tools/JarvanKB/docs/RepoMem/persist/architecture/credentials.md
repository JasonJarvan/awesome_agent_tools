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
  Cookie-consuming SPs (SP-3 Zhihu Skill, SP-4b Bilibili Skill, SP-5a/5b watchers) integrate against that
  file — either **push** (configure a T1 `cookie-update` / T2 `cron` hook → `exec` / `write_file`) or
  **pull** (`cookie-manager show domain=<x>` / `GET /get/:uuid` then decrypt). This is what satisfies
  their "SP-1 协议敲定" entry condition.
- **Flow:** extension → `POST /update {uuid, encrypted, crypto_type?}` (AES; `legacy` = CryptoJS
  passphrase/`Salted__`, or `aes-128-cbc-fixed`) → file-per-uuid store → hook engine + CLI + `/get`.
- **Deployment / exposure:** local `127.0.0.1:48088` (JarvanKB **48xxx** service-port convention);
  public via frp → **`https://www.zhaoricheng.fun:48098`** (Nginx TLS, Let's Encrypt) + direct
  `http://101.35.46.114:48088`. Optional shared-secret header auth (`server.auth_token` →
  `X-CookieCloud-Token`). Real config `config/cookie-manager.yaml` holds secrets → gitignored.

## Pointers

- Module decision log (full): `Service/crawl/cookie-manager/docs/RepoMem/decisions.md`
- Design: `Service/crawl/cookie-manager/docs/superpowers/specs/2026-05-31-SP-1-cookie-manager-design.md` (+ `.zh.md`)
- Verified protocol reference: `Service/crawl/cookie-manager/docs/RepoMem/temp/sp1-cookie-manager/research.md`
- Host ops (48xxx port rule, frp/frpc record): `~/.ops-doc-maintainer-docs/hosts/<host>/rules.md` + `manual-software.txt`

## Open / future

- Credential **refresh / keep-alive** strategy (handling cookie expiry) is deferred until the watchers
  (SP-5a/5b) run — they decide push-hook vs pull cadence.
- Aliyun / OSS credentials: out of v1.
