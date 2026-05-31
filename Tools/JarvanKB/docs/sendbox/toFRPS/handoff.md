---
from: sp1impler (JarvanKB session, client host shenzhou-CW35S)
to: frps-admin-ai (host 101.35.46.114, the frps server)
type: handoff
slug: sp1-cookie-manager-frp-expose
status: open
created: 2026-05-31
delivery: user relays this letter to the AI on the frps host
lifecycle: burn after frps-side change applied + confirmation relayed back
---

# Handoff → frps admin AI: allow remotePort 48088 for JarvanKB cookie-manager

You administer the **frps server at `101.35.46.114:10086`** (token auth + TLS). A client wants to
expose a new TCP proxy through you. The **client side is already fully configured and verified** —
the only thing missing is a **server-side `allowPorts` permission** for the new remote port.

## What the client already did (no action needed from you on these)

- Host `shenzhou-CW35S` (LAN `192.168.31.251`) runs `frpc` **v0.67.0** as systemd `frpc.service`,
  connecting to you at `101.35.46.114:10086` (token auth, `transport.tls.enable = true`).
- Existing working proxies (DO NOT TOUCH): `ssh`→remote `52222`, `9700-cloudui`→`53101`,
  `shenzhou-linux-cloudui`→`53102`.
- A NEW proxy block was appended to the client config (`~/Codes/Infra/frpc/frpc.toml`), syntax verified
  with `frpc verify` (OK):

  ```toml
  [[proxies]]
  name = "jarvankb-cookie-manager"
  type = "tcp"
  localIP = "127.0.0.1"
  localPort = 48088        # local service: JarvanKB SP-1 cookie-manager (CookieCloud-protocol cookie sync)
  remotePort = 48088       # desired public port on your frps host
  ```

## The ask (frps-side, the ONLY change needed)

Make frps **accept TCP `remotePort = 48088`**. The existing proxies all use 5xxxx ports, which suggests
your `allowPorts` is restricted to a 5xxxx range — if so, the client's `48088` proxy will be rejected at
registration ("port not allowed in allowPorts") unless you widen it.

1. In your **`frps.toml`**, ADD `48088` (recommended: the whole **48000–48999** range, to future-proof other
   JarvanKB services that follow the project's 48xxx port convention) to `allowPorts`, **keeping all
   existing entries**. frp 0.67 syntax:

   ```toml
   allowPorts = [
     # ... keep your existing ranges/entries (e.g. the 5xxxx range covering 52222/53101/53102) ...
     { start = 48000, end = 48999 },
   ]
   ```

   - If `allowPorts` is currently **unset** (all ports allowed), no change is needed — just confirm,
     because then 48088 already works.
   - If you prefer NOT to open 48088, tell us **which port/range IS allowed** and the client will switch
     its `remotePort` to match (and update the browser-extension URL accordingly).

2. Reload/restart frps: `sudo systemctl restart frps` (or your process manager / `frps reload` if enabled).

3. Leave `serverPort 10086`, the auth token, and `transport.tls` unchanged — the client depends on them.

## Verification (after you reload frps AND the client restarts frpc)

- frps log: proxy `jarvankb-cookie-manager` registers with no `port not allowed` error.
- On the frps host: `ss -tlnp | grep 48088` → frps listening on `0.0.0.0:48088`.
- End-to-end (once the client also starts its service + frpc): `curl -s http://101.35.46.114:48088/health`
  → `{"status":"ok"}`.

## Security note (please consider on your side)

This publicly exposes a **cookie-sync endpoint**. App-layer mitigations exist (payloads are AES-encrypted;
`/update` carries only `{uuid, encrypted}`; the password never transits), but there is **no transport-level
auth** for a plain TCP proxy. If your frps host has a firewall or frp supports per-proxy connection/bandwidth
limits, consider light rate-limiting on `48088`. Source-IP allowlisting is usually infeasible (mobile/cellular).

## Please reply with

(a) whether `allowPorts` now permits `48088` (or the 48xxx range), (b) that frps was reloaded, (c) that
port `48088` is listening — OR, if 48088 can't be opened, the allowed port/range so the client switches
`remotePort`. The user relays your reply back to the JarvanKB (client) session.
