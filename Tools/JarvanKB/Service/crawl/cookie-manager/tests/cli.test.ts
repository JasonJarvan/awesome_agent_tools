import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createStore } from '../src/store.js';
import { cookieEncrypt } from '../src/crypto.js';
import { parseConfig } from '../src/config.js';
import { runCli } from '../src/cli.js';

let dir: string;
const sample = {
  cookie_data: {
    '.zhihu.com': [{ name: 'a', value: '1' }],
    '.bilibili.com': [{ name: 'b', value: '2' }],
  },
  local_storage_data: {},
  update_time: 'T',
};

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
    const text = out.join('\n');
    expect(text).toContain('u1');
    expect(text).toContain('domains=2');
  });

  it('show domain= prints decrypted cookies for that domain', () => {
    const cfg = seed();
    const out: string[] = [];
    runCli(['show', 'domain=.zhihu.com'], cfg, (s) => out.push(s));
    const text = out.join('\n');
    expect(text).toContain('"name": "a"');
    expect(text).toContain('"value": "1"');
    expect(text).not.toContain('.bilibili.com');
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
