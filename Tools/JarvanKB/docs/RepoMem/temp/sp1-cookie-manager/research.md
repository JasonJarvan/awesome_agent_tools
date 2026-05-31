---
slug: sp1-cookie-manager
status: research-captured
domains: [cookie-manager]
updated_at: 2026-05-31
task_type: feature
---

# SP-1 CookieManager — Research Capture (verified)

> Captured at brainstorming Step 2/3 (RepoMem.capture). Produced by a 6-agent research
> workflow (4 parallel research + 1 adversarial crypto verifier + 1 synthesis), all
> primary-source-grounded (easychen/CookieCloud master, PyCookieCloud, examples/decrypt.py).
> Crypto facts are VERIFIER-confirmed (verdict: confirmed, no corrections).
> Temp location per handoff §3.C; `git mv` into module dir at Stage 3.

## ⚠️ Material finding that contradicts the handoff

- handoff §1 assumed **MIT license** + preferred **path A (fork CookieCloud)**.
- **easychen/CookieCloud is GPLv3 (copyleft), NOT MIT** (verified from LICENSE file).
- Forking + distributing a modified server carries a GPLv3 source-disclosure obligation
  (self-hosting alone does not trigger it — GPLv3 has no SaaS/network clause — but
  redistribution does). This **inverts** the path recommendation toward **path B (self-write)**.

## Verified CookieCloud upload protocol (authoritative)

### Endpoints
- **Upload:** `POST {endpoint}/update` (extension trims trailing slashes on host).
- **Download:** `POST|GET {endpoint}/get/:uuid` — returns parsed JSON if `password` supplied,
  else raw stored `{encrypted, crypto_type}`.

### Upload request body
- Content-Type `application/json` (browser extension; also sets `Content-Encoding: gzip`
  but body is plain JSON) OR `application/x-www-form-urlencoded` (PyCookieCloud).
  **A compatible receiver MUST accept both.**
- Fields: `uuid` (string), `encrypted` (base64 string), optional `crypto_type`
  (`'legacy'` default | `'aes-128-cbc-fixed'`). Official extension sends only `uuid`+`encrypted`.
- Server rejects `400 'Bad Request'` if `uuid` or `encrypted` missing.

### Key derivation (both modes)
`the_key = CryptoJS.MD5(uuid + '-' + password).toString().substring(0,16)`
— first 16 chars of the 32-char lowercase hex MD5 of UTF-8 string `uuid + "-" + password`
(literal hyphen). Python: `hashlib.md5((uuid+'-'+password).encode()).hexdigest()[:16]`.

### Crypto — LEGACY (default; official extension + server)
- `the_key` (16 hex chars) passed to CryptoJS as a **STRING passphrase** → OpenSSL mode:
  random 8-byte salt, **EVP_BytesToKey with iterated MD5 (NOT PBKDF2)** → 48 bytes
  (32-byte AES-256 key ∥ 16-byte IV). KDF input = **UTF-8 bytes of the 16 hex chars**.
- **AES-256-CBC + PKCS7**. Output = `base64("Salted__" + 8-byte salt + ciphertext)`.

### Crypto — AES-128-CBC-FIXED (optional; in server app.js, NOT default extension flow)
- Key = 16 UTF-8 bytes of the hex string (`CryptoJS.enc.Utf8.parse`), used directly as AES-128 key.
- Fixed IV = 16 zero bytes; AES-128-CBC + PKCS7. Output = raw base64, **NO `Salted__`**.

### Decrypt (Node, recommended — byte-for-byte compat via crypto-js)
```js
const CryptoJS = require('crypto-js');
function cookieDecrypt(uuid, encrypted, password) {
  const the_key = CryptoJS.MD5(uuid + '-' + password).toString().substring(0,16); // STRING
  const dec = CryptoJS.AES.decrypt(encrypted, the_key).toString(CryptoJS.enc.Utf8);
  return JSON.parse(dec); // { cookie_data, local_storage_data, update_time }
}
```
Keep `the_key` a STRING and feed the ciphertext string in directly — crypto-js auto-parses
the `Salted__` envelope + re-runs EVP_BytesToKey. (Hand-rolling `node:crypto` requires
reimplementing the Salted__/EVP_BytesToKey envelope.)

### Inner plaintext shape
`{ cookie_data, local_storage_data, update_time }` (0.1.5+ wrapper, not bare cookies).
Cookies under `obj.cookie_data` = map of `domain -> array of cookie objects`.

