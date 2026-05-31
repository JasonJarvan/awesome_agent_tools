# cookie-manager (SP-1)

CookieCloud-protocol-compatible cookie sync service with a hook engine and CLI.
Reuse the **official CookieCloud browser extension unchanged** — just point its
server address at this service.

## Setup
1. Install the official CookieCloud extension (PC Chrome / Android Kiwi or Yandex).
2. In the extension: set **server address** to `http://<this-host>:8088`, pick a
   **UUID** and **password** (the password is an encryption passphrase, not a login).
3. Copy `config/cookie-manager.example.yaml` to `config/cookie-manager.yaml`; fill
   `accounts` with the same uuid + password, and configure `hooks`.
4. `docker compose up -d` (or `npm run build && npm start`).

## Security
The protocol's only protection is uuid+password obscurity. **Run behind LAN/VPN/
reverse proxy; do not expose the port to the public internet.**

## CLI
- `cookie-manager list`
- `cookie-manager show domain=.zhihu.com`
- `cookie-manager dump [--uuid=<u>]`

## Hooks
Triggers: `cookie-update` (T1), `cron` (T2). Actions: `exec` (A1), `write_file` (A3).
Template vars: `{{uuid}} {{domain}} {{cookie_json}} {{encrypted}} {{crypto_type}} {{update_time}} {{ts}}`.
See `config/cookie-manager.example.yaml`.
