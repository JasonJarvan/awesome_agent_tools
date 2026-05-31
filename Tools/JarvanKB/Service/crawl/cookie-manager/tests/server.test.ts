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

describe('header auth (when auth_token is set)', () => {
  function authApp() {
    const store = createStore(dir);
    const bus = new EventEmitter();
    return createServer(store, bus, { body_limit: '50mb', auth_token: 'sEcReT', auth_header: 'X-CookieCloud-Token' });
  }
  it('401 on /update without the token header', async () => {
    expect((await request(authApp()).post('/update').send({ uuid: 'u', encrypted: 'B' })).status).toBe(401);
  });
  it('accepts /update with the correct token header', async () => {
    const res = await request(authApp()).post('/update').set('X-CookieCloud-Token', 'sEcReT').send({ uuid: 'u', encrypted: 'B' });
    expect(res.body).toEqual({ action: 'done' });
  });
  it('401 on a wrong token', async () => {
    expect((await request(authApp()).post('/update').set('X-CookieCloud-Token', 'nope').send({ uuid: 'u', encrypted: 'B' })).status).toBe(401);
  });
  it('401 on /get without the token header', async () => {
    expect((await request(authApp()).get('/get/u')).status).toBe(401);
  });
  it('leaves /health open (no token needed)', async () => {
    expect((await request(authApp()).get('/health')).status).toBe(200);
  });
});

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
    await new Promise((r) => setTimeout(r, 20));
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
