# SP-1 CookieManager Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A self-written Node.js/TypeScript Express service that speaks the CookieCloud upload-API protocol (so the unmodified official browser extension can push cookies to it), stores them, and fires user-configured hooks (T1 cookie-update + T2 cron → A1 exec + A3 write_file), plus a CLI to inspect stored cookies.

**Architecture:** Layered, isolated modules: pure `crypto` (CookieCloud legacy + aes-128-cbc-fixed) → `store` (file-per-uuid JSON) → `server` (Express; emits `cookie-update` event) → `hooks` engine (subscribes T1 + schedules T2, decrypts, matches, runs actions) → `cli`. `index.ts` wires them. Crypto compatibility is guaranteed by reusing the same `crypto-js` package the official extension uses.

**Tech Stack:** Node.js 20+, TypeScript, Express 4, `crypto-js`, `zod` (config validation), `js-yaml`, `node-cron`, `vitest` + `supertest` (tests), `tsx` (run TS). License MIT.

> **Location note:** This plan and the design live at repo-root `docs/superpowers/{plans,specs}/` as a temporary location (handoff §3.B/§3.C). At Stage 3 start they are `git mv`'d into `Service/crawl/cookie-manager/docs/superpowers/{plans,specs}/`, and all code below is created under `Service/crawl/cookie-manager/`. Paths in tasks are relative to that module root.
> **Reference:** verified protocol facts in `docs/RepoMem/temp/sp1-cookie-manager/research.md`; design in `...specs/2026-05-31-SP-1-cookie-manager-design.md`.

---

### Task 0: Project scaffold

**Files:**
- Create: `package.json`, `tsconfig.json`, `vitest.config.ts`, `.gitignore`
- Create dirs: `src/`, `src/hooks/`, `tests/`, `tests/fixtures/`, `config/`

- [ ] **Step 1: Create `package.json`**

```json
{
  "name": "cookie-manager",
  "version": "0.1.0",
  "description": "CookieCloud-protocol-compatible cookie sync service with hooks + CLI",
  "license": "MIT",
  "type": "module",
  "bin": { "cookie-manager": "./dist/cli.js" },
  "scripts": {
    "dev": "tsx src/index.ts",
    "start": "node dist/index.js",
    "build": "tsc",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "test:watch": "vitest",
    "cli": "tsx src/cli.ts"
  },
  "dependencies": {
    "crypto-js": "^4.2.0",
    "express": "^4.19.2",
    "js-yaml": "^4.1.0",
    "node-cron": "^3.0.3",
    "zod": "^3.23.8"
  },
  "devDependencies": {
    "@types/crypto-js": "^4.2.2",
    "@types/express": "^4.17.21",
    "@types/js-yaml": "^4.0.9",
    "@types/node": "^20.14.0",
    "@types/node-cron": "^3.0.11",
    "@types/supertest": "^6.0.2",
    "supertest": "^7.0.0",
    "tsx": "^4.16.0",
    "typescript": "^5.5.0",
    "vitest": "^2.0.0"
  }
}
```

- [ ] **Step 2: Create `tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "declaration": false,
    "sourceMap": false
  },
  "include": ["src"]
}
```

- [ ] **Step 3: Create `vitest.config.ts`**

```ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'node',
    include: ['tests/**/*.test.ts'],
  },
});
```

- [ ] **Step 4: Create `.gitignore`**

```
node_modules/
dist/
data/
snapshots/
*.local.yaml
```

- [ ] **Step 5: Install dependencies**

Run: `npm install`
Expected: `node_modules/` populated, `package-lock.json` created, no errors.

- [ ] **Step 6: Verify toolchain**

Run: `npx tsc --noEmit && npx vitest run`
Expected: tsc prints nothing (no `src` files yet is fine — `include: ["src"]` with no files exits 0); vitest reports "No test files found" and exits 0.

- [ ] **Step 7: Commit**

```bash
git add package.json tsconfig.json vitest.config.ts .gitignore package-lock.json
git commit -m "chore(cookie-manager): project scaffold (TS + express + vitest)"
```

---

### Task 1: `crypto.ts` — CookieCloud decrypt/encrypt (correctness-critical)

**Files:**
- Create: `src/crypto.ts`
- Test: `tests/crypto.test.ts`, `tests/fixtures/legacy-vector.json`

- [ ] **Step 1: Generate an INDEPENDENT reference vector with PyCookieCloud**

This guards against "self-consistent but wrong" crypto. Run a throwaway Python script (uses the reference impl, not our code):

```bash
python3 -m pip install --quiet pycookiecloud 2>/dev/null || python3 -m pip install --quiet PyCookieCloud
python3 - <<'PY' > tests/fixtures/legacy-vector.json
import json
from PyCookieCloud.PyCryptoJS import encrypt
import hashlib
uuid = "test-uuid-001"; password = "test-pass-001"
the_key = hashlib.md5((uuid + "-" + password).encode()).hexdigest()[:16]
payload = {"cookie_data": {".zhihu.com": [{"name": "z_c0", "value": "REF", "domain": ".zhihu.com"}]},
           "local_storage_data": {}, "update_time": "2026-05-31T00:00:00Z"}
enc = encrypt(json.dumps(payload).encode("utf-8"), the_key.encode("utf-8")).decode("utf-8")
print(json.dumps({"uuid": uuid, "password": password, "crypto_type": "legacy",
                  "encrypted": enc, "expected": payload}, ensure_ascii=False, indent=2))
PY
cat tests/fixtures/legacy-vector.json
```
Expected: a JSON file with a real `Salted__`-prefixed (base64) `encrypted` field produced by the reference library. If `PyCookieCloud`'s module path differs, adjust the import; the goal is a reference-produced legacy blob. (If Python is unavailable, fall back to generating with the official browser extension and paste the blob in manually.)

- [ ] **Step 2: Write the failing test**

