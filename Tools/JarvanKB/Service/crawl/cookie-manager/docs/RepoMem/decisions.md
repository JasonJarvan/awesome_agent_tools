# Module decision log

> Append-only, time-descending (newest at top).
> Each entry: date, slug, decision, rationale, what-changes-when-this-is-revisited.
> When a decision is promoted to global, leave a `[Promoted to global ↗]` marker pointing to `<root>/docs/RepoMem/persist/memory/`.

## 2026-05-31 (post-merge follow-ups) — sp1-cookie-manager — port 48xxx, frp public exposure, header auth

Made after SP-1 was merged, on user request. Verified end-to-end (public HTTPS push → store → hook).

- **Port 8088 → 48088.** JarvanKB services use the **48xxx** range (host port convention recorded in
  `~/.ops-doc-maintainer-docs/.../rules.md`; 40xxx had a UDP occupant). 8088 was only CookieCloud's upstream
  default, NOT a protocol constraint — the extension points at a configurable URL, so the extension's server
  address simply uses the new port.
- **Public exposure via frp.** frpc proxy `jarvankb-cookie-manager` (local 48088 → remote 48088) through frps
  `101.35.46.114`; the frps host's Nginx terminates TLS → public **`https://www.zhaoricheng.fun:48098`**
  (Let's Encrypt) and a direct plain endpoint `http://101.35.46.114:48088`. frps needed no `allowPorts` change
  (default allow). Coordinated via `docs/sendbox/toFRPS/handoff.md` (resolved). frpc recorded in ops
  `manual-software.txt`.
- **Optional shared-secret header auth.** `server.auth_token` (+ `server.auth_header`, default
  `X-CookieCloud-Token`): when set, every request except `/health` must carry the header (401, checked before
  body parsing). Disabled when empty (LAN-only / back-compat). Defense-in-depth over uuid+password obscurity;
  recommended whenever publicly exposed. The extension carries it via its "request header" field.
- **`config/cookie-manager.yaml` is gitignored** (real config = secrets: uuid/password/auth_token); only
  `*.example.yaml` / `*.smoke.yaml` templates are tracked.

**Revisit when:** moving hosts (re-pick a 48xxx port + redo the frps proxy); exposing more JarvanKB services
(allocate the next 48xxx port + ops registry entry).

## 2026-05-31 — sp1-cookie-manager — Path B: self-write, NOT fork CookieCloud

**Decision:** Implement a self-written Node.js/TypeScript Express service that speaks the
CookieCloud upload-API protocol, rather than forking easychen/CookieCloud.

**Rationale:** easychen/CookieCloud is **GPLv3 (copyleft), not MIT** (the SP-1 handoff wrongly
assumed MIT). Forking + distributing a modified server triggers source-disclosure obligations
incompatible with SP-1's MIT intent. The upstream server core is only ~287 LOC with no plugin/hook
system, a hardcoded data_dir, and no reusable WebUI — so a fork buys little code but adds copyleft
+ rebase friction. A faithful protocol-compatible receiver is ~40-70 LOC, and byte-for-byte crypto
compatibility is guaranteed by reusing the same `crypto-js` package the official extension uses.

**Revisit when:** upstream relicenses to a permissive license AND ships an extensible hook/WebUI
surface — then re-evaluate fork vs maintain.

**Candidate for global promotion:** the GPLv3 finding + "reimplement-the-protocol over fork" pattern
may be worth promoting to global persist (HITL merge decides), since other cookie-dependent modules
reference SP-1's protocol contract.

## 2026-05-31 — sp1-cookie-manager — dual crypto mode (legacy + aes-128-cbc-fixed)

**Decision:** Support both `legacy` (default; CryptoJS string-passphrase → OpenSSL Salted__ +
EVP_BytesToKey(MD5) + AES-256-CBC/PKCS7) and `aes-128-cbc-fixed` (16-UTF8-byte key, zero IV,
AES-128-CBC/PKCS7, no Salted__). Key for both: `md5(uuid + "-" + password).hex[:16]`.

**Rationale:** legacy is the official extension default (mandatory). aes-128-cbc-fixed cost ~10 LOC
and future-proofs against extension version/config changes. Correctness guarded by round-trip tests
PLUS independent `node:crypto` oracles (a different implementation than crypto-js) for BOTH modes.

**Revisit when:** CookieCloud introduces a new crypto_type — add a branch + an independent oracle test.

## 2026-05-31 — sp1-cookie-manager — config & accounts model

**Decision:** Flat per-hook YAML config. `accounts: [{uuid, password}]` maps a CookieCloud box to its
decryption passphrase — **cookies are never in config** (they arrive via `POST /update` and are stored
encrypted in `data/<uuid>.json`). Single box for v1 (operator has one Zhihu + one Bilibili login shared
across PC/Android); schema supports N accounts.

**Rationale:** the password is the CookieCloud encryption passphrase, not a website login. Decryption-only
features (domain match, `{{cookie_json}}`, CLI show/dump) need it; pure store/forward does not.

**Revisit when:** multi-box is actually used — implement most-recent-`update_time`-wins on same-domain
collision (currently CLI `show` keeps the last match in filesystem order; `--uuid` disambiguates).

## 2026-05-31 — sp1-cookie-manager — review follow-ups & accepted deviations

- **`{{cookie_json}}` shape is match-dependent:** domain-matched hooks receive that domain's cookie
  **array**; non-domain hooks receive the full `cookie_data` **map**. Documented in README. Intentional.
- **`match.uuid` is exact-or-`*`, not a full glob** (design §4 said "glob"). v1 examples only use `*` or
  exact, so true globbing is YAGNI. **Revisit** if a `prefix-*` pattern is ever needed.
- **No write-then-read-back byte-compare** (upstream CookieCloud does this; design §5 mentioned it).
  `writeFileSync` throws on failure, making the read-back redundant for our synchronous path. Accepted
  deviation; revisit only if silent partial writes are observed.
- **Build-tool deviations (Task 0):** added a 2-line `src/index.ts` stub during scaffold to satisfy
  `tsc` (TS18003 on empty `src/`; later overwritten by the real bootstrap), and `passWithNoTests: true`
  in `vitest.config.ts` (vitest v2 exits 1 on no tests). Both bootstrap-only; harmless once code exists.

## 2026-05-31 — sp1-cookie-manager — async hook dispatch

**Decision:** `POST /update` responds `{action:'done'}` BEFORE running hooks (`setImmediate` emit), so a
slow `exec` hook never stalls the browser extension's upload (which would report a sync failure). Cron
(T2) `runCronHook` is async and `await`s all dispatched hooks so the no-overlap guard in `scheduleCron`
actually spans hook execution.

**Rationale:** extension upload latency must stay low; cron correctness requires the overlap guard to
span real work. **Revisit** if hook outcomes need to be surfaced back to the caller synchronously.
