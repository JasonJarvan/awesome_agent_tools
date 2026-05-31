import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { mkdtempSync, rmSync, existsSync, readFileSync } from 'node:fs';
import { EventEmitter } from 'node:events';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createStore } from '../src/store.js';
import { cookieEncrypt } from '../src/crypto.js';
import { parseConfig } from '../src/config.js';
import { createEngine } from '../src/hooks/engine.js';

// Increase default timeout for async tests
vi.setConfig({ testTimeout: 5000 });

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

  it('renders {{update_time}} from payload (FIX 1)', async () => {
    const out = join(dir, 'update-time.txt');
    const cfg = parseConfig({
      server: { data_dir: dir },
      accounts: [{ uuid: 'u1', password: 'pw' }],
      hooks: [{ id: 'h2', on: 'cookie-update', match: { uuid: '*', domain: '.zhihu.com' },
               action: 'write_file', path: out, template: '{{update_time}}' }],
    });
    const store = createStore(dir);
    const bus = new EventEmitter();
    const engine = createEngine(cfg, store, bus);
    engine.start();

    const enc = cookieEncrypt('u1', sample, 'pw', 'legacy');
    store.save('u1', { encrypted: enc, crypto_type: 'legacy' });
    bus.emit('cookie-update', { uuid: 'u1', encrypted: enc, crypto_type: 'legacy' });

    await vi.waitFor(() => expect(existsSync(out)).toBe(true));
    expect(readFileSync(out, 'utf8')).toBe(sample.update_time);
    engine.stop();
  });
});

describe('engine T2 cron', () => {
  it('fires a cron hook and writes cookie_json end-to-end (FIX 2)', async () => {
    const out = join(dir, 'cron-out.json');
    const cfg = parseConfig({
      server: { data_dir: dir },
      accounts: [{ uuid: 'u2', password: 'pw2' }],
      hooks: [{ id: 'hcron', on: 'cron', schedule: '*/1 * * * * *', match: { uuid: '*' },
               action: 'write_file', path: out, template: '{{cookie_json}}' }],
    });
    const store = createStore(dir);
    const bus = new EventEmitter();

    const enc = cookieEncrypt('u2', sample, 'pw2', 'legacy');
    store.save('u2', { encrypted: enc, crypto_type: 'legacy' });

    const engine = createEngine(cfg, store, bus);
    engine.start();

    await vi.waitFor(() => expect(existsSync(out)).toBe(true), { timeout: 3000, interval: 100 });
    const written = JSON.parse(readFileSync(out, 'utf8'));
    expect(written).toEqual(sample.cookie_data);

    engine.stop();
  });
});
