# Module internal architecture

> Internal implementation specifics — NOT duplicated from the external `docs/architecture.md`
> (module table + data flow live there). This file records internals a maintainer needs.

## Crypto internals (`src/crypto.ts`)

- legacy decrypt relies on crypto-js auto-parsing the OpenSSL `Salted__` envelope: pass the 16-hex-char
  key as a **string** (passphrase) to `CryptoJS.AES.decrypt(encrypted, theKey)`. crypto-js extracts the
  8-byte salt from the blob and re-runs EVP_BytesToKey (iterated MD5) to recover the 32-byte key + 16-byte
  IV. Do NOT pass a WordArray for legacy — that would skip the passphrase KDF and fail.
- aes-128-cbc-fixed uses `CryptoJS.enc.Utf8.parse(theKey)` (the 16 ASCII bytes of the hex string) as the
  AES-128 key with `FIXED_IV = Hex.parse('0'*32)` (16 zero bytes), explicit CBC+Pkcs7, output is raw
  `ciphertext.toString(Base64)` (no Salted__).
- Correctness is cross-checked by independent `node:crypto` oracles in `tests/crypto.test.ts` (hand-rolled
  EVP_BytesToKey + `aes-256-cbc` for legacy; `aes-128-cbc` + zero IV for fixed). These are a DIFFERENT
  implementation than crypto-js, so they catch "self-consistent but wrong".

## Engine internals (`src/hooks/engine.ts`)

- `buildContext(uuid, encrypted, cryptoType)` decrypts ONCE and returns `{ ctx, domains, payload }`.
  `payload` is reused for per-domain `cookie_json` narrowing — no second decrypt. On no-password or
  decrypt failure, `payload = null`, domains `[]`, `update_time = ''` (engine logs + skips, never throws).
- T1 (`onCookieUpdate`): fire-and-forget `void runHook(...)` per matched hook (the HTTP response already
  returned, so latency is irrelevant here; failures are logged inside runHook).
- T2 (`runCronHook`): **async** — collects all `runHook(...)` promises and `await Promise.all(...)` so the
  `running` guard in `scheduleCron` (triggers.ts, which does `await fn()`) actually spans hook execution
  and prevents overlapping ticks.
- `runHook` swallows errors (logs) so one bad hook never crashes the engine or blocks others.

## Server internals (`src/server.ts`)

- `express.json` AND `express.urlencoded` both registered with the configured `body_limit` (default 50mb —
  the default 100kb silently truncates real cookie dumps).
- `/update` validates `crypto_type` against the whitelist (`legacy`|`aes-128-cbc-fixed`) → 400 on unknown.
- Emits `cookie-update` via `setImmediate` AFTER `res.json` so a slow hook cannot stall the extension.

## Store internals (`src/store.ts`)

- `fileFor(uuid) = join(dataDir, basename(uuid) + '.json')` — `basename` is the path-traversal guard.
- `list()` reads every `*.json`, parsing `crypto_type` from each. No index; fine for v1 single-box scale.

## Test strategy notes

- vitest + supertest. `vitest.config.ts` has `passWithNoTests: true` (bootstrap-era; harmless now).
- Cron path tested with a 6-field per-second schedule `'*/1 * * * * *'` + `vi.waitFor` (≤3s) — the only
  real-timer test; slightly slower but deterministic enough.