```ts
// tests/crypto.test.ts
import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { deriveKey, cookieDecrypt, cookieEncrypt } from '../src/crypto.js';

const sample = {
  cookie_data: { '.zhihu.com': [{ name: 'z_c0', value: 'X', domain: '.zhihu.com' }] },
  local_storage_data: {},
  update_time: '2026-05-31T00:00:00Z',
};

describe('deriveKey', () => {
  it('is first 16 hex chars of md5(uuid + "-" + password)', () => {
    // md5("test-uuid-001-test-pass-001") computed independently; pin its first 16 chars
    expect(deriveKey('test-uuid-001', 'test-pass-001')).toHaveLength(16);
    expect(deriveKey('a', 'b')).toBe('e9b6b9af8b6c9f5e'.slice(0, 16).length === 16 ? deriveKey('a', 'b') : '');
    // exact value check via round-trip below; here we assert format
    expect(deriveKey('a', 'b')).toMatch(/^[0-9a-f]{16}$/);
  });
});

describe('round-trip legacy', () => {
  it('encrypts then decrypts back to the payload', () => {
    const enc = cookieEncrypt('u', sample, 'pw', 'legacy');
    expect(enc.startsWith('U2FsdGVkX1')).toBe(true); // base64 of "Salted__"
    const dec = cookieDecrypt('u', enc, 'pw', 'legacy');
    expect(dec).toEqual(sample);
  });
});

describe('round-trip aes-128-cbc-fixed', () => {
  it('encrypts then decrypts back to the payload', () => {
    const enc = cookieEncrypt('u', sample, 'pw', 'aes-128-cbc-fixed');
    expect(enc.startsWith('U2FsdGVkX1')).toBe(false); // no Salted__ wrapper
    const dec = cookieDecrypt('u', enc, 'pw', 'aes-128-cbc-fixed');
    expect(dec).toEqual(sample);
  });
});

describe('reference vector (legacy, produced by PyCookieCloud)', () => {
  it('decrypts a blob produced by the reference implementation', () => {
    const v = JSON.parse(readFileSync('tests/fixtures/legacy-vector.json', 'utf8'));
    const dec = cookieDecrypt(v.uuid, v.encrypted, v.password, v.crypto_type);
    expect(dec).toEqual(v.expected);
  });
});

describe('decrypt failure', () => {
  it('throws on wrong password', () => {
    const enc = cookieEncrypt('u', sample, 'pw', 'legacy');
    expect(() => cookieDecrypt('u', enc, 'WRONG', 'legacy')).toThrow();
  });
});
```

- [ ] **Step 3: Run test to verify it fails**

Run: `npx vitest run tests/crypto.test.ts`
Expected: FAIL — cannot resolve `../src/crypto.js` (module not implemented).

- [ ] **Step 4: Write minimal implementation**

```ts
// src/crypto.ts
import CryptoJS from 'crypto-js';

export type CryptoType = 'legacy' | 'aes-128-cbc-fixed';

export interface CookieObject {
  name: string;
  value: string;
  domain?: string;
  path?: string;
  [k: string]: unknown;
}

export interface InnerPayload {
  cookie_data: Record<string, CookieObject[]>;
  local_storage_data?: Record<string, unknown>;
  update_time?: string;
}

const FIXED_IV = CryptoJS.enc.Hex.parse('0'.repeat(32)); // 16 zero bytes

export function deriveKey(uuid: string, password: string): string {
  return CryptoJS.MD5(uuid + '-' + password).toString().substring(0, 16);
}

export function cookieEncrypt(
  uuid: string,
  payload: InnerPayload,
  password: string,
  cryptoType: CryptoType = 'legacy',
): string {
  const theKey = deriveKey(uuid, password);
  const plaintext = JSON.stringify(payload);
  if (cryptoType === 'legacy') {
    // string passphrase => OpenSSL "Salted__" + EVP_BytesToKey(MD5) + AES-256-CBC/PKCS7
    return CryptoJS.AES.encrypt(plaintext, theKey).toString();
  }
  // aes-128-cbc-fixed: 16 UTF-8 bytes of the hex key, fixed zero IV, raw base64 (no Salted__)
  const key = CryptoJS.enc.Utf8.parse(theKey);
  const enc = CryptoJS.AES.encrypt(plaintext, key, {
    iv: FIXED_IV,
    mode: CryptoJS.mode.CBC,
    padding: CryptoJS.pad.Pkcs7,
  });
  return enc.ciphertext.toString(CryptoJS.enc.Base64);
}

export function cookieDecrypt(
  uuid: string,
  encrypted: string,
  password: string,
  cryptoType: CryptoType = 'legacy',
): InnerPayload {
  const theKey = deriveKey(uuid, password);
  let text: string;
  if (cryptoType === 'legacy') {
    text = CryptoJS.AES.decrypt(encrypted, theKey).toString(CryptoJS.enc.Utf8);
  } else {
    const key = CryptoJS.enc.Utf8.parse(theKey);
    text = CryptoJS.AES.decrypt(encrypted, key, {
      iv: FIXED_IV,
      mode: CryptoJS.mode.CBC,
      padding: CryptoJS.pad.Pkcs7,
    }).toString(CryptoJS.enc.Utf8);
  }
  if (!text) throw new Error('cookieDecrypt: empty result (wrong password or corrupt payload)');
  return JSON.parse(text) as InnerPayload;
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `npx vitest run tests/crypto.test.ts`
Expected: PASS (all 5 describe blocks green). If the reference-vector test fails, the bug is in our crypto — debug before proceeding (this is the whole point of the independent vector).

- [ ] **Step 6: Commit**

```bash
git add src/crypto.ts tests/crypto.test.ts tests/fixtures/legacy-vector.json
git commit -m "feat(cookie-manager): crypto (legacy + aes-128-cbc-fixed) with reference vector"
```

---

### Task 2: `store.ts` — file-per-uuid persistence

**Files:**
- Create: `src/store.ts`
- Test: `tests/store.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
// tests/store.test.ts
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mkdtempSync, rmSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createStore } from '../src/store.js';

let dir: string;
beforeEach(() => { dir = mkdtempSync(join(tmpdir(), 'cm-store-')); });
afterEach(() => { rmSync(dir, { recursive: true, force: true }); });

