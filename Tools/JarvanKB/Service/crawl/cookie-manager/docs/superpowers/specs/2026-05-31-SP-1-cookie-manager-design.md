# SP-1 CookieManager — Design

> Status: Stage 1 design (brainstorming output). Audience: A2A (English per `docs/RepoMem/persist/config.md`).
> Chinese translation (H2A, for the user): `2026-05-31-SP-1-cookie-manager-design.zh.md` — keep in sync on edits.
> Temp location per handoff §3.B; `git mv` into `Service/crawl/cookie-manager/docs/superpowers/specs/` at Stage 3 start.
> Verified protocol facts + path analysis: `docs/RepoMem/temp/sp1-cookie-manager/research.md`.
> Parent context: `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` §7 (SP-1 entry, dependency graph).

## 1. Context & scope

CookieManager (SP-1) is the **hard prerequisite for every cookie-dependent sub-project**
(SP-3 Zhihu Skill, SP-4b Bilibili Skill, SP-5a/5b watchers — see SP-0 §7 dependency graph).
It receives browser cookies pushed by the **unmodified official CookieCloud browser extension**,
stores them, and fires user-configured hooks so downstream crawlers can refresh their cookies.

### In scope (v1)

| Deliver | Defer (v1+) |
|---|---|
| CookieCloud upload-API-compatible receiver service (legacy + aes-128-cbc-fixed modes) | WebUI (mobile/iOS fallback) |
| Hook engine: T1 (cookie-update) + T2 (cron) triggers → A1 (exec shell) + A3 (write_file template) actions | A2 HTTP webhook action |
| CLI: `list` / `show domain=<x>` / `dump` | — |
| Docker compose deployment, **MIT** license | fork / patch of the browser extension (we reuse it unchanged) |
| — | any LLM call (CookieManager is a pure protocol service) |

### Out of scope (forbidden / non-goals)

- We do **not** fork or modify the browser extension. We implement only the **server half**
  of the CookieCloud HTTP+crypto wire protocol; the user repoints the official extension's
  "server address" to our service.
- No multi-tenant accounts/auth system. Single-user (the operator), 1..N CookieCloud boxes.

## 2. Key decisions

| # | Decision | Rationale |
|---|---|---|
| D1 | **Path B — self-write Express service** (NOT fork easychen/CookieCloud) | Upstream is **GPLv3 copyleft** (verified from LICENSE — handoff §1 wrongly assumed MIT), which clashes with SP-1's MIT intent and obliges source disclosure on redistribution. Forking buys only ~287 LOC but adds rebase friction + an upstream with no plugin/hook system + hardcoded data_dir + no reusable WebUI. A faithful protocol-compatible receiver is ~40-70 LOC; byte-for-byte crypto compat is guaranteed by reusing the same `crypto-js` package. |
| D2 | **Dual crypto mode**: legacy (default) + aes-128-cbc-fixed | legacy is the official extension default (mandatory); aes-128-cbc-fixed costs ~10 extra LOC + a `crypto_type` branch and future-proofs against extension version/config changes. |
| D3 | **Flat per-hook YAML** config (research Option 1) | Most readable for v1's small hook count; each hook self-contains trigger + match + action. |
| D4 | **TypeScript** (not plain JS) | The interop failure modes are silent (key `[:16]`, Salted__ default, body limit, `path.basename`); compile-time types lock config + protocol shapes. Cost: a `tsc`/`tsx` build step. |
| D5 | **`accounts: [{uuid, password}]`** maps box → decryption passphrase; cookies are NOT in config | Cookies arrive at runtime (extension → `/update`) and are stored encrypted in `data/<uuid>.json`. The password is the CookieCloud **encryption passphrase** (not a website login, not a cookie); needed only to decrypt for domain-matching / `{{cookie_json}}` / CLI. |
| D6 | **Single box default** (1 account), schema supports N | Operator has one Zhihu + one Bilibili login shared across PC/Android → one box, last-write-wins at whole-blob level is always a valid session. Multi-box retained in schema (`accounts` is a list); on same-domain collision across boxes, resolve to the most recent `update_time`, `--uuid` overrides. |

## 3. CookieCloud protocol (the contract we implement)

Authoritative + verifier-confirmed details in `research.md`. Essentials:

- **Upload:** `POST {endpoint}/update`, body `{uuid, encrypted, crypto_type?}`. Accept BOTH
  `application/json` and `application/x-www-form-urlencoded`. Reject `400` if `uuid`/`encrypted`
  missing. Return `{"action":"done"}` on success.
- **Download:** `GET|POST {endpoint}/get/:uuid` — return parsed JSON if `password` supplied in
  request body, else raw stored `{encrypted, crypto_type}`.
- **Key derivation (both modes):** `the_key = md5(uuid + "-" + password).hex[:16]` (first 16 chars
  of the 32-char lowercase hex MD5 of UTF-8 `uuid + "-" + password`; literal hyphen).
