import { describe, it, expect, afterEach } from 'vitest';
import { mkdtempSync, rmSync } from 'node:fs';
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
