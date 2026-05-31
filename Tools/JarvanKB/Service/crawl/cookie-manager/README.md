# cookie-manager (SP-1)

CookieCloud-protocol-compatible cookie sync service with a hook engine and CLI.
Reuse the **official CookieCloud browser extension unchanged** — just point its
server address at this service.

## Setup
1. Install the official CookieCloud extension (PC Chrome / Android Kiwi or Yandex).
2. In the extension: set **server address** to one of the Access endpoints below, pick a
   **UUID** and **password** (the password is an encryption passphrase, not a login).
3. Copy `config/cookie-manager.example.yaml` to `config/cookie-manager.yaml`; fill
   `accounts` with the same uuid + password, and configure `hooks`.
4. `docker compose up -d` (or `npm run build && COOKIE_MANAGER_CONFIG=config/cookie-manager.yaml npm start`).
   The service listens on `127.0.0.1:48088` (JarvanKB 48xxx port convention).

## Access endpoints
- **LAN:** `http://192.168.31.251:48088`
- **Public — HTTPS (recommended):** `https://www.zhaoricheng.fun:48098` — Nginx TLS (Let's Encrypt)
  → frps (`101.35.46.114`) → frpc proxy `jarvankb-cookie-manager` (remotePort 48088) → this service.
- **Public — direct HTTP:** `http://101.35.46.114:48088` — works but no transport TLS; prefer HTTPS.

(frp client config: `~/Codes/Infra/frpc/frpc.toml`; after editing it run `sudo systemctl restart frpc`.)

## Security
**Recommended for public exposure — shared-secret header auth.** Set `server.auth_token` in config; then
every request except `/health` must carry `X-CookieCloud-Token: <token>` (401 otherwise, checked before
body parsing). In the CookieCloud extension's **请求Header** field add ONE line, no spaces:
`X-CookieCloud-Token:<token>`. This blocks unauthenticated scanners from `/update` (poisoning) and `/get`
(blob retrieval) entirely — defense-in-depth on top of uuid+password. Leave `auth_token` empty to disable
(LAN-only). The header *name* (`auth_header`) defaults to `X-CookieCloud-Token`; usually leave it.

The protocol's base protection is uuid+password obscurity → also use a **long random uuid + strong password**.
Cookies are end-to-end AES-encrypted and `/update` carries only `{uuid, encrypted}` (the password never
transits), so the payload is safe even over plain HTTP. When reaching the service over the public internet,
**prefer the HTTPS endpoint (`:48098`)** — especially for any `/get?password=` call, whose password would
otherwise cross the network in cleartext. Residual risk: anyone who learns your uuid can `POST /update`, but
without the password they cannot forge a blob that decrypts (the engine logs the failure and skips) — worst
case overwrites your stored blob with garbage until the extension re-pushes. Decrypt/inspect (`show`/`dump`)
locally via the CLI, not over the public endpoint.

## CLI
- `cookie-manager list`
- `cookie-manager show domain=.zhihu.com`
- `cookie-manager dump [--uuid=<u>]`

## Hooks
Triggers: `cookie-update` (T1), `cron` (T2). Actions: `exec` (A1), `write_file` (A3).
Template vars: `{{uuid}} {{domain}} {{cookie_json}} {{encrypted}} {{crypto_type}} {{update_time}} {{ts}}`.
`{{cookie_json}}` is the matched domain's cookie array when `match.domain` is set; otherwise the full `cookie_data` map (domain → cookies).
See `config/cookie-manager.example.yaml`.