- **legacy (default):** `the_key` passed to crypto-js as a **STRING passphrase** → OpenSSL mode:
  random 8-byte salt, EVP_BytesToKey(iterated MD5) → 32-byte AES-256 key + 16-byte IV,
  AES-256-CBC + PKCS7, output `base64("Salted__" + salt + ciphertext)`.
- **aes-128-cbc-fixed:** `the_key`'s 16 UTF-8 bytes used directly as AES-128 key, fixed zero IV,
  AES-128-CBC + PKCS7, raw base64 (no `Salted__`).
- **Inner plaintext:** `{ cookie_data, local_storage_data, update_time }`; `cookie_data` =
  map of `domain -> [cookie objects]`.
- **Node decrypt:** use `crypto-js` (`CryptoJS.AES.decrypt(encrypted, the_key_string)`); it
  auto-parses the `Salted__` envelope for legacy. For aes-128-cbc-fixed, parse the 16-byte key +
  zero IV explicitly.

## 4. Module decomposition

Each unit: single responsibility, well-defined interface, independently testable.

```
src/
  config.ts      Load + validate config/cookie-manager.yaml (zod) -> typed Config.
                 Exposes: loadConfig(path): Config. Owns the YAML schema.
  crypto.ts      ★ correctness-critical. Pure functions, no IO.
                 cookieDecrypt(uuid, encrypted, password, cryptoType): InnerPayload
                 cookieEncrypt(uuid, payload, password, cryptoType): string  (for tests/smoke client)
                 deriveKey(uuid, password): string
  store.ts       File persistence; path.basename(uuid) traversal guard; data_dir configurable.
                 save(uuid, {encrypted, crypto_type}); load(uuid); list(): StoredMeta[]
  server.ts      Express app factory. Routes: POST /update, GET|POST /get/:uuid, GET /health.
                 Body parsing (json + urlencoded, configurable limit). Emits 'cookie-update'.
                 Depends on: store, config; emits to hooks.engine (event, not direct call).
  hooks/
    engine.ts    Orchestrator: subscribe T1 events + register T2 cron; on fire -> resolve cookies
                 (decrypt via account password) -> filter by match -> run action(s).
    triggers.ts  T1 = EventEmitter subscription on 'cookie-update'; T2 = node-cron scheduler.
    actions.ts   A1 = exec (child_process, timeout, env injection); A3 = write_file (render template).
    template.ts  interpolate(template, vars) for {{var}}; matchHook(match, ctx) for uuid glob + domain.
  cli.ts         Commands: list | show domain=<x> | dump [--uuid=<u>]. Reads via store + crypto.
  index.ts       Bootstrap: loadConfig -> store init -> start server -> engine.register(hooks) ->
                 graceful SIGTERM/SIGINT shutdown.
tests/
  crypto.test.ts store.test.ts server.test.ts hooks.test.ts cli.test.ts  + fixtures/
config/cookie-manager.example.yaml
Dockerfile  docker-compose.yml  package.json  tsconfig.json  vitest.config.ts  LICENSE(MIT)
```

Interfaces between units are values/events, not shared mutable state:
`server` emits `cookie-update {uuid, encrypted, crypto_type}`; `engine` consumes it and pulls the
password from `config.accounts`. `crypto` and `template` are pure. `store` is the only filesystem owner
for cookie data.

## 5. Data flow

```
[Upload]  official extension --encrypt--> POST /update {uuid, encrypted, crypto_type?}
   server: validate (missing -> 400) -> store.save (store ciphertext verbatim) -> read-back byte-compare
        -> respond {action:'done'} IMMEDIATELY  (do not block extension on hooks)
        -> (async) emit 'cookie-update' -> engine:
              lookup account.password for uuid -> crypto.decrypt -> compute domains
              -> for each T1 hook whose match passes -> run A1/A3 with interpolated vars
[Cron]    node-cron fires T2 hook -> engine: load latest stored cookies -> decrypt -> run A1/A3
[CLI]     store.load + crypto.decrypt -> print (list / show domain= / dump)
```

Rationale for async hooks: a slow exec hook must not stall the extension's upload request (it would
report sync failure). Hook outcomes go to the log.

## 6. Config schema (flat per-hook YAML)