### Storage (upstream)
File-per-uuid JSON. `data_dir = path.join(__dirname, 'data')` (hardcoded upstream). On `/update`:
write `path.join(data_dir, path.basename(uuid) + '.json')` (`path.basename` neutralizes `../`)
with `{encrypted, crypto_type}`, read back + byte-compare, return `{"action":"done"}`. No DB,
no list primitive (a WebUI would `readdir(data_dir)`).

## Path A vs Path B

| Dimension | Path A — fork easychen/CookieCloud | Path B — self-write Express |
|---|---|---|
| Maintenance | inherit ~287 LOC + carry hook patch as diff; rebase friction | own ~40-70 LOC; no upstream; frozen protocol |
| LOC (ours) | small delta on ~310 inherited | ~40 (store-only) / ~60-70 (with decrypt-on-GET) |
| Control | constrained (single file, hardcoded data_dir, no plugin system) | full control of routes/storage/hook points/config |
| WebUI path (v1+) | MODERATE — upstream serves no static; `web/` is marketing page, not admin UI | same work, on our own clean surface |
| Extension compat | native (it IS the reference server) | high IF we mirror verified spec |
| **License** | **GPLv3 copyleft** (NOT MIT) — clashes with SP-1 MIT intent | **free choice (MIT ok)** — wire-protocol reimpl is not derivative |
| Risk | clean code, but GPLv3 + messy branch hygiene (`master` vs `main` +13) | correctness on us (body limit, `[:16]`, Salted__ default, path.basename) |

**Recommendation: Path B (self-write).** Forking buys ~287 LOC but adds GPLv3 + rebase
friction + an upstream we cannot cleanly extend; self-write is ~40-70 LOC with free license,
full control over the hook injection point, and guaranteed crypto compat via crypto-js.

## Hook mechanism (handoff §1 confirmed scope: T1 cookie-update + T2 cron → A1 exec + A3 write_file)

Template vars: `{{uuid}}`, `{{domain}}`, `{{cookie_json}}`, `{{encrypted}}`, `{{crypto_type}}`,
`{{update_time}}`, `{{ts}}`.

- **Option 1 — flat per-hook YAML** (recommended start): each hook self-contains `on`(trigger)
  + `match` + `action` + params. Most readable for a small number of hooks.
- **Option 2 — separated `triggers[]`/`actions[]`/`bindings[]` JSON**: one trigger fans out to
  N actions, actions reusable; scales but heavier config.
- **Option 3 — minimal single-hook env block**: smallest config, only one hook.

Interpolation: `{{cookie_json}}` substitutes a raw JSON value (no quotes); others string-substitute;
unknown → empty. For `exec`, prefer passing `{{cookie_json}}` via env to avoid shell-escaping.
`match.domain` filters T1 against keys in decrypted `cookie_data`.

## Ecosystem signals
- No built-in post-update hook/webhook in upstream (issues #69/#68/#65 webhook, #124 WebUI all
  OPEN/unbuilt). SP-1 must fire its own hook (path B native; path A = patch `/update`).
- Closest reference design for future WebUI/selective-sync: jackluson/sync-your-cookie (679★,
  management panel + per-site rules). Not a fork — an independent analog.

## Key interop gotchas (must-get-right for extension compat)
1. Key = `md5(uuid+'-'+password).hex[:16]` used as **STRING passphrase** (not raw bytes); literal `-`.
2. Legacy default = `Salted__` OpenSSL envelope (AES-256-CBC). crypto-js handles it; don't force AES-128/fixed-IV for legacy.
3. **Body size limit**: raise `express.json({limit})` to ~50mb — default 100kb silently truncates real cookie dumps.
4. `path.basename(uuid)` before building file path — path-traversal guard, not just compat.
5. Store ciphertext verbatim (store-and-forward; never decrypt-then-reencrypt for storage).
6. Return `{"action":"done"}` on success (extension UI expects it).

## Sources (primary)
- easychen/CookieCloud `master`: README.md, extension/function.js, api/app.js, api/package.json, LICENSE
- lupohan44/PyCookieCloud: PyCookieCloud.py, PyCryptoJS.py
- easychen/CookieCloud examples/decrypt.py (official reference decryptor)
- crypto-js issues #534/#502 (passphrase → EVP_BytesToKey / Salted__ format)
- CookieCloud issues #69, #68, #65, #124, #45; jackluson/sync-your-cookie; laplace-live/login-sync