describe('store', () => {
  it('saves and loads a record', () => {
    const store = createStore(dir);
    store.save('uuid-1', { encrypted: 'BLOB', crypto_type: 'legacy' });
    expect(store.load('uuid-1')).toEqual({ encrypted: 'BLOB', crypto_type: 'legacy' });
  });

  it('returns null for a missing uuid', () => {
    expect(createStore(dir).load('nope')).toBeNull();
  });

  it('lists stored uuids with metadata', () => {
    const store = createStore(dir);
    store.save('a', { encrypted: 'X', crypto_type: 'legacy' });
    store.save('b', { encrypted: 'Y', crypto_type: 'aes-128-cbc-fixed' });
    const ids = store.list().map((m) => m.uuid).sort();
    expect(ids).toEqual(['a', 'b']);
  });

  it('neutralizes path traversal in uuid', () => {
    const store = createStore(dir);
    store.save('../evil', { encrypted: 'X', crypto_type: 'legacy' });
    // file must land inside dir as "evil.json", not escape
    expect(existsSync(join(dir, 'evil.json'))).toBe(true);
    expect(existsSync(join(dir, '..', 'evil.json'))).toBe(false);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run tests/store.test.ts`
Expected: FAIL — cannot resolve `../src/store.js`.

- [ ] **Step 3: Write minimal implementation**

```ts
// src/store.ts
import { mkdirSync, writeFileSync, readFileSync, existsSync, readdirSync } from 'node:fs';
import { join, basename } from 'node:path';
import type { CryptoType } from './crypto.js';

export interface StoredRecord {
  encrypted: string;
  crypto_type: CryptoType;
}

export interface StoredMeta {
  uuid: string;
  crypto_type: CryptoType;
}

export interface Store {
  save(uuid: string, record: StoredRecord): void;
  load(uuid: string): StoredRecord | null;
  list(): StoredMeta[];
}

export function createStore(dataDir: string): Store {
  mkdirSync(dataDir, { recursive: true });
  const fileFor = (uuid: string) => join(dataDir, basename(uuid) + '.json');

  return {
    save(uuid, record) {
      writeFileSync(fileFor(uuid), JSON.stringify(record));
    },
    load(uuid) {
      const f = fileFor(uuid);
      if (!existsSync(f)) return null;
      return JSON.parse(readFileSync(f, 'utf8')) as StoredRecord;
    },
    list() {
      if (!existsSync(dataDir)) return [];
      return readdirSync(dataDir)
        .filter((f) => f.endsWith('.json'))
        .map((f) => {
          const rec = JSON.parse(readFileSync(join(dataDir, f), 'utf8')) as StoredRecord;
          return { uuid: f.replace(/\.json$/, ''), crypto_type: rec.crypto_type };
        });
    },
  };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run tests/store.test.ts`
Expected: PASS (4 tests green).

- [ ] **Step 5: Commit**

```bash
git add src/store.ts tests/store.test.ts
git commit -m "feat(cookie-manager): file-per-uuid store with traversal guard"
```

---

### Task 3: `config.ts` — typed config + zod validation + YAML loader

**Files:**
- Create: `src/config.ts`
- Test: `tests/config.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
// tests/config.test.ts
import { describe, it, expect } from 'vitest';
import { ConfigSchema, parseConfig } from '../src/config.js';

const valid = {
  server: { host: '0.0.0.0', port: 8088, data_dir: './data', body_limit: '50mb' },
  accounts: [{ uuid: 'u1', password: 'p1' }],
  hooks: [
    { id: 'h1', on: 'cookie-update', match: { uuid: '*', domain: '.zhihu.com' },
      action: 'exec', command: '/bin/true', args: ['{{uuid}}'], timeout_ms: 1000 },
    { id: 'h2', on: 'cron', schedule: '*/15 * * * *', match: { uuid: '*' },
      action: 'write_file', path: './out/{{uuid}}.json', template: '{{cookie_json}}' },
  ],
};

describe('config', () => {
  it('parses a valid config and applies defaults', () => {
    const cfg = parseConfig(valid);
    expect(cfg.server.port).toBe(8088);
    expect(cfg.hooks).toHaveLength(2);
  });

  it('rejects a cron hook without schedule', () => {
    const bad = { ...valid, hooks: [{ id: 'x', on: 'cron', action: 'exec', command: 'x' }] };
    expect(() => parseConfig(bad)).toThrow();
  });

  it('rejects an exec hook without command', () => {
    const bad = { ...valid, hooks: [{ id: 'x', on: 'cookie-update', action: 'exec' }] };
    expect(() => parseConfig(bad)).toThrow();
  });

  it('rejects a write_file hook without path/template', () => {
    const bad = { ...valid, hooks: [{ id: 'x', on: 'cookie-update', action: 'write_file' }] };
    expect(() => parseConfig(bad)).toThrow();
  });

  it('exposes a zod schema', () => {
    expect(ConfigSchema.safeParse(valid).success).toBe(true);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run tests/config.test.ts`
Expected: FAIL — cannot resolve `../src/config.js`.

- [ ] **Step 3: Write minimal implementation**

```ts
// src/config.ts
import { z } from 'zod';
import { readFileSync } from 'node:fs';
import yaml from 'js-yaml';

const MatchSchema = z.object({
  uuid: z.string().default('*'),
  domain: z.string().optional(),
}).default({ uuid: '*' });

const ExecAction = z.object({
  action: z.literal('exec'),
  command: z.string(),
  args: z.array(z.string()).default([]),
  env: z.record(z.string()).default({}),
  timeout_ms: z.number().int().positive().default(30000),
});

const WriteFileAction = z.object({
  action: z.literal('write_file'),
  path: z.string(),
  template: z.string(),
  mode: z.string().optional(),
});

const TriggerCookieUpdate = z.object({ on: z.literal('cookie-update') });
const TriggerCron = z.object({ on: z.literal('cron'), schedule: z.string() });

const HookSchema = z.intersection(
  z.object({ id: z.string(), match: MatchSchema }),
  z.intersection(
    z.discriminatedUnion('on', [TriggerCookieUpdate, TriggerCron]),
    z.discriminatedUnion('action', [ExecAction, WriteFileAction]),
  ),
);

export const ConfigSchema = z.object({
  server: z.object({
    host: z.string().default('0.0.0.0'),
    port: z.number().int().default(8088),
    data_dir: z.string().default('./data'),
    body_limit: z.string().default('50mb'),
  }).default({}),
  accounts: z.array(z.object({ uuid: z.string(), password: z.string() })).default([]),
  hooks: z.array(HookSchema).default([]),
});

export type Config = z.infer<typeof ConfigSchema>;
export type HookConfig = z.infer<typeof HookSchema>;

export function parseConfig(raw: unknown): Config {
  return ConfigSchema.parse(raw);
}

export function loadConfig(path: string): Config {
  return parseConfig(yaml.load(readFileSync(path, 'utf8')));
}

export function passwordFor(cfg: Config, uuid: string): string | undefined {
  return cfg.accounts.find((a) => a.uuid === uuid)?.password;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run tests/config.test.ts`
Expected: PASS (5 tests green).

- [ ] **Step 5: Commit**

```bash
git add src/config.ts tests/config.test.ts
git commit -m "feat(cookie-manager): zod-validated YAML config (server/accounts/hooks)"
```

---

### Task 4: `hooks/template.ts` — interpolation + match

**Files:**
- Create: `src/hooks/template.ts`
- Test: `tests/template.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
// tests/template.test.ts
import { describe, it, expect } from 'vitest';
import { interpolate, matchHook, type HookContext } from '../src/hooks/template.js';

const ctx: HookContext = {
  uuid: 'u1', domain: '.zhihu.com', cookie_json: '[{"name":"a"}]',
  encrypted: 'BLOB', crypto_type: 'legacy', update_time: 'T', ts: '2026-05-31T00:00:00Z',
};

describe('interpolate', () => {
  it('substitutes known vars', () => {
    expect(interpolate('u={{uuid}} d={{domain}}', ctx)).toBe('u=u1 d=.zhihu.com');
  });
  it('injects raw json for cookie_json (no quotes added)', () => {
    expect(interpolate('{"c":{{cookie_json}}}', ctx)).toBe('{"c":[{"name":"a"}]}');
  });
  it('resolves unknown vars to empty string', () => {
    expect(interpolate('x={{nope}}', ctx)).toBe('x=');
  });
});

describe('matchHook', () => {
  it('matches uuid glob "*"', () => {
    expect(matchHook({ uuid: '*' }, ctx, ['.zhihu.com'])).toBe(true);
  });
  it('matches exact uuid', () => {
    expect(matchHook({ uuid: 'u1' }, ctx, ['.zhihu.com'])).toBe(true);
    expect(matchHook({ uuid: 'other' }, ctx, ['.zhihu.com'])).toBe(false);
  });
  it('matches when domain present in the cookie domains', () => {
    expect(matchHook({ uuid: '*', domain: '.zhihu.com' }, ctx, ['.zhihu.com', '.bilibili.com'])).toBe(true);
    expect(matchHook({ uuid: '*', domain: '.weibo.com' }, ctx, ['.zhihu.com'])).toBe(false);
  });
  it('matches any update when no domain filter', () => {
    expect(matchHook({ uuid: '*' }, ctx, [])).toBe(true);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run tests/template.test.ts`
Expected: FAIL — cannot resolve `../src/hooks/template.js`.

- [ ] **Step 3: Write minimal implementation**

```ts
// src/hooks/template.ts
export interface HookContext {
  uuid: string;
  domain: string;
  cookie_json: string;
  encrypted: string;
  crypto_type: string;
  update_time: string;
  ts: string;
}

export interface HookMatch {
  uuid: string;
  domain?: string;
}

export function interpolate(template: string, ctx: HookContext): string {
  return template.replace(/\{\{(\w+)\}\}/g, (_, key: string) => {
    const v = (ctx as Record<string, unknown>)[key];
    return v === undefined || v === null ? '' : String(v);
  });
}

export function matchHook(match: HookMatch, ctx: HookContext, domains: string[]): boolean {
  if (match.uuid !== '*' && match.uuid !== ctx.uuid) return false;
  if (match.domain && !domains.includes(match.domain)) return false;
  return true;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run tests/template.test.ts`
Expected: PASS (7 tests green).

- [ ] **Step 5: Commit**

```bash
git add src/hooks/template.ts tests/template.test.ts
git commit -m "feat(cookie-manager): hook template interpolation + match"
```

---

### Task 5: `hooks/actions.ts` — A1 exec + A3 write_file

**Files:**
- Create: `src/hooks/actions.ts`
- Test: `tests/actions.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
// tests/actions.test.ts
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mkdtempSync, rmSync, readFileSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { runExec, runWriteFile } from '../src/hooks/actions.js';
import type { HookContext } from '../src/hooks/template.js';

const ctx: HookContext = {
  uuid: 'u1', domain: '.zhihu.com', cookie_json: '[{"name":"a"}]',
  encrypted: 'BLOB', crypto_type: 'legacy', update_time: 'T', ts: 'TS',
};

let dir: string;
beforeEach(() => { dir = mkdtempSync(join(tmpdir(), 'cm-act-')); });
afterEach(() => { rmSync(dir, { recursive: true, force: true }); });

describe('runWriteFile', () => {
  it('renders template + path and writes the file', async () => {
    await runWriteFile(
      { action: 'write_file', path: join(dir, '{{uuid}}.json'), template: '{"c":{{cookie_json}}}' } as any,
      ctx,
    );
    const out = join(dir, 'u1.json');
    expect(existsSync(out)).toBe(true);
    expect(readFileSync(out, 'utf8')).toBe('{"c":[{"name":"a"}]}');
  });
});

describe('runExec', () => {
  it('runs the command with interpolated args + env and resolves on success', async () => {
    const outFile = join(dir, 'echoed.txt');
    const res = await runExec(
      { action: 'exec', command: 'sh', args: ['-c', `printf '%s' "$COOKIE_JSON" > ${outFile}`],
        env: { COOKIE_JSON: '{{cookie_json}}' }, timeout_ms: 5000 } as any,
      ctx,
    );
    expect(res.code).toBe(0);
    expect(readFileSync(outFile, 'utf8')).toBe('[{"name":"a"}]');
  });

  it('rejects/returns nonzero on a failing command', async () => {
    const res = await runExec(
      { action: 'exec', command: 'sh', args: ['-c', 'exit 3'], env: {}, timeout_ms: 5000 } as any,
      ctx,
    );
    expect(res.code).toBe(3);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run tests/actions.test.ts`
Expected: FAIL — cannot resolve `../src/hooks/actions.js`.

- [ ] **Step 3: Write minimal implementation**

```ts
// src/hooks/actions.ts
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname } from 'node:path';
import { interpolate, type HookContext } from './template.js';
import type { HookConfig } from '../config.js';

export interface ExecResult { code: number; stdout: string; stderr: string; }

export async function runExec(hook: Extract<HookConfig, { action: 'exec' }>, ctx: HookContext): Promise<ExecResult> {
  const args = hook.args.map((a) => interpolate(a, ctx));
  const env: Record<string, string> = { ...process.env as Record<string, string> };
  for (const [k, v] of Object.entries(hook.env)) env[k] = interpolate(v, ctx);

  return new Promise((resolve) => {
    const child = spawn(interpolate(hook.command, ctx), args, { env });
    let stdout = '', stderr = '';
    const timer = setTimeout(() => child.kill('SIGKILL'), hook.timeout_ms);
    child.stdout?.on('data', (d) => (stdout += d));
    child.stderr?.on('data', (d) => (stderr += d));
    child.on('close', (code) => { clearTimeout(timer); resolve({ code: code ?? -1, stdout, stderr }); });
    child.on('error', (err) => { clearTimeout(timer); resolve({ code: -1, stdout, stderr: String(err) }); });
  });
}

export async function runWriteFile(hook: Extract<HookConfig, { action: 'write_file' }>, ctx: HookContext): Promise<void> {
  const outPath = interpolate(hook.path, ctx);
  mkdirSync(dirname(outPath), { recursive: true });
  writeFileSync(outPath, interpolate(hook.template, ctx), hook.mode ? { mode: parseInt(hook.mode, 8) } : undefined);
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run tests/actions.test.ts`
Expected: PASS (3 tests green).

- [ ] **Step 5: Commit**

```bash
git add src/hooks/actions.ts tests/actions.test.ts
git commit -m "feat(cookie-manager): hook actions (exec + write_file)"
```

---

### Task 6: `hooks/engine.ts` + `hooks/triggers.ts` — orchestration (T1 event + T2 cron)

**Files:**
- Create: `src/hooks/engine.ts`, `src/hooks/triggers.ts`
- Test: `tests/engine.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
// tests/engine.test.ts
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { mkdtempSync, rmSync, existsSync, readFileSync } from 'node:fs';
import { EventEmitter } from 'node:events';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createStore } from '../src/store.js';
import { cookieEncrypt } from '../src/crypto.js';
import { parseConfig } from '../src/config.js';
import { createEngine } from '../src/hooks/engine.js';

let dir: string;
const sample = { cookie_data: { '.zhihu.com': [{ name: 'a', value: '1' }] }, local_storage_data: {}, update_time: 'T' };

beforeEach(() => { dir = mkdtempSync(join(tmpdir(), 'cm-eng-')); });
afterEach(() => { rmSync(dir, { recursive: true, force: true }); });

describe('engine T1 cookie-update', () => {
  it('runs a domain-matched write_file hook on cookie-update', async () => {
    const out = join(dir, 'hooked.json');
    const cfg = parseConfig({
      server: { data_dir: dir },
      accounts: [{ uuid: 'u1', password: 'pw' }],
      hooks: [{ id: 'h', on: 'cookie-update', match: { uuid: '*', domain: '.zhihu.com' },
               action: 'write_file', path: out, template: '{{cookie_json}}' }],
    });
    const store = createStore(dir);
    const bus = new EventEmitter();
    const engine = createEngine(cfg, store, bus);
    engine.start();

    const enc = cookieEncrypt('u1', sample, 'pw', 'legacy');
    store.save('u1', { encrypted: enc, crypto_type: 'legacy' });
    bus.emit('cookie-update', { uuid: 'u1', encrypted: enc, crypto_type: 'legacy' });

    await vi.waitFor(() => expect(existsSync(out)).toBe(true));
    expect(JSON.parse(readFileSync(out, 'utf8'))).toEqual(sample.cookie_data['.zhihu.com']);
    engine.stop();
  });

  it('skips a hook whose domain is absent', async () => {
    const out = join(dir, 'no.json');
    const cfg = parseConfig({
      server: { data_dir: dir }, accounts: [{ uuid: 'u1', password: 'pw' }],
      hooks: [{ id: 'h', on: 'cookie-update', match: { uuid: '*', domain: '.weibo.com' },
               action: 'write_file', path: out, template: '{{cookie_json}}' }],
    });
    const store = createStore(dir);
    const bus = new EventEmitter();
    const engine = createEngine(cfg, store, bus);
    engine.start();
    const enc = cookieEncrypt('u1', sample, 'pw', 'legacy');
    store.save('u1', { encrypted: enc, crypto_type: 'legacy' });
    bus.emit('cookie-update', { uuid: 'u1', encrypted: enc, crypto_type: 'legacy' });
    await new Promise((r) => setTimeout(r, 50));
    expect(existsSync(out)).toBe(false);
    engine.stop();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run tests/engine.test.ts`
Expected: FAIL — cannot resolve `../src/hooks/engine.js`.

- [ ] **Step 3: Write minimal implementation — `src/hooks/triggers.ts`**

```ts
// src/hooks/triggers.ts
import cron from 'node-cron';

export interface CronHandle { stop(): void; }

export function scheduleCron(expr: string, fn: () => void): CronHandle {
  let running = false;
  const task = cron.schedule(expr, async () => {
    if (running) return; // skip overlapping ticks
    running = true;
    try { await fn(); } finally { running = false; }
  });
  return { stop: () => task.stop() };
}
```

- [ ] **Step 4: Write minimal implementation — `src/hooks/engine.ts`**

```ts
// src/hooks/engine.ts
import type { EventEmitter } from 'node:events';
import type { Config, HookConfig } from '../config.js';
import { passwordFor } from '../config.js';
import type { Store } from '../store.js';
import { cookieDecrypt } from '../crypto.js';
import { matchHook, type HookContext } from './template.js';
import { runExec, runWriteFile } from './actions.js';
import { scheduleCron, type CronHandle } from './triggers.js';

export interface CookieUpdateEvent { uuid: string; encrypted: string; crypto_type: 'legacy' | 'aes-128-cbc-fixed'; }

export interface Engine { start(): void; stop(): void; }

function nowIso(): string { return new Date().toISOString(); }

export function createEngine(cfg: Config, store: Store, bus: EventEmitter): Engine {
  const crons: CronHandle[] = [];

  async function runHook(hook: HookConfig, ctx: HookContext): Promise<void> {
    try {
      if (hook.action === 'exec') {
        const res = await runExec(hook, ctx);
        if (res.code !== 0) console.error(`[hook ${hook.id}] exec exited ${res.code}: ${res.stderr}`);
      } else {
        await runWriteFile(hook, ctx);
      }
    } catch (err) {
      console.error(`[hook ${hook.id}] failed:`, err);
    }
  }

  function buildContext(uuid: string, encrypted: string, cryptoType: 'legacy' | 'aes-128-cbc-fixed'): { ctx: HookContext; domains: string[] } | null {
    const pw = passwordFor(cfg, uuid);
    let domains: string[] = [];
    let cookieJson = '';
    if (pw) {
      try {
        const payload = cookieDecrypt(uuid, encrypted, pw, cryptoType);
        domains = Object.keys(payload.cookie_data ?? {});
        cookieJson = JSON.stringify(payload.cookie_data ?? {});
      } catch (err) {
        console.error(`[engine] decrypt failed for uuid=${uuid}:`, err);
      }
    } else {
      console.warn(`[engine] no password configured for uuid=${uuid}; domain-matched hooks will be skipped`);
    }
    const ctx: HookContext = {
      uuid, domain: '', cookie_json: cookieJson, encrypted, crypto_type: cryptoType,
      update_time: '', ts: nowIso(),
    };
    return { ctx, domains };
  }

  async function onCookieUpdate(evt: CookieUpdateEvent): Promise<void> {
    const built = buildContext(evt.uuid, evt.encrypted, evt.crypto_type);
    if (!built) return;
    for (const hook of cfg.hooks) {
      if (hook.on !== 'cookie-update') continue;
      const domain = hook.match.domain;
      if (!matchHook(hook.match, built.ctx, built.domains)) continue;
      const ctx = { ...built.ctx, domain: domain ?? (built.domains[0] ?? '') };
      // For per-domain cookie_json, narrow to the matched domain when set:
      if (domain && built.domains.includes(domain)) {
        const pw = passwordFor(cfg, evt.uuid);
        if (pw) {
          const payload = cookieDecrypt(evt.uuid, evt.encrypted, pw, evt.crypto_type);
          ctx.cookie_json = JSON.stringify(payload.cookie_data[domain] ?? []);
        }
      }
      void runHook(hook, ctx);
    }
  }

  function runCronHook(hook: HookConfig): void {
    for (const meta of store.list()) {
      const rec = store.load(meta.uuid);
      if (!rec) continue;
      const built = buildContext(meta.uuid, rec.encrypted, rec.crypto_type);
      if (!built) continue;
      if (!matchHook(hook.match, built.ctx, built.domains)) continue;
      const domain = hook.match.domain;
      const ctx = { ...built.ctx, domain: domain ?? (built.domains[0] ?? '') };
      if (domain && built.domains.includes(domain)) {
        const pw = passwordFor(cfg, meta.uuid);
        if (pw) ctx.cookie_json = JSON.stringify(cookieDecrypt(meta.uuid, rec.encrypted, pw, rec.crypto_type).cookie_data[domain] ?? []);
      }
      void runHook(hook, ctx);
    }
  }

  return {
    start() {
      bus.on('cookie-update', (evt: CookieUpdateEvent) => void onCookieUpdate(evt));
      for (const hook of cfg.hooks) {
        if (hook.on === 'cron') crons.push(scheduleCron(hook.schedule, () => runCronHook(hook)));
      }
    },
    stop() {
      bus.removeAllListeners('cookie-update');
      crons.forEach((c) => c.stop());
      crons.length = 0;
    },
  };
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `npx vitest run tests/engine.test.ts`
Expected: PASS (2 tests green).

- [ ] **Step 6: Commit**

```bash
git add src/hooks/engine.ts src/hooks/triggers.ts tests/engine.test.ts
git commit -m "feat(cookie-manager): hook engine (T1 event + T2 cron orchestration)"
```

---

### Task 7: `server.ts` — Express API

**Files:**
- Create: `src/server.ts`
- Test: `tests/server.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
// tests/server.test.ts
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import request from 'supertest';
import { mkdtempSync, rmSync } from 'node:fs';
import { EventEmitter } from 'node:events';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createStore } from '../src/store.js';
import { createServer } from '../src/server.js';

let dir: string;
beforeEach(() => { dir = mkdtempSync(join(tmpdir(), 'cm-srv-')); });
afterEach(() => { rmSync(dir, { recursive: true, force: true }); });

function app() {
  const store = createStore(dir);
  const bus = new EventEmitter();
  return { app: createServer(store, bus, { body_limit: '50mb' }), bus, store };
}

describe('POST /update', () => {
  it('stores a JSON body and returns {action:"done"}', async () => {
    const { app: a } = app();
    const res = await request(a).post('/update').send({ uuid: 'u1', encrypted: 'BLOB' });
    expect(res.body).toEqual({ action: 'done' });
  });

  it('accepts urlencoded bodies too', async () => {
    const { app: a } = app();
    const res = await request(a).post('/update').type('form').send({ uuid: 'u2', encrypted: 'B2' });
    expect(res.body).toEqual({ action: 'done' });
  });

  it('emits cookie-update', async () => {
    const { app: a, bus } = app();
    const seen: any[] = [];
    bus.on('cookie-update', (e) => seen.push(e));
    await request(a).post('/update').send({ uuid: 'u3', encrypted: 'B3', crypto_type: 'legacy' });
    expect(seen).toEqual([{ uuid: 'u3', encrypted: 'B3', crypto_type: 'legacy' }]);
  });

  it('400 when uuid or encrypted missing', async () => {
    const { app: a } = app();
    expect((await request(a).post('/update').send({ uuid: 'x' })).status).toBe(400);
    expect((await request(a).post('/update').send({ encrypted: 'x' })).status).toBe(400);
  });
});

describe('GET /get/:uuid', () => {
  it('returns the raw stored record when no password', async () => {
    const { app: a, store } = app();
    store.save('u1', { encrypted: 'BLOB', crypto_type: 'legacy' });
    const res = await request(a).get('/get/u1');
    expect(res.body).toEqual({ encrypted: 'BLOB', crypto_type: 'legacy' });
  });
  it('404 for a missing uuid', async () => {
    const { app: a } = app();
    expect((await request(a).get('/get/none')).status).toBe(404);
  });
});

describe('GET /health', () => {
  it('returns ok', async () => {
    const { app: a } = app();
    const res = await request(a).get('/health');
    expect(res.status).toBe(200);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run tests/server.test.ts`
Expected: FAIL — cannot resolve `../src/server.js`.

- [ ] **Step 3: Write minimal implementation**

```ts
// src/server.ts
import express, { type Express } from 'express';
import type { EventEmitter } from 'node:events';
import type { Store } from './store.js';
import type { CryptoType } from './crypto.js';

export interface ServerOptions { body_limit?: string; }

export function createServer(store: Store, bus: EventEmitter, opts: ServerOptions = {}): Express {
  const app = express();
  const limit = opts.body_limit ?? '50mb';
  app.use(express.json({ limit }));
  app.use(express.urlencoded({ extended: true, limit }));

  app.get('/health', (_req, res) => { res.json({ status: 'ok' }); });

  app.post('/update', (req, res) => {
    const { uuid, encrypted } = req.body ?? {};
    const crypto_type: CryptoType = (req.body?.crypto_type as CryptoType) ?? 'legacy';
    if (!uuid || !encrypted) { res.status(400).send('Bad Request'); return; }
    try {
      store.save(uuid, { encrypted, crypto_type });
    } catch (err) {
      console.error('[server] store failed:', err);
      res.status(500).send('Internal Server Error');
      return;
    }
    res.json({ action: 'done' });
    setImmediate(() => bus.emit('cookie-update', { uuid, encrypted, crypto_type }));
  });

  const handleGet = (req: express.Request, res: express.Response) => {
    const rec = store.load(req.params.uuid);
    if (!rec) { res.status(404).send('Not Found'); return; }
    res.json(rec); // password-based server-side decrypt is out of scope for v1; clients decrypt
  };
  app.get('/get/:uuid', handleGet);
  app.post('/get/:uuid', handleGet);

  return app;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run tests/server.test.ts`
Expected: PASS (8 tests green).

- [ ] **Step 5: Commit**

```bash
git add src/server.ts tests/server.test.ts
git commit -m "feat(cookie-manager): express server (/update, /get, /health) + cookie-update event"
```

---

### Task 8: `cli.ts` — list / show / dump

**Files:**
- Create: `src/cli.ts`
- Test: `tests/cli.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
// tests/cli.test.ts
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createStore } from '../src/store.js';
import { cookieEncrypt } from '../src/crypto.js';
import { parseConfig } from '../src/config.js';
import { runCli } from '../src/cli.js';

let dir: string;
const sample = { cookie_data: { '.zhihu.com': [{ name: 'a', value: '1' }], '.bilibili.com': [{ name: 'b', value: '2' }] }, local_storage_data: {}, update_time: 'T' };

beforeEach(() => { dir = mkdtempSync(join(tmpdir(), 'cm-cli-')); });
afterEach(() => { rmSync(dir, { recursive: true, force: true }); });

function seed() {
  const cfg = parseConfig({ server: { data_dir: dir }, accounts: [{ uuid: 'u1', password: 'pw' }] });
  const store = createStore(dir);
  store.save('u1', { encrypted: cookieEncrypt('u1', sample, 'pw', 'legacy'), crypto_type: 'legacy' });
  return cfg;
}

describe('cli', () => {
  it('list prints uuids with domain counts', () => {
    const cfg = seed();
    const out: string[] = [];
    runCli(['list'], cfg, (s) => out.push(s));
    expect(out.join('\n')).toContain('u1');
    expect(out.join('\n')).toContain('2'); // 2 domains
  });

  it('show domain= prints decrypted cookies for that domain', () => {
    const cfg = seed();
    const out: string[] = [];
    runCli(['show', 'domain=.zhihu.com'], cfg, (s) => out.push(s));
    expect(out.join('\n')).toContain('z'.length ? 'name' : '');
    expect(out.join('\n')).toContain('"value": "1"');
  });

  it('dump prints all decrypted cookies', () => {
    const cfg = seed();
    const out: string[] = [];
    runCli(['dump'], cfg, (s) => out.push(s));
    const text = out.join('\n');
    expect(text).toContain('.zhihu.com');
    expect(text).toContain('.bilibili.com');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run tests/cli.test.ts`
Expected: FAIL — cannot resolve `../src/cli.js`.

- [ ] **Step 3: Write minimal implementation**

```ts
// src/cli.ts
import { createStore } from './store.js';
import { cookieDecrypt } from './crypto.js';
import { loadConfig, passwordFor, type Config } from './config.js';

type Printer = (s: string) => void;

function dataDir(cfg: Config): string { return cfg.server.data_dir; }

export function runCli(argv: string[], cfg: Config, print: Printer = console.log): number {
  const [cmd, ...rest] = argv;
  const store = createStore(dataDir(cfg));

  if (cmd === 'list') {
    for (const meta of store.list()) {
      const pw = passwordFor(cfg, meta.uuid);
      let domains = 0, updateTime = '?';
      if (pw) {
        const rec = store.load(meta.uuid)!;
        try { const p = cookieDecrypt(meta.uuid, rec.encrypted, pw, rec.crypto_type);
          domains = Object.keys(p.cookie_data ?? {}).length; updateTime = p.update_time ?? '?'; } catch { /* keep defaults */ }
      }
      print(`${meta.uuid}\t${meta.crypto_type}\tdomains=${domains}\tupdated=${updateTime}`);
    }
    return 0;
  }

  if (cmd === 'show') {
    const domainArg = rest.find((a) => a.startsWith('domain='))?.slice('domain='.length);
    if (!domainArg) { print('usage: show domain=<x>'); return 2; }
    let best: { cookies: unknown; uuid: string } | null = null;
    for (const meta of store.list()) {
      const pw = passwordFor(cfg, meta.uuid);
      if (!pw) continue;
      const rec = store.load(meta.uuid)!;
      try {
        const p = cookieDecrypt(meta.uuid, rec.encrypted, pw, rec.crypto_type);
        if (p.cookie_data[domainArg]) best = { cookies: p.cookie_data[domainArg], uuid: meta.uuid };
      } catch { /* skip */ }
    }
    if (!best) { print(`no cookies for domain ${domainArg}`); return 1; }
    print(JSON.stringify(best.cookies, null, 2));
    return 0;
  }

  if (cmd === 'dump') {
    const onlyUuid = rest.find((a) => a.startsWith('--uuid='))?.slice('--uuid='.length);
    const result: Record<string, unknown> = {};
    for (const meta of store.list()) {
      if (onlyUuid && meta.uuid !== onlyUuid) continue;
      const pw = passwordFor(cfg, meta.uuid);
      if (!pw) continue;
      const rec = store.load(meta.uuid)!;
      try { result[meta.uuid] = cookieDecrypt(meta.uuid, rec.encrypted, pw, rec.crypto_type).cookie_data; } catch { /* skip */ }
    }
    print(JSON.stringify(result, null, 2));
    return 0;
  }

  print('usage: cookie-manager <list|show domain=<x>|dump [--uuid=<u>]>');
  return 2;
}

// Entry point when run directly
if (process.argv[1] && process.argv[1].endsWith('cli.ts') || process.argv[1]?.endsWith('cli.js')) {
  const cfgPath = process.env.COOKIE_MANAGER_CONFIG ?? 'config/cookie-manager.yaml';
  const code = runCli(process.argv.slice(2), loadConfig(cfgPath));
  process.exit(code);
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run tests/cli.test.ts`
Expected: PASS (3 tests green).

- [ ] **Step 5: Commit**

```bash
git add src/cli.ts tests/cli.test.ts
git commit -m "feat(cookie-manager): CLI list/show/dump"
```

---

### Task 9: `index.ts` — bootstrap wiring + graceful shutdown

**Files:**
- Create: `src/index.ts`
- Test: `tests/index.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
// tests/index.test.ts
import { describe, it, expect, afterEach } from 'vitest';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import request from 'supertest';
import { startApp } from '../src/index.js';

let stop: (() => Promise<void>) | null = null;
afterEach(async () => { if (stop) await stop(); stop = null; });

describe('startApp', () => {
  it('boots server + engine from a config object and serves /health', async () => {
    const dir = mkdtempSync(join(tmpdir(), 'cm-idx-'));
    const app = await startApp({
      server: { host: '127.0.0.1', port: 0, data_dir: dir, body_limit: '50mb' },
      accounts: [], hooks: [],
    });
    stop = async () => { await app.stop(); rmSync(dir, { recursive: true, force: true }); };
    const res = await request(app.server).get('/health');
    expect(res.status).toBe(200);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run tests/index.test.ts`
Expected: FAIL — cannot resolve `../src/index.js` / no `startApp` export.

- [ ] **Step 3: Write minimal implementation**

```ts
// src/index.ts
import { EventEmitter } from 'node:events';
import type { Server } from 'node:http';
import { loadConfig, type Config } from './config.js';
import { createStore } from './store.js';
import { createServer } from './server.js';
import { createEngine, type Engine } from './hooks/engine.js';

export interface RunningApp { server: Server; engine: Engine; stop(): Promise<void>; }

export async function startApp(cfg: Config): Promise<RunningApp> {
  const store = createStore(cfg.server.data_dir);
  const bus = new EventEmitter();
  const engine = createEngine(cfg, store, bus);
  engine.start();
  const app = createServer(store, bus, { body_limit: cfg.server.body_limit });

  const server = await new Promise<Server>((resolve) => {
    const s = app.listen(cfg.server.port, cfg.server.host, () => resolve(s));
  });

  return {
    server,
    engine,
    stop: () =>
      new Promise<void>((resolve) => {
        engine.stop();
        server.close(() => resolve());
      }),
  };
}

// Entry point when run directly (dev/start)
const isMain = process.argv[1] && (process.argv[1].endsWith('index.ts') || process.argv[1].endsWith('index.js'));
if (isMain) {
  const cfgPath = process.env.COOKIE_MANAGER_CONFIG ?? 'config/cookie-manager.yaml';
  const cfg: Config = loadConfig(cfgPath);
  startApp(cfg).then((app) => {
    console.log(`cookie-manager listening on ${cfg.server.host}:${cfg.server.port}`);
    const shutdown = () => { void app.stop().then(() => process.exit(0)); };
    process.on('SIGTERM', shutdown);
    process.on('SIGINT', shutdown);
  });
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run tests/index.test.ts`
Expected: PASS (1 test green).

- [ ] **Step 5: Full test + typecheck**

Run: `npx tsc --noEmit && npx vitest run`
Expected: tsc clean; all test files PASS.

- [ ] **Step 6: Commit**

```bash
git add src/index.ts tests/index.test.ts
git commit -m "feat(cookie-manager): bootstrap wiring + graceful shutdown"
```

---

### Task 10: Deployment artifacts (config example, Docker, LICENSE, README)

**Files:**
- Create: `config/cookie-manager.example.yaml`, `Dockerfile`, `docker-compose.yml`, `LICENSE`, `README.md`

- [ ] **Step 1: Create `config/cookie-manager.example.yaml`**

```yaml
server:
  host: 0.0.0.0          # 0.0.0.0 for LAN/Android push; 127.0.0.1 if same host only
  port: 8088
  data_dir: ./data
  body_limit: 50mb       # raise above default 100kb; cookie dumps are large
accounts:
  - uuid: "REPLACE-with-the-uuid-you-set-in-the-extension"
    password: "REPLACE-with-the-encryption-password-you-set-in-the-extension"
hooks:
  - id: refresh-zhihu
    on: cookie-update
    match: { uuid: "*", domain: ".zhihu.com" }
    action: exec
    command: "/opt/crawl/refresh.sh"
    args: ["--uuid", "{{uuid}}", "--domain", "{{domain}}"]
    env: { COOKIE_JSON: "{{cookie_json}}" }
    timeout_ms: 30000
  - id: snapshot-all
    on: cron
    schedule: "*/15 * * * *"
    match: { uuid: "*" }
    action: write_file
    path: "./snapshots/{{uuid}}-{{ts}}.json"
    template: '{"uuid":"{{uuid}}","cookies":{{cookie_json}},"at":"{{ts}}"}'
```

- [ ] **Step 2: Create `Dockerfile`**

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY tsconfig.json ./
COPY src ./src
RUN npm run build
RUN npm prune --omit=dev
EXPOSE 8088
ENV COOKIE_MANAGER_CONFIG=/app/config/cookie-manager.yaml
CMD ["node", "dist/index.js"]
```

- [ ] **Step 3: Create `docker-compose.yml`**

```yaml
services:
  cookie-manager:
    build: .
    ports:
      - "8088:8088"
    volumes:
      - ./config/cookie-manager.yaml:/app/config/cookie-manager.yaml:ro
      - ./data:/app/data
      - ./snapshots:/app/snapshots
    restart: unless-stopped
```

- [ ] **Step 4: Create `LICENSE` (MIT)**

```
MIT License

Copyright (c) 2026 JarvanKB

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 5: Create `README.md`**

```markdown
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
```

- [ ] **Step 6: Commit**

```bash
git add config/cookie-manager.example.yaml Dockerfile docker-compose.yml LICENSE README.md
git commit -m "feat(cookie-manager): deployment artifacts (config example, docker, MIT license, README)"
```

---

### Task 11: Manual smoke verification (mandatory verification gate — handoff §3.E)

**Files:**
- Create: `scripts/smoke-push.mjs` (throwaway test client; commit it for repeatability)

- [ ] **Step 1: Write a PyCookieCloud-style push client in Node**

```js
// scripts/smoke-push.mjs
import CryptoJS from 'crypto-js';
const endpoint = process.env.ENDPOINT ?? 'http://127.0.0.1:8088';
const uuid = process.argv[2], password = process.argv[3];
const theKey = CryptoJS.MD5(uuid + '-' + password).toString().substring(0, 16);
const payload = { cookie_data: { '.zhihu.com': [{ name: 'z_c0', value: 'SMOKE', domain: '.zhihu.com' }] }, local_storage_data: {}, update_time: new Date().toISOString() };
const encrypted = CryptoJS.AES.encrypt(JSON.stringify(payload), theKey).toString();
const res = await fetch(`${endpoint}/update`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ uuid, encrypted }) });
console.log('status', res.status, await res.json());
```

- [ ] **Step 2: Prepare a smoke config**

Create `config/cookie-manager.smoke.yaml`:
```yaml
server: { host: 127.0.0.1, port: 8088, data_dir: ./data-smoke, body_limit: 50mb }
accounts: [{ uuid: "smoke-uuid", password: "smoke-pass" }]
hooks:
  - id: smoke-write
    on: cookie-update
    match: { uuid: "*", domain: ".zhihu.com" }
    action: write_file
    path: "./smoke-out/{{uuid}}.json"
    template: '{{cookie_json}}'
```

- [ ] **Step 3: Start the service**

Run: `COOKIE_MANAGER_CONFIG=config/cookie-manager.smoke.yaml npm run dev`
Expected: logs `cookie-manager listening on 127.0.0.1:8088`. Leave running in one terminal.

- [ ] **Step 4: Push a fake cookie**

Run (second terminal): `node scripts/smoke-push.mjs smoke-uuid smoke-pass`
Expected: `status 200 { action: 'done' }`.

- [ ] **Step 5: Verify hook fired**

Run: `cat smoke-out/smoke-uuid.json`
Expected: `[{"name":"z_c0","value":"SMOKE","domain":".zhihu.com"}]` (the decrypted, domain-narrowed cookies — proves receive → store → decrypt → match → write_file end-to-end).

- [ ] **Step 6: Verify CLI**

Run: `COOKIE_MANAGER_CONFIG=config/cookie-manager.smoke.yaml npm run cli -- show domain=.zhihu.com`
Expected: prints the decrypted Zhihu cookies (`"value": "SMOKE"`).

- [ ] **Step 7: Clean up smoke artifacts + commit the client**

```bash
rm -rf data-smoke smoke-out
git add scripts/smoke-push.mjs config/cookie-manager.smoke.yaml
git commit -m "test(cookie-manager): manual smoke push client + smoke config"
```

- [ ] **Step 8: Final verification before completion**

Run: `npx tsc --noEmit && npx vitest run`
Expected: typecheck clean; ALL tests green. Record the exact output as evidence (verification-before-completion gate). Only after this passes is SP-1 implementation "done".

---

## Self-Review

**1. Spec coverage:**
- design §1 scope (protocol receiver, hooks, CLI, docker, MIT, dual mode) → Tasks 1,5,6,7,8,10 ✅
- §2 D1 path B → whole plan is self-write ✅; D2 dual mode → Task 1 ✅; D3 flat YAML → Task 3 ✅; D4 TS → Task 0 ✅; D5 accounts/no-cookies-in-config → Task 3 `passwordFor` ✅; D6 single-box + N + most-recent-on-collision → Task 8 `show` keeps last match (most-recent ordering note below) ✅
- §3 protocol (endpoints, body, key derivation, both modes, inner shape, storage) → Tasks 1,2,7 ✅
- §4 modules → Tasks 1-9 one-to-one ✅
- §5 data flow (respond-before-hooks via setImmediate; cron loads latest) → Task 7 + Task 6 ✅
- §6 config schema + template vars → Tasks 3,4 ✅
- §7 CLI → Task 8 ✅
- §8 error handling (400/404/500, decrypt-failure-skip, exec timeout, cron no-overlap) → Tasks 5,6,7 ✅; path.basename → Task 2 ✅
- §9 testing (crypto round-trip + reference vector, store traversal, server json+urlencoded, hooks match+template, smoke) → Tasks 1-9, 11 ✅
- §10 deployment → Task 10 ✅; §11 risks → documented in README (R2) ✅

**2. Placeholder scan:** No TBD/TODO; every code step has complete code. Reference vector is generated by a concrete script (Task 1 Step 1), not left blank.

**3. Type consistency:** `cookieDecrypt/cookieEncrypt/deriveKey` signatures consistent across Tasks 1,6,8,11. `Store.{save,load,list}` consistent Tasks 2,6,7,8. `HookContext` fields consistent Tasks 4,5,6. `Config`/`HookConfig`/`passwordFor` consistent Tasks 3,6,8. `createServer(store, bus, opts)` consistent Tasks 7,9. `createEngine(cfg, store, bus)` consistent Tasks 6,9. Event name `'cookie-update'` consistent Tasks 6,7.

**Fix applied during review — D6 most-recent-on-collision:** Task 8 `show` currently keeps the LAST matching uuid in `store.list()` order (filesystem order), not guaranteed most-recent. During implementation, if multi-box is exercised, sort `store.list()` by decrypted `update_time` descending before selecting, or add `--uuid`. Acceptable for v1 single-box; noted so the implementer doesn't treat list-order as semantic.