```yaml
server:
  host: 0.0.0.0          # 0.0.0.0 for LAN/Android push; 127.0.0.1 if same host only
  port: 48088             # CookieCloud convention
  data_dir: ./data
  body_limit: 50mb       # default 100kb silently truncates real cookie dumps
accounts:                # box -> decryption passphrase; cookies are NOT here (they arrive via /update)
  - uuid: "your-uuid"    # the random id you set in the extension
    password: "your-pw"  # the encryption passphrase you set in the extension (NOT a website login)
hooks:
  - id: refresh-zhihu
    on: cookie-update                 # T1
    match: { uuid: "*", domain: ".zhihu.com" }
    action: exec                       # A1
    command: "/opt/crawl/refresh.sh"
    args: ["--uuid", "{{uuid}}", "--domain", "{{domain}}"]
    env: { COOKIE_JSON: "{{cookie_json}}" }   # large JSON via env, not argv
    timeout_ms: 30000
  - id: snapshot
    on: cron                           # T2
    schedule: "*/15 * * * *"
    match: { uuid: "*" }
    action: write_file                 # A3
    path: "./snapshots/{{uuid}}-{{ts}}.json"
    template: '{"uuid":"{{uuid}}","cookies":{{cookie_json}},"at":"{{ts}}"}'
```

Template vars: `{{uuid}} {{domain}} {{cookie_json}} {{encrypted}} {{crypto_type}} {{update_time}} {{ts}}`.
`{{cookie_json}}` substitutes a raw JSON value (no surrounding quotes). Unknown vars -> empty string.
`match.domain` filters T1 against keys in decrypted `cookie_data`; omit to fire on every update.
An account without a configured password: domain-matched hooks log a warning and skip (only
`{{encrypted}}`-based hooks can run).

## 7. CLI interface

| Command | Behavior |
|---|---|
| `cookie-manager list` | list stored uuids + `update_time` + per-uuid domain count |
| `cookie-manager show domain=<x>` | decrypt + show cookies for domain `<x>` (most recent box on collision) |
| `cookie-manager dump [--uuid=<u>]` | decrypt + dump all cookies (or a specific uuid) |

## 8. Error handling & security

- Missing `uuid`/`encrypted` -> 400; body over limit -> 413; file IO error -> 500.
- Decrypt failure (wrong password / corrupt blob) -> log + skip hook, **never crash**; CLI errors out.
- exec hook: configurable `timeout_ms`, kill on timeout; cron hook skips a tick if the previous run
  is still in flight (no overlap).
- **Security:**
  - `path.basename(uuid)` before building the file path (path-traversal guard).
  - exec commands come from the **trusted local config** (operator's own); `{{cookie_json}}` passed
    via env, never spliced into a shell string.
  - The protocol's only protection is uuid+password obscurity (same as upstream). README MUST
    instruct running behind LAN/VPN/reverse proxy; do not expose the port to the public internet.

## 9. Testing strategy (TDD — red first)

- **crypto.ts (heaviest):** (1) round-trip encrypt->decrypt; (2) a hardcoded **known vector** fixture
  cross-checked against the reference implementations (guards against self-consistent but wrong code);
  (3) both `crypto_type` branches.
- **store:** save/load/list; `../` traversal rejected.
- **server:** supertest — `POST /update` with json AND urlencoded; 400 cases; large body; `GET /get/:uuid`.
- **hooks:** `matchHook` (uuid glob + domain); template interpolation; A3 write_file (tmp dir);
  A1 exec (`echo`); cron trigger via faked timer.
- **cli:** list/show/dump against a seeded store.
- **Manual smoke (verification-before-completion gate, handoff §3.E — mandatory):** start the service,
  push a fake cookie with a small PyCookieCloud-style client (node + crypto-js), observe the hook fire
  and the file get written.

## 10. Deployment

`Dockerfile` + `docker-compose.yml` (service + data volume + mounted config) + `LICENSE` (MIT) + README
(install official extension -> point its server address at this service -> set uuid/password -> configure
hooks). We **produce** the compose file but do **not** run docker (handoff §5: deployment is the operator's action).

## 11. Open questions / risks

- **R1 (low):** Exact `Content-Type` the official extension sends — research notes it sends JSON but
  PyCookieCloud sends urlencoded; mitigated by accepting both.
- **R2 (low):** Whole-blob last-write-wins across devices could drop a domain if a device not logged
  into that site syncs last. Operator uses one box with both logins on both devices -> non-issue;
  documented in README.
- **R3 (med):** `crypto-js` is in maintenance-only mode upstream. Acceptable for v1; the decrypt path
  is small and could be reimplemented on `node:crypto` later if needed.

## 12. Self-review report

- **Placeholder scan:** no TBD/TODO remain. All sections concrete.
- **Internal consistency:** D5/D6 (accounts model, single-box default) match §6 config + §7 CLI
  collision rule; §3 protocol matches `research.md` (verifier-confirmed); §4 module interfaces match
  the §5 data flow (server emits event, engine consumes + pulls password from config).
- **Scope:** single module, single implementation plan; v1/v1+ split explicit in §1.
- **Ambiguity resolved:** "most recent box on collision" pinned to `update_time` + `--uuid` override
  (D6); async-hook ordering pinned in §5 (respond before hooks); dual content-type pinned in §3.
- **Residual risks** tracked in §11 (R1-R3), all low/med with stated mitigations.
